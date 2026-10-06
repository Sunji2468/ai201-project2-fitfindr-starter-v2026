# Acceptance criteria — FitFindr

Five criteria defining what “working” means for the agent.

**Authorship and timing:** Criteria 1–2 came from the starter. At the student's
request, Codex drafted criteria 3–5 and all five explanations after the
standalone tool checks and Milestone 5 development runs. These targets precede
the Unit 4 acceptance evaluation, but were not written before all results
existed. The original commit history is preserved.

For evaluation, run each criterion's specified input five times with response
caching disabled and `TEMPERATURE` unchanged at `0.9`. Each try must satisfy
all conditions in its criterion to pass; an exception or missing required
output counts as a failure. Observe real tool calls with wrappers or tracing
without replacing their return values. Do not lower targets after testing.

---

## 1. A matching query completes all three tools

Given a query that matches at least one listing, the agent completes all three
tool calls and returns a fit card — in at least 4 of 5 tries.

**Test input and observation:** Use `vintage graphic tee under $30, size M`
with the example wardrobe. Confirm `search_listings`, `suggest_outfit`, and
`create_fit_card` run in that order, `session["error"]` is `None`, and
`session["fit_card"]` contains a caption rather than an empty-case message.
Caption quality is checked separately in criterion 4.

**Why this target:** This path depends on two live model responses, so one
service or generation failure is allowed while successful completion must
still be the usual outcome. Requiring 5 of 5 would treat a transient external
failure the same as a consistently broken loop.

---

## 2. An impossible query stops before the second tool

Given a query that matches no listings, the agent stops before calling
`suggest_outfit` and returns a message naming what to change — 5 of 5 tries.

**Test input and observation:** Use `designer ballgown size XXS under $5`
with the example wardrobe. Confirm `search_results` is `[]`, neither
`suggest_outfit` nor `create_fit_card` is called, and `fit_card` stays `None`.
The error message must suggest changing keywords, size, or the price limit;
“No results” alone does not pass.

**Why this target:** This branch uses local data and a deterministic condition,
so model variability cannot explain a miss. Five of five is the strictest
possible target for five tries, and calling a model with no selected item is
an avoidable control-flow bug.

---

## 3. The selected listing stays consistent across tool calls

For `vintage graphic tee under $30, size M` with the example wardrobe, the
complete listing dictionary in `session["search_results"][0]` must equal
`session["selected_item"]` and the `new_item` argument received by both
`suggest_outfit` and `create_fit_card`; the `outfit` argument received by
`create_fit_card` must equal `session["outfit_suggestion"]` — in 5 of 5 tries.
Both downstream calls must occur for a try to pass, and comparing only item
names or IDs is not sufficient.

**Why this target:** Passing stored values between functions is deterministic,
even when the generated words vary. Five of five is the maximum target and
is necessary because a caption for a different item could display the wrong
price or platform without producing an obvious error.

---

## 4. The fit card is short and preserves the listing facts

For `vintage graphic tee under $30, size M` with the example wardrobe, the
returned fit card must contain two to four sentences, name the selected item
by its full title exactly once, include its correct dollar price exactly once,
and name its platform exactly once — in at least 4 of 5 tries. It must also
mention at least one wardrobe piece used in the outfit suggestion and must
not invent a brand, discount, or exclusive availability.

**Test interpretation:** Count item titles and platform names without regard
to letter case. `$18`, `$18.0`, and `$18.00` are equivalent prices; decimal
points do not split sentences. Check wardrobe references by the named piece,
allowing capitalization differences. Wording may vary between tries; it need
not match a saved caption. Missing captions and fallback messages fail.

**Why this target:** The model can vary its phrasing and occasionally miss a
formatting or factual constraint, so 4 of 5 allows one miss without accepting
unreliable captions as normal. Requiring exact repeated wording would punish
useful variation; the target instead holds the length and facts steady.

---

## 5. An empty wardrobe receives useful advice without invented ownership

For `vintage graphic tee under $30, size M` with `{"items": []}`, the agent
must return a non-empty outfit suggestion that explicitly says no wardrobe
items were supplied and proposes at least one other clothing or accessory
piece with a color or style reason for pairing it with the selected listing;
it must also return a non-empty fit card — in at least 4 of 5 tries. Neither
output may describe a suggested piece as already owned by the user, and
fallback or error messages do not count as advice or a fit card.

**Why this target:** A new user should receive concrete help before entering
a wardrobe, but both the advice and caption depend on model-generated prose.
Four of five requires dependable usefulness while allowing one generation
that is too vague or incorrectly implies ownership; 5 of 5 would allow no
such model variation.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 4 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath it, like this:

         ## 4. Something about the fit card

         The fit card is different every time.

         **Why this target:** ...

         > **Revised in unit 4:** For 5 different items, the 5 fit cards share
         > no opening sentence.
         >
         > **Why revised:** "different" wasn't checkable — two cards that
         > differed by one word still counted. The new version is something I
         > can actually score.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "I said the empty search stops it 5 of 5 times, but I got 3 of 5,
            so 3 of 5 is more realistic."

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.
     ───────────────────────────────────────────────────────────────────────── -->
