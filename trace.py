#!/usr/bin/env python3
import argparse
import csv
import json
from collections import Counter
from pathlib import Path

def read_csv(path):
    # ``DictReader`` is permissive by default: an unterminated quoted field
    # can consume the rest of the file and still produce a seemingly valid
    # row.  That can make a broken traceability file pass validation in CI.
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle, strict=True))

def _clean(value):
    """Normalize a CSV cell, including omitted trailing cells.

    ``csv.DictReader`` stores a row that omits a trailing column as ``None``.
    Treating that as an empty cell lets validation report the malformed
    traceability data instead of failing with ``AttributeError``.
    """
    return "" if value is None else str(value).strip()

def validate(requirements,tests):
    issues=[]
    # An empty export is almost always a missing or truncated input file.  It
    # must fail closed: otherwise two empty CSVs produce ``ok: true`` and a CI
    # job can report complete traceability without checking any requirement.
    if not requirements:
        issues.append({"kind":"empty_requirements"})
    if not tests:
        issues.append({"kind":"empty_tests"})
    for source, rows in (("requirements", requirements), ("tests", tests)):
        for row_number, row in enumerate(rows, 1):
            # ``csv.DictReader`` stores values beyond the declared header under
            # a ``None`` key.  Ignoring those values can make a malformed row
            # appear fully covered, so report it as invalid traceability data.
            extras = row.get(None) if isinstance(row, dict) else None
            if extras:
                issues.append({
                    "kind": "extra_csv_fields",
                    "source": source,
                    "row": row_number,
                    "count": len(extras),
                })
    requirement_ids=[_clean(row.get("id")) for row in requirements]
    requirement_counts=Counter(requirement_ids)
    duplicate_requirements={item for item, count in requirement_counts.items() if item and count>1}
    for item in sorted(duplicate_requirements): issues.append({"kind":"duplicate_requirement_id","id":item})
    test_ids=[_clean(row.get("test_id")) for row in tests]; known=set(test_ids)
    test_counts=Counter(test_ids)
    duplicates={item for item, count in test_counts.items() if item and count>1}
    for item in sorted(duplicates): issues.append({"kind":"duplicate_test_id","id":item})
    referenced=set()
    for row in requirements:
        rid=_clean(row.get("id")); links=[x.strip() for x in _clean(row.get("test_ids")).split(";") if x.strip()]; referenced.update(links)
        if not rid: issues.append({"kind":"missing_requirement_id"})
        if not links: issues.append({"kind":"uncovered_requirement","id":rid})
        for test_id in links:
            if test_id not in known: issues.append({"kind":"missing_test","requirement":rid,"test_id":test_id})
    for test_id in sorted(known-referenced): issues.append({"kind":"orphan_test","test_id":test_id})
    return {"requirements":len(requirements),"tests":len(tests),"issues":issues,"ok":not issues}

def main(argv=None):
    parser=argparse.ArgumentParser(description="Validate requirements-to-tests traceability"); parser.add_argument("requirements",type=Path); parser.add_argument("tests",type=Path); args=parser.parse_args(argv)
    try: report=validate(read_csv(args.requirements),read_csv(args.tests))
    except (OSError, csv.Error) as exc:
        print(f"error: {exc}")
        return 2
    print(json.dumps(report,indent=2,ensure_ascii=False)); return 0 if report["ok"] else 1

if __name__=="__main__": raise SystemExit(main())
