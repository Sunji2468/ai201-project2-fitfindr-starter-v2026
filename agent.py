"""
The FitFindr planning loop.

This is the file that makes FitFindr an agent rather than a script. It decides
which tool to run next based on what the last one returned.

If your loop calls all three tools no matter what comes back, you have a list
of function calls. A loop looks at the last result before it picks the next
step. **That branch is the graded part of this unit.**

Build and test your three tools in `tools.py` first. Then come here.

    python agent.py          runs both example paths below
"""

import re

import config
import trace
import mcp_client
from tools import suggest_outfit, create_fit_card
from generate import ModelUnavailable


# ── session state ─────────────────────────────────────────────────────────────

def new_session(query: str, wardrobe: dict) -> dict:
    """
    A fresh session for one user interaction.

    The session is the single source of truth for a run. Every tool result goes
    in here, and the next tool reads it back out.

    You could pass values straight from one call to the next. It would work,
    and you would not be able to test it — you can't print a variable you have
    already overwritten. Going through the session is what makes the state
    visible, and unit 4 has you write a criterion about exactly that.

    Add fields if you need them.
    """
    return {
        "query": query,              # what the user typed
        "parsed": {},                # description / size / max_price you pulled out of it
        "search_results": [],        # everything search_listings returned
        "selected_item": None,       # the one you chose — goes into suggest_outfit
        "wardrobe": wardrobe,        # the user's wardrobe
        "outfit_suggestion": None,   # what suggest_outfit returned
        "fit_card": None,            # what create_fit_card returned
        "error": None,               # set when the run ended early
    }


# ── planning loop ─────────────────────────────────────────────────────────────

def parse_query(query: str) -> dict:
    """Extract an optional price ceiling and size; keep remaining keywords."""
    price_pattern = r"\b(?:under|up to|max(?:imum)?(?: price)?)\s*\$?\s*(\d+(?:\.\d+)?)\b"
    size_pattern = (
        r"\b(?:in\s+)?size\s+"
        r"(one\s+size|w\d+(?:\s+l\d+)?|(?:us\s*)?\d+(?:\.\d+)?|"
        r"(?:xxxs|xxs|xs|xxxl|xxl|xl|s|m|l)(?:\s*/\s*(?:xxxs|xxs|xs|xxxl|xxl|xl|s|m|l))?)"
        r"(?![\w./])"
    )
    price = re.search(price_pattern, query, re.I)
    size = re.search(size_pattern, query, re.I)
    description = re.sub(price_pattern, " ", query, flags=re.I)
    description = re.sub(size_pattern, " ", description, flags=re.I)
    description = re.sub(r"^\s*(?:looking for|find me|find|show me)\s+", "", description, flags=re.I)
    description = re.sub(r"^\s*(?:a|an|the)\s+", "", description, flags=re.I)
    description = " ".join(description.replace(",", " ").split()).strip()
    return {
        "description": description,
        "size": size.group(1).strip() if size else None,
        "max_price": float(price.group(1)) if price else None,
    }


def run_agent(query: str, wardrobe: dict, *, use_trace: bool = False) -> dict:
    """Run tools through session state; optionally trace steps and handled failures."""
    trace.start_trace()
    session = new_session(query, wardrobe)
    session["parsed"] = parse_query(session["query"])
    if use_trace:
        trace.step("parse_query", inputs=query, returned=session["parsed"])
    next_step = "search"
    iterations = 0
    while True:
        iterations += 1
        trace.check_iterations(iterations)
        if next_step == "search":
            name = "search_listings (via MCP)"
            inputs = session["parsed"]
        elif next_step == "outfit":
            name = "suggest_outfit"
            inputs = {"new_item": session["selected_item"], "wardrobe": session["wardrobe"]}
        else:
            name = "create_fit_card"
            inputs = {"new_item": session["selected_item"], "outfit": session["outfit_suggestion"]}
        try:
            if next_step == "search":
                session["search_results"] = mcp_client.call_tool("search_listings", inputs)
                result = session["search_results"]
                if not result:
                    session["error"] = (
                        "No matching listings. Try broader keywords, a different size, "
                        "or a higher price limit."
                    )
                    if use_trace:
                        trace.step(name, inputs=inputs, returned=result,
                                   note="branch: empty search; stopping before model tools")
                    return session
                if use_trace:
                    trace.step(name, inputs=inputs, returned=result)
                session["selected_item"] = session["search_results"][0]
                if use_trace:
                    trace.step("select_item", inputs="first search result",
                               returned=session["selected_item"])
                next_step = "outfit"
            elif next_step == "outfit":
                session["outfit_suggestion"] = suggest_outfit(**inputs)
                if use_trace:
                    trace.step(name, inputs=inputs, returned=session["outfit_suggestion"],
                               note=f"wardrobe items: {len(session['wardrobe']['items'])}")
                next_step = "card"
            else:
                session["fit_card"] = create_fit_card(**inputs)
                if use_trace:
                    trace.step(name, inputs=inputs, returned=session["fit_card"])
                return session
        except ModelUnavailable:
            # Do not surface raw provider errors, which may contain request details.
            session["error"] = (
                f"The model request failed during {name}. Check GEMINI_API_KEY in "
                ".env and your internet connection, then retry. If you hit a rate "
                "limit, wait a minute before retrying."
            )
            if use_trace:
                trace.step(name, inputs=inputs, returned=session["error"],
                           note="model unavailable; stopping")
            return session


# ── running it directly ───────────────────────────────────────────────────────

def _show(session: dict) -> None:
    if session["error"]:
        print(f"  stopped: {session['error']}")
        print(f"  fit_card is {session['fit_card']!r} — it should still be None here")
        return

    item = session["selected_item"] or {}
    print(f"  found:    {item.get('title')} — ${item.get('price')} on {item.get('platform')}")
    print(f"  outfit:   {session['outfit_suggestion']}")
    print(f"  fit card: {session['fit_card']}")


if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe

    print("=== A query the data can match ===")
    _show(run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    ))

    print("\n=== A query it can't ===")
    _show(run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    ))

    print(
        "\nThe second one should stop before the fit card. If both paths look "
        "the same,\nthe branch isn't doing anything yet."
    )
