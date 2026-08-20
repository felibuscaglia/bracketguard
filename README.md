# bracketguard

**A fast, dependency-free command-line linter for balanced brackets, quotes, and HTML/XML tags — with precise line/column diagnostics.**

🌐 **[Live showcase & interactive demo →](https://felibuscaglia.github.io/bracketguard/)**

bracketguard reads a file in a single **O(n)** pass, using a hand-written stack to
verify that every `()`, `[]`, and `{}` is balanced — while correctly ignoring
brackets inside strings and `#` comments. When something is off, it tells you
exactly where.

```console
$ bracketguard check server.py
OK

$ bracketguard check payload.json
MISMATCH at line 4, col 12: expected '}' but found ']'
```

## Features

- **Balanced brackets** — `()`, `[]`, `{}` nesting validated with a stack.
- **String awareness** — brackets inside `"double-quoted"` strings are ignored; escaped quotes `\"` are handled.
- **Comment awareness** — everything after `#` to end-of-line is skipped.
- **Precise error locations** — every failure reports an exact `line` and `col`, pointing at the *leftmost* unclosed opener.
- **Expected-closer hints** — `expected ')' but found ']'`.
- **HTML/XML tags** — `--tags` validates open / close / self-closing tag nesting.
- **Structure stats** — `--stats` reports nesting depth and per-type pair counts.
- **Scriptable exit codes** — `0` pass · `1` mismatch · `2` file error.
- **Zero dependencies** — pure Python standard library, `>= 3.9`.

## Install

```bash
pip install git+https://github.com/felibuscaglia/bracketguard.git
```

## Usage

```bash
bracketguard check FILE            # check a file
bracketguard check FILE --stats    # also print depth + pair counts when balanced
bracketguard check FILE --tags     # validate HTML/XML tag nesting instead
bracketguard --version
```

## Architecture

| Module | Responsibility |
| --- | --- |
| `bracketguard/stack.py` | A singly-linked-list `Stack`, written from scratch — each node carries its `(col, line)` position. |
| `bracketguard/checker.py` | The scanning engines (`check` / `check_tags`), a frozen `CheckResult` dataclass, and the `ErrorKind` enum. |
| `bracketguard/cli.py` | A thin `argparse` layer that formats results for humans. |

## The showcase site

The [`docs/`](docs/) folder contains a self-contained showcase site
(deployed via GitHub Pages) with an in-browser interactive playground that runs a
faithful port of the checker. Animations use [anime.js](https://animejs.com) and
[Motion](https://motion.dev), both vendored locally so the page has no runtime
CDN dependency.
