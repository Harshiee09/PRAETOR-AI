import { mkdir, readFile, writeFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import openapiTS, { astToString } from "openapi-typescript";

const root = new URL("../", import.meta.url);
const source = new URL("../docs/api/openapi.json", root);
const schema = JSON.parse(await readFile(source, "utf8"));
const ast = await openapiTS(schema);
const target = new URL("src/lib/api/schema.ts", root);
await mkdir(new URL("src/lib/api/", root), { recursive: true });
await writeFile(
  target,
  `// Generated with openapi-typescript. Do not edit.\n// Source: docs/api/openapi.json (authoritative)\n\n${astToString(ast)}`,
);
console.info(
  `Generated ${fileURLToPath(target)} from ${fileURLToPath(source)}.`,
);

const documentSource = new URL("../docs/api/documents.provisional.json", root);
const documentSchema = JSON.parse(await readFile(documentSource, "utf8"));
const documentAst = await openapiTS(documentSchema);
const documentTarget = new URL("src/lib/api/documents-schema.ts", root);
await writeFile(documentTarget, `// Generated with openapi-typescript. Do not edit.\n// PROVISIONAL document-workflow supplement; supplied backend OpenAPI lacks these endpoints.\n\n${astToString(documentAst)}`);
console.info(`Generated provisional document types from ${fileURLToPath(documentSource)}.`);
