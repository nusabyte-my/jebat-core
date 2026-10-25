# 2026-10-25 — agentix `payment-contract-auditor` + four agent-loop guards

Repo: `D:\Jebat` (jebat-core). No deploy — repo-local agent work.

## 1. The specialist

The autoMimpi profile's recommended focus was `feature:agentix`: 2 memories against
25 catalog entries, because the agentix capability had no specialist encoding the
payment-capture failure class that cost a real customer sale (Erawan QPOS #LURNF9).

Added `payment-contract-auditor` (`4a4f4a4`) encoding the #LURNF9 doctrine —
map the contract both ways, read the message shape to classify a failure, replay
the client's EXACT body, audit transaction paths for a second pooled connection,
check sibling forks, verify the compiled artifact, never fabricate a captured sale.
4 golden tasks. Catalog now 26 specialists.

## 2. Four defects the agent loop had — each returned a NON-ANSWER

| Defect | Symptom | Fix |
|---|---|---|
| Dropped tool call | run reports "0 tool calls", ends with raw prose | retry the call; break only on a genuine end-of-turn |
| Provider error synthesised over | CLI exits 0 on a dead provider | skip synthesis on a provider error, let it propagate |
| Degenerate response loop | 20+ repeats of a garbled import line | stop after 3 identical responses, then synthesise |
| Placeholder echoed | 22-char answer `<your complete answer>` | reject a placeholder FINAL_ANSWER |

The parser also had to learn ~15 tool-call shapes: JSON, Hermes XML,
`tool_name(args: {...})`, `<arg_key>` blocks (close tag missing, first key's quote
mangled, several pairs), `tool_name key="value"`, a bare name, stray CJK glyphs —
plus malformed JSON: unescaped inner quotes, a missing outer brace, an escaped
backslash.

## 3. Two Windows shell traps — the model trusted them

- `find apps/api/src -iname "*apture*"` fails on cmd.exe
  (`File not found - "*node_modules*"`). The model concluded the file was missing,
  then invented a `dto/` directory and a `CapturePaymentDto` class — NEITHER
  EXISTS. The real DTOs are in `apps/api/src/payments/payments.controller.ts`.
- `grep -n -A 4 pattern file` (Git-Bash grep) prints context lines with a `-`
  separator (`69-      transform: true`). The model read those as a diff and
  reported the source as "garbled with duplicated lines".

Both are now in the doctrine, which opens with a step 0 on knowing the shell.

## 4. Two golden checks were WRONG, not the answers

- `not_contains "PaymentAdjustment"` failed a CORRECT answer that says
  "do NOT write a PaymentAdjustment — no money moved". The check now asserts the
  answer REJECTS the mechanism.
- The DTO check expected class names the model was never told about. It now
  accepts the real names or the real file.

Both checks now live in the GENERATOR (`scripts/gen_agentix_specialists.py`), not
the built copy — editing the built copy meant the next regeneration silently
reverted them.

## 5. Provider variance is HIGH

The same golden task passes in one run and fails in the next. **A single failure
is NOT a verdict.** Read the answer and the tool events
(`~/.jebat/agentix/runs/<id>/events.jsonl` logs every call; `result.json` holds
the raw model text) before changing anything.

Only `rootsys` (https://rootsys.cloud/v1, glm-5.3) works on this box: local
ollama is DOWN, remote_ollama/9router 401, tokenharbor 402, jebat-vps times out.
`jebat agentix eval --live` gained `--provider`/`--model` (it had no way to
override, and the manifest default resolves to the dead ollama).

## 6. Result

4/4 golden tasks pass. Full suite 422 passed, 5 skipped.
