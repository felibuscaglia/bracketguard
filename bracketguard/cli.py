"""Command-line interface for bracketguard."""

from __future__ import annotations

import argparse
import sys

from . import __version__
from .checker import check


def _cmd_check(args: argparse.Namespace) -> int:
    """Read the target file and hand its contents to the checker."""
    if len(args.file) != 1:
        args.parser.error("expected one file")
    args.file = args.file[0]
    try:
        with open(args.file, "r", encoding="utf-8") as fh:
            content = fh.read()
    except FileNotFoundError:
        print(f"bracketguard: {args.file}: no such file", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"bracketguard: {args.file}: {exc.strerror}", file=sys.stderr)
        return 2

    result = check(content, filename=args.file)
    if result["ok"]:
        print("OK")
    else:
        print(f"MISMATCH at line {result["line"]}, col {result["col"]}: {"unclosed" if result["is_opener"] else "unexpected"} '{result["value"]}'")
    return 0 if result["ok"] else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bracketguard",
        description=(
            "Fast command-line linter for balanced brackets, quotes, "
            "and HTML/XML tags with precise error locations."
        ),
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    check_parser = subparsers.add_parser(
        "check", help="Check a file for balanced brackets, quotes, and tags."
    )
    check_parser.add_argument(
        "file", nargs="+", help="Path to the file to check."
    )
    check_parser.set_defaults(func=_cmd_check, parser=check_parser)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
