import assert from "node:assert/strict";
import test from "node:test";
import Ajv2020 from "ajv/dist/2020";
import schema from "../../../contracts/analysis.schema.json";
import { getMockAnalysis } from "../src/lib/api/mock";

test("frontend fixture validates against the shared analysis schema", () => {
  const validate = new Ajv2020({ strict: false }).compile(schema);
  const analysis = getMockAnalysis();
  assert.ok(validate(analysis), JSON.stringify(validate.errors));
  assert.equal(analysis.provenance.kind, "synthetic");
  assert.equal(analysis.reps.length, 6);
  assert.equal(analysis.reps.toSorted((a, b) => (a.score ?? Infinity) - (b.score ?? Infinity))[0].repNumber, 5);
});

test("mock callers receive independent data", () => {
  const analysis = getMockAnalysis();
  analysis.reps.length = 0;
  assert.equal(getMockAnalysis().reps.length, 6);
});
