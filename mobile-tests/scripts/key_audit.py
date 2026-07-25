"""
Scans mobile/lib/screens/*.dart for TextField / ElevatedButton / IconButton
widgets that don't yet have a `key:` argument, so you know which widgets
still need a ValueKey added if you want to extend the Appium suite's
coverage beyond what this delivery already instruments.

Usage (from repo root):
    python3 mobile-tests/scripts/key_audit.py mobile/lib/screens
"""
import re
import sys
from pathlib import Path

WIDGET_PATTERN = re.compile(r"\b(TextField|ElevatedButton(?:\.icon)?|IconButton(?:\.filled)?|DropdownButtonFormField|GestureDetector|FloatingActionButton)\s*\(")
KEY_WINDOW = 120  # chars to look ahead for a `key:` argument


def audit_file(path: Path):
    text = path.read_text(encoding="utf-8", errors="ignore")
    missing = []
    for match in WIDGET_PATTERN.finditer(text):
        window = text[match.end(): match.end() + KEY_WINDOW]
        if "key:" not in window:
            line_no = text[: match.start()].count("\n") + 1
            missing.append((line_no, match.group(1)))
    return missing


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 key_audit.py <path-to-lib/screens>")
        raise SystemExit(1)

    root = Path(sys.argv[1])
    dart_files = sorted(root.glob("*.dart"))
    if not dart_files:
        print(f"No .dart files found under {root}")
        raise SystemExit(1)

    total_missing = 0
    for f in dart_files:
        missing = audit_file(f)
        if missing:
            print(f"\n{f.name}:")
            for line_no, widget in missing:
                print(f"  line {line_no}: {widget} — no ValueKey found nearby")
            total_missing += len(missing)

    print(f"\n{total_missing} widget(s) without a nearby key across {len(dart_files)} screen file(s).")
    print("Add `key: const ValueKey('some_unique_name')` to any you want to target from a Page Object.")


if __name__ == "__main__":
    main()
