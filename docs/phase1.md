# Engineering Plan: Marlowe Agent

Phase 1 — Multi-page web exploration, extraction, and evidence-backed answers

⸻

1. Product Summary

We will build a Browser Investigation Agent that can answer questions requiring systematic navigation across a website’s result set.

Example task

“On this IBM careers page, find every job that is available in California.”

The agent should:

1. Open the result page.
2. Detect whether the results use pagination, infinite scroll, or a “Load more” pattern.
3. Traverse the full result set.
4. Open each detail page.
5. Extract relevant information.
6. Evaluate each item against the user’s condition.
7. Return a structured, auditable answer with coverage metrics and evidence.

This should not be overfit to jobs. The same system should support tasks like:

* “Find all grants open to California nonprofits.”
* “Find all apartments with in-unit laundry and parking.”
* “Find all products with a 5-year warranty.”
* “Find all vendors that mention SOC 2 compliance.”

⸻

2. Core Product Thesis

The problem

Many websites contain the answer to a user’s question, but not in a form that is directly searchable or filterable.

The data is often fragmented across:

Result page → Result page → Result page
                    ↓
              Detail page

A human could manually inspect everything, but it is slow and tedious.

The software opportunity

Turn interactive websites into temporary structured datasets, then answer questions over them.

This is different from:

* a general-purpose chat browser,
* a one-off scraper,
* a search engine,
* a browser automation tool that performs a single action.

The product should optimize for:

1. Completeness — did we cover the whole relevant search space?
2. Reliability — can we traverse messy websites consistently?
3. Auditability — can we show evidence for every conclusion?
4. Generalization — can this apply beyond one website or domain?

⸻

3. Phase 1 Scope

Build

A. User-submitted investigation

Input:

* seed_url
* objective
* optional extraction preferences

Example:

URL:
https://www.ibm.com/careers/search?field_keyword_05[0]=United%20States&p=1
Objective:
Find all jobs that are available in California.

⸻

B. Site traversal

Support:

* classic pagination
* “next” pagination
* URL-parameter pagination
* “load more” buttons
* infinite scroll

⸻

C. Item discovery

The agent should identify:

* which elements represent result items,
* which click target opens the detail page,
* what stable identifier can deduplicate items.

⸻

D. Detail extraction

For each item, extract:

* title
* URL
* source page index / discovery location
* user-relevant fields
* evidence snippet
* classification result

Example:

{
  "title": "Senior Software Engineer",
  "url": "...",
  "location_text": "San Jose, CA",
  "matches_objective": true,
  "evidence": "Location: San Jose, California"
}

⸻

E. Result aggregation

Return:

* answer summary,
* matching results table,
* ambiguous results,
* non-matching optionally hidden,
* coverage report,
* downloadable CSV/JSON eventually.

⸻

F. Observability

Capture:

* pages visited,
* items discovered,
* detail pages opened,
* extraction success/failure,
* stopping reason,
* screenshots or page snapshots for debugging,
* LLM decisions.

⸻

Defer from Phase 1

Do not build yet:

* generic logged-in workflows,
* form submission,
* purchases / transactions,
* full anti-bot escalation layer,
* arbitrary freeform “do anything on the browser,”
* parallel execution at massive scale,
* deep reusable cross-site skill learning,
* full enterprise workflow builder.

⸻

4. Recommended Technology Direction

Browser execution layer

Recommendation

Use a browser-provider-agnostic architecture with a default runtime based on:

* Playwright for browser control and reliable automation primitives.
* Chrome / Chromium via CDP where lower-level control is useful.
* A pluggable remote browser provider later, such as Browser Use Cloud or Browserbase.

Playwright is mature, supports Chromium, Firefox, and WebKit, and is designed for reliable browser automation with rich primitives for navigation, selectors, waiting, and page state inspection.  ￼

⸻

Where Browser Harness fits

Browser Harness is valuable for:

* prototyping,
* exploratory agent behavior,
* studying LLM-driven browser control,
* learning how far screenshot-first and raw CDP workflows can go.

Its design is intentionally thin: it connects an LLM directly to a real Chrome browser through CDP and lets the agent improvise helper code during execution.  ￼

Recommendation

Use Browser Harness as an R&D and evaluation tool, not as the main production runtime for Phase 1.

Why:

* Our product requires durable task state, traversal ledgers, retries, extraction schemas, coverage metrics, and result aggregation.
* Browser Harness intentionally stays lightweight and leaves those orchestration concerns outside the harness.  ￼

⸻

Websites that block agents

For Phase 1, support standard public websites first.

To handle harder sites later, design the browser abstraction so that we can swap in:

* Browser Use Cloud, which advertises stealth browsers, residential proxies, CAPTCHA support, and managed infrastructure.  ￼
* Browserbase, which offers managed cloud browsers, identity/session support, and infrastructure for browser agents.  ￼

Product stance

We should not market this as “we bypass every bot protection.”

A more defensible positioning:

“We use real browser execution and can escalate to managed browser infrastructure for websites that require stronger session and anti-bot support.”

⸻

5. System Architecture

┌───────────────────────────────────────────────┐
│                Investigation API              │
│  seed URL + user objective + execution config │
└──────────────────────┬────────────────────────┘
                       │
                       ▼
┌───────────────────────────────────────────────┐
│              Investigation Planner            │
│  - interpret user objective                   │
│  - propose output schema                      │
│  - identify initial traversal goals           │
└──────────────────────┬────────────────────────┘
                       │
                       ▼
┌───────────────────────────────────────────────┐
│               Browser Session Layer           │
│  Playwright / CDP / remote-browser adapter    │
│  - goto                                       │
│  - click                                      │
│  - scroll                                     │
│  - DOM snapshot                               │
│  - screenshot                                 │
│  - JS evaluation                              │
└──────────────────────┬────────────────────────┘
                       │
                       ▼
┌───────────────────────────────────────────────┐
│               Page Understanding              │
│  - detect result cards                        │
│  - detect traversal pattern                   │
│  - detect detail link                         │
│  - detect relevant structured regions         │
└──────────────────────┬────────────────────────┘
                       │
                       ▼
┌───────────────────────────────────────────────┐
│                Traversal Engine               │
│  - pagination controller                      │
│  - load-more controller                       │
│  - infinite-scroll controller                 │
│  - exhaustion detection                       │
│  - deduplication                              │
└──────────────────────┬────────────────────────┘
                       │
                       ▼
┌───────────────────────────────────────────────┐
│                 Item Work Queue               │
│  - detail page URLs                           │
│  - discovered item identifiers                │
│  - status per item                            │
└──────────────────────┬────────────────────────┘
                       │
                       ▼
┌───────────────────────────────────────────────┐
│               Extraction & Evaluation         │
│  - extract user-relevant fields               │
│  - classify item against objective            │
│  - collect evidence                           │
│  - flag ambiguity                             │
└──────────────────────┬────────────────────────┘
                       │
                       ▼
┌───────────────────────────────────────────────┐
│               Investigation Results           │
│  - matched items                              │
│  - ambiguous items                            │
│  - coverage report                            │
│  - execution trace                            │
└───────────────────────────────────────────────┘

⸻

6. Key Design Principle

LLM for interpretation, deterministic code for exhaustion and bookkeeping

The LLM should help determine:

* “This page contains job result cards.”
* “This looks like pagination.”
* “This button likely means Next.”
* “This text indicates the job is in California.”

But the LLM should not be responsible for:

* keeping count,
* preventing duplicates,
* deciding whether three consecutive scrolls yielded no new items,
* proving full traversal,
* retrying a failed click loop.

That logic should be deterministic.

⸻

7. Core Domain Model

Investigation

class Investigation:
    id: str
    seed_url: str
    objective: str
    status: Literal[
        "created",
        "planning",
        "traversing",
        "extracting",
        "completed",
        "failed",
        "partial"
    ]
    created_at: datetime
    completed_at: datetime | None

⸻

Investigation Plan

class InvestigationPlan:
    investigation_id: str
    entity_type: str | None
    traversal_strategy: str | None
    output_schema: dict
    user_condition: str
    planner_notes: str

⸻

Page Snapshot

class PageSnapshot:
    id: str
    investigation_id: str
    url: str
    page_type: Literal["list", "detail", "unknown"]
    dom_excerpt: str | None
    screenshot_uri: str | None
    created_at: datetime

⸻

Discovered Item

class DiscoveredItem:
    id: str
    investigation_id: str
    source_page_url: str
    source_page_index: int | None
    item_url: str | None
    stable_key: str
    title_hint: str | None
    status: Literal[
        "discovered",
        "queued",
        "processing",
        "extracted",
        "failed"
    ]

⸻

Extracted Record

class ExtractedRecord:
    item_id: str
    fields: dict
    match_status: Literal["match", "no_match", "ambiguous"]
    reasoning_summary: str
    evidence: list[str]
    confidence: float | None

⸻

Traversal Ledger

class TraversalLedger:
    investigation_id: str
    traversal_type: Literal[
        "pagination",
        "url_param_pagination",
        "load_more",
        "infinite_scroll",
        "unknown"
    ]
    pages_visited: int
    scroll_rounds: int
    items_discovered: int
    duplicate_items_skipped: int
    stop_reason: str
    completion_status: Literal[
        "verified_complete",
        "exhausted_traversal",
        "partial",
        "uncertain"
    ]

⸻

8. Phase 1 User Flow

1. User submits URL + objective
2. System creates Investigation
3. Planner opens the seed page
4. Planner determines:
   - is this a result-list site?
   - what item type exists?
   - which traversal pattern is likely?
5. Traversal engine walks all list pages / scroll states
6. It collects unique item URLs or stable item keys
7. Item processor opens each item page
8. Extractor turns each page into structured record
9. Evaluator judges whether it satisfies the objective
10. Results UI displays matches, ambiguity, and coverage

⸻

9. Traversal Engine Design

This is the heart of the system.

⸻

9.1 Traversal Strategy Interface

class TraversalStrategy(Protocol):
    async def initialize(
        self,
        session: BrowserSession,
        page_model: PageModel
    ) -> TraversalState:
        ...
    async def collect_items(
        self,
        session: BrowserSession,
        state: TraversalState
    ) -> list[DiscoveredItemCandidate]:
        ...
    async def advance(
        self,
        session: BrowserSession,
        state: TraversalState
    ) -> AdvanceResult:
        ...
    async def is_exhausted(
        self,
        session: BrowserSession,
        state: TraversalState
    ) -> ExhaustionCheck:
        ...

⸻

9.2 Pagination Strategy

Stop conditions

Stop when any of the following are true:

* no “next” control exists,
* “next” is disabled,
* page number indicates final page,
* click causes no result-set change,
* next URL repeats a previously visited URL.

Pseudocode

while True:
    collect_items_from_current_page()
    current_fingerprint = fingerprint_visible_results()
    next_button = detect_next_control()
    if not next_button:
        stop("No next control")
    if is_disabled(next_button):
        stop("Next control disabled")
    await click(next_button)
    await wait_for_results_change()
    new_fingerprint = fingerprint_visible_results()
    if new_fingerprint == current_fingerprint:
        stop("Click did not change results")

⸻

9.3 URL-parameter Pagination

Some sites reveal the page number in the URL:

?p=1
?p=2
?p=3

When safe, the engine can infer and visit subsequent URLs faster than clicking. But Phase 1 should use this only when:

* the pattern is obvious,
* the page changes accordingly,
* traversal remains auditable.

This could speed up sites like the IBM example, whose URL already contains p=1.

⸻

9.4 Load More Strategy

Stop conditions

* no load-more button remains,
* button becomes disabled,
* click results in no new item IDs after N attempts.

Pseudocode

stale_rounds = 0
while stale_rounds < 2:
    before_ids = seen_item_ids.copy()
    button = detect_load_more_button()
    if not button:
        stop("No load more button")
    await click(button)
    await wait_for_new_content()
    newly_seen = discover_visible_item_ids() - before_ids
    if newly_seen:
        stale_rounds = 0
    else:
        stale_rounds += 1

⸻

9.5 Infinite Scroll Strategy

Observables

Track:

* seen item IDs,
* scroll position,
* document height,
* network activity,
* spinner state,
* visible-card hashes.

Stop conditions

Stop when:

* no new stable item IDs are discovered for N scroll rounds,
* page height does not grow,
* the UI shows an end-of-results marker,
* discovered items equal an on-page total count, if available.

Pseudocode

stale_rounds = 0
seen_item_ids = set()
while stale_rounds < 3:
    before_seen = len(seen_item_ids)
    visible_items = discover_visible_items()
    seen_item_ids.update(stable_key(item) for item in visible_items)
    await scroll_down()
    await wait_for_content_settle()
    visible_items = discover_visible_items()
    seen_item_ids.update(stable_key(item) for item in visible_items)
    after_seen = len(seen_item_ids)
    if after_seen > before_seen:
        stale_rounds = 0
    else:
        stale_rounds += 1
stop("No new items after 3 scroll rounds")

⸻

10. Stable Item Identity

To avoid duplicates and detect progress, the system needs a stable key per item.

Priority order:

1. Canonical detail URL
2. Site-provided item ID
3. HTML data-id / aria reference
4. Hash of:
    * title text
    * subtitle text
    * location text
    * card href

Example:

stable_key = sha256(
    normalized_title +
    normalized_location +
    canonical_url
)

This is crucial for:

* infinite scroll,
* deduplication,
* proving progress,
* resumability.

⸻

11. Page Understanding Layer

The planner must transform a raw page into a useful internal model.

Page Model

class PageModel:
    page_type: Literal["list", "detail", "unknown"]
    result_container_description: str | None
    result_item_selector_candidates: list[str]
    detail_link_selector_candidates: list[str]
    traversal_type_guess: str | None
    next_control_candidates: list[str]
    load_more_candidates: list[str]
    total_results_hint: int | None

⸻

Inputs to the LLM

For a page, provide:

* URL,
* trimmed DOM,
* accessibility tree when useful,
* visible text,
* screenshot,
* page metadata.

The LLM returns a structured PageModel.

This is where Browser Harness can be a useful research reference: its philosophy of direct browser control plus screenshot-driven reasoning is aligned with this page-understanding step.  ￼

⸻

12. Extraction & Evaluation Layer

Extraction prompt shape

For each detail page, the model should receive:

* user objective,
* page title,
* relevant page text,
* optional DOM hints,
* expected structured output schema.

Example structured output

{
  "entity_title": "Senior Product Manager",
  "relevant_fields": {
    "location": "San Jose, California, United States"
  },
  "match_status": "match",
  "evidence": [
    "Location: San Jose, California, United States"
  ],
  "reasoning_summary": "The location explicitly states San Jose, California."
}

⸻

Match statuses

Every extracted record should be:

Status	Meaning
match	Clearly satisfies objective
no_match	Clearly does not
ambiguous	Insufficient or unclear evidence

Example ambiguity

Objective: “Available in California”
Text: “United States, remote eligible.”

Should this count? Not automatically. It should be ambiguous, unless the user defined “remote anywhere in the U.S.” as acceptable.

⸻

13. Completion and Coverage Model

This is a major product feature.

Completion statuses

CompletionStatus =
    "verified_complete" |
    "exhausted_traversal" |
    "partial" |
    "uncertain"

⸻

Verified complete

Use when:

* site displays total result count,
* discovered unique items equal that count.

Example:

Site says: 137 results
Agent discovered: 137 unique jobs

⸻

Exhausted traversal

Use when:

* the traversal engine reached a deterministic stopping condition,
* but the site did not expose a total count.

Example:

* Next button disabled,
* three infinite-scroll attempts yielded no new items.

⸻

Partial

Use when:

* the run hit a configured item/page cap,
* a browser crash occurred,
* a page became inaccessible.

⸻

Uncertain

Use when:

* site behavior is inconsistent,
* duplicated cards or loading failures prevent strong claims.

⸻

Coverage report example

Coverage
- Traversal detected: Pagination
- List pages visited: 28
- Unique items discovered: 274
- Detail pages opened: 274
- Successful extractions: 269
- Failed extractions: 5
- Matches: 18
- Ambiguous: 4
- Completion: Exhausted traversal
- Stop reason: Next button disabled on final page

⸻

14. Browser Abstraction Layer

We should define our own minimal browser interface so the product is not locked to one provider.

class BrowserSession(Protocol):
    async def goto(self, url: str) -> None: ...
    async def click(self, target: ClickTarget) -> None: ...
    async def scroll(self, amount: int | None = None) -> None: ...
    async def screenshot(self) -> bytes: ...
    async def get_html(self) -> str: ...
    async def get_visible_text(self) -> str: ...
    async def evaluate_js(self, script: str) -> Any: ...
    async def wait_for_network_idle(self) -> None: ...
    async def current_url(self) -> str: ...

Initial implementation

* PlaywrightBrowserSession

Future implementations

* BrowserUseCloudSession
* BrowserbaseSession
* potentially BrowserHarnessSession for experimentation

Playwright provides a strong foundation because it is well-supported, works across major browser engines, and supports headless/headed modes and rich browser interactions.  ￼

⸻

15. Execution Architecture

For Phase 1, I recommend an async backend with a task-state model.

Suggested stack

Layer	Recommendation
API	FastAPI
Browser automation	Playwright
Data store	PostgreSQL
Queue	Redis + worker, or Temporal if you want durable orchestration from the start
LLM calls	Structured-output model interface
Artifacts	Object storage for screenshots/snapshots
Frontend	Next.js
Observability	Postgres event log + tracing

Given your broader interest in Temporal and durable execution, this project is actually a very good fit for Temporal once runs become long-lived and resumable. But for Phase 1, I would decide between:

Option A — Faster MVP

* FastAPI
* Celery / RQ / Arq-style async worker
* Postgres-backed run state

Option B — More robust from the beginning

* FastAPI
* Temporal workflows
* Browser worker activities
* extraction/evaluation activities
* retryable, resumable runs

If the goal is to turn this into a serious agent-training or agent-eval product, I lean toward Temporal, because browser investigations are naturally long-running, failure-prone, and stateful.

⸻

16. Proposed Service Breakdown

apps/
  api/
    investigation_api.py
    investigation_service.py
  worker/
    planner_worker.py
    traversal_worker.py
    extraction_worker.py
packages/
  browser_runtime/
    browser_session.py
    playwright_session.py
  traversal/
    strategies/
      pagination.py
      infinite_scroll.py
      load_more.py
      url_param_pagination.py
    ledger.py
    dedupe.py
  understanding/
    page_classifier.py
    page_model_schema.py
  extraction/
    detail_extractor.py
    objective_evaluator.py
    schemas.py
  persistence/
    models.py
    repositories.py

⸻

17. Workflow Definition

High-level workflow

InvestigationWorkflow
  1. Create investigation run
  2. Open seed URL
  3. Generate page model
  4. Choose traversal strategy
  5. Traverse result set
  6. Persist discovered items
  7. Process item detail pages
  8. Extract structured records
  9. Evaluate objective
  10. Generate final report

⸻

Temporal-style workflow sketch

@workflow.defn
class InvestigationWorkflow:
    @workflow.run
    async def run(self, investigation_id: str):
        plan = await workflow.execute_activity(
            plan_investigation,
            investigation_id
        )
        discovered_items = await workflow.execute_activity(
            traverse_list_pages,
            plan
        )
        extracted_records = []
        for batch in chunked(discovered_items, 10):
            batch_results = await workflow.execute_activity(
                process_item_batch,
                batch
            )
            extracted_records.extend(batch_results)
        await workflow.execute_activity(
            finalize_report,
            investigation_id,
            extracted_records
        )

⸻

18. Frontend Experience

Run creation page

Paste a URL:
[                                                    ]
What do you want to find?
[                                                    ]
Advanced:
☐ Search all results
☐ Stop after N matches
☐ Export as CSV
☐ Include ambiguous cases

⸻

Live progress view

Investigation running
Detected:
- Site type: result list with detail pages
- Traversal: pagination
- Result item type: jobs
Progress:
- Pages visited: 4
- Items discovered: 40
- Detail pages analyzed: 27
- Matches found: 3
- Ambiguous: 1

⸻

Final report view

Summary

Found 18 matching jobs.

Coverage

274 detail pages inspected across 28 list pages.

Results table

Title	Extracted Location	Match Reason	Evidence
Senior SWE	San Jose, CA	Explicit California location	“San Jose, California”

Ambiguous cases

Title	Why ambiguous
Staff Architect	US remote

⸻

19. Milestones

Phase 1A — Vertical Slice Prototype

Goal: Make the IBM-style task work end to end on 1–2 public websites.

Deliverables

* Paste URL + objective API
* Open result page
* Use LLM to identify result cards
* Detect pagination manually or semi-automatically
* Visit each result detail page
* Extract structured fields
* Generate match table

Success criteria

* Can complete the IBM California-jobs example.
* Produces a reasonable structured output.
* Records evidence snippets.
* Can show discovered item count.

⸻

Phase 1B — Generalized Traversal Engine

Goal: Move from “works on example” to “works on a class of list/detail sites.”

Deliverables

* TraversalStrategy interface
* Pagination strategy
* Load-more strategy
* Infinite-scroll strategy
* Stable item identity system
* Traversal ledger
* Exhaustion statuses

Success criteria

* Handles at least:
    * 3 paginated sites,
    * 2 infinite-scroll sites,
    * 2 load-more sites.
* Avoids duplicate item processing.
* Correctly reports stopping reason.

⸻

Phase 1C — Extraction & Judgment Quality

Goal: Reliable, evidence-backed classification.

Deliverables

* Schema-driven extraction
* Match / no-match / ambiguous output
* Evidence extraction
* Normalization helpers:
    * geographic locations,
    * salary fields,
    * boolean features,
    * dates

Success criteria

* On curated benchmark tasks:
    * high precision on match,
    * explicit ambiguity instead of unsupported guesses,
    * evidence present for every positive match.

⸻

Phase 1D — Productized Run Experience

Goal: Make it feel like a real product, not a dev tool.

Deliverables

* Run creation UI
* Live progress UI
* Final report UI
* Coverage metrics
* Item trace view
* Retry failed item extraction

Success criteria

* A user can submit a site and receive a usable answer without developer involvement.

⸻

20. Suggested Evaluation Dataset

We should build a small internal benchmark of browser investigations.

Dataset structure

Each benchmark includes:

* seed URL,
* objective,
* expected relevant item subset,
* notes on traversal pattern,
* human-verified answer.

Example categories

Benchmark	Pattern
IBM careers California jobs	Pagination
Another careers site	Pagination
E-commerce category with Load More	Load more
Directory site with infinite scroll	Infinite scroll
Grants database	Pagination + detail pages
University catalog	Search list + detail pages

⸻

Metrics

Traversal quality

* result coverage %
* duplicate rate
* stop correctness
* pages visited / expected pages

Extraction quality

* field-level accuracy
* evidence correctness
* match precision
* match recall
* ambiguity calibration

System performance

* average time per item
* LLM calls per item
* browser failures
* retry success rate

⸻

21. Recommended MVP Success Criteria

I would consider Phase 1 successful when:

1. The user can submit a public result-list URL and a query.
2. The system can identify the list/detail pattern.
3. It can traverse:
    * pagination,
    * load-more,
    * infinite scroll.
4. It can inspect 100+ items in a run.
5. It produces:
    * a match table,
    * evidence,
    * coverage report,
    * explicit ambiguity.
6. It completes at least 70–80% of curated benchmark tasks without hand-coded site logic.

That last criterion matters. We should allow some site-specific heuristics, but the core thesis is that it generalizes.

⸻

22. Risks and Mitigations

Risk 1: LLM misidentifies traversal controls

Mitigation

* return multiple candidates,
* validate by observing page change,
* fall back to alternate strategy,
* log failed decisions.

⸻

Risk 2: Infinite scroll never clearly ends

Mitigation

* detect no-progress rounds,
* track unique item IDs,
* use on-page total counts when available,
* mark completion as exhausted_traversal, not falsely verified_complete.

⸻

Risk 3: Sites block automation

Mitigation

* use real browser execution,
* rate-limit actions,
* provider abstraction for managed browser infrastructure,
* use Browser Use Cloud or Browserbase when needed.  ￼

⸻

Risk 4: Extraction is expensive

Mitigation

* DOM/text filtering before LLM calls,
* use cheaper model for page classification,
* use stronger model only for ambiguous extraction,
* batch work carefully where possible.

⸻

Risk 5: Detail pages vary significantly

Mitigation

* rely on objective-driven extraction, not fixed fields,
* extract source text snippets,
* include ambiguity status,
* keep evidence tied to the page.

⸻

Risk 6: Browser runs fail midway

Mitigation

* durable run state,
* item-level processing statuses,
* resumable queues,
* Temporal or strong workflow orchestration later.

⸻

23. Concrete API Sketch

Create investigation

POST /investigations
{
  "seed_url": "https://www.ibm.com/careers/search?...",
  "objective": "Find all jobs available in California.",
  "config": {
    "max_pages": null,
    "max_items": null,
    "include_ambiguous": true
  }
}

⸻

Get progress

GET /investigations/{id}
{
  "status": "extracting",
  "progress": {
    "pages_visited": 12,
    "items_discovered": 120,
    "items_processed": 71,
    "matches_found": 9,
    "ambiguous_found": 2
  }
}

⸻

Get results

GET /investigations/{id}/results
{
  "summary": "Found 18 matching records.",
  "completion_status": "exhausted_traversal",
  "coverage": {
    "pages_visited": 28,
    "items_discovered": 274,
    "items_processed": 274,
    "failed_items": 0
  },
  "matches": [],
  "ambiguous": []
}

⸻

24. Recommended Implementation Sequence

Step 1 — Build the basic run pipeline

* create investigation
* open seed URL
* save screenshot + HTML
* classify page
* return planner output

Step 2 — Build item discovery

* identify result cards
* extract detail URLs
* store stable keys

Step 3 — Add basic pagination traversal

* click next
* detect page change
* collect across all pages
* stop when exhausted

Step 4 — Add detail processing

* visit each detail URL
* extract data
* evaluate against objective

Step 5 — Generate result report

* matches
* ambiguous
* evidence
* coverage

Step 6 — Generalize traversal

* load more
* infinite scroll
* URL parameter pagination

Step 7 — Add reliability

* retries
* partial failure handling
* resumability
* trace logging

Step 8 — Build product UI

* start run
* view progress
* inspect final results

⸻

25. My Recommendation on Browser Harness

Use it in parallel as a research track

I would create a small R&D workstream:

“Browser Harness Exploration”

Try:

1. IBM California jobs task.
2. One infinite-scroll directory task.
3. One load-more product catalog task.

Document:

* whether it discovers traversal patterns well,
* whether it handles the task with low prompting,
* what helper code it invents,
* what we should steal conceptually.

Browser Harness is promising because it gives agents raw access to Chrome with very little framework interference, and it appears to be evolving quickly.  ￼

But the product we are designing needs workflow infrastructure around the browser, not just access to the browser. So I would treat it as a research accelerator, not the production backbone.

⸻

26. Final Architecture Recommendation

Phase 1 production architecture:
- FastAPI backend
- PostgreSQL
- Playwright browser runtime
- Structured LLM planner/extractor
- Deterministic traversal strategies
- Durable investigation state
- Next.js progress/results UI
Research track:
- Browser Harness experiments
- Browser Use Cloud / Browserbase comparison for hard websites

⸻

27. One-Sentence Engineering Goal

Build a browser agent that can reliably turn a multi-page, hard-to-query website into an evidence-backed structured answer, while proving how much of the site it actually covered.