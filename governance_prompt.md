# PromptWars Project — Governance & Scoring Rubric (Read Before Writing Any Code)

## How to respond to this message
Read this entire file. Do not summarize it back, do not start building yet, do not ask clarifying questions unless something is genuinely ambiguous. Reply with only "Understood" or "OK". You will receive the actual build instructions in the next message, and you are expected to apply everything below from that point on without being reminded.

---

## Part A — Reference Files
This project has two additional standards documents in the project root:
- `frontend_prompt.md` — UI/UX, design system, component, and animation standards
- `backend_prompt.md` — architecture, agent orchestration, and engineering standards

Read the relevant one in full before writing frontend or backend code respectively. Re-open and re-check it at the start of any new screen/component/module/agent, before introducing any new library or architectural pattern, and whenever unsure — resolve doubt by re-reading the file, not by guessing from chat history.

Tech stack and principles in those files are non-negotiable unless explicitly told otherwise. Do not substitute or "improve upon" them under time pressure.

---

## Part B — Scoring Rubric (this project is graded on these 7 axes)

**1. Code Quality** — One responsibility per function/component. Consistent naming across the whole codebase. No duplicated logic — extract to utils/hooks. Comments only on non-obvious logic. Split files that do more than one job.

**2. Security** — No hardcoded API keys/secrets — env vars only. Validate and sanitize all user input before DB/LLM/file operations. Auth checks on every route touching user data. No `eval`, unsanitized `dangerouslySetInnerHTML`, or unchecked deserialization. Grep for exposed secrets before submission.

**3. Efficiency** — Async/non-blocking, parallelize independent operations. Cache expensive or repeated calls (LLM, API, parsed documents) — never call the same thing twice for the same input. No N+1 queries; batch DB reads. Memoize expensive re-renders; lazy-load non-critical components. *(This is currently the weakest-scoring axis historically — prioritize it.)*

**4. Testing** — Unit tests on core business logic, not for show. Cover at least one edge case and one error path per critical function, not just the happy path. Confirm tests actually pass before submission.

**5. Accessibility** — Semantic HTML over div-soup. ARIA labels on icon-only buttons. Full keyboard navigation and visible focus states. Alt text on images; sufficient color contrast.

**6. Google Services** — Deliberately integrate at least one real, functional Google product: Gemini API for the AI/reasoning layer, Firebase for Auth/Firestore, Google Cloud (Vertex AI / Cloud Run) for hosting/inference, or Google Sign-In. Must be functionally wired in, not cosmetic. If the architecture doesn't naturally need one, still find a legitimate slot rather than leaving this axis at zero.

**7. Problem Statement Alignment** — Restate the exact problem statement in one sentence before building anything and keep it visible. Every feature must map back to that sentence — cut anything that doesn't serve it, however impressive. When demoing, walk through the problem statement first, then show each feature as a direct answer to it, in the same order stated.

---

## Part C — Self-Audit Before Any Deliverable Is Marked Done
Before marking any component, module, or the final submission complete, check it against:
- The relevant checklist in `frontend_prompt.md` or `backend_prompt.md`
- All 7 scoring axes above, one by one

If any axis is weak, fix that specific axis rather than polishing an already-strong one — the weakest score drags the average down more than the strongest score raises it.

## Part D — If Context Gets Long
If the conversation grows long and you notice yourself relying on summarized memory rather than these files, explicitly re-read this file plus `frontend_prompt.md` and `backend_prompt.md` before continuing. Losing track of these mid-build is the single biggest risk in this project.
