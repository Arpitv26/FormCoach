import assert from "node:assert/strict";
import test from "node:test";
import Ajv2020 from "ajv/dist/2020";
import schema from "../../../contracts/analysis.schema.json";
import fixture from "../../../contracts/examples/pushup-movement-observation.json";
import type { AnalysisResponse } from "../src/lib/api/types";
import { describeEvidence } from "../src/lib/coach/evidence";

// The component imports CSS via Next; contract/evidence checks stay framework independent.
test("zero-rep movement fixture validates and coach paths identify the interval", () => {
  const validate = new Ajv2020({ strict: false }).compile(schema);
  assert.ok(validate(fixture), JSON.stringify(validate.errors));
  const analysis = fixture as AnalysisResponse;
  assert.equal(analysis.summary.totalReps, 0);
  const evidence = describeEvidence(analysis, "movementObservations.0.medianAngleDeg");
  assert.equal(evidence.text, "130.0°");
  assert.match(evidence.label, /Movement moment 1/);
  assert.equal(evidence.rep, undefined);
  assert.equal(describeEvidence(analysis, "movementObservations.0.startMs").text, "0.00 s");
});
