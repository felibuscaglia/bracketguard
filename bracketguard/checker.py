from bracketguard.stack import Stack

PAIRS = (("(", ")"), ("[", "]"), ("{", "}"))

OPENER_TO_CLOSER = dict(PAIRS)
CLOSER_TO_OPENER = {c: o for o, c in PAIRS}

OPENERS = OPENER_TO_CLOSER  # membership via `in`
CLOSERS = CLOSER_TO_OPENER


def check(content: str, filename: str) -> object:
    stack = Stack()
    line = 1
    col = 1

    for char in content:
        if char in OPENERS:
            stack.push(value=char, line=line, col=col)
        elif char in CLOSERS:
            prev_opener = stack.pop().value if not stack.is_empty() else None

            if prev_opener is None or CLOSER_TO_OPENER[char] != prev_opener:
                return {
                    "ok": False,
                    "col": col,
                    "line": line,
                    "value": char,
                    "is_opener": False,
                    "expected": OPENER_TO_CLOSER[prev_opener] if prev_opener is not None else None
                }
        
        col += 1 if char != "\n" else 1
        line += 1 if char == "\n" else 0

    if not stack.is_empty():
        last = stack.pop()
        return {
            "ok": False,
            "col": last.position[0],
            "line": last.position[1],
            "value": last.value,
            "is_opener": True,
            "expected": None
        }
    else:
        return {"ok": True}
