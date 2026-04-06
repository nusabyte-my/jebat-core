# Acceptance Spec Example

## Change
Add approval visibility and owner state to dashboard request cards.

## Expected Outcome
Users can determine approval status and current owner without opening separate detail views or asking in chat.

## Acceptance Checks
- request cards display approval status
- request cards display current owner
- next action is visible when approval is pending
- filtered view can isolate blocked or pending items

## Risks
- inconsistent owner data in existing records
- UI crowding on smaller screens

## Non-Goals
- full audit trail
- automated reminders
- external stakeholder visibility

## Files / Systems Touched
- dashboard UI
- request status mapping logic
- permissions/ownership display rules

## Verifier
Penyemak

## Residual Risk
May still need a second iteration if approval history becomes a frequent user request.
