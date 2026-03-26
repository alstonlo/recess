import argparse
import difflib
import sys
from pathlib import Path


def fix_content(source: str) -> str:
    if "class " not in source:
        return source  # fast path

    lines = source.split("\n")
    out: list[str] = []
    n = len(lines)
    i = 0

    while i < n:
        out.append(lines[i])

        # Detect class definition lines
        stripped = lines[i].lstrip()
        if not stripped.startswith("class ") or ":" not in lines[i]:
            i += 1
            continue

        # Measure indent of the class line and expected body indent
        class_indent_len = len(lines[i]) - len(stripped)
        body_indent_len = class_indent_len + 4

        j = i + 1

        # If the first body element is an attribute, insert a blank line
        # between the class header and that attribute.
        if j < n and _is_attr(lines[j], body_indent_len):
            out.append("")

        # Skip past class-level attributes / type annotations that sit
        # between the class line and the first def.  We want the blank
        # line to go AFTER all of them, not between class attrs and def.
        #
        # Attrs look like:   "    attr: int"  "    x = 10"  "    x: int = 0"
        while j < n:
            line = lines[j]
            s = line.strip()

            # Skip blank lines within the attr block only if more attrs follow
            if s == "":
                peek = j + 1
                while peek < n and lines[peek].strip() == "":
                    peek += 1
                if peek < n and _is_attr(lines[peek], body_indent_len):
                    j += 1
                    continue
                break

            # Docstring right after class — don't touch anything
            if s.startswith(('"""', "'''", '"', "'")):
                break

            # Decorator or def/class — stop; these are what we want to space from
            if s.startswith("@") or s.startswith(("def ", "async ", "class ")):
                break

            # Class-level attribute at correct indent
            if _is_attr(line, body_indent_len):
                j += 1
                continue

            break

        # j now points at the first line after any attrs.
        # Walk over decorators to find the def/class.
        peek = j
        while peek < n and lines[peek].lstrip().startswith("@"):
            peek += 1

        if peek >= n:
            i += 1
            continue

        peek_s = lines[peek].lstrip()
        if not (peek_s.startswith(("def ", "async def ", "class "))):
            i += 1
            continue

        # Check no blank line already exists between attr_end and def/decorator
        has_blank = any(lines[k].strip() == "" for k in range(j, peek + 1))
        if has_blank:
            i += 1
            continue

        # Append any attr lines, then insert the blank line
        for k in range(i + 1, j):
            out.append(lines[k])
        out.append("")  # ← the blank line
        i = j
        continue

    return "\n".join(out)


def _is_attr(line: str, body_indent_len: int) -> bool:
    if not line or line.isspace():
        return False
    s = line.lstrip()
    indent_len = len(line) - len(s)
    if indent_len != body_indent_len:
        return False
    # Must not be a def, class, decorator, or comment-only line
    if s.startswith(("def ", "async ", "class ", "@", "#")):
        return False
    # Should start with an identifier char
    if not (s[0].isalpha() or s[0] == "_"):
        return False
    # Must look like an assignment or annotation, not a bare statement like `pass`
    if ":" not in s and "=" not in s:
        return False
    return True


def process_file(path: Path, *, check: bool = False, diff: bool = False) -> bool:
    try:
        original = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, PermissionError):
        return False

    fixed = fix_content(original)
    if original == fixed:
        return False

    if check:
        print(f"would reformat {path}", file=sys.stderr)
        return True

    if diff:
        d = difflib.unified_diff(
            original.splitlines(keepends=True),
            fixed.splitlines(keepends=True),
            fromfile=str(path),
            tofile=str(path),
        )
        sys.stdout.writelines(d)
        return True

    path.write_text(fixed, encoding="utf-8")
    print(f"reformatted {path}", file=sys.stderr)
    return True


def collect_files(paths: list[str]) -> list[Path]:
    result: list[Path] = []
    for p in paths:
        path = Path(p)
        if path.is_dir():
            result.extend(sorted(path.rglob("*.py")))
        elif path.is_file():
            result.append(path)
        else:
            print(f"warning: {path!r} is not a file or directory, skipping", file=sys.stderr)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="recess",
        description="Ensure blank line between class headers (+ attrs) and first method.",
    )
    parser.add_argument("files", nargs="+", help="Files/dirs to process, or '-' for stdin.")
    parser.add_argument("--check", action="store_true", help="Exit 1 if any file would change.")
    parser.add_argument("--diff", action="store_true", help="Print diff instead of writing.")
    args = parser.parse_args(argv)

    if args.files == ["-"]:
        source = sys.stdin.read()
        result = fix_content(source)
        if args.check:
            return 0 if source == result else 1
        if args.diff:
            d = difflib.unified_diff(
                source.splitlines(keepends=True),
                result.splitlines(keepends=True),
                fromfile="<stdin>",
                tofile="<stdin>",
            )
            sys.stdout.writelines(d)
            return 0 if source == result else 1
        sys.stdout.write(result)
        return 0

    files = collect_files(args.files)
    results = [process_file(f, check=args.check, diff=args.diff) for f in files]
    changed = any(results)
    return 1 if args.check and changed else 0


if __name__ == "__main__":
    raise SystemExit(main())
