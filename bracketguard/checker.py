from bracketguard.stack import Stack

OPENERS = ["("]
CLOSERS = [")"]
MATCHERS = {
    ")": "(",
}


def check(content: str, filename: str) -> bool:
    stack = Stack()

    for char in content:

        if char in OPENERS:
            stack.push(char)
        elif char in CLOSERS:
            prev_opener = stack.pop()

            if prev_opener is None or MATCHERS[char] != prev_opener:
                return False

    return True if stack.is_empty() else False
