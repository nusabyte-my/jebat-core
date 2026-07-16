---
name: webfetch
description: Fetch live web pages, inspect responses, extract relevant content, and summarize findings with links
category: workflow
tags:
  - web
  - fetch
  - research
  - inspection
  - http
ide_support:
  - vscode
  - zed
  - cursor
  - claude
  - gemini
author: JEBAT Team
version: 1.0.0
---

# Webfetch

## Description
Use this skill when the task depends on live web content rather than repo files. Fetch the page, inspect the response, extract only the relevant parts, and keep the result grounded in the actual source.

## When to Use
- Checking whether a public page is reachable
- Inspecting live HTML or JSON responses
- Pulling current content from documentation or status pages
- Verifying a deployed route or UI asset

## Operating Pattern
- Prefer the exact URL the user gave you
- Confirm response status before summarizing page content
- Quote sparingly and keep links visible
- Distinguish fetched facts from your own inference

## Response Defaults
- Lead with status and the important finding
- Include the URL you checked
- Call out mismatches between expected and actual content

## Example Usage
```text
@webfetch Check https://jebat.online/webui/#control and tell me whether the live page contains the new provider controls.
```
