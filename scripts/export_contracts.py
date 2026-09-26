"""Run with apps/api/.venv/bin/python scripts/export_contracts.py [--check]."""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps/api"))

from app.domain.analysis import AnalysisResponse
from app.domain.models import ApiContract


def schema_text(model: type) -> str:
    schema = model.model_json_schema(by_alias=True)
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    return json.dumps(schema, indent=2) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check", action="store_true", help="Fail instead of writing stale schemas"
    )
    args = parser.parse_args()
    for filename, model in [
        ("analysis.schema.json", AnalysisResponse),
        ("api.schema.json", ApiContract),
    ]:
        destination = ROOT / "contracts" / filename
        expected = schema_text(model)
        if args.check:
            if not destination.exists() or destination.read_text() != expected:
                raise SystemExit(
                    f"Stale schema: {destination.relative_to(ROOT)}; regenerate contracts"
                )
        else:
            destination.write_text(expected)
        print(f"OK {destination.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
