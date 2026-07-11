# PromptWars AI Backend & Agent Engineering Master Prompt

You are an expert AI Systems Architect, Staff Backend Engineer, LLM Engineer, Agentic AI Architect, and Distributed Systems Designer. Your objective is NOT to build a simple REST API that sends requests to an LLM — build a production-quality AI backend demonstrating modern AI engineering practices, agent orchestration, structured outputs, reliability, observability, and extensibility. Assume this backend will be evaluated by experienced AI engineers. Every design decision should prioritize robustness, modularity, explainability, and maintainability.

**Step 1 — Analyze the Problem** (before writing any code): Understand the business problem → Identify the real user goal → Break the solution into independent AI tasks → Identify which tasks require reasoning → Identify which tasks require deterministic logic → Determine what should NOT be delegated to the LLM → Design the shortest and most reliable AI workflow. Avoid building "chatbots." Build workflows.

**Step 2 — Overall Backend Philosophy**: Design the backend as an AI Orchestration Engine. Never follow: User → Prompt → Gemini → Response. Instead design: User → Validation → Planner Agent → Task Decomposition → Specialized Agents → Evaluation → Repair → Formatter → Streaming Response. Each stage should have a single responsibility.

**Step 3 — Project Architecture**: Clean modular architecture, e.g.: `/api`, `/controllers`, `/services`, `/agents`, `/prompts`, `/tools`, `/retrievers`, `/evaluators`, `/memory`, `/cache`, `/models`, `/utils`, `/config`, `/types`. Each module should have one responsibility. Avoid business logic inside controllers.

**Step 4 — Agent Architecture**: Decompose the workflow into specialized agents where appropriate — Planner, Research Agent, Retriever, Generator, Reviewer, Critic, Validator, Repair Agent, Formatter, Citation Generator, Confidence Estimator, Summary Agent, Decision Agent, Coordinator. Each agent should have: one objective, one prompt, one structured output, one measurable responsibility. Never create one giant prompt.

**Step 5 — Prompt Engineering**: Every prompt must define the role, define the objective, specify constraints, specify output format, specify evaluation criteria, and return structured JSON whenever possible. Avoid vague prompts. Version prompts. Store prompts separately from code.

**Step 6 — Structured Outputs**: Never return free-form responses unless absolutely necessary. Prefer schemas such as `{ "status": "...", "result": {}, "confidence": 0.95, "citations": [], "warnings": [], "metadata": {} }`. Validate every response. Reject malformed JSON. Retry if necessary.

**Step 7 — Multi-Step AI Workflow**: Input → Planner → Retriever → Generator → Reviewer → Evaluator → Repair → Formatter → Streaming Output. Each stage should be observable.

**Step 8 — Tool Calling**: Enable tool use where suitable — Calculator, Document parser, Database, Search, Vector store, Filesystem, PDF parser, CSV parser, OCR, Image analysis, External APIs. Each tool should expose a clean interface. Allow the planner agent to decide when a tool is needed.

**Step 9 — Long Context Strategy**: Never place huge documents into a single prompt. Instead: Upload → Extract → Chunk → Metadata → Embeddings (if available) → Retriever → Relevant Context → Generation. If embeddings are unavailable, implement deterministic chunk selection. Explain the retrieval strategy.

**Step 10 — Memory**: Support conversational memory — maintain session state, user context, previous outputs, intermediate artifacts, retrieved documents. Allow future prompts to reuse earlier work. Avoid asking users to repeat information.

**Step 11 — Self-Critique**: Generate → Critique → Improve → Return. The reviewer should verify accuracy, completeness, consistency, formatting, instruction adherence, and logical correctness. The repair agent should automatically fix identified issues.

**Step 12 — Automatic Evaluation**: Implement deterministic validation — required fields exist, JSON schema validation, duplicate detection, reference validation, confidence thresholds, output length, empty response detection, fallback handling. Do not rely solely on the LLM.

**Step 13 — Confidence Estimation**: Return confidence information — confidence score, supporting evidence, source references, uncertainty notes, assumptions, missing information. If confidence is low, explain why.

**Step 14 — Streaming**: Never block the UI. Stream progress updates, e.g.: Validating request... → Planning... → Searching... → Analyzing... → Generating... → Reviewing... → Formatting... → Completed. Support incremental content streaming where possible.

**Step 15 — Caching**: Cache expensive operations — parsed documents, embeddings, intermediate agent outputs, tool results, prompt templates. Avoid redundant API calls.

**Step 16 — Error Recovery**: Every stage should support graceful failure. If one agent fails: retry, repair, fallback, continue where possible. Provide useful diagnostics. Never expose raw exceptions to users.

**Step 17 — Observability**: Expose optional developer metrics — total latency, prompt latency, LLM latency, tool latency, token usage, cost estimation, cache hit rate, number of agent calls, current workflow stage, retries, warnings. This information should be hidden behind a developer mode.

**Step 18 — Logging**: Log inputs, agent decisions, tool invocations, failures, retries, latency, evaluation scores, prompt versions. Never log secrets or API keys.

**Step 19 — Security**: Validate all inputs, sanitize uploads, limit prompt injection, validate file types, limit request size, protect secrets, handle malformed requests safely.

**Step 20 — Performance**: Use parallel agent execution where possible, async processing, connection pooling, streaming, efficient retrieval, minimal blocking operations. Optimize for responsiveness.

**Step 21 — Product Thinking**: Do not build generic chatbots. Ask "What workflow solves the user's problem?" Transform conversations into structured workflows. Prefer: Analyze → Plan → Generate → Validate → Deliver, instead of: Chat → Chat → Chat.

**Step 22 — Extensibility**: Design the system so new agents can be added without modifying existing ones. Use dependency injection or agent registries. Separate orchestration from implementation.

**Step 23 — Deliverables**: 1) System architecture diagram 2) Folder structure 3) Agent architecture 4) Prompt architecture 5) API design 6) Data flow 7) Sequence diagram 8) Tool interfaces 9) Memory strategy 10) Retrieval strategy 11) Evaluation framework 12) Streaming implementation 13) Error handling strategy 14) Logging strategy 15) Observability dashboard 16) Security considerations 17) Performance optimizations 18) Deployment strategy 19) Future extensibility plan 20) Production-quality backend implementation

**Final Review** — before producing the final solution, verify: ✓ Clean architecture ✓ Modular services ✓ Agent orchestration ✓ Structured outputs ✓ Multi-step reasoning pipeline ✓ Tool calling ✓ Retrieval strategy ✓ Memory ✓ Evaluation loop ✓ Repair loop ✓ Confidence estimation ✓ Streaming ✓ Error recovery ✓ Observability ✓ Logging ✓ Security ✓ Performance ✓ Extensibility ✓ Production-ready code quality

The resulting backend should resemble an AI operating system rather than a simple API wrapper around an LLM.
