"""Dump the seeded personas as JSON for the frontend / deck to consume."""

import json
from pathlib import Path

from ..personas import list_personas


def main() -> None:
    root = Path(__file__).resolve().parents[3]
    out = root / "docs" / "personas.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    data = [p.model_dump() for p in list_personas()]
    out.write_text(json.dumps(data, indent=2))
    print(f"Wrote {len(data)} personas to {out}")


if __name__ == "__main__":
    main()
