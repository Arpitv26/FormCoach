import { readFile, writeFile } from "node:fs/promises";
import { compile } from "json-schema-to-typescript";

const schema = JSON.parse(await readFile(new URL("../../../contracts/api.schema.json", import.meta.url), "utf8"));
// Pydantic's field titles otherwise produce hundreds of aliases such as Score1.
// Keep named domain interfaces, but generate readable inline property types.
function removePropertyTitles(node) {
  if (!node || typeof node !== "object") return;
  for (const property of Object.values(node.properties ?? {})) delete property.title;
  for (const value of Object.values(node)) removePropertyTitles(value);
}
removePropertyTitles(schema);
const destination = new URL("../src/lib/api/types.ts", import.meta.url);
const output = await compile(schema, "ApiContract", {
  bannerComment: "/* Generated from contracts/api.schema.json. Do not edit by hand. Run npm run contracts:generate. */",
  ignoreMinAndMaxItems: true,
  unreachableDefinitions: true,
});
if (process.argv.includes("--check")) {
  if (await readFile(destination, "utf8") !== output) {
    throw new Error("Stale API types. Run npm run contracts:generate and coordinate the contract change.");
  }
  console.log("API types match the shared schema.");
} else {
  await writeFile(destination, output);
  console.log("Generated src/lib/api/types.ts");
}
