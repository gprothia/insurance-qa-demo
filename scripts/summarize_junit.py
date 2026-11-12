"""Turns pytest JUnit XML into a Markdown "acceptance criteria → result" table.

Usage: python scripts/summarize_junit.py junit.xml > summary.md
"""

import re
import sys
import xml.etree.ElementTree as ET

NAME = re.compile(r"test_([A-Z]+)_(\d+)_(AC\d+)_(\w+?)(?:\[(\w+)\])?$")


def main(path: str) -> None:
    root = ET.parse(path).getroot()
    rows, passed, failed = [], 0, 0
    for case in root.iter("testcase"):
        bad = case.find("failure") is not None or case.find("error") is not None
        skipped = case.find("skipped") is not None
        result = "⏭️ skipped" if skipped else ("❌ failed" if bad else "✅ passed")
        failed += bad
        passed += not bad and not skipped
        kind = "UI" if ".ui." in case.get("classname", "") else "API"
        m = NAME.match(case.get("name", ""))
        if m:
            key, ac, desc = f"{m[1]}-{m[2]}", m[3], m[4].replace("_", " ")
        else:
            key, ac, desc = "—", "—", case.get("name", "")
        rows.append((key, ac, kind, desc, result))

    status = "✅ All acceptance tests passed" if failed == 0 else f"❌ {failed} acceptance test(s) failed"
    print(f"### Spec-driven test results: {status}\n")
    print(f"{passed} passed · {failed} failed · ran in an ephemeral GKE Autopilot namespace\n")
    print("| Jira | AC | Layer | Test | Result |")
    print("|---|---|---|---|---|")
    for row in sorted(rows):
        print("| " + " | ".join(row) + " |")


if __name__ == "__main__":
    main(sys.argv[1])
