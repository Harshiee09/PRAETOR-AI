import { spawn } from "node:child_process";
const child = spawn(
  process.execPath,
  [
    "node_modules/next/dist/bin/next",
    "dev",
    "--hostname",
    "127.0.0.1",
    ...process.argv.slice(2),
  ],
  {
    stdio: "inherit",
    env: { ...process.env, PRAETOR_MOCK: "1" },
  },
);
child.on("exit", (code) => process.exit(code ?? 1));
