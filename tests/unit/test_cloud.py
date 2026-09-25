"""Cloud-deployment pieces (DECISIONS D58): Bedrock provider, Tesseract output parsing, OCR engine choice."""

from botocore.stub import Stubber

from app.llm.base import Message
from app.llm.bedrock import BedrockClient, _client


def test_bedrock_converse_request_and_answer():
    client = _client("ap-south-1", 180.0)
    response = {"output": {"message": {"role": "assistant", "content": [{"text": "Fifteen days [S1]."}]}},
                "usage": {"inputTokens": 12, "outputTokens": 5, "totalTokens": 17}, "stopReason": "end_turn",
                "metrics": {"latencyMs": 10}}
    expected = {"modelId": "apac.amazon.nova-pro-v1:0", "system": [{"text": "sys"}],
                "messages": [{"role": "user", "content": [{"text": "q"}]}],
                "inferenceConfig": {"maxTokens": 50, "temperature": 0.0}}
    with Stubber(client) as stub:
        stub.add_response("converse", response, expected)
        out = BedrockClient("apac.amazon.nova-pro-v1:0", "ap-south-1").generate(
            [Message("user", "q")], system="sys", max_tokens=50, temperature=0.0)
    assert out.text == "Fifteen days [S1]." and out.input_tokens == 12 and out.output_tokens == 5


def test_tesseract_words_become_lines_in_reading_order():
    from app.ocr.tesseract import parse_tsv

    header = "level\tpage_num\tblock_num\tpar_num\tline_num\tword_num\tleft\ttop\twidth\theight\tconf\ttext"
    rows = [header,
            "5\t1\t1\t1\t1\t2\t120\t100\t300\t30\t91.5\tCancellation",
            "5\t1\t1\t1\t1\t1\t40\t100\t60\t30\t95.0\t7.5",
            "4\t1\t1\t1\t1\t0\t40\t100\t380\t30\t-1\t",
            "5\t1\t1\t1\t2\t1\t40\t140\t200\t28\t88.0\tThe",
            "5\t1\t1\t1\t2\t2\t250\t140\t90\t28\t-1\t "]
    lines = parse_tsv("\n".join(rows), scale=0.5)
    assert [ln.text for ln in lines] == ["7.5 Cancellation", "The"]
    assert lines[0].x0 == 20 and lines[0].x1 == 210 and lines[0].size == 15


def test_ocr_engine_uses_tesseract_languages_off_windows(monkeypatch):
    import app.ocr.engine as engine

    monkeypatch.setattr(engine.sys, "platform", "linux")
    monkeypatch.setattr(engine, "tesseract_available", lambda: True)
    monkeypatch.setattr(engine, "tesseract_languages", lambda: ("eng", "hin", "tam", "osd"))
    assert engine.ocr_language("Latn") == "tesseract:eng+hin"
    assert engine.ocr_language("Taml") == "tesseract:tam+eng"
    assert engine.ocr_language("Beng") == "tesseract:eng"
    monkeypatch.setattr(engine, "tesseract_available", lambda: False)
    assert engine.ocr_language("Latn") is None
