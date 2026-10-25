import unittest
from trace import validate

class TraceTests(unittest.TestCase):
    def test_detects_gaps_and_orphans(self):
        report=validate([{"id":"R1","test_ids":"T1"},{"id":"R2","test_ids":""}],[{"test_id":"T1"},{"test_id":"T2"}])
        kinds={item["kind"] for item in report["issues"]}; self.assertIn("uncovered_requirement",kinds); self.assertIn("orphan_test",kinds); self.assertFalse(report["ok"])

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
if __name__=="__main__": unittest.main()
