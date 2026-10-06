"""
The runs your test needs. ← UNIT 4, MILESTONE 3

Each of your five criteria needs something run against it. A criterion about
the empty-search branch needs an impossible query. One about the fit card needs
the same item run more than once. Working that out is Milestone 3's first step,
and this file is where you write it down.

`run_eval.py` runs everything here five times and writes the run log — five
because your criteria are written out of five.

One scenario per criterion, using the exact inputs fixed in criteria.md.
"""

SCENARIOS = [
    {"name": "Full three-tool run returns a fit card", "query": "vintage graphic tee under $30, size M", "wardrobe": "example", "criterion": 1},
    {"name": "Empty search stops before model tools", "query": "designer ballgown size XXS under $5", "wardrobe": "example", "criterion": 2},
    {"name": "Complete state matches tool arguments", "query": "vintage graphic tee under $30, size M", "wardrobe": "example", "criterion": 3},
    {"name": "Fit card length and listing facts", "query": "vintage graphic tee under $30, size M", "wardrobe": "example", "criterion": 4},
    {"name": "Empty wardrobe gets useful advice", "query": "vintage graphic tee under $30, size M", "wardrobe": "empty", "criterion": 5},
]

WARDROBES = ("example", "empty")


def validate() -> list[str]:
    """Complain about anything malformed, before a long run rather than during."""
    problems = []
    for i, scenario in enumerate(SCENARIOS, 1):
        if not scenario.get("query", "").strip():
            problems.append(f"scenario {i} has no query")
        if scenario.get("wardrobe") not in WARDROBES:
            problems.append(
                f"scenario {i} has wardrobe {scenario.get('wardrobe')!r} — "
                f"it should be one of {WARDROBES}"
            )
    if sorted((s.get("criterion") for s in SCENARIOS), key=str) != [1, 2, 3, 4, 5]:
        problems.append("Expected exactly one scenario for each criterion 1–5")
    return problems
