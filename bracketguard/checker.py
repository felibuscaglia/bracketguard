from dataclasses import dataclass
from enum import Enum
from typing import Optional

from bracketguard.stack import Stack

PAIRS = (("(", ")"), ("[", "]"), ("{", "}"))

OPENER_TO_CLOSER = dict(PAIRS)
CLOSER_TO_OPENER = {closer: opener for opener, closer in PAIRS}


class ErrorKind(str, Enum):
    UNEXPECTED_CLOSER = "unexpected_closer"
    UNCLOSED_OPENER = "unclosed_opener"
    UNTERMINATED_STRING = "unterminated_string"


@dataclass(frozen=True)
class CheckResult:
    ok: bool
    kind: Optional[ErrorKind] = None
    line: Optional[int] = None
    col: Optional[int] = None
    found: Optional[str] = None
    expected: Optional[str] = None

    @classmethod
    def success(cls) -> "CheckResult":
        return cls(ok=True)

    @classmethod
    def failure(
        cls,
        kind: ErrorKind,
        line: int,
        col: int,
        found: Optional[str] = None,
        expected: Optional[str] = None,
    ) -> "CheckResult":
        return cls(
            ok=False, kind=kind, line=line, col=col, found=found, expected=expected
        )


def check(content: str) -> CheckResult:
    stack = Stack()
    line = 1
    col = 1
    quote_line = None
    quote_col = None
    quote_opened = False
    is_comment = False

    for index, char in enumerate(content):
        if char == "\n":
            if quote_opened:
                return CheckResult.failure(
                    ErrorKind.UNTERMINATED_STRING, quote_line, quote_col
                )
            is_comment = False
            line += 1
            col = 1
            continue

        if not is_comment:
            if char == '"':
                escaped = index > 0 and content[index - 1] == "\\"
                if quote_opened and not escaped:
                    quote_opened = False
                elif not quote_opened:
                    quote_opened = True
                    quote_line, quote_col = line, col
            elif not quote_opened:
                if char == "#":
                    is_comment = True
                elif char in OPENER_TO_CLOSER:
                    stack.push(value=char, line=line, col=col)
                elif char in CLOSER_TO_OPENER:
                    node = stack.pop()
                    opener = node.value if node is not None else None
                    if opener is None or CLOSER_TO_OPENER[char] != opener:
                        return CheckResult.failure(
                            ErrorKind.UNEXPECTED_CLOSER,
                            line,
                            col,
                            found=char,
                            expected=(
                                OPENER_TO_CLOSER[opener] if opener is not None else None
                            ),
                        )

        col += 1

    if quote_opened:
        return CheckResult.failure(
            ErrorKind.UNTERMINATED_STRING, quote_line, quote_col
        )

    node = stack.pop()
    if node is not None:
        opener_col, opener_line = node.position
        return CheckResult.failure(
            ErrorKind.UNCLOSED_OPENER,
            opener_line,
            opener_col,
            found=node.value,
            expected=OPENER_TO_CLOSER[node.value],
        )

    return CheckResult.success()
