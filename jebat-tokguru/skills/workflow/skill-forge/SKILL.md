---
name: skill-forge
description: Generate a new skill from a simple prompt, then run an enhancer pass to tighten trigger rules, workflow, and output quality
category: workflow
tags:
  - skill
  - prompt
  - generator
  - enhancer
  - workflow
ide_support:
  - vscode
  - zed
  - cursor
  - claude
  - gemini
author: JEBAT Team
version: 1.0.0
---

# Skill Forge

## Description
Use this skill when you want a fast prompt to create a new skill, plus a second pass that improves the skill so it is cleaner, easier to trigger, and more reusable.

## When to Use
- Creating a brand new skill from scratch
- Turning a rough idea into a usable skill prompt
- Refining an existing skill that feels too vague or bloated
- Forcing clearer trigger rules and leaner instructions

## Base Prompt
Use this first:

```text
Create a new AI skill for: [skill idea]

Goal:
- Make it practical and reusable
- Keep it concise
- Include clear trigger conditions
- Define the workflow step by step
- Include response defaults
- Add one short example usage

Output format:
1. Skill name
2. Description
3. When to use
4. Workflow
5. Response defaults
6. Example usage
```

## Enhancer Prompt
Run this on the draft:

```text
Enhance this skill draft.

Improve it by:
- removing fluff
- tightening trigger rules
- making the workflow more deterministic
- reducing overlap with general assistant behavior
- keeping only high-signal instructions
- improving the example so it matches real usage

Then return the improved final skill in the same structure.
```

## Fast Combined Prompt
Use this when you want one-shot generation:

```text
Create a new AI skill for: [skill idea]

Requirements:
- concise and practical
- clear trigger conditions
- step-by-step workflow
- response defaults
- one realistic example

Then self-enhance the result by:
- removing vague wording
- tightening trigger rules
- simplifying the workflow
- keeping only essential instructions

Return the final improved skill only.
```

## Response Defaults
- Prefer a narrow, specific scope over a broad one
- Keep the workflow short unless the task is fragile
- Avoid generic advice that the base assistant already knows
- Make the example realistic enough to trigger the skill correctly

## Example Usage
```text
@skill-forge Create a new AI skill for summarizing product feedback into bug reports and feature requests.
```
