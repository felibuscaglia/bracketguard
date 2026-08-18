"""Command-line interface for bracketguard."""

from __future__ import annotations

import argparse
import sys

from . import __version__
from .checker import PAIRS, CheckResult, ErrorKind, check

_STATS_MIN_WIDTH = 16


def _print_stats(result: CheckResult) -> None:
    rows = [("depth", str(result.depth))]
    rows.extend(
        (f"{opener}{closer}", str(result.counts.get(opener, 0)))
        for opener, closer in PAIRS
    )
    inner = max(
        _STATS_MIN_WIDTH,
        len("Stats"),
        max(len(label) + 2 + len(value) for label, value in rows),
    )
    rule = "─" * (inner + 2)

    print()
    print(f"╭{rule}╮")
    print(f"│ {'Stats'.ljust(inner)} │")
    print(f"├{rule}┤")
    for label, value in rows:
        gap = inner - len(label) - len(value)
        print(f"│ {label}{' ' * gap}{value} │")
    print(f"╰{rule}╯")


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

    result = check(content)


    if result.ok:
        print("OK")

        if args.stats:
            _print_stats(result)

        return 0

    where = f"MISMATCH at line {result.line}, col {result.col}"

    if result.kind is ErrorKind.UNTERMINATED_STRING:
        print(f"{where}: unterminated string")
    elif result.kind is ErrorKind.UNCLOSED_OPENER:
        print(f"{where}: unclosed '{result.found}'")
    elif result.expected is None:
        print(f"{where}: unexpected '{result.found}'")
    else:
        print(f"{where}: expected '{result.expected}' but found '{result.found}'")

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
        help="Print statistics about the checked file.",
    )
    check_parser.set_defaults(func=_cmd_check, parser=check_parser)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
