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
> The three tools and planning loop are implemented. The query above runs
> search, outfit suggestions, and a fit card; an empty search stops early.
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
observation for the sample query; search was not implemented at this milestone.

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

FitFindr is being built to turn a thrift-shopping request such as
`vintage graphic tee under $30` into a matching find, outfit advice, and a
short caption. Its standalone search tool filters 40 local sample listings
by keywords, size, and price; its two model tools suggest outfits using a
supplied wardrobe and write a two-to-four-sentence fit card. An empty
wardrobe receives general styling advice, and an empty search returns `[]`.
The CLI runs those tools through a shared session, choosing the first match
or stopping with suggestions to change the search when nothing matches.


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

The tools and agent loop now implement the contracts and branch below.
Inputs use the dataset shapes above. A model service failure remains
the adapter's `ModelUnavailable` exception, distinct from a valid empty
wardrobe or blank response. The agent now catches it, sets `session["error"]`
with recovery steps, and returns without calling later tools.

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

**Branch rule:** Call `mcp_client.call_tool("search_listings", session["parsed"])`
and store its return value in
`session["search_results"]`. If it is `[]`, set `session["error"]` to
`No matching listings. Try broader keywords, a different size, or a higher price limit.`
and return the session immediately; `selected_item`, `outfit_suggestion`,
and `fit_card` stay `None`, and neither model tool runs. Otherwise, store
the first result in `session["selected_item"]`, call `suggest_outfit` with
that item and `session["wardrobe"]`, and store its string in
`session["outfit_suggestion"]`. Then call `create_fit_card` with that string
and the same selected item, store it in `session["fit_card"]`, and return
the session.

**Where it lives:** `agent.py::run_agent`.

**How the query is parsed:** `agent.py::parse_query` uses case-insensitive
regular expressions for `under`, `up to`, or `max` price clauses and sizes
introduced by `size` (letters, slash alternatives, US shoe sizes, waist and
optional length, or One Size). It removes these clauses and leading phrases
such as “looking for a” to produce the remaining search description. The
price ceiling is inclusive. This is a limited parser, not general natural
language understanding; unsupported phrasings may remain search keywords.

**What moves through the session:** `query` and `wardrobe` are stored first,
then `parsed` → `search_results` → `selected_item` → `outfit_suggestion` →
`fit_card`. Each tool result is stored before the next tool reads it from the
session. The empty-search branch sets `error` and returns with later fields
still `None`. A loop advances through search, outfit, and card steps and calls
`trace.check_iterations` before each step to enforce `MAX_ITERATIONS`.
With `--trace`, parsing, the MCP search, item selection, and both model tools
are printed through `trace.step()`. A model failure preserves completed state,
sets `error`, and stops; tracing is silent by default.

---

## Sample Run

<!-- Two things go here.

     1. One FULL query and its output, pasted as text.
     2. Your three per-tool terminal tests — the command and what it printed. -->

**One full query — Milestone 5**

```text
$ python app.py ask 'vintage graphic tee under $30'
  Found:    Y2K Baby Tee — Butterfly Print — $18.0 on depop

  Outfit:   **Outfit 1: Y2K Streetwear**
Pair the Y2K Baby Tee — Butterfly Print with the Baggy straight-leg jeans, dark wash, Chunky white sneakers, and Black crossbody bag.
*Why it works:* The fitted crop length of the baby tee balances the loose, relaxed volume of the dark wash straight-leg jeans for a classic early 2000s silhouette, while the white sneakers tie in the white tones of the butterfly graphic.

**Outfit 2: Casual Grunge**
Combine the Y2K Baby Tee — Butterfly Print with the Wide-leg khaki trousers, Vintage black denim jacket, and Black combat boots.
*Why it works:* The earthy tan trousers ground the playful pink and purple butterfly print, and layering the slightly cropped black denim jacket with black combat boots adds an edgy contrast to the sweet cottagecore and Y2K aesthetic.

  Fit card: Channel classic early 2000s energy by pairing this Y2K Baby Tee — Butterfly Print with baggy straight-leg jeans, chunky white sneakers, and a black crossbody bag for the ultimate Y2K streetwear vibe. Snag this fitted crop top for $18.00 exclusively on depop to complete your nostalgic look.

2 model calls this session, 1217 prompt + 252 output tokens
```

```text
$ python app.py ask 'designer ballgown size XXS under $5'
  No matching listings. Try broader keywords, a different size, or a higher price limit.

0 model calls this session
```

The full sessions and identity-check results are saved in
[results/milestone5_checks.json](results/milestone5_checks.json). After the
live CLI run, a second run used the normal response cache and wrapped
`suggest_outfit` to inspect its actual arguments: its item was the same
object as `session["selected_item"]` and `session["search_results"][0]`.
The impossible query never called that tool and kept `fit_card` as `None`.

All 11 local checks passed with `python -m unittest discover -s tests -v`,
including tool order, session identity, parsing, the iteration guard, and
stopping before model tools on empty search. These are implementation checks,
not the next unit's five-try acceptance evaluations. The live caption's word
“exclusively” is not supported by the listing; factual embellishment remains
a model-output limitation to evaluate.

**The three tools, tested one at a time — Milestone 4**

Run from the repo with `.venv` activated. These are actual terminal outputs.
These standalone checks were recorded before the loop was implemented.
The completed loop runs appear above.

```text
$ python -c "from tools import search_listings; print(search_listings('graphic tee', size='M', max_price=30)); print('No matches:', search_listings('designer ballgown', size='XXS', max_price=5))"
[{'id': 'lst_002', 'title': 'Y2K Baby Tee — Butterfly Print', 'description': 'Super cute early 2000s baby tee with butterfly graphic. Fitted crop length. Tag says medium but fits like a small.', 'category': 'tops', 'style_tags': ['y2k', 'vintage', 'graphic tee', 'cottagecore'], 'size': 'S/M', 'condition': 'excellent', 'price': 18.0, 'colors': ['white', 'pink', 'purple'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_017', 'title': 'Mesh Long-Sleeve Top — Black', 'description': 'Sheer black mesh long-sleeve. Great for layering under a graphic tee or over a bralette. Stretchy material, fits true to size.', 'category': 'tops', 'style_tags': ['y2k', 'grunge', 'goth', 'layering'], 'size': 'S/M', 'condition': 'excellent', 'price': 15.0, 'colors': ['black'], 'brand': None, 'platform': 'depop'}]
No matches: []
```

```text
$ python -c "from tools import suggest_outfit; from utils.data_loader import get_example_wardrobe, get_empty_wardrobe, load_listings; item = load_listings()[5]; print('With wardrobe:', suggest_outfit(item, get_example_wardrobe())); print('Empty wardrobe:', suggest_outfit(item, get_empty_wardrobe()))"
With wardrobe: **Outfit 1: Effortless Grunge Streetwear**
*   Graphic Tee — 2003 Tour Bootleg Style
*   Baggy straight-leg jeans, dark wash
*   Black combat boots
*   Black crossbody bag

**Why it works:** The black-on-dark color palette leans directly into the vintage grunge aesthetic of the tee. Pairing the boxy graphic tee with Baggy straight-leg jeans creates a balanced, relaxed silhouette, while the Black combat boots and Black crossbody bag anchor the outfit with matching dark hardware and textures.

**Outfit 2: Casual Contrast**
*   Graphic Tee — 2003 Tour Bootleg Style
*   Wide-leg khaki trousers
*   Chunky white sneakers

**Why it works:** The tan and khaki tones of the trousers soften the heavy, faded black of the tee, offering an earth-tone contrast that feels modern and intentional. Finishing with Chunky white sneakers ties in the casual streetwear vibe and lightens up the bottom half of the look.
Empty wardrobe: No wardrobe items were supplied. Here are two ways to style the Graphic Tee — 2003 Tour Bootleg Style:

**Outfit 1: Effortless Grunge**
Pair the tee with distressed light-wash denim and classic black canvas high-top sneakers. Layer an oversized flannel shirt over top for added texture. The casual, worn-in feel of the vintage-style graphic naturally complements the relaxed aesthetic of ripped jeans and grunge layering pieces.

**Outfit 2: Streetwear Edge**
Combine the tee with black cargo trousers and chunky leather boots. Add a silver chain necklace and a black leather crossbody bag. The monochrome black palette creates a sleek, cohesive look that lets the faded tour graphic stand out, while the mix of textures adds visual depth.
```

```text
$ python -c "import config; config.CACHE_ENABLED = False; from tools import create_fit_card; from utils.data_loader import load_listings; from generate import usage; item = load_listings()[5]; cards = [create_fit_card('Pair the tee with baggy dark-wash jeans and chunky white sneakers for a relaxed streetwear outfit.', item) for _ in range(3)]; [print(str(i) + ': ' + card) for i, card in enumerate(cards, 1)]; print('Distinct captions:', len(set(cards))); print('Empty outfit:', create_fit_card('   ', item)); print(usage())"
1: Achieve the ultimate relaxed streetwear aesthetic by styling this vintage-style graphic tee with baggy dark-wash jeans and chunky white sneakers. Grab the piece for $24.0 on depop before it's gone.
2: Channel a relaxed streetwear vibe by styling this Graphic Tee — 2003 Tour Bootleg Style with baggy dark-wash jeans and chunky white sneakers. This vintage-inspired piece is available now on depop for $24.00 to complete your grunge aesthetic.
3: Achieve the ultimate relaxed streetwear aesthetic by styling this vintage-style Graphic Tee — 2003 Tour Bootleg Style with baggy dark-wash jeans and chunky white sneakers. This 100% cotton top is currently available on depop for $24.00 to complete your casual grunge look.
Distinct captions: 3
Empty outfit: Cannot create a fit card without an outfit suggestion.
3 model calls this session, 747 prompt + 163 output tokens
```

The caption command temporarily sets `config.CACHE_ENABLED = False` in that
Python process so all three calls reach the model. The normal cache setting
remains enabled, and `config.TEMPERATURE` remains `0.9`. All three captions
were distinct, each used two sentences and included the $24 price and depop
once. Two began similarly, so different wording does not guarantee a different
opening style.

Search returned a mesh top because its description contains “graphic tee.”
This follows the specified keyword-overlap scoring but is a relevance
limitation. The wardrobe output named supplied pieces, while its mention of
“matching dark hardware” was not grounded in the wardrobe data; model prose
still needs review. The empty-wardrobe output explicitly acknowledged that no
items were supplied and offered general ideas.

Additional local checks:

```text
$ python -m unittest discover -s tests -v
Ran 7 tests in 0.003s
OK
```

These checks cover size boundaries, price filtering, empty searches, ranking
and ties, result limits, empty-outfit handling without a model call, blank
model responses, and model failure propagation. They are tool-level checks,
not Unit 4 acceptance evaluations. The acceptance criteria were drafted later, after these development checks;
see the authorship and timing note in `criteria.md`.

---

## How I Used AI

<!-- Two specific moments. What you asked, what came back, what you changed.

     "I used Claude to help me code" is not enough.

     "I gave Claude my search_listings spec. It returned None on no match
     instead of an empty list, so I changed it" is the level we want. -->

**Moment 1**

- *What I asked for:* I gave Codex the Milestone 2 instructions to specify the three tools before implementation.
- *What came back:* Codex read the stubs and data and wrote typed inputs, concrete return shapes, empty cases, and a planned branch rule. It made size matching explicit: `M` can match `S/M`, but `S` must not match `US 9`, and `L` must not match `XL`.
- *What I changed:* The README gained those contracts in commit `1073006`. Codex made these edits directly; I did not manually rewrite the spec in this session. The tools were still stubs at that point.

**Moment 2**

- *What I asked for:* I gave Codex the Milestone 4 instructions to implement and test each tool separately without wiring the loop.
- *What came back:* Codex implemented the three tools, added seven local checks, and ran live wardrobe and caption checks. Three uncached captions differed, but the output also exposed a mesh-top search match based on its description and an unsupported reference to “matching dark hardware” in styling advice.
- *What I changed:* Codex replaced the stubs in `tools.py`, added `tests/test_tools.py`, and pasted actual commands and outputs into this README in commit `ec10b20`. It disabled caching only in the caption comparison process, leaving the normal configuration unchanged. The limitations were documented rather than reported as solved; I have not made a separate manual correction to them.


**Unit 4 — MCP and failure tracing**

- *What I asked for:* I gave Codex the instructions to move one tool onto MCP, trigger the three failure cases, and show the agent's steps.
- *What came back:* Codex registered only `search_listings`, checked its results against direct calls, and confirmed the normal and empty-search paths. It added opt-in traces and a handler for model failures, then captured an actual rejected-key request with caching off.
- *What I changed:* Codex edited `mcp_server.py`, `agent.py`, `app.py`, and the trace formatting, added regression tests, and recorded the real output in commits `dfd2a48` and `f650f11`. The invalid key existed only in a child process; my saved `.env` stayed unchanged. These were direct AI-assisted edits, not changes I separately implemented by hand.

**Unit 4 — Evaluation, diagnosis, and one prompt change**

- *What I asked for:* I asked Codex to run five trials per criterion, challenge the verdicts, fix one diagnosed issue, and rerun the same test.
- *What came back:* Codex captured 25 uncached tries before and 25 after, including real tool arguments for the state criterion. The review found omitted full titles outside the assigned caption-quality row; the after-run fixed those omissions but introduced ambiguous price attribution in one scored caption.
- *What I changed:* Codex replaced one caption instruction with a requirement to copy the full title verbatim, then wrote both scored logs and the comparison in commit `7566044`. I did not manually rewrite the model outputs or change the targets. The README records the mixed result: title inclusion improved from 18/20 to 20/20, while criterion 4 fell from 5/5 to 4/5. Codex also performed the scoring and wording review; it was not an independent human assessment.

---

## Unit 3 Submission Status

Fork URL to submit and reuse in Unit 4:
[Sunji2468/ai201-project2-fitfindr-starter-v2026](https://github.com/Sunji2468/ai201-project2-fitfindr-starter-v2026).
Keep this repository and its commit history for both units.

- The three standalone tools, their contracts, and their terminal checks are recorded above.
- Four new commits already followed starter commit `69997cf`: `c05b1e6`, `1073006`, `ec10b20`, and `9863686`. The Milestone 5 completion adds another commit; the original history is preserved.
- `criteria.md` now has five measurable criteria and five target explanations. At my explicit request, Codex drafted criteria 3–5 and the explanations after development checks. This differs from the assignment’s student-authorship and before-testing instructions; the timing is disclosed in that file.
- Milestone 5 is now complete: the loop and query parser are implemented, both branches were checked, and real sample output and session evidence are recorded. Codex implemented this after I supplied the full assignment, including the previously skipped Milestone 5 instructions.
- The fork URL is saved here. Submission to the course portal has not been performed or verified.

The implementation and write-up are present. The criteria authorship/timing departure above remains disclosed, and course-portal submission still needs confirmation.

<!-- ═══════════════════════ UNIT 4 — THE TEST ═══════════════════════

     Don't fill these in during unit 3.
     ═══════════════════════════════════════════════════════════════════ -->

---

## Run Log — Before

Command: `python run_eval.py --label before`.
Five scenarios, each run five separate times; caching disabled, temperature
`0.9`. Agent code and criteria were unchanged throughout this evaluation.
The runner's observation wrappers called the original tools and copied their
actual arguments and returns; no results were substituted. The runner also
passes `use_trace=True` so the traces are captured.

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1. Full three-tool run returns a fit card | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 2. Empty search stops before model tools | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. Complete state matches tool arguments | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 4. Fit card length and listing facts | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 5. Empty wardrobe gets useful advice | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |

Evidence: [complete run log](results/run_2026-10-06_134724_before.md),
[raw sessions and calls](results/run_2026-10-06_134724_before.json), and
[per-try scoring notes](results/run_2026-10-06_134724_before_scored.json).
All 25 tries completed without a crash. The four model-backed scenarios each
made 10 model requests; empty search made zero. Total: **40 model calls**,
21,648 prompt tokens and 5,033 output tokens. Each model-backed scenario
produced five distinct captions. The starter paced requests when needed.
Scoring combines recorded call/state checks with reading every criterion 4
and 5 output. A 5/5 result on these fixed inputs does not establish reliability
for other inputs or eliminate the limitations noted elsewhere in this README.

**Criterion 1 — actual output from try 1**

Query: `vintage graphic tee under $30, size M`. Produced by `agent.py::run_agent` and `tools.py::create_fit_card`; call order captured by `run_eval.py::run_once`.

```text
search_listings (via MCP) → suggest_outfit → create_fit_card
Embrace classic Y2K street style with this super cute butterfly print baby tee, listed for $18.00 on depop. Pair it with baggy dark wash jeans and chunky white sneakers for a fitted, cropped look that balances effortless volume.
```

**Criterion 2 — actual output from try 1**

Query: `designer ballgown size XXS under $5`. Produced by `agent.py::run_agent`; trace captured by `run_eval.py::run_once`.

```text
[1] parse_query
      in:  designer ballgown size XXS under $5
      out: {'description': 'designer ballgown', 'size': 'XXS', 'max_price': 5.0}
[2] search_listings (via MCP)
      in:  {'description': 'designer ballgown', 'size': 'XXS', 'max_price': 5.0}
      out: [] (empty)
      →    branch: empty search; stopping before model tools
No matching listings. Try broader keywords, a different size, or a higher price limit.
fit_card: None
model_calls: 0
```

**Criterion 3 — actual output from try 1**

Query: `vintage graphic tee under $30, size M`. Session from `agent.py::run_agent`; tool-argument snapshots from `run_eval.py::run_once`. These are complete listing dictionaries, not ID-only comparisons.

```json
{
  "search_results[0]": {
    "id": "lst_002",
    "title": "Y2K Baby Tee — Butterfly Print",
    "description": "Super cute early 2000s baby tee with butterfly graphic. Fitted crop length. Tag says medium but fits like a small.",
    "category": "tops",
    "style_tags": [
      "y2k",
      "vintage",
      "graphic tee",
      "cottagecore"
    ],
    "size": "S/M",
    "condition": "excellent",
    "price": 18.0,
    "colors": [
      "white",
      "pink",
      "purple"
    ],
    "brand": null,
    "platform": "depop"
  },
  "selected_item": {
    "id": "lst_002",
    "title": "Y2K Baby Tee — Butterfly Print",
    "description": "Super cute early 2000s baby tee with butterfly graphic. Fitted crop length. Tag says medium but fits like a small.",
    "category": "tops",
    "style_tags": [
      "y2k",
      "vintage",
      "graphic tee",
      "cottagecore"
    ],
    "size": "S/M",
    "condition": "excellent",
    "price": 18.0,
    "colors": [
      "white",
      "pink",
      "purple"
    ],
    "brand": null,
    "platform": "depop"
  },
  "suggest_outfit.new_item": {
    "id": "lst_002",
    "title": "Y2K Baby Tee — Butterfly Print",
    "description": "Super cute early 2000s baby tee with butterfly graphic. Fitted crop length. Tag says medium but fits like a small.",
    "category": "tops",
    "style_tags": [
      "y2k",
      "vintage",
      "graphic tee",
      "cottagecore"
    ],
    "size": "S/M",
    "condition": "excellent",
    "price": 18.0,
    "colors": [
      "white",
      "pink",
      "purple"
    ],
    "brand": null,
    "platform": "depop"
  },
  "create_fit_card.new_item": {
    "id": "lst_002",
    "title": "Y2K Baby Tee — Butterfly Print",
    "description": "Super cute early 2000s baby tee with butterfly graphic. Fitted crop length. Tag says medium but fits like a small.",
    "category": "tops",
    "style_tags": [
      "y2k",
      "vintage",
      "graphic tee",
      "cottagecore"
    ],
    "size": "S/M",
    "condition": "excellent",
    "price": 18.0,
    "colors": [
      "white",
      "pink",
      "purple"
    ],
    "brand": null,
    "platform": "depop"
  },
  "outfit_argument_matches_session": true
}
```

**Criterion 4 — actual output from try 1**

Query: `vintage graphic tee under $30, size M`. Produced by `tools.py::create_fit_card`, stored by `agent.py::run_agent`.

```text
Pair the Y2K Baby Tee — Butterfly Print with baggy dark wash jeans and chunky white sneakers for the ultimate relaxed streetwear vibe. This super cute cropped top is listed for $18.0 on Depop.
```

**Criterion 5 — actual output from try 1**

Query: `vintage graphic tee under $30, size M`. Empty wardrobe. Produced by `tools.py::suggest_outfit` and `tools.py::create_fit_card`, stored by `agent.py::run_agent`.

```text
No wardrobe items were supplied. Here are two ways to style a Y2K Baby Tee — Butterfly Print:

**Outfit 1: Casual Streetwear**
Pair the baby tee with a pair of low-rise baggy cargo pants in a neutral shade like khaki or olive green, and finish the look with chunky platform sneakers.
*Why it works:* The fitted, feminine silhouette of the crop top balances the relaxed, utilitarian vibe of the cargo pants, creating an effortless Y2K contrast.

**Outfit 2: Sweet & Retro**
Style the tee with a pleated denim mini skirt, pastel platform slides, and a small shoulder bag.
*Why it works:* The white, pink, and purple butterfly graphic pops against the classic denim, while the matching pastel accessories tie the nostalgic 2000s color palette together.

Fit card:
Channel effortless 2000s street style by pairing the Y2K Baby Tee — Butterfly Print with low-rise baggy cargo pants and chunky platform sneakers. Available for $18.0 on depop, this fitted crop top creates the ultimate nostalgic balance.
```

---

## Verdicts and Diagnoses

Verdicts use the five preassigned tries for each criterion from
[the before run](results/run_2026-10-06_134724_before.md), checked against the
unchanged targets in `criteria.md`. Codex re-read the raw outputs and argued
against the initial all-pass scoring; this is an AI-assisted review, not an
independent human evaluation.

| # | Criterion | Target | Verdict | How I decided |
|---|---|---|---|---|
| 1 | Full three-tool run returns a fit card | 4 of 5 | MET (5/5) | All five call records show MCP search, outfit, then card; each session has no error and a non-fallback caption. This criterion explicitly checks completion, not caption quality. |
| 2 | Empty search stops before model tools | 5 of 5 | MET (5/5) | All five runs contain only the MCP search call, return an empty results list, keep fit_card as None, and suggest changing keywords, size, or price. |
| 3 | Complete state matches tool arguments | 5 of 5 | MET (5/5) | Compared the entire first search result and selected-item dictionaries with both downstream new_item arguments in all five snapshots; the outfit argument also equals the stored suggestion, and both calls completed. |
| 4 | Fit card length and listing facts | 4 of 5 | MET (5/5) | The five assigned captions have 2, 2, 3, 3, and 2 sentences; each contains the full title, correct $18 price, and depop once, plus a named wardrobe piece from its outfit. None invents a brand, discount, or exclusivity. |
| 5 | Empty wardrobe gets useful advice | 4 of 5 | MET (5/5) | All five advice strings explicitly acknowledge no supplied items, suggest other pieces with color or silhouette reasons, and produce captions without claiming those pieces are already owned. |

**Diagnoses**

No criterion missed its target in its five assigned tries, so there is no
failed row to diagnose. That does not mean the agent has no defects. The
following findings are outside the scored conditions, not retroactive changes
to the before table:

- **Model output at `tools.py::create_fit_card`: inconsistent full titles.** Criterion 1 tries 1 and 4 say “butterfly print baby tee” instead of the full title `Y2K Baby Tee — Butterfly Print`. The caption prompt asks to mention the item, but does not explicitly require copying its full title, and there is no output check enforcing that requirement. This is a plausible mechanism for the variation: the model paraphrases the item even when the session contains the correct title. These are two examples of the same prompt/validation gap. They pass criterion 1's completion test; they would fail criterion 4's full-title condition if scored under it. Criterion 4's own five preassigned captions all included the title, so its recorded verdict remains MET.
- **Model output at `tools.py::suggest_outfit`: unsupported fit descriptions.** Criterion 4 try 1 describes the khaki trousers as “high-waisted,” although that item's notes are null. Tries 2 and 4 describe the dark jeans as “low-slung,” although their supplied notes say “High-waisted, sits above the hip.” The full wardrobe reaches the tool, so this is not evidence of lost session state. The model adds stereotypical Y2K fit details instead of consistently following the supplied notes; the prompt discourages invented facts but no check rejects these claims. These examples share one grounding problem. The current caption criterion does not score the factual accuracy of outfit prose, so they do not change its verdict.

**Challenge to the verdicts**

The strongest argument against criterion 4 being MET is that two captions
from other runs of the same query omitted the full title. That is real
counterevidence to a broad claim of reliability, but the scenario-to-criterion
mapping was fixed before the run: it does not change which five tries form
criterion 4's row. No tries were replaced, discarded, or rerun to obtain a
pass. The correct conclusion is “MET on this assigned sample,” not “the
caption always satisfies the contract.”

The strongest objection to criterion 5 is try 3's phrase “to complete your
nostalgic wardrobe.” Read in context, the preceding advice explicitly says
no wardrobe items were supplied and offers pieces as suggestions; the caption
does not claim the user owns the cargo pants or sneakers. That satisfies the
written ownership condition. Grammar such as “Here are a general styling
ideas” is poor, but grammatical quality is not one of the criterion's
conditions and cannot be added after observing the result.

**Were the targets too low? What would be tightened?**

The coverage was too narrow for a broad claim that FitFindr works reliably:
all four model-backed scenarios selected the same baby tee, and each used
only one wording of the query. Criteria 2 and 3 already demand 5/5, while
criteria 1, 4, and 5 allow one failure; raising a number alone would not address
this coverage gap. Criterion 1 intentionally has a low quality bar, and
criterion 4 checks only a limited subset of factual claims.

For a future evaluation, criterion 4 is the one to tighten: require every
concrete fit/material/ownership claim in both the advice and caption to be
supported by the provided listing or wardrobe, with absent details left
unspecified. Also test a fixed set of different listings and wardrobes,
including missing brands and notes. This is a proposed future extension, not
a revision or a new score for this run. The existing criteria were measurable;
none has been deleted, rewritten, or relaxed. The next improvement can target
one of the observed prompt gaps and be measured against the same baseline.

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

```text
$ python app.py ask 'vintage graphic tee under $30' --trace
[1] parse_query
      in:  vintage graphic tee under $30
      out: {'description': 'vintage graphic tee', 'size': None, 'max_price': 30.0}
[2] search_listings (via MCP)
      in:  {'description': 'vintage graphic tee', 'size': None, 'max_price': 30.0}
      out: 10 items: Y2K Baby Tee — Butterfly Print, Graphic Tee — 2003 Tour Bootleg Style, Vintage Band Tee — Faded Grey … +7 more
[3] select_item
      in:  first search result
      out: Y2K Baby Tee — Butterfly Print ($18.0, depop)
[4] suggest_outfit
      in:  {'new_item': {'id': 'lst_002', 'title': 'Y2K Baby Tee — Butterfly Print', 'description': 'Super cute early 200…
      out: **Outfit 1: Y2K Streetwear** Pair the Y2K Baby Tee — Butterfly Print with the Baggy straight-leg jeans, dark w…
      →    wardrobe items: 10
[5] create_fit_card
      in:  {'new_item': {'id': 'lst_002', 'title': 'Y2K Baby Tee — Butterfly Print', 'description': 'Super cute early 200…
      out: Channel classic early 2000s energy by pairing this Y2K Baby Tee — Butterfly Print with baggy straight-leg jean…

  Found:    Y2K Baby Tee — Butterfly Print — $18.0 on depop

  Outfit:   **Outfit 1: Y2K Streetwear**
Pair the Y2K Baby Tee — Butterfly Print with the Baggy straight-leg jeans, dark wash, Chunky white sneakers, and Black crossbody bag.
*Why it works:* The fitted crop length of the baby tee balances the loose, relaxed volume of the dark wash straight-leg jeans for a classic early 2000s silhouette, while the white sneakers tie in the white tones of the butterfly graphic.

**Outfit 2: Casual Grunge**
Combine the Y2K Baby Tee — Butterfly Print with the Wide-leg khaki trousers, Vintage black denim jacket, and Black combat boots.
*Why it works:* The earthy tan trousers ground the playful pink and purple butterfly print, and layering the slightly cropped black denim jacket with black combat boots adds an edgy contrast to the sweet cottagecore and Y2K aesthetic.

  Fit card: Channel classic early 2000s energy by pairing this Y2K Baby Tee — Butterfly Print with baggy straight-leg jeans, chunky white sneakers, and a black crossbody bag for the ultimate Y2K streetwear vibe. Snag this fitted crop top for $18.00 exclusively on depop to complete your nostalgic look.

0 model calls this session, 2 served from cache
```

**Empty search**

```text
$ python app.py ask 'designer ballgown size XXS under $5' --trace
[1] parse_query
      in:  designer ballgown size XXS under $5
      out: {'description': 'designer ballgown', 'size': 'XXS', 'max_price': 5.0}
[2] search_listings (via MCP)
      in:  {'description': 'designer ballgown', 'size': 'XXS', 'max_price': 5.0}
      out: [] (empty)
      →    branch: empty search; stopping before model tools

  No matching listings. Try broader keywords, a different size, or a higher price limit.

0 model calls this session
```

**Empty wardrobe**

```text
$ python app.py ask 'vintage graphic tee under $30' --empty-wardrobe --trace
(running with an empty wardrobe)
[1] parse_query
      in:  vintage graphic tee under $30
      out: {'description': 'vintage graphic tee', 'size': None, 'max_price': 30.0}
[2] search_listings (via MCP)
      in:  {'description': 'vintage graphic tee', 'size': None, 'max_price': 30.0}
      out: 10 items: Y2K Baby Tee — Butterfly Print, Graphic Tee — 2003 Tour Bootleg Style, Vintage Band Tee — Faded Grey … +7 more
[3] select_item
      in:  first search result
      out: Y2K Baby Tee — Butterfly Print ($18.0, depop)
[4] suggest_outfit
      in:  {'new_item': {'id': 'lst_002', 'title': 'Y2K Baby Tee — Butterfly Print', 'description': 'Super cute early 200…
      out: No wardrobe items were supplied. Here are a general styling ideas using the Y2K Baby Tee — Butterfly Print:  *…
      →    wardrobe items: 0
[5] create_fit_card
      in:  {'new_item': {'id': 'lst_002', 'title': 'Y2K Baby Tee — Butterfly Print', 'description': 'Super cute early 200…
      out: Embrace the early 2000s aesthetic by pairing the Y2K Baby Tee — Butterfly Print with low-rise baggy cargo pant…

  Found:    Y2K Baby Tee — Butterfly Print — $18.0 on depop

  Outfit:   No wardrobe items were supplied. Here are a general styling ideas using the Y2K Baby Tee — Butterfly Print:

**Outfit 1: Casual Streetwear**
Pair the baby tee with a pair of low-rise baggy cargo pants and chunky platform sneakers.
*Why it works:* The fitted, cropped silhouette of the baby tee balances the oversized volume of the cargo pants, while the white, pink, and purple butterfly graphic pops against casual streetwear staples for a classic early 2000s look.

**Outfit 2: Sweet & Retro**
Style the top with a pleated denim mini skirt, knee-high white socks, and retro platform sandals, adding a pastel shoulder bag to finish the look.
*Why it works:* The playful pink and purple tones in the butterfly print tie effortlessly into pastel accessories, and the mini skirt leans into the nostalgic Y2K aesthetic while keeping the outfit light and fun.

  Fit card: Embrace the early 2000s aesthetic by pairing the Y2K Baby Tee — Butterfly Print with low-rise baggy cargo pants and chunky platform sneakers for a casual streetwear vibe. You can find this fitted crop top available on depop for $18.00.

2 model calls this session, 660 prompt + 247 output tokens
```

**Model unavailable**

One character of the key was changed only in the child process environment;
`AI201_CACHE=0` forced a real request. The saved `.env` was never edited, and
the script verified its bytes were unchanged. Neither key value was logged.
The command below ran inside that temporary environment.

```text
$ python app.py ask 'rust corduroy wide-leg pants size W28 under $37.42' --trace
[1] parse_query
      in:  rust corduroy wide-leg pants size W28 under $37.42
      out: {'description': 'rust corduroy wide-leg pants', 'size': 'W28', 'max_price': 37.42}
[2] search_listings (via MCP)
      in:  {'description': 'rust corduroy wide-leg pants', 'size': 'W28', 'max_price': 37.42}
      out: 2 items: Corduroy Wide-Leg Pants — Rust, Straight Leg Black Jeans — Faded
[3] select_item
      in:  first search result
      out: Corduroy Wide-Leg Pants — Rust ($32.0, depop)
[4] suggest_outfit
      in:  {'new_item': {'id': 'lst_005', 'title': 'Corduroy Wide-Leg Pants — Rust', 'description': 'Beautiful rust-color…
      out: The model request failed during suggest_outfit. Check GEMINI_API_KEY in .env and your internet connection, the…
      →    model unavailable; stopping

  The model request failed during suggest_outfit. Check GEMINI_API_KEY in .env and your internet connection, then retry. If you hit a rate limit, wait a minute before retrying.

1 model calls this session
```

**What changed and what these checks show**

`agent.py::run_agent` catches `ModelUnavailable` at either model tool and
returns an actionable error in the session instead of a raw traceback. It
keeps completed search/selection data and any completed outfit suggestion;
`fit_card` remains `None` on model failure. `app.py` passes the trace option
into the agent. `trace.py` now shows values for general dictionaries instead
of only key names; long inputs and outputs are still abbreviated.

Reproduce these cases with `python scripts/check_failure_modes.py`. The script
uses the real CLI and MCP server, changes the key only for the bad-key child
process, and writes [results/unit4_failure_checks.json](results/unit4_failure_checks.json).
It checks for successful process exits and no raw traceback. The recorded
happy path reused two model responses; empty wardrobe made two real requests;
the bad-key case made one real request with caching disabled. These are
failure probes, not the five-try acceptance evaluation.

All 17 local tests passed, including failures at either model step, retained
session state, trace reset, default silence, and the shorter empty-search path.

**Reading the messages as a user (AI review):**

- Empty search: I would use broader keywords, choose a different size, or raise the price ceiling. The message names all three options.
- Empty wardrobe: I would try the proposed combinations or supply my actual wardrobe for more specific advice. The output acknowledges that no items were supplied and gives useful general suggestions.
- Model unavailable: I would check the key in `.env` and my connection, then retry; if rate-limited, I would wait a minute. The message identifies the failed model step and gives actions, though it does not distinguish the precise provider failure.

**On the MCP move — Unit 4, Milestone 1:** Only `search_listings` is
registered with FastMCP in `mcp_server.py`. Its wrapper delegates to the
existing `tools.search_listings` implementation, preserving the Tool Inventory
inputs: required `description: str`, optional `size: str | None = None`, and
optional inclusive `max_price: float | None = None` in dollars.

`agent.py::run_agent` now calls
`mcp_client.call_tool("search_listings", session["parsed"])`. The supplied
client starts a local stdio server with the same Python interpreter, unwraps
the response into `list[dict]`, and closes the server after the request.
`suggest_outfit` and `create_fit_card` remain local calls. No new dependencies
were installed and no client changes were needed.

Discovery output:

```text
$ python mcp_client.py
Asking mcp_server.py what it offers…

  search_listings
    Search local listings by keyword description, optional size string, and inclusive max_price in dollars; return ranked listing dictionaries or [] when nothing matches.
    - description: string
    - size: string  (optional)
    - max_price: number  (optional)
```

Validation:

```text
$ python -m unittest discover -s tests -v
Ran 13 tests in 3.000s
OK
```

The real stdio tests compared full returned records and ordering against the
direct implementation for five inputs: description-only search, combined
size/price filtering, numeric shoe size with an explicit null price, an
impossible query, and an empty description. All results were equal, including
`[]` for no matches. A separate check confirmed the server rejects a call
missing the required description. The agent checks still verify tool order,
state identity after search, and early stopping.

The following full query was rerun through MCP:

```bash
python app.py ask 'vintage graphic tee under $30'
```

It returned the same $18 Y2K Baby Tee listing, outfit suggestions, and caption
shown in Sample Run. Search went through the real MCP server; the two model
responses came from the existing cache (`0 model calls this session, 2 served
from cache`). This validates the transport change, not fresh model variation.

```text
$ python app.py ask 'designer ballgown size XXS under $5'

  No matching listings. Try broader keywords, a different size, or a higher price limit.

0 model calls this session
```

The MCP move succeeded with no observed return-value differences. Trace
instrumentation and the three failure probes are now recorded above; repeated
uncached acceptance runs are now recorded under Run Log — Before.


---

## The Improvement

**What I changed:** One instruction in `tools.py::create_fit_card`'s system
prompt. Previously it said “Mention the selected item”; it now says:

```text
Copy selected_item.title verbatim exactly once; do not shorten or paraphrase it.
```

The outfit prompt, search, MCP transport, loop, criteria, scenarios, temperature,
and evaluation runner were unchanged. No second fix was made after seeing the
results. Local regression checks still passed: 17 tests.

**Which failure it was meant to fix:** The before-run diagnosis found shortened
titles in criterion 1 tries 1 and 4. Those passed that row's completion check,
but did not satisfy the full-title requirement used by criterion 4. Across
all 20 before-run captions, 18 included the full title exactly once. The old
prompt allowed paraphrasing, so this change explicitly requests a verbatim copy.

**How it was measured:** `python run_eval.py --label after`, five identical
scenarios with five tries each, caching off and temperature `0.9`. The agent
was unchanged during the run. It made 40 model requests (21,976 prompt tokens,
5,301 output tokens); all 25 tries returned without crashes. Each of the four
model-backed scenarios produced five distinct captions. These are fresh
outputs, not cached copies of the before run.

### Run Log — Before (repeated for comparison)

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1. Full three-tool run returns a fit card | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 2. Empty search stops before model tools | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. Complete state matches tool arguments | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 4. Fit card length and listing facts | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 5. Empty wardrobe gets useful advice | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |

### Run Log — After

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1. Full three-tool run returns a fit card | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 2. Empty search stops before model tools | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. Complete state matches tool arguments | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 4. Fit card length and listing facts | 4 of 5 | PASS | PASS | PASS | PASS | FAIL | MET (4/5) |
| 5. Empty wardrobe gets useful advice | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |

After evidence: [full output](results/run_2026-10-06_135609_after.md), [sessions and call snapshots](results/run_2026-10-06_135609_after.json),
and [per-try scoring](results/run_2026-10-06_135609_after_scored.json). Both runs use the original targets.

**Did it help, and how do I know:** The title-copying change helped on this
sample (18/20 → 20/20 full titles), but overall caption quality did not improve:
criterion 4 dropped from 5/5 to 4/5 because one caption ambiguously attached
the tee's price to a jacket. All five criteria still meet their targets.
The title count is a supplementary diagnostic across all captions, not a new
acceptance criterion or a replacement for criterion 4's five assigned tries.
With one before/after batch and stochastic model outputs, these observations
do not prove the prompt caused either the improvement or the regression.

**Actual after-run failure — criterion 4, try 5**

Produced by `tools.py::create_fit_card`, stored by `agent.py::run_agent`:

```text
Channel early 2000s skater proportions by styling the Y2K Baby Tee — Butterfly Print with dark wash baggy straight-leg jeans and a vintage black denim jacket for $18.00 on depop. You can also style it with wide-leg khaki trousers and a brown leather belt for a modern-retro aesthetic. Both looks are grounded with chunky white sneakers for the ultimate casual streetwear vibe.
```

The numeric price is correct, but the phrase “a vintage black denim jacket
for $18.00 on depop” does not clearly assign that price to the selected tee.
I scored this FAIL under the existing requirement to include the selected
item's correct price; the full title alone cannot make this caption pass.
The step is the model output from `create_fit_card`: the prompt requests a
price mention but does not require a separate, unambiguous statement tying it
to the selected item, and no output check enforces that relationship.
Criterion 1 try 4 also attaches “for $18.0 on depop” to a sentence about
sneakers and a crossbody bag, showing the same pattern outside the quality row.
It still passes criterion 1's explicitly narrower completion check.

I kept this one prompt change and recorded the mixed result. Repairing price
attribution would be a separate improvement with its own before/after test.
The baseline results and acceptance criteria remain intact.

---

## What's Still Broken

No criterion remains MISSED against its original target in the after-run:
criteria 1, 2, 3, and 5 passed 5/5, and criterion 4 passed 4/5 against a 4/5
target. That still leaves an observed caption failure and limits on what the
evaluation establishes.

- **Price attribution remains unreliable.** In criterion 4, after try 5, the caption places “for $18.00 on depop” after “a vintage black denim jacket,” making the tee's price ambiguous. This is a model-output failure in `create_fit_card`, not a missing price in session state. I would require a separate sentence explicitly pairing the selected item's title with its price and platform, then check that relationship in the output. I stopped after the title-only prompt change to keep this unit's before/after comparison attributable to one change; I have not tested a price-attribution fix.
- **Outfit advice can invent fit details.** The unchanged `suggest_outfit` prompt still produced “low-slung” descriptions of jeans whose wardrobe notes say high-waisted, including criterion 4 after tries 1 and 3. I would tighten that tool's prompt to treat supplied notes as constraints and leave unknown fit details unspecified, then evaluate advice against several wardrobes. I left that separate prompt unchanged to preserve the one-change experiment.
- **Search can match incidental words.** Keyword overlap can return the mesh top because its description mentions a graphic tee. I would test relevance on a fixed set of queries and compare stronger title/tag weighting or required garment terms. No relevance improvement was measured here, so the README does not claim it was solved.
- **Coverage is narrow.** The model-backed scenarios all selected the same baby tee, and the regex parser supports only documented price/size phrases. I would add varied listings, missing-note cases, and alternate phrasings in a separate evaluation. I kept the current inputs fixed so the before and after results remained comparable rather than expanding the test after seeing results.

**MCP move:** `agent.py::run_agent` now calls
`mcp_client.call_tool("search_listings", session["parsed"])`, and
`mcp_server.py` exposes the existing local search implementation as one typed
tool. Five direct-versus-MCP checks found identical lists, ordering, and empty
results. The client now starts a subprocess per search; the two model tools
remain local. No return-value differences were observed in those checks.

## Unit 4 Submission Status

The before and after run logs, five verdicts, diagnoses, real traces, failure
probes, and remaining limitations are included in this README and `results/`.
The unit has at least four new commits: `dfd2a48`, `f650f11`, `d92a3b4`,
`2796d17`, and `7566044`, followed by this final write-up commit. The same
repository and prior history are preserved; the criteria authorship and
chronology note remains in `criteria.md`.

Submit this same fork URL through the Course Portal:
[Sunji2468/ai201-project2-fitfindr-starter-v2026](https://github.com/Sunji2468/ai201-project2-fitfindr-starter-v2026).
The URL is saved here for reuse. Course-portal submission has not been
performed or verified from this workspace.

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

       [x] mcp_server.py exists with one tool registered
           (or a written record of exactly where the rewire broke)
       [x] Run Log — Before, five criteria, five tries each
       [x] Real output pasted underneath, naming file and function
       [x] A verdict on every criterion
       [x] A diagnosis for every miss, naming a place AND a mechanism
       [x] Loop Trace, with the MCP call visible in it
       [x] All three failure modes triggered and handled
       [x] One improvement, with Run Log — After in the same format
       [x] What's Still Broken
       [x] At least four new commits
       [x] The SAME repository URL as last unit

     Do not delete and recreate this repository. Your commit history is what
     shows your criteria existed before your results did.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**
