import { cpSync, existsSync, mkdirSync, rmSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const from = join(root, "web", "out");
const to = join(root, "dist");

if (!existsSync(from)) {
  console.error("Expected Next.js static export at web/out. Set output: 'export' in web/next.config.mjs.");
  process.exit(1);
}

rmSync(to, { recursive: true, force: true });
mkdirSync(to, { recursive: true });
cpSync(from, to, { recursive: true });
console.log("Copied web/out to dist for financial-planning-frontend.");
