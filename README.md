# FitFindr

> ### 👋 Start here
>
> **New to this repo? Read [RUNNING.md](RUNNING.md) first** — setup, every
> command, and what to do when something breaks.
>
> Once `python test.py` passes:
>
> ```bash
> python app.py listings --full -n 6      # read the data (Milestone 1)
> python app.py fields                    # what you can filter on
> python app.py ask 'vintage graphic tee under $30'
> ```
>
> All three tools are stubs, so that last command will do nothing useful yet.
> That's the starting position.
>
> **The rest of this file is your submission.** Fill it in as you go.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     HOW TO USE THIS FILE

     This is your submission. Fill each section in as you finish the milestone
     it belongs to — don't leave it all to the end.

     Unit 3 asks for the first five sections. Unit 4 adds the five below them.
     Leave the unit 4 sections alone until then; they're here so you know
     what's coming.

     Everything is pasted as TEXT. No screenshots, no images, no video links.
     A typed block of output gets full credit; a picture of the same output
     gets none.
     ───────────────────────────────────────────────────────────────────────── -->

<!-- ═══════════════════════ UNIT 3 — THE BUILD ═══════════════════════ -->

## Milestone 1 — Data Review and Starter Run

Reviewed the six complete records `lst_001` through `lst_006`: Levi's jeans,
butterfly baby tee, oversized flannel, track jacket, corduroy pants, and
bootleg-style graphic tee.

Listing field names:

- `id`, `title`, `description`, `category`
- `style_tags`, `size`, `condition`, `price`
- `colors`, `brand`, `platform`

Three fields to remember are `category`, `size`, and `price`. `price` is
numeric; `colors` and `style_tags` are lists of strings. `brand` can be
`null`. Sizes are strings with mixed formats, such as `W30 L30`, `S/M`, and
`XL (oversized)`, so size filtering needs to account for the actual text.
Fit details can appear in the description: the baby tee's tag says medium
but it fits like a small. There is no separate fit or measurements field.

Among these six records, the $18 baby tee and $24 graphic tee both have
`vintage` and `graphic tee` style tags and are below $30. This is a data
observation for the sample query; search is not implemented yet.

The wardrobe passed to `suggest_outfit` is a dictionary with an `items`
list. Each item has `id`, `name`, `category`, `colors`, `style_tags`, and
optional `notes`; the example includes `null` notes. The example wardrobe
contains 10 items. An empty wardrobe returned by the data loader is
`{"items": []}`. The JSON template also has a documentation-only `_note`
that the loader removes.

Ran these commands in the project's virtual environment:

```bash
python app.py fields
python app.py listings --full -n 6
python app.py examples
python app.py ask 'vintage graphic tee under $30'
```

The starter query exited successfully and printed:

```text
  The planning loop isn't built yet — see the TODO in agent.py.

0 model calls this session
```

This is the expected starting behavior for Milestone 1.

---

## What This Does

<!-- Three or four sentences: what a user asks for, and what they get back. -->



---

## Tool Inventory

<!-- Four lines per tool. This is worth 2 points and it's the single most
     common place students lose them.

     "Returns a list" earns NOTHING. The description has to say what is IN
     the list.

     The empty case isn't optional either — it's the thing your loop branches
     on, and if you don't decide it here you'll discover it as a crash in
     Milestone 5. -->

### `search_listings`

- **What it does:** Searches the local listings by keyword overlap, with optional size and inclusive price filters, without calling the model.
- **Inputs:** `description` (`str`); `size` (`str | None`, default `None` to skip size filtering); `max_price` (`float | None`, default `None` to skip price filtering).
- **Returns:** A `list[dict]` of up to `config.SEARCH_RESULT_LIMIT` (currently 10) matching original listings, each containing `id`, `title`, `description`, `category`, `style_tags` (`list[str]`), `size`, `condition`, `price` (numeric), `colors` (`list[str]`), `brand` (`str | None`), and `platform`; all other fields are strings. Sort by keyword score descending, preserving dataset order for ties.
- **When it has nothing:** Returns `[]` for no matches or a description with no searchable tokens, never `None` or an error string.

Search rules: lowercase and tokenize the description and each listing's
`title`, `description`, `category`, and `style_tags` using `[a-z0-9]+`.
Score one point per distinct query token found in those listing tokens;
keep only positive scores after filtering. Partial keyword overlap is
allowed; no synonyms, stemming, or model-based interpretation. Enforce
`price <= max_price` when a ceiling is supplied.

Size rules: trim whitespace, compare case-insensitively, and remove
parenthetical fit notes. Compare whole size alternatives split on `/`,
with any shared alternative counting as a match: `M` matches `S/M` and
`L` matches `L/XL`, but `L` does not match `XL`. Normalize a bare numeric
shoe size such as `8.5` to `US 8.5`; `8` does not match `US 8.5`, and `S`
does not match `US 9`. A waist-only request `W30` matches `W30 L30`;
a request specifying both waist and length must match both. Normalize
sizes beginning with `One Size` to `One Size`, which only matches a
`One Size` request. Other sizes require exact normalized equality.

### `suggest_outfit`

- **What it does:** Uses `generate()` to suggest one or two outfits combining a selected listing with the user's wardrobe.
- **Inputs:** `new_item` (`dict`, one complete listing with the fields above); `wardrobe` (`dict`) containing `items` (`list[dict]`), whose items have `id`, `name`, `category` (strings), `colors`, `style_tags` (`list[str]`), and optional `notes` (`str | None`).
- **Returns:** A non-empty `str` naming the selected item and specific wardrobe pieces by their supplied names, explaining how their colors or styles work together. It must not invent owned pieces or a brand when `brand` is `None`.
- **When it has nothing:** With `{"items": []}`, returns non-empty general styling advice from `generate()`, explicitly stating that no wardrobe items were supplied and presenting suggested pieces as ideas, not owned items. If the model returns blank text, returns `No outfit suggestion was generated. Please try again.`

### `create_fit_card`

- **What it does:** Uses `generate()` to turn an outfit suggestion and selected listing into a short, post-ready caption.
- **Inputs:** `outfit` (`str`, the suggestion from `suggest_outfit`); `new_item` (`dict`, the same complete listing used for that suggestion).
- **Returns:** A non-empty `str` containing a two-to-four-sentence caption that mentions the item, its listed price, and its platform once each and describes the outfit's specific style. Use the supplied outfit and listing facts; omit an unknown brand rather than inventing one.
- **When it has nothing:** For an empty or whitespace-only `outfit`, returns `Cannot create a fit card without an outfit suggestion.` without calling the model. If the model returns blank text, returns `No fit card was generated. Please try again.`

These are contracts for the upcoming implementation; the tools are still
stubs. Inputs use the dataset shapes above. A model service failure remains
the adapter's `ModelUnavailable` exception, distinct from a valid empty
wardrobe or blank response; the agent's handler is added in Unit 4.

---

## Planning Loop

<!-- Your branch rule, stated as a rule — the condition AND both paths — plus
     the file and function that holds it.

     Like this:
       "If search_listings returns an empty list, put a message in the session
        and stop. Otherwise take the first result and go to suggest_outfit."
        — agent.py::run_agent

     The grader checks your code against what you claim here, so the file and
     function have to be real. -->

**Branch rule:** Store the return value of `search_listings` in
`session["search_results"]`. If it is `[]`, set `session["error"]` to
`No matching listings. Try broader keywords, a different size, or a higher price limit.`
and return the session immediately; `selected_item`, `outfit_suggestion`,
and `fit_card` stay `None`, and neither model tool runs. Otherwise, store
the first result in `session["selected_item"]`, call `suggest_outfit` with
that item and `session["wardrobe"]`, and store its string in
`session["outfit_suggestion"]`. Then call `create_fit_card` with that string
and the same selected item, store it in `session["fit_card"]`, and return
the session.

**Where it lives:** `agent.py::run_agent` (planned for Milestone 5).

**How the query is parsed:** <!-- regex, string splitting, or asking the model — say which -->

**What moves through the session:** <!-- which fields, in what order -->

---

## Sample Run

<!-- Two things go here.

     1. One FULL query and its output, pasted as text.
     2. Your three per-tool terminal tests — the command and what it printed. -->

**One full query**

```
$ python app.py ask '...'

```

**The three tools, tested one at a time**

```
$ python -c "from tools import search_listings; print(search_listings('graphic tee', max_price=30))"

```

```
$ python -c "from tools import suggest_outfit; ..."

```

```
$ python -c "from tools import create_fit_card; ..."

```

---

## How I Used AI

<!-- Two specific moments. What you asked, what came back, what you changed.

     "I used Claude to help me code" is not enough.

     "I gave Claude my search_listings spec. It returned None on no match
     instead of an empty list, so I changed it" is the level we want. -->

**Moment 1**

- *What I asked for:*
- *What came back:*
- *What I changed:*

**Moment 2**

- *What I asked for:*
- *What came back:*
- *What I changed:*

<!-- ═══════════════════════ UNIT 4 — THE TEST ═══════════════════════

     Don't fill these in during unit 3.
     ═══════════════════════════════════════════════════════════════════ -->

---

## Run Log — Before

<!-- Five criteria, five tries each, in this exact format.

     Five, because your criteria are written out of five. Mark each try PASS
     or FAIL, count the passes, and read that count against your target — a
     row targeting 4 of 5 with three PASS cells is MISSED (3/5).

     `python run_eval.py --label before` runs everything and writes the table
     into results/. Paste it here and fill in the verdicts. -->

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Real output from one try**, pasted as text, naming the file and function
that produced it:

```

```

---

## Verdicts and Diagnoses

<!-- MET or MISSED per criterion against LAST UNIT's target, plus a sentence on
     how you decided.

     Then, for every miss: which of the four places it happened — a tool, the
     loop's branch, the session, or the model's output — AND the mechanism.

     Not a diagnosis:  "The fit card was bad."
     A diagnosis:      "The fit card criterion missed on 2 of 5 items. Both had
                        an empty brand field. My prompt puts the brand in the
                        first sentence, so the card opened with a blank and read
                        like a fragment. The tool worked; the prompt assumed a
                        field that isn't always there."

     Look for a pattern. Three misses on the same tool is one problem, not
     three. -->

| # | Criterion | Target | Verdict | How I decided |
|---|---|---|---|---|
| 1 |  |  |  |  |
| 2 |  |  |  |  |
| 3 |  |  |  |  |
| 4 |  |  |  |  |
| 5 |  |  |  |  |

**Diagnoses**



---

## Loop Trace

<!-- One full run, printed step by step, with the MCP call visible in it.

     `python app.py ask '...' --trace` once you've added the trace.step()
     calls in Milestone 2.

     Worth pasting BOTH the happy path and the empty-search path. The empty
     one should be visibly shorter, because it stops. If your two traces are
     the same length, your branch isn't working — and this is the fastest way
     anyone will ever find that out. -->

**Happy path**

```

```

**Empty search**

```

```

**On the MCP move:** <!-- what changed in your code, and whether anything
behaved differently afterwards. If the rewire didn't work, say exactly where it
broke — the error text and the last thing that worked. That earns the point in
full. -->



---

## The Improvement

<!-- What you changed, why your diagnosis pointed at it, and the after-run in
     the same table format. One change, measured properly.

     `python run_eval.py --label after` -->

**What I changed:**

**Which failure it was meant to fix:**

### Run Log — After

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Did it help, and how do I know:**

<!-- If it made things worse, say that. Honestly reported, that earns full
     credit and is more interesting than one that worked. -->



---

## What's Still Broken

<!-- For each criterion still missed: what you'd do, and why you stopped where
     you did. "I ran out of time" is fine if it's true. Pretending nothing is
     left is not. -->



<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST — unit 3

       [ ] criteria.md has five numbered criteria, each with a target
       [ ] Each criterion has a reason underneath it
       [ ] All five unit 3 sections above have real content
       [ ] Tool Inventory: all three tools, inputs WITH TYPES, a specific
           return value, and the empty case
       [ ] Planning Loop names the branch rule and agent.py::run_agent
       [ ] Sample Run: one full query plus the three per-tool tests, as text
       [ ] At least four new commits
       [ ] Repository URL submitted — WRITE IT DOWN, you submit the same one
           next unit

     SUBMISSION CHECKLIST — unit 4

       [ ] mcp_server.py exists with one tool registered
           (or a written record of exactly where the rewire broke)
       [ ] Run Log — Before, five criteria, five tries each
       [ ] Real output pasted underneath, naming file and function
       [ ] A verdict on every criterion
       [ ] A diagnosis for every miss, naming a place AND a mechanism
       [ ] Loop Trace, with the MCP call visible in it
       [ ] All three failure modes triggered and handled
       [ ] One improvement, with Run Log — After in the same format
       [ ] What's Still Broken
       [ ] At least four new commits
       [ ] The SAME repository URL as last unit

     Do not delete and recreate this repository. Your commit history is what
     shows your criteria existed before your results did.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**
