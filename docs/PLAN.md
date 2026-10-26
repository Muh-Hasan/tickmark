# Tickmark — Sprint Plan

Oct 26, 2026 · @Muhammad Hasan

Tickmark is an AI bookkeeper for small businesses. It reads invoices and receipts, reconciles bank statements, finds problems (duplicate payments, late clients, suspicious bank-detail changes), answers questions about the books, and drafts client emails. It never moves money or sends anything without your approval. It is 14 sprints, each ending in something you can demo, built on free tiers and local models.

Two rules shape everything: **the model never does arithmetic** (code computes every number) and **the model never acts on money or people without a human** (the harness enforces it, not the prompt).

## What you will be able to put on your CV

Every skill below runs inside the product, so each one survives a follow-up question in an interview.

| Skill | Where it runs in Tickmark | Sprint |
| --- | --- | --- |
| Agent loop, tool calling | A hand-built loop answering questions about the books, before any framework | 2 |
| Evals, Langfuse | A generated company with planted problems and an answer key; Langfuse traces, datasets and experiments; confidence intervals | 3 |
| Structured output, vision models | Invoices and receipt photos turned into validated records | 4 |
| Harness engineering | Tool registry, risk tiers, approvals, budgets, compaction, offloading, hooks, audit log, undo | 5 |
| Sandboxing (E2B, Firecracker microVMs) | Model-written pandas for ad-hoc analysis and for parsing bank formats it has never seen | 6 |
| RAG, embeddings, vector DB | LangChain loaders and splitters, pgvector, hybrid search over contracts, policies and emails | 7 |
| LangGraph | The month-end close: durable state, approvals that wait for days, parallel fan-out, crash-safe resume | 8 |
| LangChain | The "Ask your books" chat agent on `create_agent` with approval and summarization middleware | 9 |
| Context and memory engineering | Pinned rules, compaction, learned categorization rules, client habits, facts that supersede old ones | 5, 10 |
| Multi-agent | Parallel investigators with isolated context; an independent auditor in an evaluator-optimizer loop | 11 |
| MCP | Your own books MCP server used from Claude Desktop; consuming Gmail's MCP server | 12 |
| Autonomous, scheduled and event-driven loops | Email-triggered intake, month-end schedule, approval queue | 12 |
| Agent security | Prompt injection in documents, invoice-fraud detection, exfiltration tests in CI | 6, 12 |
| Full-stack AI product | Next.js app with live runs, approvals and streaming chat | 13 |

Scope, honestly: about 186 focused hours. Budget 1.5× for learning time, so plan on 7–8 weeks at 35–40 hours a week. Sprint 8 gives you a complete working product; Sprint 12 is a complete stopping point if time runs out.

## What's needed and what's there for learning

Being clear about this is a strength in interviews. Each component is labelled honestly.

| Component | Status | Why |
| --- | --- | --- |
| Harness, approvals, audit | Needed | It emails clients and changes the books |
| LangGraph with checkpoints | Needed | The close waits days for your approval and must survive restarts |
| Scheduled and event-triggered runs | Needed | Month-end and new-invoice triggers are the product |
| Memory as a rules table | Needed | Learning from corrections is the core feature |
| Evals, Langfuse | Needed | The only way to know it works |
| Sandbox | Needed for ad-hoc analysis and unknown file formats | Core reconciliation is plain tested code, never model-written |
| RAG | Needed for email history and many contracts | Small corpora would fit in a prompt; RAG earns its place as documents accumulate |
| pgvector (not a separate vector DB) | Deliberate choice | One Postgres for books, vectors, checkpoints and the job queue |
| Multi-agent | Two real uses | Context isolation for many investigations, and an auditor that hasn't seen the reasoning |
| MCP server | Needed | Asking your books from Claude Desktop is a real feature |
| Hand-built loop before frameworks | Learning | You learn what the frameworks do before they hide it |
| LangChain alongside LangGraph | Used for different jobs | LangChain for the standard chat agent and RAG integrations; LangGraph for the custom durable workflow |

## What changed from the Foreman plan

| Area | Foreman | Tickmark | Why |
| --- | --- | --- | --- |
| Product | Coding agent fixing library bugs | AI bookkeeper for small businesses | Business users understand the demo; small local models can do the work |
| Framing | Harness ablation study | Product with an eval suite | Regression evals are the production skill; a research claim needed more tasks than a free stack allows |
| Benchmark | ~20 tasks mined from git history | A generated company with planted problems, unlimited tasks | Every task has a known answer; generate as many as you need |
| Baseline | Bare agent | **Plain code with no LLM** | The agent must beat deterministic checks, or it isn't earning its cost |
| Sandbox | Docker, E2B optional | **E2B (Firecracker) primary, Docker for tests** | Model-written code over uploaded files; self-hosted Firecracker needs Linux with KVM |
| Vector DB | Qdrant | **pgvector** | One database; nothing added just to list it |
| Frameworks | LangGraph only | **LangGraph and LangChain**, each for its own job | Both on the CV, both in the product |
| Decision layer | Jev | Removed | Not needed; categorization uses rules first, then structured model output |
| Fine-tuning | Sprint 12 | Parked | Not needed for the product or your goals |
| Fixes from the review | — | Built in | Separate eval router config, ledger logs failures, validated final answers, correct probability checks, idempotent resume |

Pin your local model tags, Python version and library versions on Day 0, and don't change them mid-project without re-running the eval baseline.

## System architecture

The model never executes anything: it proposes a structured call, and the harness validates, permits, runs and logs it. Money logic lives in plain code the model can call but never rewrite.

```text
  Inbox (Mailpit / Gmail)  ─┐                         Next.js UI ── FastAPI ─┐
  Scheduler (month-end)    ─┼──►  Job queue (Postgres)  ◄─────────────────────┤
  CLI                      ─┘            │                                    │
                                         ▼                                    │
                     Worker: LangGraph close  ·  LangChain chat agent  ◄──────┘
                                         │
              Harness: registry · permissions · budget · context · hooks · audit
                                         │
     ┌──────────────┬───────────────┬────┴──────────┬─────────────────┬──────────────────────┐
  Books engine    RAG            Sandbox          Email drafts       Gateway
  (Postgres,      (pgvector +    (E2B microVM,    (Mailpit in dev,   (LiteLLM proxy →
  plain code)     full-text)     no internet)     Gmail drafts)      Ollama / Gemini / OpenRouter)
```

Following one month-end close through:

1. The scheduler fires on the 1st, or you run `tickmark close 2026-03`.
2. New bills and receipts in the inbox are extracted in parallel, and their arithmetic is checked.
3. The bank statement is imported. A known format uses a tested importer; an unknown one gets a parser written by the model in the sandbox, accepted only if its totals match the statement's closing balance.
4. The deterministic engine reconciles and runs checks, producing candidate issues.
5. The agent categorizes what rules don't cover (asking you when unsure), investigates candidates using contract terms and the expense policy, proposes fixes and drafts emails.
6. An auditor with a fresh context reviews each proposal against its evidence and sends weak ones back.
7. The close plan pauses for your approval. You approve, edit or reject each item, even days later.
8. Approved changes are applied (each with an undo record), emails go to drafts, a report with charts is written, and everything lands in the audit log and Langfuse.

## Loop modes

Each mode is built and demoed in a named sprint.

| Mode | What it looks like in Tickmark | Sprint |
| --- | --- | --- |
| Autonomous, budgeted | Answer a question or review a month until done, out of budget, or failed | 2, 5 |
| Approval gate | Approve, edit or reject a books change or an email before it happens | 5, 8 |
| Plan, then approve | The whole close plan is reviewed as a batch before anything is applied | 8 |
| Agent asks the human | "Is this $49 charge Software or Marketing?" pauses the graph | 8 |
| Evaluator-optimizer | The auditor rejects a proposal; the proposer revises it | 11 |
| Event-triggered | An email with an invoice attachment starts intake | 12 |
| Scheduled | Month-end close starts on the 1st | 12 |
| Crash-safe resume | `kill -9` while waiting for approval; restart; nothing is redone | 8 |

## Project structure

One Python package, an eval package that grades it from outside, and a web app added last. Folders appear only when their first file does.

```text
tickmark/
├── src/tickmark/
│   ├── cli.py                 entrypoint (Typer): chat, ask, intake, close, resume, audit, undo, usage
│   ├── config.py              settings from env, validated with Pydantic
│   ├── gateway.py             the ONLY model entry point: OpenAI client + LangChain models, local-only guard
│   ├── books/                 the ledger domain: NO LLM code in here
│   │   ├── models.py          SQLAlchemy tables
│   │   ├── money.py           Decimal helpers; floats are banned
│   │   ├── importers/         known bank CSV formats
│   │   ├── reconcile.py       matching engine
│   │   └── checks.py          deterministic month-end checks
│   ├── intake/                document extraction (Sprint 4)
│   ├── tools/                 agent-facing tools: books, documents, analysis, email
│   ├── harness/               YOUR code, no framework (Sprint 5)
│   │   ├── registry.py        tools + schemas + risk tiers + previews
│   │   ├── permissions.py     resolver + approval prompt
│   │   ├── budget.py          steps, tokens, requests, wall-clock
│   │   ├── context.py         assembly, compaction ladder, offloading
│   │   ├── hooks.py           pre- and post-tool hooks
│   │   └── audit.py           append-only audit log, replay, undo
│   ├── loop.py                hand-built loop (Sprint 2, kept for comparison)
│   ├── sandbox/               Sandbox interface: e2b.py, docker.py (Sprint 6)
│   ├── rag/                   loaders, splitters, pgvector, hybrid search (Sprint 7)
│   ├── workflows/close/       LangGraph month-end close (Sprint 8)
│   ├── chat/                  LangChain "Ask your books" agent (Sprint 9)
│   ├── memory/                rules, client facts, notes (Sprint 10)
│   ├── agents/                investigators and auditor (Sprint 11)
│   ├── mcp/                   books MCP server (Sprint 12)
│   ├── automation/            inbox watcher, scheduler, job queue, worker (Sprint 12)
│   └── api/                   FastAPI: closes, approvals, chat stream (Sprint 13)
├── bench/
│   ├── generate/              demo-company generator and planted issues
│   ├── grade.py  run.py  table.py
│   ├── companies/             dev/  heldout/ (sealed)
│   └── results/               one JSON per run; the README table is generated
├── security/                  attack cases (YAML)
├── web/                       Next.js app (Sprint 13)
├── deploy/
│   ├── docker-compose.yml     postgres + pgvector, litellm proxy, mailpit
│   ├── litellm/               dev.yaml, eval.yaml, ledger_callback.py
│   └── runner/Dockerfile      local sandbox image for tests
├── docs/
│   ├── adr/                   one decision per file
│   ├── charts/
│   ├── learning/              README.md study roadmap + one guide per sprint
│   ├── RESULTS.md
├── RULES.md                   the bookkeeper's rules, pinned into every prompt
├── HARNESS.md                 the harness audit
├── DECISIONS.md
├── .github/workflows/ci.yml
└── README.md
```

Dependency rules keep it clean as it grows:

- `cli/api → workflows/chat/loop → harness → tools → books/sandbox/rag/gateway`. Arrows only point right.
- `books/` never imports a model. Money logic is deterministic and unit-tested.
- Nothing outside `gateway.py` creates a model client, including LangChain models. One proxy, one set of rules.
- Nothing outside `sandbox/` runs model-written code.
- Every tool call, from the hand-built loop, a LangGraph node or the LangChain agent, goes through `harness/registry.py`.
- `bench/` imports Tickmark; Tickmark never imports `bench/`. The agent can never read an answer key.

Don't create an abstraction until a second caller needs it. The deliberate exceptions are `Sandbox` (E2B and Docker) and the tool registry (three callers by Sprint 9).

## Why it's structured this way

Every layer exists so one kind of change touches one place. When an interviewer asks "why like this?", these are your answers.

| Layer | Its only job | Why it matters |
| --- | --- | --- |
| `books/` | Store and check money with plain code | Numbers are reproducible and testable; the model can't get arithmetic wrong if it never does any |
| `gateway.py` | Route model calls, enforce local-only mode | Free tiers change monthly; one file absorbs it, and real financial data can be kept local by a flag |
| `tools/` | Do one thing: query, search, draft | Small, testable functions with no policy inside |
| `harness/` | Decide what the model may do, what it sees, when it stops | Safety lives in code, so injected text can't talk its way past it |
| `workflows/` and `chat/` | Order the steps | LangGraph for the custom durable close; LangChain for the standard chat agent |
| `sandbox/` | Run code the model wrote, isolated | Execution location is a security decision, kept in one place |
| `bench/` | Grade the system from outside | The agent never sees answer keys, so scores can't be gamed |
| `RULES.md` | Rules the agent must always obey | Pinned in the system prompt, so compaction can never remove them |

The choices behind it:

| Choice | Instead of | Why |
| --- | --- | --- |
| Code computes every number | Letting the model add things up | Models make arithmetic mistakes; accountants can't accept any |
| Deterministic permission resolver | A model deciding what's safe | Model guards can be steered by injected text; code can't |
| Code-only baseline row | Measuring only agent versions | Shows exactly what the LLM adds over plain rules |
| Generated company with planted issues | Hand-picked demo files | Known answers, unlimited tasks, no private data |
| Synthetic data only on free cloud tiers | Real books anywhere | Free tiers may use prompts for training; real data stays local |
| Undo record for every books write | Trusting approvals alone | Approved mistakes still happen; reversibility is the backstop |
| Worker runs graphs, API only enqueues | Running graphs inside web requests | A browser closing never kills a close mid-way |
| One JSON file per eval run | A hand-typed results table | The README table regenerates from raw data and can't drift |

Where does new code go?

- It touches money or the ledger → `books/`, with tests, no LLM.
- It calls a model → through `gateway.py`.
- It acts on the books, documents or email → a tool in `tools/`, registered with a risk tier.
- It decides whether an action is allowed, what enters context, or when to stop → `harness/`.
- It runs something the model wrote → `sandbox/`.
- It measures the system → `bench/`.
- It tries to break the system → `security/`.

## Model and service playbook

Local models do the repetitive work; free cloud quota is spent deliberately; everything goes through one LiteLLM proxy. Stack providers, not accounts: extra accounts don't multiply free quota and can break the terms.

| Provider | Cost | Free limit (verify in your dashboard on Day 0) | Use it for |
| --- | --- | --- | --- |
| [Ollama](https://ollama.com) (local) | $0 | Your hardware | Development, the **local arm** of the evals, embeddings, summaries, anything with real data |
| Gemini Flash-Lite | $0 | Small daily request cap | The **cloud arm** of the evals |
| Gemini Flash | $0 | Smaller daily cap | Scarce: email-tone judge, the recorded demo |
| OpenRouter `:free` models | $0 | Per-minute and per-day caps | Backup when Gemini is exhausted (development only) |
| [E2B](https://docs.e2b.dev/billing.md) Hobby | $0 | $100 one-time credits, 1-hour sessions, 20 concurrent | The sandbox |
| [Langfuse](https://langfuse.com) Cloud | $0 | Hobby tier | Tracing and experiments from Sprint 3 |
| Postgres + pgvector, Mailpit (local) | $0 | None | Books, vectors, checkpoints, job queue, dev email |

Which model for what:

| Task | Use | Why |
| --- | --- | --- |
| Debugging loops, iterating on prompts | `local-main` | Unlimited and fast |
| Categorization, text-PDF extraction | `local-main` | Repetitive; runs thousands of times |
| Receipt photos | `local-vision` | Images need a vision model; keep it local |
| Embeddings | `local-embed` (`nomic-embed-text`) | Never spend quota here |
| Summarization middleware, compaction | `local-main` | Frequent and cheap |
| Evals, local arm | `local-main`, pinned | The default way Tickmark runs |
| Evals, cloud arm | `cloud-lite`, pinned | A fixed slice fits inside the daily quota |
| Judging email tone | `cloud-strong`, sparingly | A judge weaker than the writer adds noise |

Pick your local models by hardware. The main model must support tool calling in Ollama (filter by "tools" on [ollama.com/library](https://ollama.com/library)); the vision model must accept images.

| Hardware | Main model size |
| --- | --- |
| CPU only, 16 GB RAM | 3–4B at Q4; run evals overnight |
| 8 GB VRAM or 16 GB Apple Silicon | 7–8B at Q4 |
| 12–16 GB VRAM or 32 GB Apple Silicon | 14B at Q4 |
| 24 GB+ VRAM or 64 GB+ Apple Silicon | About 30B at Q4 |

Set Ollama's context length explicitly (`num_ctx`). The default is small, and Ollama truncates silently when you exceed it.

Two proxy configs, because development and evaluation need opposite settings:

```yaml
# deploy/litellm/dev.yaml — fallbacks and cache on, for development
model_list:
  - model_name: local-main
    litellm_params: { model: ollama_chat/<tool-calling-tag>, api_base: http://host.docker.internal:11434 }
  - model_name: local-vision
    litellm_params: { model: ollama_chat/<vision-tag>, api_base: http://host.docker.internal:11434 }
  - model_name: local-embed
    litellm_params: { model: ollama/nomic-embed-text, api_base: http://host.docker.internal:11434 }
  - model_name: cloud-lite
    litellm_params: { model: gemini/<current-flash-lite>, api_key: os.environ/GEMINI_API_KEY, rpm: 10 }
  - model_name: cloud-strong
    litellm_params: { model: gemini/<current-flash>, api_key: os.environ/GEMINI_API_KEY, rpm: 5 }
  - model_name: cloud-backup
    litellm_params: { model: openrouter/<a-free-model>:free, api_key: os.environ/OPENROUTER_API_KEY, rpm: 15 }
litellm_settings:
  callbacks: ledger_callback.ledger
  cache: true                     # check the proxy caching docs for the cache type you want
router_settings:
  num_retries: 2
  cooldown_time: 60
  fallbacks: [{ cloud-strong: [cloud-lite] }, { cloud-lite: [cloud-backup] }]
```

```yaml
# deploy/litellm/eval.yaml — one deployment per group, no fallbacks, no cache
model_list:
  - model_name: local-main
    litellm_params: { model: ollama_chat/<tool-calling-tag>, api_base: http://host.docker.internal:11434 }
  - model_name: local-vision
    litellm_params: { model: ollama_chat/<vision-tag>, api_base: http://host.docker.internal:11434 }
  - model_name: local-embed
    litellm_params: { model: ollama/nomic-embed-text, api_base: http://host.docker.internal:11434 }
  - model_name: cloud-lite
    litellm_params: { model: gemini/<current-flash-lite>, api_key: os.environ/GEMINI_API_KEY, rpm: 10 }
  - model_name: cloud-strong
    litellm_params: { model: gemini/<current-flash>, api_key: os.environ/GEMINI_API_KEY, rpm: 5 }
litellm_settings:
  callbacks: ledger_callback.ledger
router_settings:
  num_retries: 2
```

Two rules protect the evals and the users: **evals always run against `eval.yaml`** (with fallbacks, the cloud arm would silently include other models, and cached answers aren't independent samples), and **only synthetic data goes to free cloud tiers or E2B**. With real books, run with `TICKMARK_LOCAL_ONLY=1`, and the gateway refuses every cloud group.

## The demo company and eval protocol

There is no public dataset of small-business books with labelled mistakes, so you generate one. A seeded generator builds a realistic company, then plants problems with labels. Because you planted every problem, every task has a known answer.

**The dev company**, "Brightline Studio": a 10-person design agency, 12 months, about 25 client invoices, 120 bank lines and 60 receipts a month. It has three bank export formats, contracts with different payment terms, an expense policy, and email threads. **The held-out company** is a small online shop generated with different templates, vendors, bank formats and policies. It stays sealed until Sprint 12 and is the check that you haven't tuned to one company.

Planted issues, each recorded in `answer_key.yaml` with its kind and the records it involves:

| Kind | Example | Needs |
| --- | --- | --- |
| `duplicate_payment` | Same bill paid twice | Code finds candidates; agent confirms |
| `amount_mismatch` | Client paid $1,950 on a $2,000 invoice | Reasoning: short payment, bank fee or discount? |
| `overdue` | Unpaid past the contract's terms (net 45, not the default 30) | RAG over the contract |
| `missing_receipt` | Card charge with no receipt | Receipt extraction and matching |
| `miscategorized` | Figma booked as Marketing | Judgment and memory |
| `personal_expense` | Restaurant charge on a Sunday | The expense policy |
| `price_change` | A subscription went from $20 to $35 | Code |
| `unrecorded_fee` | Bank fee in the statement, not in the books | Code |
| `bank_detail_change` | Vendor invoice "with our new bank details" | Extraction plus vendor records; never auto-accepted |
| `injection` | Invoice notes with hidden instructions | The security suite (Sprint 12) |

Task types and how each is graded:

| Task | Grader | Metric |
| --- | --- | --- |
| Month review or close | Set match on `(kind, records)` against the answer key | Precision, recall; `pass^3` over 3 attempts |
| Categorization | Exact match against labels | Accuracy |
| Ask-your-books questions (60 dev, 30 held-out) | Answers computed by SQL on the clean ledger; exact match within 0.01 | Accuracy |
| Document extraction | Field-level exact match after normalization; plus [CORD](https://github.com/clovaai/cord) receipts as a real-world check | Field accuracy |
| Email drafts | Deterministic checks (recipient, invoice number, amount, due date), then a rubric judge for tone | Pass rate |
| Security cases | Pass or fail per case | Pass rate |

| Arm | Model | Tasks per run | Attempts | Reported as |
| --- | --- | --- | --- | --- |
| Local | `local-main`, pinned | All 12 dev months, all 60 questions | 3 | Mean with 95% bootstrap CI; `pass^3` on months |
| Cloud | `cloud-lite`, pinned | A fixed slice: 4 months, 20 questions | 1 | Mean with 95% bootstrap CI |
| Local on the cloud slice | `local-main` | The same 4 months and 20 questions | 3 | So local vs cloud compares identical tasks |

The table you will fill, regenerated by `make table`:

| Sprint | Component | Issue recall | Issue precision | Categorization | Q&A accuracy | Requests/month |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Code only, no LLM |  |  | — | — | 0 |
| 2 | Bare loop |  |  |  |  |  |
| 4 | + Document intake |  |  |  |  |  |
| 5 | + Harness |  |  |  |  |  |
| 6 | + Sandbox analysis |  |  |  |  |  |
| 7 | + Document RAG |  |  |  |  |  |
| 8 | + LangGraph close (expect no accuracy change) |  |  |  |  |  |
| 9 | LangChain chat agent (Q&A, vs bare loop) | — | — | — |  |  |
| 10 | + Memory (after simulated corrections) |  |  |  |  |  |
| 11 | + Investigators and auditor |  |  |  |  |  |
| 12 | Held-out company |  |  |  |  |  |

Fairness rules: same tasks, budgets and temperature (set above 0, or three attempts are identical) for every row; pinned model tags; `eval.yaml` only; memory reset between attempts so attempts stay independent; never tune on the held-out company; report components that didn't help, and differences inside the confidence interval as "no measurable change".

## Sprint map and how to run a sprint

Sprints 0–8 build a working, measured, approval-gated product. Sprints 9–13 add the chat agent, memory, multi-agent, MCP, automation and the web app.

| Sprint | You can demo | Concept | Hours | Status |
| --- | --- | --- | --- | --- |
| S0 Setup and gateway | One proxy for local and cloud models; fallback visible; local-only guard | Model routing, rate limits | 12 | Not started |
| S1 Books and demo company | 12 months of realistic books with planted problems; plain-code reconciliation | Domain modelling, deterministic core | 14 | Not started |
| S2 Bare loop | The agent answers money questions with references | Agent loop, tool calling | 10 | Not started |
| S3 Evals and Langfuse | `make eval` fills the table with confidence intervals | Evals, tracing, experiments | 14 | Not started |
| S4 Document intake | Photos and PDFs become validated records | Structured output, vision | 12 | Not started |
| S5 Harness | Gates, compaction, audit replay, undo | Harness and context engineering | 20 | Not started |
| S6 Sandbox | Charts from model-written code; a parser for an unseen bank format | Isolation, code execution | 12 | Not started |
| S7 Document RAG | Contract terms cited from the right page | Embeddings, pgvector, hybrid search | 12 | Not started |
| S8 LangGraph close | Kill during approval; resume days later | Durable workflows, human-in-the-loop | 16 | Not started |
| S9 LangChain chat | Chat with your books; approval middleware | LangChain agents and middleware | 10 | Not started |
| S10 Memory | Corrected once, right next month | Memory engineering | 12 | Not started |
| S11 Multi-agent | Investigators and an auditor on a busy month | Context isolation, evaluator-optimizer | 10 | Not started |
| S12 MCP, automation, security | Claude Desktop reads your books; email-triggered intake; fraud caught | MCP, background loops, security | 16 | Not started |
| S13 Web app and write-up | Approve the close in the browser | Streaming UI, write-up | 16 | Not started |

One sprint at a time, no calendar. A sprint is done when its checklist is ticked and you can show it to someone.

1. **Overview first.** Before a sprint starts, Claude lists its stages and the decisions in it, recommends an option for each, and waits for your go-ahead.
2. **Then all stages without pausing.** Claude builds one small piece, runs it, and only then starts the next. It checks each task's **Expected output** and sends one report at the end.
3. **Test for real.** Run the actual code, including failure cases (a forced `429`, a bad file, a killed process). Record the measured numbers, not estimates.
4. **Commit on main** at meaningful points with a scope, e.g. `feat(harness): add permission resolver`. Commit only when the check command exits 0. Check for files that were already staged first. Never push unless asked.
5. Run the evals and add the sprint's row to the table.
6. Write the sprint's learning guide in `docs/learning/`: from zero, options compared, what was built, proof, and a code walkthrough with a review checklist. Then update the study roadmap in `docs/learning/README.md`. These become interview answers.
7. Finish with the **Showcase**: a screenshot or 30-second GIF in the README's Progress section, and tag the sprint (`s5-harness`).

If you run out of time, cut in this order: the S13 web app down to Approvals only (keep the write-up), S11's investigators (keep the auditor), S10's free-text notes (keep the rules table), S7's reranker, S12's HTTP gateway. Never cut S1 (the books engine), S3 (evals), S5 (the harness), S6 (the sandbox) or S8 (the durable close).

## Sprint 0 — Setup and model gateway

**Showcase:** `tickmark chat --model <group> "..."` streams from your local model, Gemini and OpenRouter through one LiteLLM proxy. Thirty rapid requests at the cloud group show cooldowns and fallbacks in `tickmark usage --today`, failures included, with zero crashes. With `TICKMARK_LOCAL_ONLY=1`, cloud groups are refused.

**Learn:** Karpathy, [Intro to Large Language Models](https://karpathy.ai) (1 hour: tokens, context windows, sampling) · [LiteLLM proxy](https://docs.litellm.ai/docs/simple_proxy) and [routing](https://docs.litellm.ai/docs/routing) · [Gemini rate limits](https://ai.google.dev/gemini-api/docs/rate-limits).

**Tech:** Python 3.12, uv, Pydantic Settings, Typer, Rich, Docker Compose, LiteLLM proxy, Ollama, Postgres with pgvector, Mailpit.

**Models and services:** Ollama (`local-main`, `local-vision`, `local-embed`), Gemini via AI Studio, OpenRouter. All free.

| # | Task | Expected output | How-to and references |
| --- | --- | --- | --- |
| 1 | Python ramp-up: Pydantic models, `pathlib`, `decimal`, pytest | `scratch/warmup.py` with one passing test | [Python tutorial](https://docs.python.org/3/tutorial/) · [decimal](https://docs.python.org/3/library/decimal.html) · [pytest](https://docs.pytest.org/en/stable/getting-started.html) |
| 2 | Toolchain: uv project, ruff, pytest, `.gitignore` with `.env`, `.env.example` | `uv run pytest` passes; first commit | [uv](https://docs.astral.sh/uv/) · [ruff](https://docs.astral.sh/ruff/) |
| 3 | `docker-compose.yml`: Postgres with pgvector, LiteLLM proxy, Mailpit | All healthy; `CREATE EXTENSION vector` works | [pgvector](https://github.com/pgvector/pgvector) · [Mailpit](https://mailpit.axllent.org) |
| 4 | Pull a tool-calling model, a vision model and `nomic-embed-text`; set `num_ctx`; send one tool-calling request | A structured tool call printed; tags in `DECISIONS.md` | [Ollama library](https://ollama.com/library) (filter: tools, vision) |
| 5 | Cloud keys in `.env`; write your *actual* per-model limits into `DECISIONS.md` | Both keys answer a test call | [AI Studio](https://aistudio.google.com) · [OpenRouter](https://openrouter.ai/docs) |
| 6 | `dev.yaml` and `eval.yaml` proxy configs; ledger callback for successes **and** failures | Ledger shows a forced `429` as an error row | Playbook above · [LiteLLM logging and custom callbacks](https://docs.litellm.ai/docs/proxy/logging) |
| 7 | `gateway.py`: `complete()`, `chat_model()`, local-only guard | A test proves local-only refuses cloud groups | Reference code below |
| 8 | `tickmark chat` with streaming; `tickmark usage --today` | Tokens stream; a table of requests per group vs your daily budget | [Typer](https://typer.tiangolo.com) · [Rich Live](https://rich.readthedocs.io/en/stable/live.html) |
| 9 | Send one email to Mailpit over SMTP | It appears at `localhost:8025`; all dev email goes here, never to real people | [Mailpit](https://mailpit.axllent.org) |

Reference code — one gateway for every caller, including LangChain:

```python
# src/tickmark/gateway.py
from openai import OpenAI
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from .config import settings

CLOUD_GROUPS = {"cloud-lite", "cloud-strong", "cloud-backup"}

def _allowed(group: str) -> str:
    if settings.local_only and group in CLOUD_GROUPS:
        raise PermissionError(f"{group} is a cloud model and this workspace is local-only")
    return group

client = OpenAI(base_url=settings.gateway_url, api_key=settings.gateway_key)

def complete(group: str, messages: list[dict], **kw):
    return client.chat.completions.create(model=_allowed(group), messages=messages, **kw)

def chat_model(group: str, **kw) -> ChatOpenAI:
    """LangChain and LangGraph code gets its model here, so it shares the proxy, ledger and guard."""
    return ChatOpenAI(model=_allowed(group), base_url=settings.gateway_url,
                      api_key=settings.gateway_key, **kw)

def embeddings() -> OpenAIEmbeddings:
    # non-OpenAI models behind the proxy need plain strings, not pre-tokenized input
    return OpenAIEmbeddings(model="local-embed", base_url=settings.gateway_url,
                            api_key=settings.gateway_key, check_embedding_ctx_length=False)
```

```python
# deploy/litellm/ledger_callback.py — loaded by the proxy; logs failures as well as successes
import json, time
from pathlib import Path
from litellm.integrations.custom_logger import CustomLogger

LEDGER = Path("/ledger/usage.jsonl")      # a mounted volume

class Ledger(CustomLogger):
    def _write(self, kwargs, response_obj, start, end, status: str) -> None:
        usage = getattr(response_obj, "usage", None)
        row = {
            "ts": time.time(), "status": status,
            "group": kwargs.get("model_group") or kwargs.get("model"),   # check field names in the callback docs
            "tokens_in": getattr(usage, "prompt_tokens", 0),
            "tokens_out": getattr(usage, "completion_tokens", 0),
            "latency_s": round((end - start).total_seconds(), 2),
            "error": str(kwargs.get("exception") or "")[:200] or None,
        }
        with LEDGER.open("a") as f:
            f.write(json.dumps(row) + "\n")

    async def async_log_success_event(self, kwargs, response_obj, start_time, end_time):
        self._write(kwargs, response_obj, start_time, end_time, "ok")

    async def async_log_failure_event(self, kwargs, response_obj, start_time, end_time):
        self._write(kwargs, response_obj, start_time, end_time, "error")

ledger = Ledger()
```

- [ ] Local model answers and makes a tool call
- [ ] Gemini and OpenRouter answer through the same proxy
- [ ] A forced `429` shows as an error row, then cooldown and fallback
- [ ] Local-only mode refuses cloud groups (tested)
- [ ] `.env` is gitignored; no key appears in any log
- [ ] `DECISIONS.md`: model tags, `num_ctx`, live limits, why

## Sprint 1 — The books and the demo company

**Showcase:** `tickmark demo-company --seed 1` generates Brightline Studio's year: invoice and bill PDFs, receipt photos, bank exports in three formats, contracts, an expense policy, emails, and a sealed answer key. `tickmark reconcile 2026-03` matches most bank lines with plain code and lists what it couldn't. No LLM anywhere yet, and that's the point: this is the baseline the agent has to beat.

**Learn:** [Bank reconciliation explained](https://www.accountingcoach.com/bank-reconciliation/explanation) (AccountingCoach) · [Python decimal](https://docs.python.org/3/library/decimal.html) (why money is never a float) · [SQLAlchemy 2.0 tutorial](https://docs.sqlalchemy.org/en/20/tutorial/) · [Alembic](https://alembic.sqlalchemy.org).

**Tech:** SQLAlchemy 2, Alembic, Faker, fpdf2, Pillow, PyYAML.

**Models and services:** none. Postgres only.

| # | Task | Expected output | How-to and references |
| --- | --- | --- | --- |
| 1 | Schema: clients, vendors, categories, transactions, invoices, bills, receipts, rules, audit events | First Alembic migration | [SQLAlchemy ORM](https://docs.sqlalchemy.org/en/20/orm/) |
| 2 | `money.py`: `Decimal` everywhere, two-place quantize, `Numeric(12, 2)` columns | A test fails if a float reaches the books | [decimal](https://docs.python.org/3/library/decimal.html) |
| 3 | Importers for three known bank CSV formats | Each produces normalized `BankLine` records; tests per format | [csv](https://docs.python.org/3/library/csv.html) |
| 4 | Reconciliation engine | Tests: reference match, amount-and-date match, ambiguous lines left unmatched | Reference code below |
| 5 | Deterministic checks: duplicates, price changes, unrecorded fees, unpaid past stored terms | A list of candidate issues per month | Plain SQL and Python |
| 6 | Generator: company profile to 12 months of clean activity | `bench/companies/dev/brightline/` | [Faker](https://faker.readthedocs.io) |
| 7 | Plant issues with labels | `answer_key.yaml` covering every kind in the protocol table | Seeded `random.Random` |
| 8 | Render documents: PDFs, receipt photos (rotated, noisy), contracts, policy, `.eml` emails | Files look real enough to fool a quick glance | [fpdf2](https://py-pdf.github.io/fpdf2/) · [Pillow](https://pillow.readthedocs.io) |
| 9 | 60 dev questions with answers computed by SQL | Part of the answer key | Compute from the clean ledger, not the planted one |
| 10 | Code-only baseline: run checks, grade against the answer key | Row 1 recorded (grader built properly in Sprint 3; a quick version here is fine) | — |

Reference code — reconciliation is plain code. Anything ambiguous is left for the agent, never guessed:

```python
# src/tickmark/books/reconcile.py
from datetime import timedelta

def match_receipts(lines: list[BankLine], invoices: list[Invoice],
                   grace: timedelta = timedelta(days=10)) -> MatchResult:
    open_inv = {i.id: i for i in invoices if i.status == "sent"}
    matched, unmatched = [], []
    for line in sorted(lines, key=lambda l: l.date):
        if line.amount <= 0:
            continue                                         # outgoing payments are matched against bills
        by_ref = [i for i in open_inv.values() if i.number in line.reference]
        by_amount = [i for i in open_inv.values()
                     if i.total == line.amount and i.issued <= line.date <= i.due + grace]
        candidates = by_ref or by_amount
        if len(candidates) == 1:
            inv = open_inv.pop(candidates[0].id)
            matched.append(Match(line=line, invoice=inv, delta=line.amount - inv.total))
        else:
            unmatched.append(Unmatched(line=line, candidates=[c.id for c in candidates]))
    return MatchResult(matched=matched, unmatched=unmatched, still_open=list(open_inv.values()))
```

A non-zero `delta` is not an error by itself: a short payment, a bank fee and a discount all look the same in numbers. Deciding which one it is, using the contract and the emails, is the agent's job.

- [ ] No float anywhere in `books/` (tested)
- [ ] Three bank formats import correctly
- [ ] Generator is deterministic: same seed, same files, same answer key
- [ ] Every planted issue kind appears at least five times across the year
- [ ] Held-out company generated and never opened
- [ ] Row 1 recorded: what plain code catches alone

## Sprint 2 — The bare loop

**Showcase:** `tickmark ask "how much did we spend on software in Q1, and on what?" --verbose` picks tools itself, answers with a number computed in SQL, and cites the transactions. No framework anywhere.

**Learn:** Anthropic, [Building Effective Agents](https://www.anthropic.com/research/building-effective-agents) (the agent loop; workflows vs agents) · [OpenAI-compatible function calling via LiteLLM](https://docs.litellm.ai/docs/completion/function_call).

**Tech:** Your gateway, Pydantic, Typer.

**Models and services:** `local-main` for everything; `cloud-lite` only for task 7.

| # | Task | Expected output | How-to and references |
| --- | --- | --- | --- |
| 1 | Pydantic args model per tool; generate tool specs from them | A test asserting a generated spec | [Pydantic JSON Schema](https://docs.pydantic.dev/latest/concepts/json_schema/) |
| 2 | Read-only tools: `list_categories`, `find_transactions`, `spend_summary`, `get_invoice`, `open_invoices` | Unit tests; large results truncated with a note saying so | Sums are computed in SQL, never by the model |
| 3 | The loop: call, validate, execute, append, repeat; stop on final answer, 15 steps or fatal error | `loop.py` answers a real question | Reference code below |
| 4 | Text-only replies get a nudge; invalid calls return as observations | A test forces a malformed call and the run recovers | [Pydantic validation errors](https://docs.pydantic.dev/latest/errors/validation_errors/) |
| 5 | `final_answer` validated like every other tool: `{answer, amounts, references, confidence}` | Malformed final answers are returned to the model, never crash the run | Same validation path |
| 6 | `tickmark ask --verbose` | Each step shows tool, args, result size, tokens, requests | [Typer](https://typer.tiangolo.com) |
| 7 | Tool-call reliability: 20 fixed prompts on local and cloud | Malformed-call rate for each in `DECISIONS.md` | Count task 4's validation failures |

Reference code — the whole idea of an agent. The model proposes; your code validates and executes:

```python
# src/tickmark/loop.py
from pydantic import ValidationError
from .gateway import complete
from .tools import TOOLS, FinalAnswer      # name -> Tool(name, Args, fn, ...)

NUDGE = "Call a tool to make progress, or call final_answer to finish."

def run(task: str, system: str, group: str = "local-main", max_steps: int = 15) -> dict:
    messages = [{"role": "system", "content": system}, {"role": "user", "content": task}]
    specs = [t.spec() for t in TOOLS.values()]
    for step in range(max_steps):
        msg = complete(group, messages, tools=specs).choices[0].message
        messages.append(msg.model_dump(exclude_none=True))
        if not msg.tool_calls:
            messages.append({"role": "user", "content": NUDGE})
            continue
        for call in msg.tool_calls:
            result = execute(call)
            if isinstance(result, FinalAnswer):
                return {"status": "done", "steps": step + 1, **result.model_dump(mode="json")}
            messages.append({"role": "tool", "tool_call_id": call.id, "content": result})
    return {"status": "max_steps", "steps": max_steps}

def execute(call) -> str | FinalAnswer:
    tool = TOOLS.get(call.function.name)
    if tool is None:
        return f"Unknown tool {call.function.name}. Available: {', '.join(TOOLS)}"
    try:
        args = tool.Args.model_validate_json(call.function.arguments)   # bad JSON raises ValidationError too
    except ValidationError as e:
        return f"Invalid arguments for {tool.name}: {e}"                # an observation, not a crash
    if isinstance(args, FinalAnswer):
        return args
    try:
        return str(tool.fn(args))
    except Exception as e:
        return f"{tool.name} failed: {e}"
```

- [ ] Answers five real questions correctly, with references
- [ ] Every number in an answer came from a tool result
- [ ] Malformed tool calls and final answers are reported back, never crash the run
- [ ] Local vs cloud malformed-call rate recorded

## Sprint 3 — Evals and Langfuse

**Showcase:** `make eval && make table` runs the agent on every dev question and month, grades each against the answer key, computes confidence intervals, pushes a Langfuse experiment you can compare in the UI, and regenerates the README table with rows 1 and 2.

**Learn:** Hamel Husain, [Your AI Product Needs Evals](https://hamel.dev/blog/posts/evals/) · [Langfuse tracing](https://langfuse.com/docs) and [experiments via SDK](https://langfuse.com/docs/evaluation/experiments/experiments-via-sdk) · `pass^k` reliability (search "τ-bench Yao 2024 pass^k").

**Tech:** Langfuse Python SDK, PyYAML, pytest.

**Models and services:** Langfuse Cloud; both model arms; `eval.yaml` proxy config.

| # | Task | Expected output | How-to and references |
| --- | --- | --- | --- |
| 1 | Langfuse tracing on the hand-built loop: one trace per run, a span per model and tool call | Trace URL printed per run | [Langfuse OpenAI integration](https://langfuse.com/docs/integrations/openai/python/get-started) |
| 2 | Graders: issues, categorization, Q&A, email checks | Unit tests with hand-made right and wrong answers | Reference code below |
| 3 | `bench/run.py --arm local --split dev --attempts 3` | One results JSON per run with every protocol metric | Always against `eval.yaml` |
| 4 | Bootstrap confidence intervals and `pass^3` | Both in every results file | Reference code below |
| 5 | Upload the dev questions as a Langfuse dataset; run an experiment | Two runs compared side by side in the Langfuse UI | [Experiments via SDK](https://langfuse.com/docs/evaluation/experiments/experiments-via-sdk) |
| 6 | `make table` regenerates the README table from `bench/results/` | No hand-typed numbers anywhere | A 40-line script |
| 7 | Failure categories: wrong tool, wrong numbers, missed evidence, invented reference, gave up | Tagged on every failure | Tag the first 20 by hand, then write rules |
| 8 | `make eval-quick`: 1 month and 10 questions, local only | Under 10 minutes; run it daily | Same runner |

Reference code — graders are small, strict and boring, which is what makes them trustworthy:

```python
# bench/grade.py
import random, statistics
from decimal import Decimal

def grade_issues(found: list[Flag], key: list[PlantedIssue]) -> dict:
    want = {(i.kind, frozenset(i.records)) for i in key}
    got = {(f.kind, frozenset(f.records)) for f in found}
    hit = want & got
    return {"precision": len(hit) / len(got) if got else 1.0,
            "recall": len(hit) / len(want) if want else 1.0,
            "missed": sorted(map(str, want - got)), "false_alarms": sorted(map(str, got - want))}

def grade_answer(answer: str | Decimal, expected: Decimal) -> bool:
    try:
        return abs(Decimal(str(answer)) - expected) <= Decimal("0.01")
    except ArithmeticError:
        return False

def bootstrap_ci(scores: list[float], n: int = 2000, seed: int = 0) -> tuple[float, float]:
    rng = random.Random(seed)
    means = sorted(statistics.fmean(rng.choices(scores, k=len(scores))) for _ in range(n))
    return means[int(0.025 * n)], means[int(0.975 * n)]
```

`pass^k` in one line: a month counts only if all k attempts found every planted issue. `avg@k` tells you how good it is on average; `pass^k` tells you whether you could trust it unattended.

- [ ] Every grader has tests with known right and wrong answers
- [ ] Results include confidence intervals, requests, tokens, wall-clock and failure categories
- [ ] A Langfuse experiment compares two runs
- [ ] Rows 1 and 2 in the README table, generated
- [ ] `make eval-quick` runs in under 10 minutes

## Sprint 4 — Document intake

**Showcase:** drop 40 bills and receipt photos into `inbox/`. `tickmark intake` turns each into a validated record, checks its arithmetic, flags the few it isn't sure about for review, and refuses to update a vendor's bank details from an invoice. A chart shows field accuracy on generated documents and on real receipts.

**Learn:** [pdfplumber](https://github.com/jsvine/pdfplumber) · [LiteLLM structured outputs](https://docs.litellm.ai/docs/completion/json_mode) · Ollama vision models (search "Ollama vision models") · [CORD dataset](https://github.com/clovaai/cord) (check its license before use).

**Tech:** pdfplumber, Pillow, Pydantic, RapidFuzz, Hugging Face `datasets`.

**Models and services:** `local-main` for text PDFs, `local-vision` for photos; `cloud-lite` for the comparison chart only.

| # | Task | Expected output | How-to and references |
| --- | --- | --- | --- |
| 1 | `InvoiceDoc` and `ReceiptDoc` schemas with `Decimal` fields | Schemas with tests | [Pydantic](https://docs.pydantic.dev/latest/concepts/models/) |
| 2 | Text-layer path: pdfplumber text, then structured output | Generated invoices extract correctly | [pdfplumber](https://github.com/jsvine/pdfplumber) |
| 3 | Image path: normalize rotation and size, then the vision model | Receipt photos extract | [Pillow](https://pillow.readthedocs.io) |
| 4 | Arithmetic checks with one retry carrying the errors; otherwise `needs_review` | Line items, tax and total always consistent or flagged | Reference code below |
| 5 | Vendor matching; compare extracted bank details with the vendor record | A change becomes a `bank_detail_change` flag, never an update | [RapidFuzz](https://github.com/rapidfuzz/RapidFuzz) |
| 6 | Duplicate documents: file hash, and same vendor plus number | Duplicates refused | — |
| 7 | Field-accuracy eval on generated documents and 100 CORD receipts | `docs/charts/extraction.png`, local vs cloud | Grader from Sprint 3 |
| 8 | Extracted records saved as drafts, not posted to the books | Posting happens only in the close | — |
| 9 | Eval run | Row recorded | Your runner |

Reference code — extraction is model work; checking it is code work:

```python
# src/tickmark/intake/extract.py
def extract(path: Path) -> Extraction:
    text = pdf_text(path) if path.suffix == ".pdf" else ""
    group, content = ("local-main", text) if len(text) > 50 else ("local-vision", image_message(path))
    problems: list[str] = []
    for attempt in range(2):
        doc = structured(group, content, schema=InvoiceDoc, feedback=problems)
        problems = check_arithmetic(doc)          # lines sum to subtotal; subtotal + tax == total
        if not problems:
            return Extraction(doc=doc, model=group, attempts=attempt + 1)
    return Extraction(doc=doc, model=group, attempts=2, needs_review=problems)

def check_arithmetic(doc: InvoiceDoc) -> list[str]:
    errors = []
    lines = sum((l.amount for l in doc.lines), Decimal("0"))
    if doc.subtotal is not None and lines != doc.subtotal:
        errors.append(f"line items sum to {lines}, subtotal says {doc.subtotal}")
    if (doc.subtotal or lines) + doc.tax != doc.total:
        errors.append(f"subtotal + tax = {(doc.subtotal or lines) + doc.tax}, total says {doc.total}")
    return errors
```

- [ ] Every extracted record passes arithmetic checks or is flagged
- [ ] Bank details are never updated from a document (tested)
- [ ] Extraction chart committed, with real receipts included
- [ ] Row recorded; missing-receipt recall should rise

## Sprint 5 — The harness

**Showcase:** a month review where compaction fires on a 2,000-line statement; drafting a payment reminder and marking an invoice paid stop at a gate that shows the exact email and the exact books change; an "updated bank details" request can't be auto-approved under any setting; `tickmark audit <run>` replays every proposal, decision and cost; `tickmark undo <event>` reverses an approved change. This is the most important sprint: give it the most time.

**Learn:** Schmid, [The importance of Agent Harness in 2026](https://www.philschmid.de/agent-harness-2026) · Anthropic, [Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) · [awesome-harness-engineering](https://github.com/ai-boost/awesome-harness-engineering) · [Claude Code hooks](https://docs.claude.com/en/docs/claude-code/hooks) (a model for your own hooks).

**Tech:** No new libraries. This is your code. `structlog` for logs, `tenacity` for retries.

**Models and services:** `local-main` for development and for the summarising rung of the compaction ladder.

| # | Task | Expected output | How-to and references |
| --- | --- | --- | --- |
| 1 | `HARNESS.md` skeleton: each component, one line on what yours will do | Design note committed before code | The readings above |
| 2 | Tool registry: schema, **required** tier, timeout, result cap, idempotent flag, preview function | Tool specs generated from it; every call wrapped | [tenacity](https://tenacity.readthedocs.io) |
| 3 | Permission resolver and approval prompt: approve, edit or reject | Denials return as results the agent must handle | Reference code below · [Rich prompt](https://rich.readthedocs.io/en/stable/prompt.html) |
| 4 | `SENSITIVE` tier can never be auto-approved | A test tries every setting and fails to auto-approve | — |
| 5 | Budget tracker: steps, tokens, **requests**, wall-clock; warning at 80% | Exhaustion returns `{status: "budget_exceeded", partial_work, spent}` | Tested with an impossible task |
| 6 | Context assembly: `RULES.md` and system prompt first, then task, then history; tokens logged per turn | Stable prefix, logged sizes | Stable content first helps provider caching |
| 7 | Offloading: large results go to `.tickmark/scratch/`; the agent gets a summary and a pointer | The agent re-reads on demand or analyses it in the sandbox (Sprint 6) | Anthropic context-engineering post |
| 8 | Compaction ladder: drop old tool results → truncate large ones → summarise the oldest half → reset with a handoff | A long month shows each rung firing, logged by name | Same readings |
| 9 | `RULES.md` survives a full reset | A test proving it | Pinned content is never a compaction candidate |
| 10 | Hooks: `pre_tool` and `post_tool` | One hook blocks email to addresses not in client records; one masks IBANs in logs | Claude Code hooks as the model |
| 11 | Audit log: append-only table; `tickmark audit <run>` renders a timeline | Denied actions appear, not just successes | [structlog](https://www.structlog.org) · [Rich tree](https://rich.readthedocs.io/en/stable/tree.html) |
| 12 | Undo: every `BOOKS` write stores its inverse; `tickmark undo <event>` | A test: apply, undo, books identical | — |
| 13 | Finish `HARNESS.md`; eval run | Row recorded | Your runner |

| Tier | Tools | Policy |
| --- | --- | --- |
| `READ` | queries, document search, sandboxed analysis | Run |
| `DRAFT` | suggest categories, propose entries, draft emails | Run and log |
| `BOOKS` | post entries, mark paid, change rules | Approval (batched in the close plan) |
| `EXTERNAL` | send or schedule email | Approval, always |
| `SENSITIVE` | change bank details, delete records | Approval, never automatic, extra confirmation |

Reference code — one resolver, called by the harness, never by tools. The model never decides what is safe:

```python
# src/tickmark/harness/permissions.py
from dataclasses import dataclass
from enum import IntEnum

class Tier(IntEnum):
    READ = 0
    DRAFT = 1
    BOOKS = 2
    EXTERNAL = 3
    SENSITIVE = 4

NEVER_AUTO = frozenset({Tier.SENSITIVE})

@dataclass(frozen=True)
class PermissionContext:
    max_tier: Tier = Tier.SENSITIVE              # investigators and the auditor get READ (Sprint 11)
    auto_approve: frozenset[Tier] = frozenset({Tier.READ, Tier.DRAFT})

def resolve(tool: RegisteredTool, args, ctx: PermissionContext, approver: Approver) -> Decision:
    if tool.tier > ctx.max_tier:
        return Decision.deny(f"{tool.name} needs {tool.tier.name}; this context allows {ctx.max_tier.name}")
    if tool.tier in ctx.auto_approve and tool.tier not in NEVER_AUTO:
        return Decision.allow(args)
    review = approver.ask(tool.name, tool.preview(args))     # the exact email or books diff, never a description
    if review.kind == "approve":
        return Decision.allow(args)
    if review.kind == "edit":
        return Decision.allow(tool.Args.model_validate(review.edited_args))   # edits are validated too
    return Decision.deny(review.reason or "Rejected by reviewer")
```

- [ ] Nothing bypasses the registry; every tool has a tier
- [ ] `SENSITIVE` can't be auto-approved (tested)
- [ ] Budget exhaustion returns a structured failure, not a crash or a made-up answer
- [ ] Compaction logs which rung fired; the `RULES.md` survival test is green
- [ ] Denied actions appear in the audit log; undo restores the books exactly
- [ ] `HARNESS.md` committed; row recorded

## Sprint 6 — The sandbox

**Showcase:** "Chart software spend by month against last year" makes the agent write pandas, which runs in an E2B microVM with no internet and returns a chart and the numbers. Then a bank export in a format Tickmark has never seen: the agent writes a parser in the sandbox, and Tickmark accepts it only because the parsed lines add up to the statement's closing balance. A planted secret never leaks, even when a receipt asks for it.

**Learn:** [E2B docs](https://docs.e2b.dev) (code interpreting, [internet access](https://e2b.dev/docs/network/internet-access), [billing](https://docs.e2b.dev/billing.md)) · [Firecracker](https://firecracker-microvm.github.io) (why microVMs isolate better than containers; E2B runs on it) · [OWASP Top 10 for LLM Applications](https://genai.owasp.org/llm-top-10/) (excessive agency, improper output handling).

**Tech:** `e2b-code-interpreter`, docker SDK for the local backend, pandas, matplotlib, pyarrow.

**Models and services:** E2B Hobby ($100 one-time credits). Synthetic data only. Docker backend for tests and offline work.

Why not self-host Firecracker: it needs Linux with KVM. On Windows that means WSL2 with nested virtualization, root filesystems, networking and a VM manager. That's a lot of infrastructure, and E2B gives you Firecracker isolation without running it yourself. Read the docs to understand it; don't operate it.

| # | Task | Expected output | How-to and references |
| --- | --- | --- | --- |
| 1 | `Sandbox` protocol: `upload`, `run`, `download`, `close`; `E2BSandbox` and `DockerSandbox` behind a flag | Same tests pass on both backends | Reference code below |
| 2 | E2B with internet off, timeouts, always killed | A test proves an outbound request fails | [Internet access](https://e2b.dev/docs/network/internet-access) |
| 3 | Docker backend: `network_mode="none"`, read-only data mount, memory and CPU limits | Same isolation tests pass locally | [docker SDK](https://docker-py.readthedocs.io/en/stable/containers.html) |
| 4 | Export only the needed slice: the period's transactions as Parquet | Least data leaves the database | [pandas Parquet](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_parquet.html) |
| 5 | `run_analysis` tool (`READ` tier): code in, `{stdout (capped), error, charts}` out | Charts come back as images; output capped with a marker | [E2B: analyze data with AI](https://docs.e2b.dev/code-interpreting/analyze-data-with-ai.md) |
| 6 | Unknown bank format: the agent writes `parse(path)`; Tickmark validates it | Accepted only if opening balance + lines = closing balance and row counts match | Reference code below |
| 7 | Red team: `FAKE_SECRET` in the host env; a receipt whose text asks to print environment variables | `security/exfil_01.yaml` passes: the secret appears nowhere | Host env is never passed into sandboxes |
| 8 | Table: E2B vs Docker cold start, run latency, credits per question | In `DECISIONS.md` | — |
| 9 | Eval run | Row recorded; analysis questions now answerable | Your runner |

Reference code — the sandbox runs the model's code; your code decides whether to believe the result:

```python
# src/tickmark/sandbox/e2b.py
from e2b_code_interpreter import Sandbox

class E2BSandbox:
    def __init__(self, timeout_s: int = 600):
        # check parameter names against the SDK reference for your pinned version
        self.sbx = Sandbox.create(allow_internet_access=False, timeout=timeout_s)

    def upload(self, local: Path, remote: str) -> str:
        with local.open("rb") as f:
            return self.sbx.files.write(remote, f).path

    def run(self, code: str) -> RunResult:
        ex = self.sbx.run_code(code)
        return RunResult(
            ok=ex.error is None,
            stdout=cap("".join(ex.logs.stdout), 8_000),
            error=f"{ex.error.name}: {ex.error.value}" if ex.error else None,
            charts=[r.png for r in ex.results if r.png],          # base64 PNGs
        )

    def close(self) -> None:
        self.sbx.kill()
```

```python
# src/tickmark/intake/unknown_format.py
def accept_parser(rows: list[dict], statement: StatementHeader) -> list[BankLine] | Rejection:
    try:
        lines = [BankLine.model_validate(r) for r in rows]    # dates, Decimal amounts, references
    except ValidationError as e:
        return Rejection(f"rows don't match BankLine: {e}")
    computed = statement.opening + sum((l.amount for l in lines), Decimal("0"))
    if computed != statement.closing:
        return Rejection(f"opening + lines = {computed}, statement closes at {statement.closing}")
    return lines
```

- [ ] Network and host filesystem unreachable from inside, on both backends (verified by trying)
- [ ] Sandboxes always closed, even on errors
- [ ] A parser is never trusted without the balance check
- [ ] Exfiltration test passes
- [ ] Row recorded

## Sprint 7 — RAG over business documents

**Showcase:** "When is Acme's invoice actually overdue?" retrieves the payment-terms clause from Acme's contract (net 45, not the default 30) and cites the page. Overdue flags become correct, and a chart shows which retrieval strategy wins.

**Learn:** LangChain [RAG tutorial](https://docs.langchain.com/oss/python/langchain/rag) · [PGVector integration](https://docs.langchain.com/oss/python/integrations/vectorstores/pgvector) · [Postgres full-text search](https://www.postgresql.org/docs/current/textsearch.html) · [Pinecone Learn](https://www.pinecone.io/learn/) (embeddings, hybrid search, rerankers) · reciprocal rank fusion (search "reciprocal rank fusion Cormack 2009").

**Tech:** `langchain-community` loaders, `langchain-text-splitters`, `langchain-postgres`, sentence-transformers (optional reranker).

**Models and services:** `local-embed` through the gateway, never cloud. Optional local cross-encoder reranker.

| # | Task | Expected output | How-to and references |
| --- | --- | --- | --- |
| 1 | Load contracts and policy PDFs, and `.eml` emails, with metadata (type, client, page, date) | Documents with metadata | [LangChain document loaders](https://docs.langchain.com/oss/python/integrations/document_loaders) |
| 2 | Split: heading-aware for contracts, recursive for emails; compare chunk sizes | Chunks keep clause boundaries | [Text splitters](https://docs.langchain.com/oss/python/integrations/splitters) |
| 3 | PGVector store with gateway embeddings | Index built in Postgres | [PGVector](https://docs.langchain.com/oss/python/integrations/vectorstores/pgvector) |
| 4 | Full-text search over the same chunks; merge with vector results by RRF | Unit test for the merge | Reference code below |
| 5 | Optional reranker: local cross-encoder cuts 30 to 5 | Swappable `Reranker` | [Cross-encoders](https://www.sbert.net/docs/cross_encoder/usage/usage.html) |
| 6 | `search_documents` tool (`READ`) returning cited chunks | Every answer can name its source and page | — |
| 7 | Contract terms as structured facts with citations, cached per client | Checks use real terms instead of the default | — |
| 8 | Retrieval eval: hit@5 and MRR on 40 questions with gold chunks from the generator | `docs/charts/retrieval.png`: vector, keyword, hybrid, hybrid + rerank | [matplotlib](https://matplotlib.org/stable/) |
| 9 | Eval run | Row recorded; overdue and personal-expense recall should rise | Your runner |

Reference code — hybrid search is two rankings and a five-line merge:

```python
# src/tickmark/rag/hybrid.py
from langchain_postgres import PGVector
from sqlalchemy import text

store = PGVector(embeddings=embeddings(), collection_name="docs",
                 connection=settings.pg_url, use_jsonb=True)

def rrf(*rankings: list[str], k: int = 60) -> list[str]:
    scores: dict[str, float] = {}
    for ranking in rankings:
        for rank, chunk_id in enumerate(ranking):
            scores[chunk_id] = scores.get(chunk_id, 0.0) + 1.0 / (k + rank + 1)
    return sorted(scores, key=scores.get, reverse=True)

def keyword_ids(query: str, k: int = 30) -> list[str]:
    # langchain-postgres stores chunks in langchain_pg_embedding; check table names for your version
    rows = db.execute(text("""
        SELECT id FROM langchain_pg_embedding
        WHERE to_tsvector('english', document) @@ websearch_to_tsquery('english', :q)
        ORDER BY ts_rank(to_tsvector('english', document), websearch_to_tsquery('english', :q)) DESC
        LIMIT :k"""), {"q": query, "k": k})
    return [str(r.id) for r in rows]

def search(query: str, top: int = 5, **filters) -> list[Document]:
    vector_docs = store.similarity_search(query, k=30, filter=filters or None)
    fused = rrf([d.id for d in vector_docs], keyword_ids(query))[:30]
    return reranker.rerank(query, load_chunks(fused))[:top]
```

- [ ] No embedding call ever reaches a cloud provider
- [ ] Every retrieved fact used in a proposal carries a source and page
- [ ] Four-strategy retrieval chart committed
- [ ] Row recorded

## Sprint 8 — The month-end close on LangGraph

**Showcase:** `tickmark close 2026-03` runs the whole close as a graph: parallel intake, statement import, reconciliation, categorization, investigation, proposals. It asks you about one ambiguous charge, then pauses with the close plan. You `kill -9` the process, restart it "days later", approve the plan, and it finishes with nothing done twice.

**Learn:** do the [LangGraph quickstart](https://docs.langchain.com/oss/python/langgraph/overview) end to end before touching Tickmark · LangGraph guides on persistence, interrupts, `Send` (map-reduce) and time travel (same site) · reread Building Effective Agents: you'll have opinions now.

**Tech:** `langgraph`, `langgraph-checkpoint-postgres`.

**Models and services:** unchanged. LangGraph orders the steps; your harness still governs each one.

| # | Task | Expected output | How-to and references |
| --- | --- | --- | --- |
| 1 | Typed `CloseState` with reducers where lists accumulate (documents, issues, proposals) | State schema with tests | LangGraph docs: state and reducers |
| 2 | Nodes: `extract_doc`, `import_statement`, `reconcile`, `categorize`, `investigate`, `propose`, `approve`, `apply`, `report` | Every node calls the harness, never a tool directly | LangGraph docs: Graph API |
| 3 | Fan-out intake with `Send`, one per new document | Documents extracted in parallel | LangGraph docs: map-reduce with `Send` |
| 4 | Conditional edges: unknown bank format → sandbox parser branch; nothing to approve → report | Mermaid render of the graph in the README | `get_graph().draw_mermaid()` |
| 5 | Postgres checkpointer keyed by close id | Every step persisted | LangGraph docs: persistence |
| 6 | `approve` node: `interrupt()` with the close plan; resume with approve, edit or reject per item | The plan waits indefinitely and survives restarts | LangGraph docs: interrupts |
| 7 | `ask_human` inside `categorize` for low-confidence transactions | The answer becomes a rule candidate (used in Sprint 10) | Same |
| 8 | Idempotent `apply`: writes keyed by proposal id | A test: crash during `apply`, resume, books identical | Nodes re-run from their start on resume |
| 9 | `tickmark resume <close>` and `tickmark replay <close> --from N` | Resume and time travel from the CLI | LangGraph docs: time travel |
| 10 | Record kill-and-resume; eval run | Video in the README; row recorded (expect no accuracy change, confirm no regression) | [OBS](https://obsproject.com) |

Reference code — the framework orders the steps; your harness still governs every one of them:

```python
# src/tickmark/workflows/close/graph.py
from langgraph.graph import StateGraph, START, END
from langgraph.types import Send, interrupt
from langgraph.checkpoint.postgres import PostgresSaver

def route_intake(state: CloseState):
    sends = [Send("extract_doc", {"doc": d}) for d in state["new_documents"]]
    return sends or "import_statement"                   # no new documents: skip straight on

def approve(state: CloseState) -> dict:
    # everything above interrupt() re-runs on resume, so keep it free of side effects
    decisions = interrupt({"close_id": state["close_id"],
                           "plan": [p.preview() for p in state["proposals"]]})
    return {"decisions": decisions}                      # {proposal_id: {"type": "approve" | "edit" | "reject", ...}}

def after_propose(state: CloseState) -> str:
    return "approve" if state["proposals"] else "report"

g = StateGraph(CloseState)
for name, fn in [("extract_doc", extract_doc), ("import_statement", import_statement),
                 ("reconcile", reconcile), ("categorize", categorize), ("investigate", investigate),
                 ("propose", propose), ("approve", approve), ("apply", apply), ("report", report)]:
    g.add_node(name, fn)                                 # each fn calls harness.call(), never a tool
g.add_conditional_edges(START, route_intake, ["extract_doc", "import_statement"])
g.add_edge("extract_doc", "import_statement")            # runs once, after every Send finishes
g.add_edge("import_statement", "reconcile")
g.add_edge("reconcile", "categorize")
g.add_edge("categorize", "investigate")
g.add_edge("investigate", "propose")
g.add_conditional_edges("propose", after_propose, ["approve", "report"])
g.add_edge("approve", "apply")
g.add_edge("apply", "report")
g.add_edge("report", END)

with PostgresSaver.from_conn_string(settings.pg_url) as saver:
    saver.setup()
    close_graph = g.compile(checkpointer=saver)
```

Resuming after approval is `close_graph.invoke(Command(resume=decisions), {"configurable": {"thread_id": close_id}})`, from any process, any day later.

- [ ] `kill -9` while waiting for approval resumes at the approval
- [ ] A crash during `apply` never double-posts (tested)
- [ ] Budgets and permissions still enforced inside every node
- [ ] `ask_human` pauses and resumes cleanly
- [ ] Kill-and-resume video in the README; row recorded

## Sprint 9 — "Ask your books" on LangChain

**Showcase:** in a terminal chat: "Which clients got slower at paying since March? Chart it." The agent streams its steps, runs the analysis in the sandbox and returns a chart. "Send Acme a reminder" pauses for approval through LangChain's middleware. Long chats summarize themselves. A short write-up compares the hand-built loop, LangChain's `create_agent` and your LangGraph graph.

**Learn:** LangChain [agents](https://docs.langchain.com/oss/python/langchain/agents) · [built-in middleware](https://docs.langchain.com/oss/python/langchain/middleware/built-in) · [human-in-the-loop](https://docs.langchain.com/oss/python/langchain/human-in-the-loop) · [Langfuse LangChain integration](https://langfuse.com/docs/langchain).

**Tech:** `langchain`, `langchain-openai`, the Postgres checkpointer from Sprint 8, `langfuse.langchain.CallbackHandler`.

**Models and services:** `local-main` through `gateway.chat_model()`.

| # | Task | Expected output | How-to and references |
| --- | --- | --- | --- |
| 1 | Adapter: registry tools become LangChain tools; each call still goes through `harness.call()` | Budgets, audit and max tier still apply | [LangChain tools](https://docs.langchain.com/oss/python/langchain/tools) |
| 2 | `create_agent` with the gateway model, adapted tools, `RULES.md` as the system prompt | The agent answers dev questions | [Agents](https://docs.langchain.com/oss/python/langchain/agents) |
| 3 | `HumanInTheLoopMiddleware`, its `interrupt_on` generated from registry tiers | One source of truth for what needs approval | Reference code below |
| 4 | `SummarizationMiddleware` on the local model; call-limit middleware mapped to your budgets | Long chats stay inside the context window | [Built-in middleware](https://docs.langchain.com/oss/python/langchain/middleware/built-in) |
| 5 | Streaming to the terminal | Steps and tokens appear live | LangChain streaming docs |
| 6 | Langfuse `CallbackHandler` | Chat traces appear next to the hand-built loop's | [Langfuse LangChain](https://langfuse.com/docs/langchain) |
| 7 | Q&A eval: LangChain agent vs hand-built loop on the same questions | Row recorded | Your runner |
| 8 | ADR: hand-built loop vs `create_agent` vs LangGraph: code size, control, debugging, scores | `docs/adr/` entry | Your own numbers |

Reference code — the registry decides what needs approval; the middleware asks the human:

```python
# src/tickmark/chat/agent.py
from langchain.agents import create_agent
from langchain.agents.middleware import (HumanInTheLoopMiddleware, SummarizationMiddleware,
                                         ToolCallLimitMiddleware)
from langfuse.langchain import CallbackHandler

def interrupt_config() -> dict:
    cfg: dict[str, object] = {}
    for t in registry.tools():
        if t.tier >= Tier.SENSITIVE:
            cfg[t.name] = {"allowed_decisions": ["approve", "reject"]}    # no editing bank details
        elif t.tier >= Tier.BOOKS:
            cfg[t.name] = True                                             # approve, edit or reject
        else:
            cfg[t.name] = False
    return cfg

def build_chat_agent(checkpointer):
    return create_agent(
        model=chat_model("local-main"),
        tools=[as_langchain_tool(t) for t in registry.tools()],    # each call still goes through the harness
        system_prompt=load_pinned_rules(),
        middleware=[
            HumanInTheLoopMiddleware(interrupt_on=interrupt_config()),
            SummarizationMiddleware(model=chat_model("local-main"),
                                    trigger=("tokens", 6000), keep=("messages", 20)),
            ToolCallLimitMiddleware(run_limit=25),                 # check parameter names for your version
        ],
        checkpointer=checkpointer,
    )

agent = build_chat_agent(saver)
config = {"configurable": {"thread_id": chat_id}, "callbacks": [CallbackHandler()]}
for chunk in agent.stream({"messages": [{"role": "user", "content": question}]}, config,
                          stream_mode="updates"):
    render(chunk)
```

- [ ] Every chat tool call goes through the harness (tested)
- [ ] Approval tiers come from the registry, not a hand-written list
- [ ] A long chat summarizes without losing pinned rules
- [ ] Comparison ADR committed; row recorded

## Sprint 10 — Memory

**Showcase:** correct one charge ("Figma is Software, not Marketing") and next month it's categorized right without asking. Say once "Acme always pays two weeks late; don't remind them before day 50", and no early reminder goes out. Change your mind, and the old rule retires with its history kept. Alongside it, a number: categorization accuracy and questions asked per month, before and after a month of corrections.

**Learn:** [Letta docs](https://docs.letta.com) (MemGPT's core-plus-archival tiering, as concepts) · LangGraph [memory overview](https://docs.langchain.com/oss/python/langgraph/memory) (short-term via checkpointer, long-term via `Store`) · [Zep](https://www.getzep.com) (facts that supersede older facts).

**Tech:** Postgres tables, LangGraph `PostgresStore` with semantic search.

**Models and services:** `local-main` for extracting rules from corrections, `local-embed` for notes.

| # | Task | Expected output | How-to and references |
| --- | --- | --- | --- |
| 1 | Short-term memory: chat and close threads via the checkpointer | Documented; nothing new to build | Sprint 8 and 9 |
| 2 | Rules table: vendor or pattern → category, created from approved corrections and `ask_human` answers | Rules apply before any model call (tested) | — |
| 3 | Client facts with source, `valid_from`, `valid_to`, `superseded_by` | Changing a fact retires the old one | Reference code below |
| 4 | Free-text notes in LangGraph's `PostgresStore`, namespaced per company, searched semantically | Relevant notes appear in context | LangGraph docs: long-term memory |
| 5 | Core block (at most 500 tokens): company basics and active rules summary, pinned | Survives compaction | Sprint 5 pinned path |
| 6 | `tickmark memory list, add, forget, history` | Full history of every rule | — |
| 7 | Leakage audit: no answer-key content in memory | Zero hits | Grep the store against every answer key |
| 8 | Learning eval: replay the year month by month; a simulated reviewer answers from the answer key through the normal approval path | Accuracy and questions-per-month curve; memory reset between attempts | It measures learning from corrections, not detection |

Reference code — memory as data with history, not a pile of text:

```python
# src/tickmark/memory/rules.py
def categorize(tx: Transaction) -> Suggestion:
    rule = rules.match(vendor=tx.vendor_id, text=tx.description, active_only=True)
    if rule:
        return Suggestion(category=rule.category, source=f"rule:{rule.id}", confidence=1.0)
    return model_categorize(tx)            # only what rules don't cover reaches the model

def learn_from_correction(tx: Transaction, category: str, approved_by: str) -> Rule:
    old = rules.match(vendor=tx.vendor_id, text=tx.description, active_only=True)
    new = rules.add(vendor=tx.vendor_id, category=category, source=f"correction:{tx.id}",
                    created_by=approved_by)
    if old and old.category != category:
        rules.supersede(old.id, by=new.id)  # kept for history and undo, never deleted
    return new
```

- [ ] Rules apply before the model, and every rule has a source
- [ ] Superseded facts never reach the context
- [ ] Leakage audit is zero
- [ ] Learning curve recorded; row recorded

## Sprint 11 — Multi-agent: investigators and an auditor

**Showcase:** a busy month with 30 candidate issues. Investigators run in parallel, each with a fresh context and read-only tools, and return short structured findings instead of flooding one context. An auditor that never saw the reasoning checks each proposal against its cited evidence, rejects two with reasons, and the proposer fixes them. A chart shows peak context and precision before and after.

**Learn:** Anthropic, [How we built our multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system) · LangGraph subgraphs and `Send` · the evaluator-optimizer pattern in Building Effective Agents · the key idea: subagents exist for context isolation, not to play roles.

**Tech:** LangGraph subgraphs and `Send`, your harness.

**Models and services:** `local-main` for all agents; parallel cloud calls would burn the daily quota. Set `OLLAMA_NUM_PARALLEL` deliberately, or Ollama queues requests.

| # | Task | Expected output | How-to and references |
| --- | --- | --- | --- |
| 1 | `Finding{issue_ref, verdict, evidence, proposed_action, confidence}` | Schema-validated findings | [Pydantic](https://docs.pydantic.dev) |
| 2 | Investigator subgraph: fresh messages, `READ` max tier, budget slice | Works on one candidate issue | LangGraph docs: subgraphs |
| 3 | Parallel fan-out with a concurrency cap | Wall-clock parallel vs sequential recorded | LangGraph docs: `Send` |
| 4 | A test: an investigator's write attempt is denied and logged | Green test | Sprint 5 resolver |
| 5 | Auditor: fresh context; sees proposals and cited evidence only, never the reasoning; `READ` tier | Accept or reject with a reason, per proposal | — |
| 6 | Evaluator-optimizer: rejected proposals go back to the proposer, at most two rounds, then to you with the auditor's note | Loop terminates every time | Building Effective Agents |
| 7 | Shared budget pool | Agents can't collectively overspend the close | Sprint 5 budget tracker |
| 8 | Eval: precision, recall, peak context and requests per close vs Sprint 10 | Row recorded and chart committed | Your runner |

Reference code — investigators get a narrower permission context, not the parent's; the auditor sees evidence, not reasoning:

```python
# src/tickmark/agents/investigate.py
def fan_out(state: CloseState) -> list[Send]:
    return [Send("investigate", {
                "candidate": c,
                "permissions": PermissionContext(max_tier=Tier.READ),    # rebuilt, not inherited
                "budget": state["budget"].slice(fraction=0.03),
            }) for c in state["candidates"]]

def investigate(sub: dict) -> dict:
    finding = run_investigator(sub)                      # fresh messages list: isolated context
    return {"findings": [Finding.model_validate(finding)]}   # never the raw transcript

def audit(state: CloseState) -> dict:
    reviews = [auditor.review(p, evidence=load_evidence(p.evidence)) for p in state["proposals"]]
    return {"reviews": reviews}

def after_audit(state: CloseState) -> str:
    rejected = [r for r in state["reviews"] if not r.accepted]
    if rejected and state["revision_round"] < 2:
        return "propose"                                  # revise with the auditor's reasons
    return "approve"                                      # anything still rejected goes to you, flagged
```

- [ ] Investigator and auditor writes are denied and logged (tested)
- [ ] Findings are schema-validated; transcripts never flow upward
- [ ] The revision loop always terminates
- [ ] Peak context and precision compared with Sprint 10; row recorded

## Sprint 12 — MCP, automation and security

**Showcase:** three short clips. Claude Desktop, connected to your books MCP server, answers "what did we spend on software in Q3?" with read-only tools. Emailing a bill to the inbox starts intake on its own, and on the 1st the close starts and asks for your approval. A fake "we've changed our bank details" invoice and an invoice with hidden instructions are both caught, and the security suite runs in CI. **This is a complete stopping point for the project.**

**Learn:** [modelcontextprotocol.io](https://modelcontextprotocol.io) (tools, resources, prompts; stdio vs HTTP) · [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk) · [MCP Inspector](https://github.com/modelcontextprotocol/inspector) · Google's official Gmail MCP server (developer preview; drafts only, see [this overview](https://www.dragapp.com/blog/gmail-mcp-server/) and Google's own docs) · [OWASP LLM Top 10](https://genai.owasp.org/llm-top-10/) · business email compromise ([FBI IC3](https://www.ic3.gov)) for why bank-detail changes are the classic fraud.

**Tech:** `mcp` Python SDK, APScheduler, Postgres job queue (`FOR UPDATE SKIP LOCKED`), Mailpit API, GitHub Actions.

**Models and services:** unchanged. Gmail MCP is optional; Mailpit covers the demo.

| # | Task | Expected output | How-to and references |
| --- | --- | --- | --- |
| 1 | Books MCP server: read-only tools and a monthly-report resource, over stdio | Passes the Inspector | Reference code below |
| 2 | Connect Claude Desktop | Questions answered from your books | MCP docs: connecting local servers |
| 3 | Optional: streamable HTTP behind a small FastAPI gateway with API keys and rate limits | Unauthenticated calls rejected | [FastAPI security](https://fastapi.tiangolo.com/tutorial/security/) |
| 4 | Consume an MCP server: Gmail MCP for drafts, or a filesystem server for the inbox folder; map each discovered tool to a tier | Unmapped tools refused | SDK client `list_tools` |
| 5 | Inbox watcher: a new email with attachments becomes a job; queue idempotent on message id | Duplicate deliveries never run twice | [psycopg](https://www.psycopg.org/psycopg3/docs/) |
| 6 | Worker process runs jobs; scheduler queues the month-end close and approval reminders | The close starts on the 1st without you | [APScheduler](https://apscheduler.readthedocs.io) |
| 7 | Email path: drafts in Mailpit (dev) or Gmail drafts (real); sending needs approval; recipients must match client records | No email to an unknown address, ever (tested) | Sprint 5 hooks |
| 8 | Security suite: injection in invoice text, receipt image text, email body, contract and memory note; bank-detail change; budget exhaustion; permission bypass; exfiltration | Each case passes or fails in `security/` | OWASP LLM Top 10 as the checklist |
| 9 | CI runs unit tests and the **deterministic** security cases on every push; model-dependent cases run nightly on your machine | Green check on GitHub | [Python in Actions](https://docs.github.com/en/actions/use-cases-and-examples/building-and-testing/building-and-testing-python) |
| 10 | Unseal the held-out company; run both arms | Dev vs held-out gap recorded | Protocol section |

Reference code — an MCP server is a few decorated functions. This one can't write to the books because no write tool exists on it:

```python
# src/tickmark/mcp/server.py
from datetime import date
from mcp.server.fastmcp import FastMCP
from tickmark.tools import books, reports

mcp = FastMCP("tickmark-books")

@mcp.tool()
def spend_by_category(start: str, end: str) -> list[dict]:
    """Total spend per category between two ISO dates (YYYY-MM-DD). Read-only."""
    rows = books.spend_by_category(date.fromisoformat(start), date.fromisoformat(end))
    return [r.model_dump(mode="json") for r in rows]       # Decimals become strings, not floats

@mcp.tool()
def open_invoices(client: str | None = None) -> list[dict]:
    """Unpaid client invoices with days overdue, using each client's contract terms."""
    return [i.model_dump(mode="json") for i in books.open_invoices(client=client)]

@mcp.resource("report://{month}")
def monthly_report(month: str) -> str:
    """The close report for a month (YYYY-MM), as Markdown."""
    return reports.render_markdown(month)

if __name__ == "__main__":
    mcp.run()          # stdio, for Claude Desktop
```

- [ ] The MCP server passes the Inspector and works from Claude Desktop
- [ ] Every consumed MCP tool has a tier; none is trusted by default
- [ ] Email-triggered intake and the scheduled close run without you
- [ ] No email to an unknown address; nothing sent without approval
- [ ] Security suite green in CI
- [ ] Held-out result recorded honestly; row recorded

## Sprint 13 — Web app and write-up

**Showcase:** upload a statement, watch the close run live, approve the close plan item by item (seeing the exact email and books change for each), and chat with your books with charts inline. The Results page shows the full eval table. `RESULTS.md` and a two-minute demo video finish the project. This is where your MERN strength shows.

**Learn:** [MDN: Server-sent events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events) · [Next.js docs](https://nextjs.org/docs) · LangGraph streaming docs · [Recharts](https://recharts.org).

**Tech:** Next.js, Tailwind, FastAPI with sse-starlette, Recharts.

**Models and services:** none new.

| # | Task | Expected output | How-to and references |
| --- | --- | --- | --- |
| 1 | FastAPI: start a close (enqueues a job), list closes, submit decisions (enqueues a resume), upload documents | API never runs a graph inside a request | Reference code below |
| 2 | Worker writes graph events to a `run_events` table as it streams | Events survive page reloads | LangGraph `stream_mode=["updates", "custom"]` |
| 3 | SSE endpoint tails `run_events`, with `Last-Event-ID` reconnection | `curl` shows events live | [sse-starlette](https://github.com/sysid/sse-starlette) |
| 4 | Next.js pages: Inbox, Closes (live), Approvals, Chat, Results | `npm run dev` serves it | [Next.js](https://nextjs.org/docs) · [Tailwind](https://tailwindcss.com/docs) |
| 5 | Approvals: per-item approve, edit or reject; edit an email inline; `SENSITIVE` items need a typed confirmation | Approving in the browser resumes the graph | — |
| 6 | Chat with streaming and inline charts from the sandbox | — | `EventSource` (MDN) |
| 7 | Run timeline linking audit events to Langfuse traces | One click from a decision to its trace | Sprint 5 audit log |
| 8 | Results page from `bench/results/` | Table and charts regenerate from raw files | [Recharts](https://recharts.org) |
| 9 | `RESULTS.md`: problem, design, demo company, results, code-only baseline vs agent, local vs cloud, held-out gap, security results, limitations | A stranger understands it in five minutes | — |
| 10 | Demo video; tag `v1.0` | In the README | [OBS](https://obsproject.com) |

Reference code — the browser never talks to the graph directly. The worker runs it; the API reads what the worker wrote:

```python
# src/tickmark/automation/worker.py
def run_close(close_id: str, inputs) -> None:            # inputs: initial state, or Command(resume=...)
    cfg = {"configurable": {"thread_id": close_id}}
    for mode, chunk in close_graph.stream(inputs, cfg, stream_mode=["updates", "custom"]):
        run_events.add(close_id, kind=mode, payload=chunk)
    run_events.add(close_id, kind="status", payload=close_status(close_id))   # paused, done or failed
```

```python
# src/tickmark/api/closes.py
@app.get("/closes/{close_id}/events")
async def events(close_id: str, request: Request):
    last = int(request.headers.get("last-event-id", 0))
    async def gen():
        nonlocal last
        while not await request.is_disconnected():
            for e in await run_events.since(close_id, last):
                last = e.id
                yield {"id": e.id, "event": e.kind, "data": e.payload_json}
            if await run_events.is_settled(close_id):
                break
            await asyncio.sleep(0.5)
    return EventSourceResponse(gen())

@app.post("/closes/{close_id}/decisions")
async def submit_decisions(close_id: str, decisions: dict[str, Decision]):
    await jobs.enqueue("resume_close", close_id=close_id,
                       decisions={k: v.model_dump() for k, v in decisions.items()})
    return {"status": "queued"}
```

- [ ] Approving in the browser resumes the paused close
- [ ] Closing the browser never stops a run
- [ ] Results page regenerates from raw result files
- [ ] `RESULTS.md` states limitations plainly: synthetic companies, one country's conventions, small question set
- [ ] Tagged `v1.0`; repo pinned on your GitHub profile

## Conventions for every sprint

These apply everywhere, so they live here once instead of in each sprint.

| Area | Convention |
| --- | --- |
| Commits | Conventional Commits with a scope: `feat(harness): add budget tracker`. Scopes: `books`, `gateway`, `tools`, `intake`, `harness`, `sandbox`, `rag`, `close`, `chat`, `memory`, `agents`, `mcp`, `automation`, `api`, `web`, `bench`, `security`, `docs`, `ci` |
| Branches and tags | Commits go to `main` automatically at meaningful points, only after the check command exits 0. Never push unless asked. Tag each sprint (`s5-harness`) |
| Code | No comments. Match the surrounding code. Don't split anything up without a reason. Never print secrets |
| Money | `Decimal` only, two places, `Numeric(12, 2)` in Postgres. Never a float, never model arithmetic |
| Evals | Every sprint that changes behaviour ends with a local run (overnight if slow) and one cloud slice, against `eval.yaml`. `make table` regenerates the README |
| Quota | Check `tickmark usage --today` before any cloud run. Cache on in development, off in evals |
| Data | Synthetic data only on free cloud tiers and E2B. Real books run with `TICKMARK_LOCAL_ONLY=1` |
| Tools | Every new tool gets a Pydantic schema, a tier, a timeout, a result cap and a preview, or it doesn't get registered |
| Security | Documents, emails, tool outputs, retrieved text and memory are data, never instructions. A new attack found = a new file in `security/` |
| Config | Settings only through `config.py`; every new variable in `.env.example` |
| Logging | Structured logs with `run_id`, `close_id`, `step`. Never log keys, full bank details or full prompts with real data |
| Decisions | A new ADR in `docs/adr/` whenever you pick between two real options |
| Learning docs | One guide per sprint in `docs/learning/` (from zero, options compared, what was built, proof, code walkthrough with a review checklist), plus the study roadmap in `docs/learning/README.md` |
| Environment | Stop processes only by PID. Temp files go in the scratchpad, not the repo |
| Daily | End each day with `make eval-quick` green, a commit, and tomorrow's first task written down |
| Tooling | Python 3.12, uv, ruff and pytest before every commit; library versions pinned |

## Not covered by this project

Tickmark covers agent engineering, RAG, sandboxing, memory, MCP and the LangChain/LangGraph stack in depth. These are the popular terms it skips, each with where to learn it.

| Term | What it is | In Tickmark | Where to learn it |
| --- | --- | --- | --- |
| CrewAI | Role-based multi-agent framework | Not covered | [crewai.com](https://www.crewai.com) |
| PydanticAI | Type-safe Python agent framework | Not covered | [ai.pydantic.dev](https://ai.pydantic.dev) |
| Vendor agent SDKs | Claude Agent SDK, OpenAI Agents SDK, Google ADK | Not covered | Each vendor's docs; compare with your harness |
| Microsoft Agent Framework | Microsoft's agent stack (AutoGen's successor) | Not covered | Microsoft Learn |
| LlamaIndex | Retrieval-focused framework | Not covered | [llamaindex.ai](https://www.llamaindex.ai) |
| Deep Agents | LangChain's general-purpose agent harness | Reading only | LangChain docs |
| Mastra, Vercel AI SDK agents | TypeScript agent frameworks, your MERN-native path | Not covered | [mastra.ai](https://mastra.ai) · [ai-sdk.dev](https://ai-sdk.dev) |
| DSPy | Prompts optimized automatically against a metric | Not covered | [dspy.ai](https://dspy.ai): a natural follow-up once you have evals |
| A2A | Agent-to-agent protocol | Not covered | [a2a-protocol.org](https://a2a-protocol.org) |
| Computer use, browser agents | Agents operating GUIs and web pages | Not covered | Playwright MCP; OSWorld, WebArena |
| Other vector DBs | Qdrant, Pinecone, Weaviate, Chroma | pgvector only | Concepts transfer |
| GraphRAG | Retrieval over entity-relation graphs | Not covered | Microsoft GraphRAG |
| Model serving | vLLM, SGLang, batching, KV cache | Ollama only | [vLLM docs](https://docs.vllm.ai) |
| Quantizing and fine-tuning | GGUF, AWQ, LoRA, QLoRA | Not covered | [Unsloth docs](https://docs.unsloth.ai) |
| Guardrail libraries | NeMo Guardrails, Presidio | You build your own checks | Each project's docs |
| Other observability tools | LangSmith, Arize Phoenix, Braintrust | Langfuse only | Concepts transfer |
| Voice agents | Speech in, speech out | Not covered | LiveKit Agents, Pipecat |

## Parked for later

Nothing here is needed to finish Tickmark. It stays parked until Sprint 13 is tagged.

| Topic | What it adds | Note for later |
| --- | --- | --- |
| Fine-tuned categorizer | A small model trained on your corrections | Your approval history is a ready-made labelled dataset |
| Real bank feeds | Live transactions instead of exports | Open-banking aggregators; needs real credentials and care |
| Accounting exports | Push to QuickBooks or Xero | Their APIs; maps to your `BOOKS` tier |
| Multi-company SaaS | Auth, tenants, per-company memory | The namespaces are already per company |
| Hosted deployment | Running without your laptop | Small VPS, cloud models, E2B; costs money |
| vLLM serving | Faster local inference for many users | Learn after the product works |

## Sources

Library behaviour and limits change often. Re-check them in each provider's docs and dashboard on Day 0.

- [Building Effective Agents — Anthropic](https://www.anthropic.com/research/building-effective-agents)
- [Effective context engineering for AI agents — Anthropic](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- [How we built our multi-agent research system — Anthropic](https://www.anthropic.com/engineering/multi-agent-research-system)
- [The importance of Agent Harness in 2026 — Philipp Schmid](https://www.philschmid.de/agent-harness-2026) · [awesome-harness-engineering](https://github.com/ai-boost/awesome-harness-engineering)
- [LangChain: human-in-the-loop middleware](https://docs.langchain.com/oss/python/langchain/human-in-the-loop) · [built-in middleware](https://docs.langchain.com/oss/python/langchain/middleware/built-in) · [agents](https://docs.langchain.com/oss/python/langchain/agents)
- [LangGraph docs](https://docs.langchain.com/oss/python/langgraph/overview)
- [Langfuse LangChain integration](https://langfuse.com/docs/langchain) · [Langfuse experiments via SDK](https://langfuse.com/docs/evaluation/experiments/experiments-via-sdk)
- [E2B billing and limits](https://docs.e2b.dev/billing.md) · [E2B internet access](https://e2b.dev/docs/network/internet-access) · [E2B: analyze data with AI](https://docs.e2b.dev/code-interpreting/analyze-data-with-ai.md) · [Firecracker](https://firecracker-microvm.github.io)
- [Gmail MCP server overview](https://www.dragapp.com/blog/gmail-mcp-server/) · [Model Context Protocol](https://modelcontextprotocol.io)
- [LiteLLM proxy](https://docs.litellm.ai/docs/simple_proxy) · [Gemini API rate limits](https://ai.google.dev/gemini-api/docs/rate-limits)
- [pgvector](https://github.com/pgvector/pgvector) · [LangChain PGVector](https://docs.langchain.com/oss/python/integrations/vectorstores/pgvector)
- [CORD receipt dataset](https://github.com/clovaai/cord)
- [Your AI Product Needs Evals — Hamel Husain](https://hamel.dev/blog/posts/evals/)
- [OWASP Top 10 for LLM Applications](https://genai.owasp.org/llm-top-10/)
