

# Session 12: Production Agent Patterns - Guardrails, Caching, and A2A

### [Quicklinks](https://github.com/AI-Maker-Space/The-AI-Engineering-Certification-v1.0/tree/main/00_Docs/Modules)


| 📰 Session Sheet                      | ⏺️ Recording | 🖼️ Slides | 👨‍💻 Repo    | 📝 Homework | 📁 Feedback |
| ------------------------------------- | ------------ | ---------- | ------------- | ----------- | ----------- |
| [Session 12: Production 101: Guardrails & Caching](https://github.com/AI-Maker-Space/The-AI-Engineering-Certification-v1.0/tree/main/00_Docs/Modules/12_Production) |[Recording!](https://us02web.zoom.us/rec/share/Yx3VqEBLbCZAXsjTL1L98NupP5hfadVQUYIvV3BX94edcmkRJAKczcUAKZ0NMGtQ.aDpXtTci_YW4ovbs) <br> passcode: `6JWfF%r&`| [Session 12 Slides](https://canva.link/mu8p2oni7jylf95) |You are here! | [Optional Session 12 Assignment](https://forms.gle/PVMnzonTDGoaNwZ48) | [Feedback 7/9](https://forms.gle/NVyhkaEERgB9zhGQ7) |




## Main Assignment

Previous sessions built, evaluated, and served the cat health agent. Session 12 prepares it for production with three small, self-contained concepts:

```text
01 Guardrails -> control what goes into and comes out of the agent   (notebook)
02 Caching    -> stop paying for the same answer twice               (notebook)
a2a/          -> let your agent talk to other agents over a protocol (runnable mini-project)
```

Each part is deliberately short: one new concept and a handful of tasks. The parts are independent — there is no set order or outline for this session. Pick whichever interests you most, or work through all three.

## The Parts

**`01_Cat_Health_Agent_Guardrails.ipynb`** — Build layered guardrails around the agent: deterministic input rails (emergency escalation, injection blocking, PII redaction), a model-based topical guard, and output rails that check and repair draft replies, wired into the agent loop with LangChain middleware.

**`02_Cat_Health_Agent_Caching.ipynb`** — Stop paying for repeated work: exact-match response caching, a from-scratch semantic cache (and why it is dangerous in a health domain), embedding and tool-result caches, and provider-side prompt caching you can measure in the usage details.

**`a2a/`** — Build the A2A protocol from the wire up: a specialist agent behind a minimal A2A server (`server.py`), a discovery-driven client (`client.py`), and a front-desk agent that delegates across the protocol (`front_desk.py`). Start with [`a2a/README.md`](a2a/README.md) — it walks through starting the server and testing it with curl, the client, the delegation demo, and a no-API-key smoke test.

## Setup

From this folder, install the environment with uv:

```bash
uv sync
```

Then open the notebooks in Cursor or VS Code and select the Python/Jupyter environment created by uv.

You will need an OpenAI API key available when running the notebooks:

```bash
export OPENAI_API_KEY="your-key"
```

Optional LangSmith tracing:

```bash
export LANGSMITH_TRACING=true
export LANGSMITH_API_KEY="your-key"
```

The `a2a/` mini-project starts a local HTTP server on port 9999. Nothing leaves your machine; stop it with `Ctrl+C`.

## Questions

### ❓ Question #1

In `01_Cat_Health_Agent_Guardrails.ipynb`, input rails run in a specific order: deterministic checks (emergency, injection, PII) first, then the model-based topical guard. Why is that ordering important in production — and why do the rails return decisions like `escalate`, `block`, and `rewrite` instead of a simple boolean pass/fail?

#### ✅ Answer

**Why the ordering matters — it's a cost/latency/certainty funnel.** The deterministic rails (regex, keyword, allowlist matching) cost essentially nothing and run in microseconds; the model-based topical guard costs one model call and hundreds of milliseconds on *every* request that reaches it. So you run the cheapest, most certain checks first and let only the inputs that survive them "earn" the paid check. This has three payoffs in production:

- **Cost.** A request that's an obvious emergency or injection attempt is caught for free and never triggers a paid guard call — or a paid agent call. Blocked/escalated requests spend zero model tokens.
- **Latency.** The common cases exit early instead of waiting on a network round-trip to the guard model.
- **Correctness/auditability.** Deterministic rails are exact, reproducible, and logged with the rail that fired and why. You put the unavoidable-but-probabilistic model judgment *last*, only where genuine judgment is actually needed (e.g., "is this even about cat health?"), which regex can't decide.

The ordering also reflects severity: the emergency rail is the single most important guard, so it fires first and short-circuits before anything else can turn a poisoning report into a leisurely educational answer.

**Why decisions, not booleans.** A pass/fail boolean throws away the information needed to respond correctly, and different violations demand fundamentally different handling:

- `allow` → pass through unchanged.
- `block` → refuse with a fixed safe message (e.g., injection attempts) — the model is never called.
- `escalate` → short-circuit with an urgent redirect ("call your vet/poison control now"). This is the point of the whole system: for a health assistant, recognizing an emergency and *refusing to be a chatbot about it* is more important than filtering bad input. A boolean "fail" couldn't distinguish "refuse silently" from "escalate loudly."
- `rewrite` → pass through, modified (PII redacted). The user did nothing wrong, so blocking would be wrong; we just strip contact details out of model context, logs, and traces before continuing.

These decisions map directly onto middleware behavior: `escalate`/`block` return a canned message and jump to `end` (zero tokens), while `rewrite` edits the message in place and lets the loop continue. A boolean can't carry the action, the reason, or the "which rail fired" metadata that makes the guardrail debuggable — and a guardrail you can't audit is one you can't debug.

### ❓ Question #2

In `02_Cat_Health_Agent_Caching.ipynb`, a semantic cache can serve a paraphrased FAQ for the price of one embedding call — but the notebook also shows how a one-word difference (treat vs. poison) can produce a catastrophic cache hit. Why can't you fix this with a better similarity threshold alone, and what should a production health agent do instead for high-stakes queries?

#### ✅ Answer

**Why the threshold can't save you.** Embeddings measure how *alike two sentences look*, not *how much the difference between them matters*. "Is chicken a good treat for my cat?" and "Is chocolate poison for my cat?" are nearly identical in surface form — same structure, one swapped noun — so they land close together in embedding space, even though one is about dinner and the other is a poisoning emergency. Similarity is not equivalence. Whatever threshold you choose, there will always exist some pair of critically different queries whose cosine similarity sits just above it. Raise the threshold to exclude that pair and you start missing legitimate paraphrases (the whole reason you built a semantic cache); lower it and more dangerous collisions get through. There's no single number that separates "safe paraphrase" from "catastrophic near-duplicate," because the distinction isn't geometric. Worse, the failure is high-confidence: the chocolate-ingestion user gets a cheerful "chicken is a fine treat" answer served *faster and more confidently* than a live model would have.

**What a production health agent should do instead:** don't rely on the threshold — gate the cache with a guardrail so high-stakes queries bypass it entirely.

- **Route through the input rails first (Notebook 1).** If `run_input_rails` returns `escalate` (emergency), never consult *and* never populate the semantic cache for that query. Guardrails and caches aren't separate features — the rails decide what is *safe to cache*. Deterministic emergency detection is exactly the right gate because it keys on danger, not on surface similarity.
- **Layer additional safety bounds on the cache:** a TTL so answers can't go stale (an emergency answer must never be served old), a bounded size with eviction, and per-user scoping so one user's cached context never leaks to another.

In short: keep the cheap semantic cache for genuinely low-stakes, repetitive FAQ traffic, and force every high-stakes query straight to a fresh model call. The correctness win from bypassing the cache far outweighs the fraction of a cent it saves.

## Submitting Your Homework

Follow these steps to prepare and submit your homework:

1. Pull the latest updates from upstream into the main branch of your AIE9 repo:

```bash
git checkout main
git pull upstream main
git push origin main
```

1. Start Cursor from the `12_Production_Agent_Patterns` folder.
2. Work through the parts you chose (notebooks and/or the `a2a/` mini-project).
3. Keep useful outputs that help explain your work — for example guardrail decision tables, cache hit/miss timings, or the A2A delegation trace. Remove secrets and excessively noisy outputs.
4. Add, commit, and push your modified work to your origin repository.

When submitting your homework, provide the GitHub URL to your AIE9 repo.
