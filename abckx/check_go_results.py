"""Check complete go test -json output against exact upstream failures (#18)."""
import json
import pathlib
import sys


def validate(log: pathlib.Path, known: pathlib.Path, status: int) -> list[str]:
    expected: set[tuple[str, str]] = set()
    errors: list[str] = []
    for line in known.read_text().splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        fields = line.split(" | ")
        identity = fields[0].split()
        if len(fields) != 3 or len(identity) != 2 or not all(fields):
            errors.append(f"Malformed known failure: {line}")
            continue
        key = (identity[0], identity[1])
        if key in expected:
            errors.append(f"Duplicate known failure: {key}")
        expected.add(key)

    failures: set[tuple[str, str]] = set()
    started: set[str] = set()
    finished: dict[str, str] = {}
    try:
        for line in log.read_text().splitlines():
            event = json.loads(line)
            package = event.get("Package", "")
            action = event.get("Action", "")
            test = event.get("Test", "")
            output = event.get("Output", "")
            if output.startswith(("WARNING: DATA RACE", "panic:", "fatal error:")) or "[build failed]" in output:
                errors.append(f"Infrastructure/race/panic failure: {output.strip()}")
            if action == "build-fail":
                errors.append(f"Build failed: {event}")
            if action == "start" and package:
                started.add(package)
            if action == "fail" and test:
                failures.add((package, test))
            if action in ("pass", "fail", "skip") and not test and package:
                finished[package] = action
    except (ValueError, TypeError, AttributeError) as error:
        errors.append(f"Invalid Go JSON stream: {error}")

    # Parents fail when a child fails; only exact listed leaves may be tolerated.
    leaves = {key for key in failures if not any(
        child[0] == key[0] and child[1].startswith(key[1] + "/") for child in failures
    )}
    for key in sorted(leaves - expected):
        errors.append(f"Unexpected failure: {' '.join(key)}")
    for key in sorted(expected - leaves):
        errors.append(f"Stale/missing known failure (remove or investigate): {' '.join(key)}")
    for package, action in finished.items():
        if action == "fail" and not any(key[0] == package for key in failures):
            errors.append(f"Package failed without a listed test: {package}")
    if not started or started != set(finished):
        errors.append("Empty/incomplete Go package stream")
    if status not in (0, 1) or (status == 0) != (not failures and "fail" not in finished.values()):
        errors.append(f"Unexpected Go exit status: {status}")
    return errors


if __name__ == "__main__":
    try:
        problems = validate(pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]), int(sys.argv[3]))
    except (OSError, ValueError, IndexError) as error:
        problems = [str(error)]
    for problem in problems:
        print(problem, file=sys.stderr)
    if not problems:
        print("Go result gate passed: only exact known upstream failures; no stale entries.")
    sys.exit(bool(problems))
