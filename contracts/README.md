# Shared contracts

Both computers depend on this directory. `contractVersion` is **1.0**.

- `examples/pushup-comparison-analysis.json`: explicitly synthetic three-rep example with two evidence-backed review flags; no video or scores.
- `examples/pushup-analysis.json`: explicitly synthetic one-rep timing/angle fixture; null scores, no matching video.
- `examples/squat-analysis.json`: explicitly synthetic six-rep UI fixture. Not a CV result.
- `examples/live-pose-batch.json`: two synthetic frames showing the request shape. Not enough to count a rep.
- `examples/pushup-video-with-pose.json`: synthetic analysis/pose-track envelope; authored geometry, no matching video. New additive endpoint, old analysis shape unchanged.
- `analysis.schema.json`: standalone analysis JSON Schema, draft 2020-12.
- `api.schema.json`: schema bundle for all JSON request/response types. The bundle wrapper is not an endpoint.

Read [API contract](../docs/API_CONTRACT.md) for semantics that schemas alone cannot capture:
coordinates, timestamps, cumulative batching, unknowns, scores, and issue references.
Python validators also enforce index/name agreement, temporal order, and related-field invariants.

## Sources and regeneration

Pydantic models in `apps/api/app/domain/` are the type source. Generated TypeScript is checked
in so Computer B can work without Python or a running API. Do not edit it by hand.
After agreeing on a shared contract change, run from the repository root:

```bash
apps/api/.venv/bin/python scripts/export_contracts.py
cd apps/web
npm run contracts:generate
```

Expected: two `OK contracts/...` lines and `Generated src/lib/api/types.ts`.
Update this documentation, API_CONTRACT.md, and affected examples as part of the same change.
Run all README checks before committing. To check without changing files:

```bash
# From the repository root
apps/api/.venv/bin/python scripts/export_contracts.py --check
cd apps/web
npm run contracts:check
```

The generator disables fixed-size TypeScript tuple expansion for arrays; numeric bounds and
cross-field constraints remain the backend's responsibility. Schemas validate structure;
they are not clinical validation and do not prove that an analysis was really measured.

Coordinate generated frontend type edits with Computer B. Never land incompatible schema,
example, and frontend types in separate uncoordinated commits.
