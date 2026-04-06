# Fifth Batch External Reviews

## 1. agentgate

### Summary
Gateway pattern for separating credentials from the agent and requiring human approval for write actions.

### Strong patterns
- read/write separation
- human approval queue for writes
- credentials on separate host
- good fit with Jebat’s safety and privacy model
- explicit intent comments for write requests are a strong idea

### Concerns
- bypass mode weakens the trust model if misused
- depends on external server and credentials
- richer frontmatter and environment assumptions need careful integration

### Jebat decision
- **APPROVE WITH CAUTION** as a pattern source
- strong fit conceptually for safe external action boundaries

### Planned Jebat use
- strengthen approval discipline for risky writes
- improve external action boundary design
- keep credentials and dangerous writes gated when possible

---

## 2. billy-emergency-repair

### Summary
Highly specific remote repair skill for a named system and specific authorized user.

### Strong patterns
- explicit authorization boundary
- clear emergency-only scope
- audit logging mindset
- backup before repair

### Concerns
- extremely environment-specific
- hardcoded host/service assumptions
- direct remote repair flow is too specialized for general Jebat adaptation
- not broadly reusable outside its original owner context

### Jebat decision
- **PATTERN ONLY**
- useful as an example of tightly scoped authorization and emergency procedure design

### Planned Jebat use
- emergency procedure template ideas only
- authorization + audit + backup pattern for sensitive repair flows

---

## Net takeaway

`agentgate` is a meaningful governance pattern for safe external actions.
`billy-emergency-repair` is mostly a reminder that tightly-scoped emergency skills can be safe when authorization and scope are explicit, but it is not a general stack fit.
