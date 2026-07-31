<p align = "center" draggable="false" ><img src="https://github.com/AI-Maker-Space/LLM-Dev-101/assets/37101144/d1343317-fa2f-41e1-8af1-1dbb18399719"
     width="200px"
     height="auto"/>
</p>

<h1 align="center" id="heading">Session 11: Claude Code & the Claude Agent SDK</h1>

| 📰 Session Sheet | ⏺️ Recording | 🖼️ Slides | 👨‍💻 Repo | 📝 Homework | 📁 Feedback |
|:-----------------|:-------------|:----------|:----------|:------------|:------------|
| [Session 11: Claude Code & Claude Agent SDK ](https://github.com/AI-Maker-Space/The-AI-Engineering-Certification-v1.0/tree/main/00_Docs/Modules/11_Claude_Code) |[Recording!](https://us02web.zoom.us/rec/share/2I5HA6DwVFgmtyjPaq1SJDgkaVEuYZoWYyMCK8DOAZ99Zm6f7dTi0IGONXj6mRel.YHFzKF03mI5v6JAM) <br> passcode: `&Qhi!cf0`| [Session 11 Slides](https://canva.link/uw1cl42x84tm6zh) |You are here! <br><br> [Certification Challenge](https://github.com/AI-Maker-Space/The-AI-Engineering-Certification-v1.0/tree/main/00_Docs/Certification%20Challenge) | [Optional Session 11 Assignment](https://forms.gle/sAyr5BgBLTfgJV8EA) <br><br>  [Cert Challenge Submission Form](https://forms.gle/xtM9F38nfRKcdjH97)| [Feedback 7/7](https://forms.gle/oDrguLDNvva65mtM8) |

## Useful Resources

**Claude Code**
- [Claude Code Documentation](https://code.claude.com/docs) — official docs: setup, workflows, settings
- [Claude Code Quickstart](https://code.claude.com/docs/en/quickstart) — from install to first session
- [Claude Code Best Practices](https://www.anthropic.com/engineering/claude-code-best-practices) — Anthropic engineering guide

**Claude Agent SDK**
- [Agent SDK Overview](https://docs.anthropic.com/en/api/agent-sdk/overview) — what the SDK is and when to use it
- [Building Agents with the Claude Agent SDK](https://www.anthropic.com/engineering/building-agents-with-the-claude-agent-sdk) — Anthropic engineering deep dive

## Main Assignment

**Build a chat web app powered by the Claude Agent SDK** — and build it *with* Claude Code.

This session is markdown-only on purpose. There is no starter code and no notebook: every line of code in your final app will be written in collaboration with Claude Code. The session has one build arc across a single breakout room:

```text
you → Claude Code → chat app skeleton → wire in Agent SDK query()
      (FastAPI + chat UI, echo stub)      ├─ tools: Read / Glob / Grep
                                           └─ your custom tool
```

The finished product: a **codebase concierge** — a chat interface in the browser where an agent (with real tools) answers questions about any repository you point it at. In Session 10 you served models behind endpoints; today you serve an *agent* behind one.

Work through the three guides in order:

```text
01_Installing_Claude_Code.md   # install, authenticate, verify
02_Using_Claude_Code.md        # drive Claude Code; scaffold the chat app skeleton
03_Claude_Agent_SDK.md         # add the agent and connect it to your website
```

## Outline

### Breakout Room #1: Claude Code, the Agent SDK, and the Connection

- Task 1: Install Claude Code and authenticate ([guide](./01_Installing_Claude_Code.md))
- Task 2: Learn the loop — explore a repo you didn't write ([guide](./02_Using_Claude_Code.md))
- Task 3: Scaffold the chat app skeleton with Claude Code (plan → implement → verify)
- Task 4: Write the project's `CLAUDE.md`
- Question #1 and Question #2
- Task 5: Install the Agent SDK and run your first `query()` ([guide](./03_Claude_Agent_SDK.md))
- Task 6: Wire the agent into `/api/chat` — replace the echo stub
- Task 7: Conversation memory — resume sessions across messages
- Task 8: Give the agent a custom tool
- Question #3 and Question #4
- Activity #1: Level Up the Chat App

## Questions

### ❓ Question #1

While scaffolding in Task 3 you used **plan mode** before letting Claude Code write anything. Why does an agent that can execute shell commands need a permission system at all, and why is plan mode particularly valuable when starting a project from an empty directory?

#### ✅ Answer

An agent that can run shell commands has the same power as the person at the keyboard: it can create, overwrite, and delete files, install packages, hit the network, spend money against API keys, and run destructive commands like `rm -rf`. Unlike a chat model that only produces text, these actions have real, often irreversible side effects on the machine and outside world. The agent is also non-deterministic — it can misunderstand the task or hallucinate a wrong command. A permission system puts a human checkpoint in front of consequential actions so the model proposes and the user approves, keeping a fallible autonomous process from acting unilaterally. It also lets you scope trust: cheap, reversible reads (Read/Glob/Grep) can be auto-allowed while writes and shell commands require confirmation.

Plan mode is a read-only mode: Claude Code can explore and reason but cannot edit files or execute commands until you approve a plan. This is especially valuable on an empty directory because that first burst of scaffolding is where the most decisions get baked in at once — framework, project layout, dependencies, naming, config. Once files are written, undoing bad structural choices is expensive. Plan mode forces the agent to surface its intended approach *before* touching disk, so you can correct the direction (wrong framework, over-engineered structure, missing pieces) while it's still just text and cheap to change — turning a "generate and pray" scaffold into a review-then-commit workflow.

### ❓ Question #2

`CLAUDE.md` is loaded into context at the start of every session. What belongs in it — and what *doesn't*? How does this relate to what you learned about context management and memory in Session 3?

#### ✅ Answer

**What belongs:** durable, high-signal facts the agent can't cheaply rediscover and that pay off on almost every task — how to run/build/test the app, the project layout and where key things live, non-obvious conventions and gotchas, the tech stack and versions, and standing preferences ("use uv, not pip"; "run the linter before committing"). The test is: is this stable, project-wide, and useful often enough to justify occupying context in *every* session?

**What doesn't:** anything transient, narrow, or easily re-derived — a blow-by-blow of the current task, large code excerpts or full file contents (the agent can just read the file), one-off notes, secrets/API keys, and exhaustive documentation that only matters for a single feature. Bloating `CLAUDE.md` is actively harmful: it's a fixed tax on every session.

**Relation to Session 3 (context management & memory):** the context window is a scarce, finite resource, and everything in it competes for the model's attention — irrelevant tokens dilute the signal and cost money/latency on every turn. `CLAUDE.md` is exactly the "persistent memory vs. working context" distinction from Session 3 made concrete: it's the small, curated long-term memory you *always* pay to load, so it should hold only the facts with the highest (relevance × frequency) payoff, while everything episodic stays out and is pulled into working context on demand (via reading files, retrieval, or tool calls) only when a specific task needs it.

### ❓ Question #3

The Agent SDK gives you the same agent loop that powers Claude Code. Compare this to the agent loops you hand-built with LangGraph in Sessions 2–4: what does the SDK give you for free, and what control do you give up?

#### ✅ Answer

**What you get for free:** the entire production-grade agent loop that you wired by hand in LangGraph — the reason/act/observe cycle, tool-call parsing and dispatch, feeding results back into context, and looping until done. On top of that the SDK ships batteries the LangGraph builds didn't have: a built-in, battle-tested toolset (Read/Glob/Grep/Edit/Bash, etc.), the permission system and tool allowlisting, session persistence for conversation memory (resume via session IDs), context management/compaction as history grows, MCP server integration, and prompt-caching optimizations. You describe *what* the agent should do and hand it tools; you don't implement the orchestration, the state graph, or the tool-execution plumbing.

**What you give up:** fine-grained control over the loop itself. With LangGraph you owned the state machine — you could define arbitrary nodes and edges, insert conditional branches, checkpoints, human-in-the-loop interrupts, parallel fan-out, and custom routing between steps, with full visibility into and control over state. The SDK's loop is largely opaque and opinionated: it runs Anthropic's fixed agentic loop, so you can't restructure control flow, swap in a non-Claude model, or intervene at arbitrary points — you influence behavior through the edges it exposes (system prompt, tool set, permissions, hooks/options) rather than by rewriting the graph. The trade is the usual one: less boilerplate and a proven loop, in exchange for less bespoke control and provider lock-in.

### ❓ Question #4

Your chat app could have called a chat completions API directly, the way you did early in the course. What do you gain by routing every message through the Agent SDK's `query()` instead — and what new risks does an agent with tools introduce that a plain chat completion doesn't have? How did your tool allowlist and permission mode address them?

#### ✅ Answer

**What you gain:** a plain chat completion is a single turn of text in, text out — it can only answer from what's already in its context (and its training data), so to build the codebase concierge you'd have to manually fetch files, stuff them into the prompt, and hope you grabbed the right ones. Routing through `query()` gives the model *agency*: it can decide which files to read, Grep for a symbol, follow references, and iterate over multiple tool calls until it has actually gathered the evidence to answer — grounding responses in the real repository instead of guessing. You get retrieval, multi-step reasoning, and action for free, which is what turns "a chatbot about code" into "an agent that investigates the code."

**New risks an agent with tools introduces:** the moment the model can act, it can act *wrongly*. It can read files it shouldn't (secrets, `.env`), run destructive or expensive shell commands, write/delete files, or hit the network — and because the browser exposes it to arbitrary user input, it's exposed to prompt injection: a malicious message (or malicious text inside a file it reads) could try to steer it into exfiltrating data or running harmful commands. A plain chat completion can only ever emit text, so none of these side-effect risks exist.

**How the allowlist and permission mode addressed them:** I constrained the agent to a minimal, read-only tool allowlist — `Read`, `Glob`, `Grep`, plus my custom read-only tool — so it can *investigate* the repo but has no ability to write files, delete, or run arbitrary `Bash`. Whatever isn't on the allowlist simply isn't callable, which caps the blast radius of both agent mistakes and injection attempts to "read the repo," an action with no destructive side effects. Combined with a restrictive permission mode (denying anything outside the allowed set rather than prompting/auto-approving), this enforces least privilege: the concierge has exactly the capabilities it needs to answer questions and nothing more.

## Activity 1: Level Up the Chat App

Extend your working chat app with **at least one** of the following (built with Claude Code, of course):

1. **Live progress streaming** — stream the agent's activity to the browser (e.g. via Server-Sent Events) so users see tool calls ("reading `app.py`…") while the agent works, instead of a spinner
2. **Multi-conversation support** — a sidebar of separate conversations, each mapped to its own SDK session
3. **A second custom tool** — something genuinely useful for your target repo (e.g. `git_log` for recent changes, or a test-runner summary tool)

Whichever you pick, demo it in your Loom video and explain the design decision in one paragraph.

## Advanced Activity: The Cat Shop Concierge

Connect your Session 8 cat shop MCP server to your chat app's agent via the SDK's `mcp_servers` option. Your chat app becomes a shopping concierge: users can browse the catalog, fill a cart, and check out — in natural language, through the UI you built, hitting the OAuth-protected server you wrote in Session 8.

Include your findings and a demo in your Loom video.

## Ship 🚢

The working chat app!

### Deliverables

- A short Loom showing:
  - Claude Code scaffolding or extending the app (plan → implement → verify — show the plan!); and
  - the chat app answering real questions about a repository, including at least one visible custom-tool use

## Share 🚀

Make a social media post about your final application!

### Deliverables

- Make a post on any social media platform about what you built!

Here's a template to get you started:

```
🚀 Exciting News! 🚀

I am thrilled to announce that I have just built and shipped a chat app powered by the Claude Agent SDK — scaffolded entirely with Claude Code! 🎉🤖

🔍 Three Key Takeaways:
1️⃣
2️⃣
3️⃣

Let's continue pushing the boundaries of what's possible in the world of AI agents. Here's to many more innovations! 🚀
Shout out to @AIMakerspace !

#ClaudeCode #AgentSDK #AIAgents #Innovation #AI #TechMilestone

Feel free to reach out if you're curious or would like to collaborate on similar projects! 🤝🔥
```

## Submitting Your Homework (Optional For Extra Mark)

Follow these steps to prepare and submit your homework:

1. Pull the latest updates from upstream into the main branch of your repo:

```bash
git checkout main
git pull upstream main
git push origin main
```

2. Work through `01_Installing_Claude_Code.md`, `02_Using_Claude_Code.md`, and `03_Claude_Agent_SDK.md` in order.
3. Build your chat app in a new `chat-app/` folder inside this session directory (include its `CLAUDE.md` — we want to see it!).
4. Fill in your answers to Questions #1–#4 in this README.
5. Complete Activity #1 and record your Loom video.
6. Add, commit, and push your work to your origin repository. Remove `.env` files and API keys before committing.

When submitting your homework, provide the GitHub URL to your repo.
