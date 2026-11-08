"""Reject fork changes outside abckx/ without an exact PATCHES.md table row."""
import argparse
import pathlib
import re
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default="origin/master", help="Upstream mirror ref (full history required)")
    args = parser.parse_args()
    try:
        root = pathlib.Path(subprocess.run(
            ["git", "rev-parse", "--show-toplevel"], check=True,
            capture_output=True, text=True).stdout.strip())
        manifest = (root / "abckx/PATCHES.md").read_text()
        listed = set(re.findall(r"^\| `([^`]+)` \|", manifest, re.MULTILINE))
        # Disable rename detection: both removed and new paths need inventory rows.
        result = subprocess.run(
            ["git", "diff", "--name-only", "--no-renames", "-z", f"{args.base}...HEAD", "--"],
            cwd=root, check=True, capture_output=True)
        changed = {p for p in result.stdout.decode().split("\0") if p and not p.startswith("abckx/")}
    except (OSError, UnicodeError, subprocess.CalledProcessError) as error:
        print(f"Patch manifest check failed: {error}", file=sys.stderr)
        return 1
    missing = changed - listed
    if missing:
        print("Missing abckx/PATCHES.md rows:\n" + "\n".join(sorted(missing)), file=sys.stderr)
        return 1
    print(f"Patch manifest: {len(changed)} changed paths covered (base: {args.base}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
