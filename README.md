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
uncached acceptance runs remain a later milestone.


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
