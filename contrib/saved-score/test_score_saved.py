"""Portable contract checks, recursive edit oracle and real pinned regression."""
import itertools
import json
import subprocess
import sys
import tempfile
import unittest
from functools import lru_cache
from pathlib import Path

from score_saved import check_manifest, check_snapshot, edit_alignment, make_report, parse_gold, parse_machine, score_pair

PACKAGE = Path(__file__).resolve().parent


@lru_cache(None)
def oracle(a, b):
    if not a or not b:
        return len(a) + len(b)
    return min(oracle(a[1:], b) + 1, oracle(a, b[1:]) + 1,
               oracle(a[1:], b[1:]) + (a[0] != b[0]))


def cli(*extra):
    return subprocess.run([sys.executable, "-B", str(PACKAGE / "score_saved.py"),
        "--gold", str(PACKAGE / "inputs/f179r.txt"),
        "--machine", str(PACKAGE / "inputs/f179r_machine_blind.txt"),
        "--manifest", str(PACKAGE / "manifest.json"), *map(str, extra)], capture_output=True, text=True)


class ScoringTests(unittest.TestCase):
    def test_exhaustive_recursive_oracle(self):
        words = ["".join(c) for n in range(4) for c in itertools.product("ab", repeat=n)]
        for a, b in itertools.product(words, repeat=2):
            with self.subTest(a=a, b=b):
                result = edit_alignment(a, b)
                self.assertEqual(result["edit_errors"], oracle(a, b))
                self.assertEqual(sum(result["operations"].values()), result["edit_errors"])

    def test_analytic_edits_indices_and_unclamped_accuracy(self):
        self.assertEqual(edit_alignment("kitten", "sitting")["edit_errors"], 3)
        self.assertEqual(edit_alignment("abc", "axc")["changes"][0]["reference_index"], 1)
        self.assertEqual(edit_alignment("abc", "ac")["operations"]["deletion"], 1)
        self.assertEqual(edit_alignment("ac", "abc")["operations"]["insertion"], 1)
        self.assertLess(edit_alignment("a", "aaaa")["accuracy_percent"], 0)
        self.assertIsNone(edit_alignment("", "a")["accuracy_percent"])

    def test_signs_spelling_and_unresolved_standins(self):
        gold = parse_gold("0|10-30|QKl P R & v j #")[0]
        self.assertEqual(gold.glyphs, "QKLPR&HI#")
        self.assertEqual(gold.letters, "quequilpourparetui#")
        machine = parse_machine("0 M[M] L[L] v[H] j[I]")[0]
        self.assertEqual(machine.letters, "MLui")

    def test_alternatives_are_retained_without_oracle_selection(self):
        row = parse_machine("0 sil[F(G)IL] nous[ABHG(FH)] #[#(M)]")[0]
        self.assertEqual(row.glyphs, "FILABHG#")
        self.assertEqual(len(row.alternatives), 3)
        self.assertEqual(row.alternatives[1]["glyph_index"], 6)

    def test_strict_formats_row_ids_and_unavailable_gold(self):
        for text in ["", "0|||extra", "0||é", "0|30-10|abc", "0||=", "0||abc\n0||abc", "1||a\n0||b"]:
            with self.subTest(gold=text), self.assertRaises(ValueError):
                parse_gold(text)
        for text in ["", "bad a[A]", "0 bareword", "0 a[A()]", "0 a[A(B]", "0 a[A] garbage", "0 a[Z]", "0 a[A]\n0 a[A]"]:
            with self.subTest(machine=text), self.assertRaises(ValueError):
                parse_machine(text)
        with self.assertRaises(ValueError):
            score_pair(parse_gold("0||a"), parse_machine("1 a[A]"))
        with self.assertRaises(ValueError):
            score_pair(parse_gold("0||=M"), parse_machine("0 m[M]"))

    def test_placeholder_policy_and_page_line_difference(self):
        result = score_pair(parse_gold("0||a#"), parse_machine("0 a[A] #[#]"))
        self.assertEqual(result["glyph"]["reference_length"], 2)
        self.assertEqual(result["letter"]["reference_length"], 1)
        self.assertEqual(result["letter_with_name_placeholders_sensitivity"]["reference_length"], 2)
        self.assertIsNone(result["coverage"]["name_identity_accuracy"])
        # A boundary shift may cancel at page level, but not line level.
        shifted = score_pair(parse_gold("0||a\n1||b"), parse_machine("0 ab[AB]\n1 #[#]"))
        self.assertEqual(shifted["letter"]["edit_errors"], 0)
        self.assertEqual(shifted["letter"]["sum_of_per_line_errors"], 2)

    def test_pinned_snapshot_regression_and_stable_identity(self):
        args = [(PACKAGE / path).read_bytes() for path in ["inputs/f179r.txt", "inputs/f179r_machine_blind.txt", "manifest.json"]]
        one, two = make_report(*args), make_report(*args)
        self.assertEqual(one["run_id"], two["run_id"])
        result = one["results"]
        self.assertEqual(result["coverage"]["line_ids"], list(range(21)))
        self.assertEqual((result["glyph"]["edit_errors"], result["glyph"]["reference_length"]), (4, 1301))
        self.assertEqual((result["letter"]["edit_errors"], result["letter"]["reference_length"]), (23, 1369))
        self.assertEqual(result["coverage"]["gold_name_placeholders"], 4)

    def test_manifest_identity_schema_duplicate_keys_and_tamper(self):
        data = (PACKAGE / "manifest.json").read_bytes()
        original = check_manifest(data)
        for key, value in [("commit", "wrong"), ("schema", "wrong"), ("inputs", {})]:
            altered = {**original, key: value}
            with self.subTest(key=key), self.assertRaises(ValueError):
                check_manifest(json.dumps(altered).encode())
        altered = json.loads(data)
        altered["inputs"]["gold"]["sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            check_manifest(json.dumps(altered).encode())
        with self.assertRaises(ValueError):
            check_manifest(b'{"schema":"a","schema":"b"}')
        with self.assertRaises(ValueError):
            check_snapshot("gold", (PACKAGE / "inputs/f179r.txt").read_bytes() + b"\n")

    def test_cli_explicit_paths_and_report_schema(self):
        completed = cli()
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(json.loads(completed.stdout)["schema"], "desportes-saved-report-v1")
        missing_args = subprocess.run([sys.executable, "-B", str(PACKAGE / "score_saved.py")], capture_output=True)
        self.assertNotEqual(missing_args.returncode, 0)

    def test_cli_failure_has_no_report_and_preserves_existing_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            report = temp / "result.json"
            report.write_bytes(b"previous frozen result\n")
            failed = cli("--output", report)
            self.assertNotEqual(failed.returncode, 0)
            self.assertEqual(report.read_bytes(), b"previous frozen result\n")
            self.assertEqual(failed.stdout, "")
            for options in [("--gold", temp / "missing"), ("--machine", temp), ("--output", temp / "missing/result.json")]:
                failed = cli(*options)
                self.assertNotEqual(failed.returncode, 0)
                self.assertEqual(failed.stdout, "")
            corrupt = temp / "corrupt.txt"
            corrupt.write_bytes(b"0 a[A]\n")
            new_report = temp / "new.json"
            failed = cli("--gold", corrupt, "--output", new_report)
            self.assertNotEqual(failed.returncode, 0)
            self.assertFalse(new_report.exists())
            corrupt.write_bytes(b"\xff")
            failed = cli("--manifest", corrupt, "--output", new_report)
            self.assertNotEqual(failed.returncode, 0)
            self.assertFalse(new_report.exists())
            accepted = cli("--output", new_report)
            self.assertEqual(accepted.returncode, 0, accepted.stderr)
            self.assertEqual(json.loads(new_report.read_text())["results"]["glyph"]["edit_errors"], 4)


if __name__ == "__main__":
    unittest.main()
