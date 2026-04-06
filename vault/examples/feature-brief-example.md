# Feature Brief Example

## Objective
Add role-based approval visibility to the operations dashboard so staff can see who owns the next action and whether a request is blocked.

## User / Audience
- admin staff
- operations manager

## Problem
Requests are moving through the dashboard without clear approval state, causing repeated follow-up and manual clarification in chat.

## Desired Outcome
Users can identify pending approval, current owner, and next required action without asking in WhatsApp.

## Constraints
- must fit the current dashboard information model
- should avoid a large workflow-engine rewrite
- should ship within the current retainer cycle

## Risks
- adding too many states may confuse users
- permissions logic may become ambiguous if owner roles are not explicit

## Scope
- Must have
  approval status label
  current owner display
  next-action indicator
- Nice to have
  approval history timeline
  notification hooks

## Acceptance Criteria
- dashboard items show approval status consistently
- owner and next step are visible at a glance
- unresolved approvals are easy to filter or identify

## Roles Needed
- Strategi Produk
- Pembina Aplikasi
- Tukang Web
- Penyemak

## Verification
Use engineering and UI/UX checklists; confirm the flow reduces support clarifications.
