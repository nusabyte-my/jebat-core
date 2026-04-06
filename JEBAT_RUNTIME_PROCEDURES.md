# JEBAT Runtime Procedures

## Goal

Turn drafted JEBAT skills into **real procedures** Jebat can follow inside OpenClaw today.

---

## 1. Memory Procedure

### Use when
- user asks to remember something
- prior context matters
- a decision should persist
- project facts or preferences were discovered

### Procedure
1. decide if the information is temporary, daily, or long-term
2. if temporary/session-level → keep in current context only
3. if important but recent → write to `memory/YYYY-MM-DD.md`
4. if durable preference / project truth / architecture decision → update `MEMORY.md`
5. if it changes how Jebat should operate → update `AGENTS.md`, `TOOLS.md`, or skill docs

### Promotion rules
- raw event → daily memory
- repeated fact / preference → MEMORY.md
- repeated workflow → procedural doc / skill

---

## 2. Research Procedure

### Use when
- facts need verification
- external information is needed
- user asks for comparison, best practices, or latest status

### Procedure
1. check local docs first if topic is OpenClaw-specific
2. use `web_search`
3. fetch strongest sources with `web_fetch`
4. compare agreements and disagreements
5. answer with synthesis, not source dumping
6. if outcome matters later, store findings in memory

---

## 3. Orchestration Procedure

### Use when
- task is complex
- parallel work helps
- specialist judgment improves quality
- coding or long-running analysis is needed

### Procedure
1. decide if task is small enough to do directly
2. if not, decompose into subtasks
3. choose direct tools vs spawned sessions
4. use `sessions_spawn` for specialists / ACP when justified
5. use `sessions_yield` if waiting for spawned work
6. merge outputs into one coherent answer
7. store important decisions to memory

---

## 4. Cybersecurity Procedure

### Use when
- user asks for audit, vulnerabilities, exposure review, or risk analysis

### Procedure
1. classify as defensive assessment unless user explicitly requests authorized offensive validation
2. inspect configs, docs, logs, and versions
3. run safe diagnostics where available
4. identify findings by severity and evidence
5. provide remediation, not fear theater
6. store key findings and follow-up items in memory

---

## 5. Hardening Procedure

### Use when
- user wants to secure a host, service, app, OpenClaw deployment, SSH, firewall, updates, or configs

### Procedure
1. inspect current state
2. identify weak defaults / unnecessary exposure
3. suggest minimal safe changes first
4. ask before risky or production-affecting changes
5. prefer reversible edits and backups
6. verify after changes

---

## 6. Pentesting Procedure

### Use when
- explicit authorization exists
- scope is defined
- user requests offensive validation

### Procedure
1. confirm authorization and scope explicitly
2. define out-of-scope targets
3. plan recon → vuln validation → reporting
4. avoid destructive actions unless explicitly allowed
5. document every finding and impact clearly
6. hand off remediation to cybersecurity/hardening flow

If authorization is unclear, stop and ask.

---

## 7. Hermes Routing Procedure

### Every task
1. classify
2. recall memory if prior work matters
3. choose the smallest correct tool/action
4. escalate only when complexity demands it
5. verify outcome
6. write down what should persist

---

## 8. Useful External Skill Categories to Adapt Next

High-value categories:
- incident response
- deployment / release operator
- database operator
- documentation architect
- API designer
- repo maintenance / changelog automation

Do not import fluff skills just because they look fancy.
