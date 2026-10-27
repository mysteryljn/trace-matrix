import csv
import tempfile
import unittest
from pathlib import Path

from trace import main, read_csv, validate

class TraceTests(unittest.TestCase):
    def test_detects_gaps_and_orphans(self):
        report=validate([{"id":"R1","test_ids":"T1"},{"id":"R2","test_ids":""}],[{"test_id":"T1"},{"test_id":"T2"}])
        kinds={item["kind"] for item in report["issues"]}; self.assertIn("uncovered_requirement",kinds); self.assertIn("orphan_test",kinds); self.assertFalse(report["ok"])

    def test_rejects_empty_traceability_exports(self):
        report = validate([], [])
        self.assertIn({"kind":"empty_requirements"}, report["issues"])
        self.assertIn({"kind":"empty_tests"}, report["issues"])
        self.assertFalse(report["ok"])

    def test_detects_duplicate_requirement_ids(self):
        report=validate(
            [{"id":"R1","test_ids":"T1"},{"id":"R1","test_ids":"T2"}],
            [{"test_id":"T1"},{"test_id":"T2"}],
        )
        self.assertIn({"kind":"duplicate_requirement_id","id":"R1"}, report["issues"])
        self.assertFalse(report["ok"])

    def test_handles_missing_csv_cells(self):
        report=validate(
            [{"id":None,"test_ids":None}],
            [{"test_id":None}],
        )
        self.assertIn({"kind":"missing_requirement_id"}, report["issues"])
        self.assertIn({"kind":"uncovered_requirement","id":""}, report["issues"])
        self.assertFalse(report["ok"])

    def test_duplicate_scan_does_not_require_quadratic_list_count(self):
        class CountForbiddenList(list):
            def count(self, value):
                raise AssertionError("duplicate detection must use one-pass counts")

        report=validate(
            CountForbiddenList([{"id":"R1","test_ids":"T1"},{"id":"R2","test_ids":"T2"}]),
            CountForbiddenList([{"test_id":"T1"},{"test_id":"T2"}]),
        )
        self.assertTrue(report["ok"])

    def test_rejects_rows_with_extra_csv_fields(self):
        report=validate(
            [{"id":"R1","test_ids":"T1",None:["unexpected"]}],
            [{"test_id":"T1"}],
        )
        self.assertIn(
            {"kind":"extra_csv_fields","source":"requirements","row":1,"count":1},
            report["issues"],
        )
        self.assertFalse(report["ok"])

    def test_rejects_unterminated_quoted_csv(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "requirements.csv"
            path.write_text(
                "id,description,test_ids\nR1,Requirement,\"T1\n",
                encoding="utf-8",
            )
            with self.assertRaises(csv.Error):
                read_csv(path)

    def test_rejects_duplicate_csv_headers(self):
        # DictReader keeps only the last value for a repeated header, which
        # can silently discard a requirement ID and make bad traceability
        # data appear valid.
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "requirements.csv"
            path.write_text(
                "id,id,test_ids\nR1,R2,T1\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(csv.Error, "duplicate CSV header"):
                read_csv(path)

    def test_rejects_non_utf8_csv_without_traceback(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "requirements.csv"
            path.write_bytes(b"id,test_ids\nR1,T1\n\xff\xfe")
            with self.assertRaises(csv.Error):
                read_csv(path)

            tests_path = Path(directory) / "tests.csv"
            tests_path.write_text("test_id\nT1\n", encoding="utf-8")
            exit_code = main([str(path), str(tests_path)])
            self.assertEqual(exit_code, 2)

if __name__=="__main__": unittest.main()
