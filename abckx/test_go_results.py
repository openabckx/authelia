"""Fail-closed contracts for the approved upstream failure ratchet."""
import importlib.util
import json
import pathlib
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent


class GoResultsTest(unittest.TestCase):
    def check(self, events, expected=("example/model TestKnown/sub",), status=1, raw=None):
        spec = importlib.util.spec_from_file_location("go_results", ROOT / "check_go_results.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as directory:
            log = pathlib.Path(directory) / "results.jsonl"
            known = pathlib.Path(directory) / "known.txt"
            log.write_text(raw if raw is not None else "".join(json.dumps(event) + "\n" for event in events))
            known.write_text("\n".join(entry + " | reason | upstream SHA" for entry in expected))
            return module.validate(log, known, status)

    def events(self):
        return [
            {"Action": "start", "Package": "example/model"},
            {"Action": "fail", "Package": "example/model", "Test": "TestKnown/sub"},
            {"Action": "fail", "Package": "example/model", "Test": "TestKnown"},
            {"Action": "fail", "Package": "example/model"},
        ]

    def test_exact_known_failure_is_accepted(self):
        self.assertEqual([], self.check(self.events()))

    def test_clean_suite_with_empty_list_is_accepted(self):
        events = [{"Action": "start", "Package": "example/model"},
                  {"Action": "pass", "Package": "example/model"}]
        self.assertEqual([], self.check(events, expected=(), status=0))

    def test_unexpected_sibling_or_other_package_fails(self):
        for package, test in [("example/model", "TestKnown/new"), ("example/other", "TestKnown/sub")]:
            with self.subTest(package=package, test=test):
                self.assertTrue(self.check(self.events() + [{"Action": "fail", "Package": package, "Test": test}]))

    def test_stale_passing_or_missing_entry_fails(self):
        for action in ("pass", "skip"):
            events = self.events()
            events[1]["Action"] = action
            self.assertTrue(self.check(events))
        self.assertTrue(self.check(self.events(), expected=("example/model TestMissing",)))

    def test_package_build_failure_or_truncation_fails(self):
        self.assertTrue(self.check(self.events() + [{"Action": "fail", "Package": "example/build"}]))
        self.assertTrue(self.check(self.events()[:-1]))
        self.assertTrue(self.check([]))
        self.assertTrue(self.check(self.events(), status=2))
        self.assertTrue(self.check(self.events(), status=0))

    def test_race_or_panic_is_never_tolerated(self):
        for output in ("WARNING: DATA RACE", "panic: unexpected", "fatal error: bad"):
            self.assertTrue(self.check(self.events() + [{"Action": "output", "Package": "example/model", "Output": output}]))

    def test_recovered_panic_log_in_passing_test_is_not_a_crash(self):
        event = {"Action": "output", "Package": "example/model", "Output": 'level=error msg="recovered panic: boom"'}
        self.assertEqual([], self.check(self.events() + [event]))

    def test_malformed_json_and_build_events_fail(self):
        for raw in ('not JSON', '{"Action":', '[]', '{"Action":"output","Output":null}'):
            self.assertTrue(self.check([], raw=raw))
        self.assertTrue(self.check(self.events() + [{"Action": "build-fail", "ImportPath": "example/model"}]))

    def test_duplicate_or_malformed_entries_fail(self):
        self.assertTrue(self.check(self.events(), expected=("example/model TestKnown/sub",) * 2))
        self.assertTrue(self.check(self.events(), expected=("malformed",)))


if __name__ == "__main__":
    unittest.main()
