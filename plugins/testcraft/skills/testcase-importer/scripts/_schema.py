"""Canonical test-case schema — single source of truth for the testcase-importer skill.

Imported by both normalize_testcases.py (writer) and render_console.py (reader) so the
10-column contract is defined exactly once within this skill.

Note: the sibling userflow-to-testcases skill deliberately keeps its own copy of this list
(in validate_cases.py). Each skill ships as a self-contained bundle — the installer copies
only a skill's own dir into the universal store — so importing across skill boundaries would
break a standalone install. Cross-skill repetition of this constant is intentional.
"""

CANON = ["ID", "Group", "Type", "Outcome", "Priority", "Severity_Reasoning",
         "Transition", "Title", "Steps / Test Data",
         "Expected Result + Downstream Impact / Fix"]
