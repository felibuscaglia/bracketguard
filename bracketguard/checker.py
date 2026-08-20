from dataclasses import dataclass, field
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
    MALFORMED_TAG = "malformed_tag"


@dataclass(frozen=True)
class CheckResult:
    ok: bool
    depth: Optional[int] = None
    kind: Optional[ErrorKind] = None
    line: Optional[int] = None
    col: Optional[int] = None
    found: Optional[str] = None
    expected: Optional[str] = None
    counts: dict[str, int] = field(default_factory=dict)
    tags: bool = False

    @classmethod
    def success(
        cls,
        depth: int = 0,
        counts: Optional[dict[str, int]] = None,
        tags: bool = False,
    ) -> "CheckResult":
        if counts is None:
            counts = {opener: 0 for opener, _ in PAIRS}
        return cls(ok=True, depth=depth, counts=counts, tags=tags)

    @classmethod
    def failure(
        cls,
        kind: ErrorKind,
        line: int,
        col: int,
        found: Optional[str] = None,
        expected: Optional[str] = None,
        tags: bool = False,
    ) -> "CheckResult":
        return cls(
            ok=False,
            kind=kind,
            line=line,
            col=col,
            found=found,
            expected=expected,
            tags=tags,
        )


def _leftmost_unclosed(stack: Stack):
    """Return the earliest still-open stack node (bottom), or None."""
    leftmost = None
    node = stack.pop()
    while node is not None:
        leftmost = node
        node = stack.pop()
    return leftmost


def check(content: str) -> CheckResult:
    stack = Stack()
    line = 1
    col = 1
    quote_line = None
    quote_col = None
    quote_opened = False
    is_comment = False
    depth = 0
    curr_depth = 0
    pair_counts = {opener: 0 for opener, _ in PAIRS}

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
                    curr_depth += 1
                elif char in CLOSER_TO_OPENER:
                    depth = max(depth, curr_depth)
                    curr_depth -= 1
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
                    pair_counts[opener] += 1

        col += 1

    if quote_opened:
        return CheckResult.failure(
            ErrorKind.UNTERMINATED_STRING, quote_line, quote_col
        )

    node = _leftmost_unclosed(stack)
    if node is not None:
        opener_col, opener_line = node.position
        return CheckResult.failure(
            ErrorKind.UNCLOSED_OPENER,
            opener_line,
            opener_col,
            found=node.value,
            expected=OPENER_TO_CLOSER[node.value],
        )

    return CheckResult.success(depth=depth, counts=pair_counts)


def check_tags(content: str) -> CheckResult:
    """Validate HTML/XML tag nesting (open / close / self-closing)."""
    stack = Stack()
    i = 0
    line = 1
    col = 1
    n = len(content)

    while i < n:
        ch = content[i]
        if ch == "\n":
            line += 1
            col = 1
            i += 1
            continue

        if ch != "<":
            col += 1
            i += 1
            continue

        tag_line, tag_col = line, col
        i += 1
        col += 1

        if i >= n:
            return CheckResult.failure(
                ErrorKind.MALFORMED_TAG, tag_line, tag_col, tags=True
            )

        is_close = False
        if content[i] == "/":
            is_close = True
            i += 1
            col += 1

        name_chars: list[str] = []
        while i < n and content[i].isalnum():
            name_chars.append(content[i])
            i += 1
            col += 1
        name = "".join(name_chars)

        if not name:
            return CheckResult.failure(
                ErrorKind.MALFORMED_TAG, tag_line, tag_col, tags=True
            )

        rest_chars: list[str] = []
        while i < n and content[i] != ">":
            if content[i] == "\n":
                rest_chars.append(content[i])
                line += 1
                col = 1
                i += 1
                continue
            rest_chars.append(content[i])
            i += 1
            col += 1

        if i >= n:
            return CheckResult.failure(
                ErrorKind.MALFORMED_TAG, tag_line, tag_col, tags=True
            )

        # Consume '>'.
        i += 1
        col += 1

        rest = "".join(rest_chars)
        if is_close:
            if rest.strip():
                return CheckResult.failure(
                    ErrorKind.MALFORMED_TAG, tag_line, tag_col, tags=True
                )
            node = stack.pop()
            opener = node.value if node is not None else None
            found = f"</{name}>"
            if opener is None:
                return CheckResult.failure(
                    ErrorKind.UNEXPECTED_CLOSER,
                    tag_line,
                    tag_col,
                    found=found,
                    tags=True,
                )
            if opener != name:
                return CheckResult.failure(
                    ErrorKind.UNEXPECTED_CLOSER,
                    tag_line,
                    tag_col,
                    found=found,
                    expected=f"</{opener}>",
                    tags=True,
                )
            continue

        self_closing = rest.rstrip().endswith("/")
        if not self_closing:
            stack.push(value=name, line=tag_line, col=tag_col)

    node = _leftmost_unclosed(stack)
    if node is not None:
        opener_col, opener_line = node.position
        return CheckResult.failure(
            ErrorKind.UNCLOSED_OPENER,
            opener_line,
            opener_col,
            found=f"<{node.value}>",
            tags=True,
        )

    return CheckResult.success(tags=True)
