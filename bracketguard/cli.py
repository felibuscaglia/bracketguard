"""Command-line interface for bracketguard."""

from __future__ import annotations

import argparse
import sys

from . import __version__
from .checker import PAIRS, CheckResult, ErrorKind, check, check_tags


def _print_stats(result: CheckResult) -> None:
    pairs = ", ".join(
        f"{opener}{closer} = {result.counts.get(opener, 0)}"
        for opener, closer in PAIRS
    )
    print(f"depth: {result.depth}")
    print(f"pairs: {pairs}")


def _format_mismatch(result: CheckResult) -> str:
    where = f"MISMATCH at line {result.line}, col {result.col}"

    if result.kind is ErrorKind.MALFORMED_TAG:
        return f"{where}: malformed tag"
    if result.kind is ErrorKind.UNTERMINATED_STRING:
        return f"{where}: unterminated string"

    if result.tags:
        if result.kind is ErrorKind.UNCLOSED_OPENER:
            return f"{where}: unclosed {result.found}"
        if result.expected is None:
            return f"{where}: unexpected {result.found}"
        return f"{where}: expected {result.expected} but found {result.found}"

    if result.kind is ErrorKind.UNCLOSED_OPENER:
        return f"{where}: unclosed '{result.found}'"
    if result.expected is None:
        return f"{where}: unexpected '{result.found}'"
    return f"{where}: expected '{result.expected}' but found '{result.found}'"


def _cmd_check(args: argparse.Namespace) -> int:
    """Read the target file and hand its contents to the checker."""
    if len(args.file) != 1:
        args.parser.error("expected one file")
    path = args.file[0]
    try:
        with open(path, "r", encoding="utf-8") as fh:
            content = fh.read()
    except OSError:
        print(f"error: cannot open '{path}'")
        return 2

    result = check_tags(content) if args.tags else check(content)

    if result.ok:
        print("OK")
        if args.stats and not args.tags:
            _print_stats(result)
        return 0

    print(_format_mismatch(result))
    return 1


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
    check_parser.add_argument("file", nargs="+", help="Path to the file to check.")
    check_parser.add_argument(
        "--stats",
        action="store_true",
        help="Print nesting depth and per-type pair counts when balanced.",
    )
    check_parser.add_argument(
        "--tags",
        action="store_true",
        help="Validate HTML/XML tag nesting instead of brackets.",
    )
    check_parser.set_defaults(func=_cmd_check, parser=check_parser)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
