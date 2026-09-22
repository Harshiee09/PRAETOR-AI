"""`praetor gpu-check`: prove CUDA works and bge-m3 embeds on the GPU, with device, VRAM and timings."""

from __future__ import annotations

import shutil
import subprocess
import time

from app.config import Settings

# Smoke-test inputs only (not legal content). The first three say the same thing in English, Hindi and Tamil,
# so their embeddings should be closer to each other than to the unrelated sentences.
SENTENCES = [
    "Where is the nearest court?",
    "निकटतम न्यायालय कहाँ है?",
    "அருகிலுள்ள நீதிமன்றம் எங்கே?",
    "The train leaves the station at seven in the morning.",
    "Rice and lentils are cooked together in many homes.",
    "The library opens after the holiday.",
    "Rain is expected over the coast this week.",
    "She planted three mango trees in the garden.",
    "The bridge was repainted last year.",
    "A cricket match was played in the evening.",
]


def _nvidia_smi() -> str | None:
    if not shutil.which("nvidia-smi"):
        return None
    out = subprocess.run(
        ["nvidia-smi", "--query-gpu=name,driver_version,memory.total,memory.used", "--format=csv,noheader"],
        capture_output=True, text=True, timeout=30,
    )
    return out.stdout.strip() or out.stderr.strip()


def run(settings: Settings) -> int:
    import torch

    print(f"nvidia-smi       : {_nvidia_smi() or 'not found'}")
    print(f"torch            : {torch.__version__} (CUDA build {torch.version.cuda})")
    ok = torch.cuda.is_available()
    print(f"cuda available   : {ok}")
    if not ok:
        print("FAIL: CUDA is not available to torch. Check the driver and that torch came from a cu128+ index.")
        return 1

    props = torch.cuda.get_device_properties(0)
    print(f"device           : {props.name}, sm_{props.major}{props.minor}, {props.total_memory / 2**30:.2f} GiB")
    print(f"arch list        : {', '.join(torch.cuda.get_arch_list())}")

    a = torch.randn(4096, 4096, device="cuda", dtype=torch.float16)
    for _ in range(5):
        a @ a
    torch.cuda.synchronize()
    n, t0 = 50, time.perf_counter()
    for _ in range(n):
        a @ a
    torch.cuda.synchronize()
    dt = time.perf_counter() - t0
    print(f"fp16 matmul      : {n} x 4096^2 in {dt:.3f}s = {n * 2 * 4096**3 / dt / 1e12:.1f} TFLOPS")
    del a
    torch.cuda.empty_cache()
    torch.cuda.reset_peak_memory_stats()

    from app.embeddings.embedder import Embedder

    emb = Embedder(settings.embed_model, device="cuda", batch_size=settings.embed_batch_size)
    t0 = time.perf_counter()
    emb.encode(["warm-up"])
    load_s = time.perf_counter() - t0
    t0 = time.perf_counter()
    vecs = emb.encode(SENTENCES)
    torch.cuda.synchronize()
    enc_s = time.perf_counter() - t0
    norms = (vecs**2).sum(axis=1) ** 0.5
    sims = vecs @ vecs.T
    cross_lingual = min(sims[0, 1], sims[0, 2])
    unrelated = max(sims[0, 3:])
    print(f"embed model      : {settings.embed_model} on {emb.device}, dim {vecs.shape[1]}")
    print(f"load + warm-up   : {load_s:.1f}s")
    print(f"embed 10 texts   : {enc_s * 1000:.0f} ms")
    print(f"norms            : min {norms.min():.4f}, max {norms.max():.4f}")
    print(f"cosine en~hi/ta  : {cross_lingual:.3f} (min)  vs unrelated: {unrelated:.3f} (max)")
    print(f"peak VRAM (torch): {torch.cuda.max_memory_allocated() / 2**30:.2f} GiB")

    failures = []
    if emb.device != "cuda":
        failures.append("embedding did not run on CUDA")
    if vecs.shape[1] != 1024:
        failures.append(f"expected dim 1024, got {vecs.shape[1]}")
    if abs(norms.min() - 1) > 1e-3 or abs(norms.max() - 1) > 1e-3:
        failures.append("vectors are not L2-normalised")
    if cross_lingual <= unrelated:
        failures.append("cross-lingual sanity check failed")
    if failures:
        print("FAIL: " + "; ".join(failures))
        return 1
    print("OK: CUDA in use for compute and embeddings.")
    return 0
