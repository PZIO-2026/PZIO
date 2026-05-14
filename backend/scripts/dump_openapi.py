"""Dump the FastAPI OpenAPI spec as YAML.

By default writes to stdout, so it works the same way whether you run it
locally or via ``docker compose exec``. Pass ``--out PATH`` to write directly
to a file.

Local (requires backend deps installed)::

    python backend/scripts/dump_openapi.py --out docs/api/openapi.yaml

Inside the running container::

    docker compose exec backend python -m scripts.dump_openapi > docs/api/openapi.yaml

Re-run after every change to routers or Pydantic schemas so the file checked
in under ``docs/api/openapi.yaml`` stays in sync with the live API.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

# Allow ``python backend/scripts/dump_openapi.py`` (cwd = repo root) by adding
# the backend dir to sys.path. ``python -m scripts.dump_openapi`` already
# inherits the package's import path.
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from pzio.main import app  # noqa: E402  (sys.path tweak above)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Write the YAML spec to this path. Defaults to stdout.",
    )
    args = parser.parse_args()

    text = yaml.safe_dump(
        app.openapi(),
        sort_keys=False,
        allow_unicode=True,
        width=100,
        default_flow_style=False,
    )

    if args.out is None:
        sys.stdout.write(text)
    else:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
        print(f"Wrote {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
