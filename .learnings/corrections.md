## 2026-10-01 (Erawan QPOS) — Positional booking item mapping drops units on qty > 1

**Error:** On walk-in checkouts with `qty > 1` (e.g. 2× HBS30 under invoice EAK-0000132327), only 1 item was converted to an active session; the 2nd item remained scheduled at `now + duration`, rendering as an overlapping phantom block with its own "Start Session" button.
**Cause:** `captureCheckout` and `captureMultiGuest` mapped cart lines to created `BookingItem` rows positionally via `walkinBooking.items?.[idx]`. Because the backend expands `qty` into multiple `BookingItem` rows, `itemsToCharge[0]` (qty: 2) received only `items[0]`, leaving `items[1]` completely unlinked.
**Fix (6ba19cd):** Implemented consuming-cursor mapping (`itemCursor += ci.qty`). Cart lines with `qty > 1` are left unpinned so that the start pass falls back to the existing `sourceBookingId` resolution, selecting and converting ALL items of the walk-in booking into a single consolidated session.
**Prevention:** Never use bare `items[idx]` positional mapping between shopping cart lines and database entities when cart items can carry a `qty > 1` multiplier. Consume by expansion offset or match by `(versionId, guestIndex)`.

## 2026-10-01 (Erawan QPOS) — Extra time (ET) split missed when BookingItem.extraMinutes is 0

**Error:** A completed session modal showed plain `100m` instead of `90m + 10m ( ET )` for Thai90 + 10m ET.
**Cause:** Extra time was stamped directly into the assignment window (`endsAt − startsAt = 100m`) during checkout/convert, while `BookingItem.extraMinutes` remained `0`. The summary helper inspected only `item.extraMinutes`, found 0, and fell back to the plain label.
**Fix (3037521):** The block builders now derive extra time authoritatively as `Math.max(item.extraMinutes, windowMinutes − baseMinutes)`.
**Prevention:** When legacy or operational flows store an adjustment in two places (entity column vs. planned interval difference), always derive the displayed delta from the actual window duration rather than trusting the column alone.

## 2026-09-24 (Erawan QPOS) — Scoped edit item deletion skipped by `if (!isScopedEdit)`

**Error:** In `booking-form.tsx`, front desk reported "unable to remove session n save" when editing an individual guest (e.g. `Edit Guest 2 · Enya` with 3 sessions). Removing Session 3 and saving left Session 3 in the database.
**Cause:** `handleSubmit` wrapped item deletion in `if (!isScopedEdit) { ... }`. When editing a specific guest, `isScopedEdit` is `true`, so backend item deletion was completely disabled to prevent deleting other guests' sessions from the same booking.
**Fix (1944d38):** Scoped deletion properly to the target guest (`belongsToThisTargetGuest = isScopedEdit ? (targetScopedItemIds ? targetScopedItemIds.has(it.id) : (it.guestIndex ?? 0) === (editGuestIndex ?? 0)) : true`). Sibling guests remain protected, and removed sessions on the target guest are deleted via `DELETE /bookings/:id/items/:itemId`.
**Prevention:** Never use a blanket negation `if (!isScoped)` to avoid multi-entity side effects. Scope the predicate to the entity under edit (`item.guestIndex === targetIndex` or `scopedItemIds.has(item.id)`) so removals work within the scope.
## 2026-09-21 (jebatcore) — dream-state mirror written by the engine itself

**Error:** Every tool-side `mimpi_dream` left `memory/.dream-state.json` stale — I reconciled it manually again (third time since 2026-08-18).
**Cause:** The 2026-08-18 fix made the ENGINE persist `~/.jebat/dream_state.json`, but session bootstrap reads the WORKSPACE mirror `<cwd>/memory/.dream-state.json`, which only the standalone `run_mimpi_dream.py` script wrote. Two files, one writer — the tool path had none.
**Fix (a49b7e5):** `mimpi_dream` atomically mirrors engine state (tmp + os.replace) to `<cwd>/memory/.dream-state.json` after every successful dream, cwd-derived so per-project scoping matches `project_remember`. Mirror path returned as `dream_state_mirror` in the response.
**Prevention:** When a subsystem owns state file A but consumers read file B, the write path must cover BOTH — or collapse to one canonical file. "State updated" claims need a verified writer for every file every consumer reads.

## 2026-08-20 (Erawan QPOS) — branch isolation that deletes a legitimate workflow

**Error:** after 4a67192 "branch isolation", Ave-K could no longer pull NU-S masseurs (RAT/EWM-300 report: "all those in NU Sentral not shown on the pool"). The fix filtered `helpingElsewhere` masseurs out of the roster modal + morning wizard pools — erasing the "Other Branch" tier that WAS the cross-branch pull surface.
**Cause:** the tier *looked* like a leak (other-branch names visible to branch users) but it was the read side of a sanctioned write flow: click → `check-conflict` → CrossBranchConflictDialog → `activateForBranch` moves the queue row + fires a cross_branch_activation alert. Hiding the read killed the write.
**Fix:** restored tier visibility (dac06a3); kept the actual isolation guards (filteredQueue pool-presence filter + inBranchQueue analytics gate) so other-branch masseurs still never enter queue/ranking/stats without the explicit conflict-prompted move.
**Prevention:** before filtering any list for isolation, enumerate every FEATURE that reads that list. If a legitimate flow depends on the rows, keep visibility and gate the WRITE, not the READ. Also: a commit comment claiming a workflow is "an owner concern" is a smell — verify against how the client actually operates.

---



**Error:** user reported queue-row hover still present ("still have hover effect") after the fix was verified working in local dev (DOM-verified `opacity: 1`, 16px icons).
**Cause:** fix existed only in the working tree — no commit, no push, no deploy. User was looking at PRODUCTION. Verification of a fix in local dev ≠ fix shipped. Mid-task interruptions make this drift worse (fix verified → second task arrives → deploy deferred → forgotten).
**Fix:** finished the outstanding work, committed, deployed v2.1.0.
**Prevention:** when a user reports a bug that was "already fixed", FIRST check `git status` + prod deploy state before re-debugging. The delta between local tree and prod HEAD is the first suspect.

## 2026-08-19 (Erawan QPOS) — window-only overlap checks re-pick over-run sessions

**Error:** auto-assign stacked a new session on a masseur/room whose session was still physically running but whose PLANNED `endsAt` had passed (over-run). `assignmentConflictWhere` blocks running sessions only when the candidate starts at-or-before `now` — future-start candidates fall through to the planned-window check, which an over-run session no longer satisfies.
**Fix (client directive — strict rule):** any running (`active`/`paused`) assignment on the business date excludes that masseur AND room from auto-pick entirely, regardless of the new window. Applied in `autoPickMasseur`, `autoPickRoom`, and `getFreeMasseurs` (FD alternatives list must match auto-pick truth).
**Verification discipline:** the first room test was inconclusive (picked B1 by group-priority anyway) — decisive test = put the running session in the room the picker WANTS, confirm it takes the next-best. Verified live: over-run active on Thoo/B1 → Tuay/B3; clean → Thoo/B1.
**Data check first:** `SELECT COUNT(*) FROM "Assignment" a JOIN b ... overlapping same-room pairs` = 0 in prod → rooms are de-facto 1-session-at-a-time, so the strict room rule cannot over-block.

## 2026-08-19 (Erawan QPOS) — branch isolation: 4 separate leak paths, not 1

**Discovery:** "branch sees other-branch masseurs" was 4 distinct leaks, each needing its own fix: (1) roster modal "Other Branch" tier + morning wizard amber rows (`helpingElsewhere` visible to branch users), (2) `/queue/live` global fallback when the branch has no queue rows yet (advance-date booking support) leaking into Daily Queue Order fallback + ranking + stats, (3) "Yesterday" copy fetching `daily-order` WITHOUT branchId → copies other-branch masseurs into this branch's queue, (4) `Clear` DELETE without branchId → **wipes BOTH branches' queues** (cross-branch destructive bug found en route).
**Rule:** a "scope leak" report means audit EVERY read AND write of the scoped data on the surface, not just the visible list. Writes are worse than reads — the Clear bug was silently corrupting the other branch's day.

## 2026-08-19 (tooling) — SSH heredoc scripts from PowerShell get CRLF-poisoned

**Error:** `@' ... '@ | ssh host bash` worked for pnpm but `tail -n 8` failed with "invalid number of lines: '8\r'" — PowerShell pipeline re-adds CRLF when piping a string to ssh stdin, and bash reads the literal `\r` into arguments.
**Fix:** base64-encode the script and run `echo <b64> | base64 -d | bash` — byte-exact, no line-ending translation.
**Prevention:** for any non-trivial remote script from Windows pwsh, always go base64. Also: `sudo -E env PATH=$PATH` must keep `$PATH` inside the remote shell's double quotes or `env` receives `--filter` as its binary (env-quoting bug seen same session).

---

## 2026-08-18 (Erawan QPOS) — dev+build `.next` collision & PWA SW stale UI

**Error 1:** `Runtime Error ENOENT ... .next/server/vendor-chunks/lucide-react@...js` on /masseur after running verification gates.
**Cause:** `pnpm --filter @erawan/web build` rewrote `.next/` with prod chunk hashes while `next dev` was still running — dev then requested a dev-mode chunk path the prod build had replaced.
**Fix:** stop dev (find pid via `Get-CimInstance Win32_Process` CommandLine match on `next*dev*--port*5500`) → wipe `.next` → restart dev. **Prevention:** never run the prod build while dev is live on the same checkout — sequence build FIRST, then start dev.

**Error 2:** user reported "still showing old UI" after clean recompile; served chunk verified NEW server-side.
**Cause:** Erawan web is a PWA — `public/sw.js` caches `/_next/static/*` (cache-first) under `erawan-qpos-static-vN`. Old v7 served stale chunks indefinitely.
**Fix:** bump `STATIC_CACHE` version in `sw.js` (v7→v8) — activate handler deletes old caches. **Prevention:** any UI deploy of Erawan must bump the SW cache version or returning browsers keep the old app.

---

## 2026-08-18 (jebatcore) — AutoMimpi dream state never persists (architectural gap)

**Error:** Dream cycles ran (08-17 "#17", 08-18 "#18") but `.dream-state.json` stayed at totalDreams=16 / sessionsSinceDream=15. Both sessions assumed persistence.

**Cause:** `AutoMimpi.dream()` (`jebat/features/memory/automimpi.py`) updates `last_dream_at`/`dream_count` in memory only. Grep across both workspaces: NO code writes `.dream-state.json` or `~/.jebat/dream_state.json` — they're session-convention files maintained by hand.

**Fix (interim):** manual reconcile — both files set to totalDreams=18, sessionsSinceDream=0, lastDreamAt=2026-08-18T03:20Z. Permanent fix queued: persist state inside `dream()` with the 9f4a2c2 empty-save guard pattern.

**Prevention:** When a subsystem claims "state updated", verify a WRITER exists for the state file before trusting the claim — especially after refactors. Same family as the traces.json store-clobber: claims without flushed artifacts.

---

## 2026-08-06 (Erawan QPOS) — Ranking workflow drift risk: duplicated status literals

**Error:** `SERVED_STATUSES` + `notIn: ["cancelled","no_show"]` were re-inlined across queue.service, bookings.service (×2), live-matrix, recommendations, ai-ops, dashboard-agent — any future edit to one site silently diverges the workflow between branches.

**Fix:** Centralized in `packages/core/src/index.ts`: `SERVED_STATUSES`, `COMMISSION_EXCLUDED_STATUSES`, `buildQueueCandidate`, `rankQueueCandidates`. All API consumers import from core. Grep gate: `rg -F '["active", "paused", "completed", "stopped"]' apps/api` must return nothing.

**Prevention:** When touching ranking/commission in Erawan, ALWAYS import from `@erawan/core` — never write the status array inline. The workflow (available→rotation/commission→manualOrder) is documented in AGENTS.md as ENFORCED.

---


**Error:** Avenue-K "Commission Ranking" panel showed rotation order (May RM77 #2) instead of commission order (On RM59 should be #2).

**Cause:** `completedCycles = min(servedJobsToday)` across ALL queue masseurs. Chai (queue pos 8) had 0 served (her only booking was cancelled) → `minServed=0` → `systemCycle=1` → comparator stays in cycle-1 morning-rotation mode all day, commission sorting never activates. One idle masseur pins the whole branch.

**Fix:** `completedCycles` = min over masseurs with `served > 0` only. Never-served masseurs rank first via commission (0 = lowest). Applied in queue.service.ts + bookings.service.ts (2 spots).

**Prevention:** When diagnosing "wrong ranking" in this codebase, first reproduce `systemCycle` with live DB data (min served across branch queue), then trace comparator branch. A single 0-served masseur = cycle stuck at 1 = rotation mode forever.

## 2026-08-06 (Erawan) — PowerShell `head` alias + backtick in node -e

**Error:** `| head` fails in pwsh (`head` not a cmdlet); `node -e` with backtick template literals → `SyntaxError: Expected unicode escape`.

**Fix:** Use `Select-Object -First N` or `.Substring()` in pwsh; write multi-line node simulations to a temp `.mjs` file and run `node file.mjs` instead of `node -e`.

**Prevention:** Never `node -e` multi-line scripts with template literals in pwsh. Compose to temp file.

## 2026-08-06 (Erawan) — Tesseract 2/5/9 ambiguity on receipt postcodes

**Error:** OCR read NU Sentral postcode as "90470"/"20470" at 69-94% confidence; code had 50470.

**Fix:** scipy.ndimage.label connected components + ASCII glyph projection to disambiguate. "2" = top bar + left stem + middle bar + right-sweep diagonal; "5" = top bar + left stem + middle bar + bottom-left stem (verified against known 50400 control). Also crop exact bbox + 8x upscale + digit whitelist for reliable reads.

**Prevention:** For legal/printed data (tax IDs, postcodes), verify digit-by-digit with glyph projection, not single OCR pass.

---


**Error:** `sudo -E env PATH=$PATH pnpm --filter @erawan/web build` → `env: '--filter': No such file or directory`.

**Cause:** In a non-interactive SSH command string, `$PATH` expansion + `env` interplay made `env` treat `--filter` as the program to exec. The documented `sudo -E env` incantation works interactively but not as a one-shot SSH arg.

**Fix:** `sudo -H -u root bash -lc 'export NVM_DIR=/usr/local/nvm; . /usr/local/nvm/nvm.sh; cd /opt/erawanQPOS-v2 && pnpm --filter @erawan/web build'` — `-H` resets HOME to root (pm2 lives under /root/.pm2), `bash -lc` sources the env inside a fresh login shell, and explicit nvm source puts node/pnpm on PATH.

**Prevention:** For any sudo+node+pm2 command over non-interactive SSH, use the `sudo -H -u root bash -lc '<nvm source + command>'` pattern. Never `sudo -E env PATH=$PATH pnpm` in one-shot SSH strings.

---

## 2026-08-04 (Erawan QPOS) — PowerShell backtick mangling in inline SQL

**Error:** `ParserError: The Unicode escape sequence is not valid` when running inline psql through a double-quoted PowerShell string containing backtick-escaped SQL identifiers.

**Cause:** Backtick is PowerShell's escape character. `\`id\`` style escaping from bash habits doesn't survive PowerShell parsing.

**Fix:** Build the SQL in a PowerShell here-string (no backticks), write via `[System.IO.File]::WriteAllText(temp, sql, [System.Text.UTF8Encoding]::new($false))` (LF, no BOM), pipe with `Get-Content -Raw temp | ssh ... "docker exec -i erawanqpos-postgres-1 psql -U erawan -d erawan_qsys"`.

**Prevention:** Never inline psql through pwsh→ssh. Always compose SQL to a temp file with LF endings, pipe via stdin. Same class as the earlier quote-nesting hell — compose locally, pipe remotely.

---

## 2026-08-04 (Erawan QPOS) — Wrong schema assumptions in ad-hoc SQL

**Error:** Queries referenced `b.code` (Booking), `RoomItem`, `a.bookingItemId` — all nonexistent.

**Cause:** Assumed Booking had a display code and that RoomItem was the sub-slot table, based on UI labels ("A1 — Slot 1"). Actual schema: Booking has NO code (join Customer for name), slots are `SubRoom`, `preferredTime`/`roomId`/`assignmentId` are on `BookingItem` (not Booking), and the FK from BookingItem→Assignment is `bi.assignmentId = a.id`.

**Fix:** Grepped `packages/db/prisma/schema.prisma` for the actual model blocks before rewriting the query.

**Prevention:** Before ad-hoc SQL on this schema, read the Prisma model blocks for Booking/BookingItem/SubRoom/Assignment. Don't trust UI labels or AGENTS.md prose for column names — verify from schema.prisma.

---

## 2026-08-02 (Erawan QPOS) — Prisma inferred-type TS2339 on subRooms

**Error:** `pnpm --filter @erawan/api build` failed: TS2339 Property 'subRooms' does not exist on inferred room type in bookings.service.ts available-rooms map.

**Cause:** `/rooms/analytics` returned subRooms in the API response but the service-side inferred type didn't know about the opt-in relation array.

**Fix:** Cast `(room as any).subRooms ?? []`, committed as `d8914e7` (separate from the feature commit).

**Prevention:** When adding an opt-in nested relation to an API response, expect a TS2339 on the inferred type at every usage site; cast or extend the DTO explicitly.

---

## 2026-08-01 (Erawan QPOS) — 400 Bad Request on convert-consolidated

**Error:** `400 Bad Request` when calling `/bookings/:id/convert-consolidated` with `startAt` in body.

**Cause:** `ConsolidatedConvertDto` did not declare `startAt` field. NestJS `forbidNonWhitelisted: true` rejected the unknown param.

**Fix:** Added `startAt?: string` to `ConsolidatedConvertDto`.

**Prevention:** Before adding any new field to a frontend request body, grep the backend DTO file for that param name. If missing, add it to the DTO first.

---

## 2026-08-01 (Erawan QPOS) — Material Symbols icons showing as text

**Error:** Checkbox in POS showed literal text "check" instead of an icon.

**Cause:** `<span className="material-symbols-outlined">check</span>` requires Google Material Symbols font loaded via CSS import. Font was never imported in the app.

**Fix:** Replaced all 3 instances with `<Check className="text-white" size={12} strokeWidth={3} />` from lucide-react (already bundled).

**Prevention:** Never use web font icons (Material Symbols, Font Awesome) unless the font is explicitly loaded. Prefer bundled icon libraries (Lucide, Heroicons).

---

## 2026-07-26 (Norman R2) — usePathname hydration mismatch in fixed nav

**Error:** `Hydration failed … <div> vs <Suspense>` at StickyMobileCta.

**Cause:** First attempt fixed pathname-mismatch with `mounted` + `return null` — server then rendered nothing while client rendered nav. Worse divergence.

**Fix:** Removed `usePathname()` + active-class branching entirely from the component. Render identical tree on server/client; style active state via CSS only if needed.

**Prevention:** In fixed-position client components under App Router SSR, avoid any hook/state that differs server→client at first paint. Prefer CSS `aria-current` or `data-*` selectors for active styling.

---

## 2026-07-26 (Norman R2) — SW serves deleted chunk

**Error:** `Module … FloatingMenu.tsx … module factory is not available` after deleting component.

**Cause:** PWA service worker kept cached JS chunk referencing deleted module.

**Fix:** Bump `CACHE` name (`nmr-static-v1` → `v2`) in `public/sw.js` on every structural deploy; instruct user hard-refresh / unregister SW.

**Prevention:** Treat SW cache name as deploy version. Any component deletion/route change = bump.

---

## 2026-07-26 (Norman R2) — Anchor link to wrong section id

**Error:** Bottom nav "Testimoni" link `/#testimoni` did nothing.

**Cause:** Section component used `id="ulasan"`, not `testimoni`. IDs drifted during copy iterations.

**Fix:** Point nav to `/#ulasan`.

**Prevention:** Grep `id="` in section components before wiring anchor nav; or centralize section IDs as constants.

---

## 2026-07-26 (Norman R2) — Generic maps embed

**Error:** Iframe showed area map, not business pin.

**Cause:** Used `/maps?q=<address>&output=embed` — query embed lacks place identity.

**Fix:** Use `/maps/embed?pb=…` with encoded place params (place id hex from share URL, e.g. `0x50a41c15e51348a1`).

---

## 2026-07-26 (Norman) — Deployed empty main branch

**Error:** VPS `git clone` got only LICENSE/README; `npm ci` failed (no lock).

**Cause:** GitHub default branch `main` was old placeholder; full app pushed only to `master`.

**Fix:** `git push --force origin master:main` so HEAD/main == app; redeploy from `main`.

**Prevention:** After first push, set default branch or always push both; `git ls-remote origin HEAD` before deploy.

---

## 2026-07-26 (Norman) — Lucide Instagram missing

**Error:** Build failed — `Export Instagram doesn't exist`.

**Cause:** lucide-react version without brand icon export.

**Fix:** Use `Camera` for IG, keep `Music2` for TikTok.

---

## 2026-07-26 (Norman) — better-sqlite3 native build fail

**Error:** node-gyp / no Visual Studio on Windows.

**Cause:** Native module.

**Fix:** File-based CMS (`content.json`).

---
# Corrections Log

Errors made, why, and how fixed. Newest first.

## 2026-07-26 (S2) â€” POS modal inserted into wrong component scope

**Error:** Added `<BusyMasseurModal>` at end of POS page JSX, but the `return (` I targeted belonged to `CheckoutStatusOverlay` sub-component (defined later in same file), not `PosPage`. Typecheck: `Cannot find name 'busyModal'` at the modal JSX.

**Cause:** POS page is 5000+ lines with multiple sub-components (`CheckoutStatusOverlay`, `ReceiptModal`, `_Card`, `_InsightRow`) defined in the same file. The closing `);}` I matched was not `PosPage`'s â€” it was an inner component's. State vars (`busyModal`, `masseurs`, `setAssignMasseur`) only exist in `PosPage` scope.

**Fix:** Found actual `PosPage` return-close by searching `^  \);$` at 2-space indent + verifying next line was `function _Card(` (the first sub-component after PosPage). Moved modal JSX before that boundary.

**Prevention:** In monolith files with multiple component definitions, never assume a closing `);}` is the outer component's. Verify by checking what function/component follows it. Search for `^export default function` / `^function ` to map the structure first.

---

## 2026-07-26 (S2) â€” Stray ternary tail after refactor

**Error:** After replacing the `masseurReassigned` ternary block in `convertConsolidated` with a flat `const assignedMasseurName: string | null = null;`, a leftover `: null;` line remained. Typecheck: `TS1128: Declaration or statement expected`.

**Cause:** The old code was a multi-line ternary:
```
const assignedMasseurName = masseurReassigned
  ? (await ...)?.name ?? null
  : null;
```
My oldString match ended at `?? null` (the true-branch), leaving the `: null;` false-branch orphaned.

**Fix:** Removed the stray `: null;` line.

**Prevention:** When replacing ternary expressions, match the FULL ternary including the false-branch (`: ...`). Don't end oldString mid-expression. Read 5-10 lines past the edit point to catch dangling tails.

---

## 2026-07-26 â€” Prisma include on non-existent relation (500)

**Error:** Added `masseur: { select: { id: true, name: true } }` to `BOOKING_ITEM_INCLUDE` in `bookings.service.ts`. Every `/bookings` endpoint returned 500.

**Cause:** `BookingItem` Prisma model has `masseurId String?` scalar FK but NO `masseur Masseur @relation(...)` field defined. Prisma rejects includes on non-existent relations.

**Fix:** Reverted the include. Resolved masseur name client-side instead â€” POS `useEffect` backfills `masseurName` from the `/queue/live` masseurs list using `masseurId`.

**Prevention:** Always check Prisma schema for the actual relation field before adding includes. Scalar FK (`masseurId`) â‰  relation (`masseur`). If no `@relation` exists, Prisma include is impossible without a migration.

---

## 2026-07-26 â€” pm2 "online" but process dead (wrong interpreter)

**Error:** After `pm2 restart erawan-api-v2`, pm2 reported "online" but port 4001 not listening. PID showed N/A, mem 0b.

**Cause:** pm2 process config had `exec_interpreter: 'node'` (bare). Node installed via nvm at `/usr/local/nvm/versions/node/v20.20.2/bin/node` â€” not in sudo's `$PATH`. pm2 couldn't spawn the process but reported "online" anyway.

**Fix:** Delete + recreate with `--interpreter /usr/local/nvm/versions/node/v20.20.2/bin/node`. `pm2 save` to persist.

**Prevention:** Always verify with `curl` or `ss -tlnp` after pm2 restart â€” never trust `pm2 status` alone. When using nvm, always pass the full node path as `--interpreter`.

---

## 2026-07-26 â€” Modal state not persisted before navigation

**Error:** FD selected masseur in booking modal â†’ clicked "Pay & Start" â†’ POS cart showed "Unassigned".

**Cause:** The unpaid "Pay & Start" button called `router.push('/pos?bookingId=...')` directly. Modal's `masseurId` state lived only in React state â€” never PATCHed to DB. POS builds cart from DB (`GET /bookings/:id`), so saw null masseurId.

**Fix:** New `persistSelectionAndGoToPos` callback â€” PATCHes booking items with `{masseurId, roomId}` before `router.push`.

**Prevention:** Any modal that edits DB-backed data and then navigates away MUST persist changes before navigation. React state is ephemeral; the destination page reads from the server, not from the source page's state.

---

## 2026-07-30 — PowerShell eats remote shell $( ) and $var escapes over SSH

**Error:** `ssh root@host "JWT_SECRET=$(openssl rand -hex 32)"` → `openssl: The term 'openssl' is not recognized` — PowerShell evaluated `$(...)` LOCALLY before SSH ever saw it.

**Fix:** Build the secret locally in PowerShell, then pipe the finished content: `$secret = -join (...); "...$secret..." | ssh root@host "cat > /path/.env"`.

**Prevention:** Never use `$(...)` or `$var` inside double-quoted SSH command strings in PowerShell — they expand locally. Escape with backtick, or compose content locally and pipe via stdin. Same class of bug as the SQL-quote-nesting issue: compose-locally + pipe beats inline quoting.

---

## 2026-07-30 — sed edit avoided by runtime flag (better pattern)

**Error:** sed replace of package.json start path → `unterminated 's' command` (slashes in path confused delimiter even with alternate delimiter).

**Fix:** Skipped sed entirely — `pm2 start dist/src/main.js` passes the explicit path at runtime. No file edit needed.

**Prevention:** When sed gets fiddly, step back: pm2/nginx/systemd all accept explicit paths/flags. Edit files only when no runtime flag exists.

---

## 2026-07-30 — pnpm 11 blocks native builds without approval

**Error:** `pnpm install` on fresh VPS → `[ERR_PNPM_IGNORED_BUILDS]` for @prisma/client, bcrypt, prisma, @nestjs/core. Postinstall scripts silently skipped.

**Fix:** `pnpm approve-builds --all` then `pnpm rebuild`. Prisma generate worked after.

**Prevention:** pnpm 11+ on fresh machines always needs `approve-builds` before native modules (bcrypt, prisma engines) work. Add to deploy scripts for new VPS setups.

## 2026-08-04 — ALAND Excel verification error

**Wrong:** Trusted explore-subagent's structured extraction of GDV & GDC v2 sheet. Subagent reported "H306=K84 (gross GDV), H307=L84 (nett GDV)" implying split-base B8. Built whole fix + report on that. Wrong.

**Right:** Direct openpyxl check revealed H306='=L84' — NETT GDV. All three workbooks (v1 Landed, v2 Landed, HR) agree: every B8 percentage fee uses nett GDV. Engine was already correct.

**Fix:** Verify cell references directly with openpyxl before reporting on Excel structure. Subagent extractions of large cell ranges can transpose/misattribute formulas. Parity tests (workbookParity.test.ts) caught the regression immediately — the test suite was the real safety net.

**Reusable rule:** When an Excel verification contradicts an existing passing parity test, re-verify the Excel read before touching the engine. The test is likelier right than the fresh read.

---

## 2026-08-10 - Erawan prod server topology: 72.60.42.163 is ACTIVE, not refused

**Wrong (carried in AGENTS.md/MEMORY.md since 2026-07-14):** "72.60.42.163 refused as of 2026-07-14" — treated as a dead legacy IP.

**Right:** That IPv4 lives on the SAME active prod box (host `erawanhq`, Hostinger, dual-stack). `ip -4 addr` shows `inet 72.60.42.163/24 scope global eth0` alongside the IPv6 `2a02:4780:5e:20bd::1`. DNS A-record for `qpos.erawanwellness.com` → `72.60.42.163` and it serves the latest code. The 2026-07-14 "refused" observation was likely a transient network/DNS state, not a topology change.

**Fix:** AGENTS.md table + gotcha #4 updated to dual-stack framing (IPv6 primary for SSH `-6`, IPv4 for DNS/web). MEMORY.md Erawan entry corrected.

**Reusable rule:** Before declaring an IP dead, verify against the live box's interfaces (`ip addr`) and DNS — an IP can be reachable-but-slow or transiently-blocked, and mislabeled topology propagates into every future deploy session.

---

## 2026-08-10 - Erawan nginx: /uploads/ was never proxied to the API (latent avatar bug)

**Error:** Receipt logo upload worked (file written, branding saved) but the served URL 404'd. Root cause: nginx had NO `location /uploads/` — the path fell through to the web server (port 5501), which has no such assets. The API writes uploads to `process.cwd()/uploads` (= `apps/api/uploads` under pm2) and serves them static, but nginx never routed `/uploads/*` to the API.

**Also:** masseur avatars (`uploads/masseurs`) had the SAME latent defect — no avatar files existed yet so it never surfaced.

**Fix:** added `location /uploads/ { proxy_pass http://127.0.0.1:4001; proxy_cache_valid 200 1d; }` to the prod nginx config. Verified uploaded receipt logo serves 200 image/png.

**Reusable rule:** when adding an upload feature to this stack, the nginx routing is a separate deployment step — `/uploads/` must point at the API (4001), not the web server. Grep the prod nginx config for the asset prefix before declaring an upload feature done. Also: `cmd | tail -3` in a remote SSH deploy chain MASKS the exit code — a failed `next build` still let `pm2 restart` run with a stale build. Capture exit codes explicitly (`cmd; echo EXIT=True`) or chain with real conditionals.

---

## 2026-08-10 - autoMimpi zero patterns = tag problem, not content problem

**Wrong assumption:** "autoMimpi extracted 0 patterns" meant the store had no signal. Actually the store was stale (21 traces, none from today) AND freshly-remembered facts were saved with EMPTY tags — _extract_patterns groups by tag, so untagged traces never even enter a group. Only after _load reconstruction do file-traces carry tags (category:gotcha, project:Erawan-QSys).

**Fix:** always pass 	ags_set when calling EnhancedMemorySystem.remember() — pattern extraction is tag-group-driven. Tag discipline = pattern yield.

**Also discovered (2 real bugs in the memory system):**
1. EnhancedMemorySystem._save swallows exceptions (xcept Exception: print) — a trace whose memory_type is a string (pass 'semantic' instead of MemoryType.SEMANTIC) crashes 	o_dict at .value and the ENTIRE save silently no-ops. Traces lost without error.
2. 
emember(memory_type=...) accepts a string but MemoryTrace.to_dict does self.memory_type.value — string input is not normalized. Must pass the enum.

**Reusable rule:** pass enums + tags explicitly when writing to the memory system; verify persistence by reloading (in-memory save success is not proof).

## 2026-08-10 (Erawan QPOS) - computeNextSubRoom misses completed assignments + nested sudo pm2

**Error 1:** Missed-key batch put Lee AND Lisa both on A1a. computeNextSubRoom uses assignmentConflictWhere which only counts BUSY statuses (scheduled/recommended/confirmed/active/paused) - future scheduling semantics. Missed-key assignments are COMPLETED, so the second same-room entry never saw the first as occupying the bed. Worse: A1a was ACTUALLY occupied by Thiam Foot45 (11:51-13:05 UTC) overlapping the 12:34 window, so neither entry deserved A1a.

**Fix:** Inline sub-room pick in missedKey with the wider status set [scheduled..completed] + true window overlap (startsAt < endsAt && endsAt > startsAt). Corrected prod data to A1b (Lee) / A1c (Lisa).

**Prevention:** When a helper is built for FUTURE scheduling (busy statuses only), never reuse it for retroactive/backfill paths where completed records are the norm. The duplicate guard hit the SAME trap (assignmentConflictWhere excludes completed) and was fixed the same way.

**Error 2:** sudo -H -u root bash -lc '... sudo -H -u root env PATH=\ pm2 restart ...' -> nv: 'restart': No such file or directory. Nested sudo+env+pm2 inside bash -lc breaks.

**Fix:** pm2 restart as its own top-level SSH command: ssh ... "sudo -H -u root bash -lc 'export NVM_DIR=...; . nvm.sh; pm2 restart X'".

**Prevention:** One sudo layer per command. Builds in one bash -lc, pm2 restart in a separate call.

## 2026-08-11 (Karya Web-Builder) — Phase 0 blast: 5 blockers killed + quickwins

**Error (pre-existing, never shipped as functional):** Karya (src/ of Web-Builder) was an early prototype that could not run end-to-end: no React Context (every useEditor() call got its own state copy → addElement never reached canvas, selection never reached properties panel, localStorage writes clobbered each other), canvas.tsx referenced undefined handleDrop/handleDragOver (ReferenceError on /editor mount), sidebar.tsx used React.* without import, tsc failed on ~30 unused imports (noUnusedLocals), routing resolved pages by projectId, and public/index.html (stale, referencing /src/main.tsx) would overwrite the built index.html in dist → prod build served no JS.

**Fix:** Rewrote src/hooks/useEditor.ts → useEditor.tsx as EditorProvider + useEditor() context consumer (single store). Route param is now resolved via selectProject(projectId) + setCurrentPage(pageId) instead of page-by-URL. Fixed drag/drop in store. Cleaned all unused. Deleted $null, nul, public/index.html. Installed tailwindcss-animate (referenced but never installed). Renamed .ts→.tsx because JSX in .ts fails TS1005.

**Prevention (reusable):**
1. Before any UI polish, grep for createContext/Provider — a "context API" claim in README is not proof it exists (SETUP_SUMMARY claimed Context API; grep returned 0).
2. public/ files are copied into dist AFTER build — a stale public/index.html silently nukes the production bundle. Never keep an index.html in public/ for a Vite SPA.
3. Lucide-react version drift: v0.400 lacks Paste/DistributeHorizontal/DistributeVertical — use Clipboard/ArrowLeftRight/ArrowUpDown (always check exports before importing).
4. react-colorful v5 API is onChange, not onColorChange.
5. Canvas info badges (element name/lock) need pointer-events-none — they were intercepting clicks on the element.
6. updateElementStyle replaced the whole style object (spread merge needed) — properties panel edits were wiping sibling style props.

**Discovery:** playwright-python + system Chrome (executable_path) = zero-download headless UI verification loop on Windows. Verified: sidebar add → canvas render → select → properties panel edit → canvas update, zero page errors; dark mode persists; AlertDialog delete renders. Great pre-deploy smoke test.

## 2026-08-11 (Karya) — StrictMode localStorage clobber class bug

**Error:** After wiring real BYOK, reloading the app silently reset BYOK to disabled despite stored keys. Root cause: the byok save effect `useEffect(() => localStorage.setItem(...), [byokConfig])` runs on the first commit with the DEFAULT config. React 18 StrictMode double-invokes mount effects, so the second init read saw the freshly-clobbered default → loaded bad state.

**Fix:** hydration must be STATE batched with the loaded value: `byokHydrated` set in the same render cycle as `setByokConfig(loaded)`; save effect skips until `byokHydrated`. A ref set inside the init effect does NOT work — sibling effects in the same commit still run after it and see the ref as already-true.

**Reusable rule:** any load-then-autosave localStorage pattern must gate the save on a hydration state batched with the load (or use a "skip first N runs" ref keyed on the loaded data), or StrictMode will clobber stored data on every mount.

**Second rule:** async fetches in UI need hard timeouts — a hanging provider fetch left isGenerating stuck true forever (button disabled with spinner). AbortController 15s on the direct-call path.

## 2026-08-11 (ALAND) - B5 bucket total propagates preliminaries: test must model ×(1+pct)

**Error:** New parity test asserted construction bucket delta = (500-120) x GFA, ignoring preliminaries. Engine returned 2,052,000 vs expected 1,900,000 (diff = 152,000 = exactly 0.08 = preliminariesPct).

**Fix:** expectedDelta = rateDelta x GFA x (1 + preliminariesPct), preliminariesPct read from baseline construction.

**Reusable rule:** in this engine, B5 bucket total = subTotal + preliminaries (pct of subTotal). ANY delta assertion against a bucket amount that contains a pct-of-subtotal line must multiply by (1+pct). Grep the bucket's line list before writing delta expectations.

**Discovery:** Start-Process on Windows can't launch pnpm directly (npm shim = not a Win32 app, "%1 is not a valid Win32 application"). Use cmd.exe /c "pnpm dev > log 2> err" with WindowStyle Hidden for background dev stack. Frontend :5175 binds ~5s, backend :3001 takes ~15-25s (tsx watch + dotenvx env injection).

## 2026-08-11 (ALAND) - Live-verify found pre-existing NaN class: legacy persisted inputs vs newer schema

**Error:** Stored study 3 (saved before ancillary qty fields existed) had `construction.ancillary` missing guardHouseUnits/refuseCompartmentUnits/managementOfficeSF/clubHouseSF. Engine: `undefined * undefined = NaN` → construction.total NaN → gdc.total NaN → B5 bucket header rendered "RM 0" (fmtRM non-finite guard). gdc.total NaN poisons every downstream ratio.

**Detection path (reusable):** B5 bucket header showed "RM 0" while rows showed real amounts — a NaN smell, not a zero. fmtRM's `Number.isFinite` guard converts NaN → "RM 0", masking the true state. When a total looks suspiciously 0, probe the engine result directly (ran `calculate` on the stored inputsJson via tsx) — lines were fine, bucket amount NaN.

**Fix:** module-level `num(v)` = finite-number-or-0, applied to every runtime numeric in construction.ts (both modes): ancillary products, per-acre rates, HR psf terms, gfaShareSF. Never NaN from missing input again.

**Reusable rule:** persisted study JSON is canonical (no load-time defaults merge — unit type ids are regenerated per getDefaults() call, blind merge would clobber them). Therefore the ENGINE is the last line of defense against schema drift: any arithmetic over persisted input fields should coalesce. Same class of bug will lurk in other engines — audit other bucket files for bare `a.x * b.y` over persisted data.

**Other learnings:**
- Browser requests favicon.ico for EVERY origin it visits. A missing `<link rel="icon">` = 1 console 404 per origin. Frontend index.html now declares /icons/icon.svg. Backend origin 404 is dev-only noise (no HTML there).
- Playwright console errors carry `m.location.url` — filter to the app origin before treating them as failures; cross-origin noise (API favicon) pollutes otherwise-clean pages.
- Verify scripts that edit real study rows leave DB residue — always reset the study data after a UI verification run.
- `git diff` on this box invokes a pager and returns empty in non-interactive shells: use `git --no-pager diff`.


## 2026-08-11 (ALAND) - NaN class was systemic; fixed at engine choke point with schema backfill

**Discovery:** the "missing ancillary field" NaN was not one bug — ALL stored studies NaN'd in the marketing bucket (missing `*PctOfNettGDV` fields). Any study saved before any schema addition NaN'd somewhere. Per-file num() sprinkling would have been 80+ edits; the systemic fix is a schema-aware numeric backfill at calculate() entry (walk defaults shape → missing numeric leaf = 0). Arrays skipped (historical element shapes) — those need num() at the use site.

**Architecture rule (reusable):** for persisted-JSON-fed engines, protect arithmetic in ONE of two places:
1. A schema backfill at the engine entry (catches missing top-level/nested numeric leaves) — systemic, protects every consumer.
2. num() at the use site (catches array-element gaps the backfill can't reach).
Doing both = belt + suspenders with clear division of labor. And: never mutate the caller's object — clone first (structuredClone) or React state corrupts silently.

**Semantic decision:** missing numeric = 0 ("absent = zero contribution"), NOT rebase to workbook default. Rebasing silently changes historical studies' economics whenever defaults change — 0 is safe and predictable. Document this so nobody "fixes" it to defaults later.

**Verification discipline:** probe ALL stored studies through the real engine (not just defaults) — that's how the systemic nature surfaced (3/3 NaN). Tests lock the classes (backfill, no-mutation, array gap).

**Smoke lesson:** `page.locator("main")` hits 2 elements (app shell + tabpanel role=main) — strict mode violation. Target `#group-panel-<id>` for group content.


## 2026-08-11 (ALAND) - NaN-era residue in derived DB columns + export verification discipline

**Finding:** the NaN engine bug left permanent residue: studies 1 + 3 had the literal STRING "NaN" in the numeric `profitPercent` column (saved during the NaN era). Dashboard rendered "NaN" margins even after the engine was fixed — code fixes don't retroactively repair stored derived data.

**Fix:** recompute derived metrics (nettGDVMillions, profitPercent) from the engine on all stored studies and UPDATE the columns. Reversible (old values known), source-authoritative.

**Reusable rule:** after fixing a NaN/computation bug, ALWAYS audit derived/stored columns for residue (string "NaN" in a numeric column is the tell) and recompute from the fixed engine. Also verify every surface consuming the fixed path — not just the code path: exports (xlsx/md/pdf) + dashboard cards.

**Scan discipline:** when grepping for NaN in exported content, case-insensitive /NaN/ false-positives on "Financial"/"Governance"/"Finance" — use strict token regex or exact "NaN"/#NUM!/Infinity/undefined, and treat sheet cell scans separately from raw text.


## 2026-08-12 (Erawan QPOS) — Stale active assignment from a PREVIOUS day blocks assignment forever

**Error:** `assignmentConflictWhere` matched on status+window only, no `businessDate`. A stale `active` assignment (session ran, never Completed/Stopped) from a previous business day matched the "running blocks now" branch for every later window → FD cannot pin the therapist (masseur_busy), POS drops the pin, auto-pick silently assigns the next therapist. Live queue showed "free" (date-scoped) while the pinned check said "busy" — split-brain between two consumers of the same rule.

**Fix:** `assignmentConflictWhere` derives `businessDate` from candidate `startsAt` (MYT) unless caller passes explicit `extra.businessDate`. One helper = all call sites fixed. Also scoped missedKey dup guard + sub-room pick to entry businessDate. Closed the stale row (completed — commission credited).

**Prevention:** When diagnosing "therapist free in queue but can't assign", first query `Assignment WHERE status IN ('active','paused') AND businessDate < today`. Any row found = the blocker. There is NO auto-sweeper; consider one (nightly: close stale running rows, completed if commission exists else stopped). Any new availability/conflict query must scope by businessDate — recommendations.service already did, the helper now enforces it by default.

---

## 2026-08-19 (WiraSiber) — "stale SW chunk 404" was actually maldet quarantine + CF-cached 404

**Error:** blank page on wirasiber.my; console showed classic stale-SW-chunk-404 pattern (old SW v4.0.0 + 404 entry chunk + new SW install). Two days of debugging prior sessions attributed similar issues to SW cache discipline.

**Cause (3 layers):** (1) maldet nightly scan quarantined the live entry chunk + src/constants.ts as `{HEX}php.generic.globals.503` false positive — minified React bundles trigger ClamAV HEX sigs. (2) nginx bare `try_files =404` + CF aggressive caching = the 404 got edge-cached for 24h, so even after rebuilding the chunk, browsers still received HIT-404 (curl got 200 — different cache-key variant by Accept-Encoding). (3) The user's stale SW was downstream noise.

**Fix:** maldet ignore_paths for app dirs + ignore_sigs for the two HEX sigs; rebuild; CF purge_everything; nginx error_page 404 → asset-404.html with `no-store` so CF can never cache an asset 404 again.

**Prevention:** on shared VPS .65 — "asset vanished after deploy" or "file deleted from disk with no git explanation" → check `tail /usr/local/maldetect/event_log` FIRST before blaming git/worktrees. And any nginx `try_files =404` location serving immutable assets must attach a no-store error page. Single-URL CF purges can miss cache variants — purge_everything on small zones.

---

## 2026-08-19 (WiraSiber) — shipped UI changes without SW VERSION bump (own project rule)

**Error:** commit c98f9da (About story rewrite) touched src/components/AboutGame.tsx — UI-affecting code — and shipped to prod WITHOUT bumping sw.js VERSION. The project's enforced rule (from 2026-08-06, memory) is: any JS/CSS/UI deploy must bump SW VERSION or returning browsers keep serving the old app shell via the cache-first SW.

**Why it slipped:** the story rewrite felt like "content only," so the SW-bump mental trigger (visual/JS change) didn't fire. But AboutGame.tsx is a code-split lazy chunk — content edits ARE chunk-hash changes.

**Fix:** SW v5.0.5 (74766ae), deployed + live-verified same session. Caught by skeptical todo-review during the continuation pass, not by a gate.

**Prevention:** on WiraSiber, ANY commit touching src/** or index.html must include the sw.js VERSION bump in the SAME commit. Candidate future gate: pre-deploy check that diffs public/sw.js when src/ changed. Same class as Erawan/Norman SW-cache lessons — third project, same trap.

---

## 2026-08-19 (WiraSiber) — "deployed" art wasn't on the SPA surfaces

**Error:** after shipping AI-generated art (837544c), user reported "live site still showing old build". Verified server/edge current — but I had only wired the art into the STATIC /about page. The SPA (landing panorama, About overlay) still used CSS/SVG art; app bundle unchanged since 3.0.2. Half a deploy reads as a failed one.

**Fix:** <picture> wiring in LandingPage.tsx + AboutGame.tsx (551be31), app 3.0.3 + SW v5.0.7, Playwright-verified both SPA surfaces render the webp.

**Prevention:** when replacing a visual asset, enumerate EVERY consumer first (SPA components, static generated pages, og:image tags, emails) — grep the old filename across src/ + scripts/ before declaring done. "Verified on one surface" ≠ "deployed".

---

## 2026-08-21 (evolvepayboost-web) — SMTP failure code 5527 was Stalwart, not Hostinger; and settings need a reload action

**Error:** app SMTP failed (`5527` wrapping `535 5.7.8 Authentication credentials invalid`, then `501 5.5.4 You are not allowed to send from this address`). I initially diagnosed it as a Hostinger SMTP credential problem and drafted a SendGrid migration + reset-password advice. Wrong on both counts.

**Why it slipped:** `mail.evolveplayboost.com` looks like a hosting-provider mail host. It actually resolves to our own VPS (72.62.254.65) — the mail server is Stalwart v0.16.14 in Docker. Diagnosis-by-assumption instead of `dig MX` + comparing the IP against our own infrastructure. The 501 was Stalwart's `mustMatchSender` default, and the first auth fix only appeared broken because **Stalwart v0.16 settings changes do not apply until `stalwart-cli create Action/ReloadSettings` is run** — I applied a correct patch, tested, saw it "fail", and nearly reverted to an unconditional (insecure) open setting before discovering the reload action.

**Fix:** scoped `mustMatchSender` expression (noreply@ may send From any local-domain address), then `Action/ReloadSettings` — verified live. Second-stage fix: outbound mail to Gmail landed in spam because Stalwart delivered over IPv6 while SPF `v=spf1 mx -all` has no AAAA coverage — pinned `MtaConnectionStrategy.sourceIps` to 72.62.254.65 + `MtaRoute.ipLookupStrategy=v4Only` + reload.

**Prevention:** (1) before debugging any SMTP host, `dig MX <domain>` + `dig A` and compare against our own VPS IPs — self-hosted MTAs are common in this stack. (2) After ANY Stalwart settings change, always run `Action/ReloadSettings` before testing. (3) When a correct-looking config change ""doesn't work"", suspect a reload/propagation step before rewriting the config. (4) SMTP spam right after an auth fix on a dual-stack VPS: check which IP family the outbound connection used (Gmail greeting reveals it) against SPF coverage.

---

## 2026-08-23 (Jentayu) — "state updated" claims need an import audit, not just a writer check

**Error:** /api/accounts/refresh-tokens referenced decryptToken without importing it — typechecked nowhere because the engine package had NO typescript devDep and NO tsconfig.json. Would have crashed at runtime on first real refresh, months after ship.
**Fix:** added tsconfig.json to apps/beduk + typescript/@types/bun devDeps; import fixed; whole-engine typecheck now runs and surfaced 7 more strictness bugs (unguarded array destructures, unsafe RowList casts).
**Prevention:** new Bun workspace = create its own tsconfig.json extending root BEFORE first commit; run un x --bun tsc --noEmit as a gate (plain un x tsc resolves through Node and lies). Extends the 2026-08-18 rule: claims about subsystem behavior need a verifiable artifact — here the artifact is a green typecheck.

## 2026-08-24 (Erawan-QSys) - trace seed dedup: category-word marker falsely drops real traces

**Error:** write seed `run_mimpi_erawan_20260824.py` borrowed the dedup from `run_mimpi_update.py` - `existing` was built from `content.split("]")[0]` and match tested `marker in e` where `marker` was just the bare category word ("gotcha"/"command"/"feature"). Prose traces that mention "gotcha" (no clean [tag] prefix) made `any(marker in e)` True, so 3 of 6 real today-traces were silently SKIPped on first run.
**Fix:** exact-match dedup (`t.content.strip() in existing`), re-ran -> 3 missing landed (126 traces total, dream_count 31).
**Prevention:** seed dedup must key on the FULL content (or a hash), never a substring category word. Verify the seed added-count matches the intended trace count before trusting the dream; a +3 of +6 is a red flag. Same class as the 2026-08-23 rule: an import-audit, not a writer-check.

Also discovered (Erawan 2026-08-24): the PrintReceiptModal "Ticket" button was printing NOTHING - it passed the limited `onCaptured` receipt (no masseurId/roomCode) to `openTherapistTicketWindow`, which filtered `i.masseurName||i.roomCode` -> empty serviceItems -> returned early. Only the standalone ReceiptModal (rich receipt) actually printed. Lesson: verify a print path's receipt carries the fields the renderer reads before assuming the button works.

## 2026-08-24 — serambi tiffin: WhatsApp OTP → session JWT
- Wrong: OTP verification returned success only; existing customers then hit protected payment endpoints with no Authorization header and failed.
- Fixed: verify-otp signs the standard { id, role, phone } JWT (config.jwtSecret, 7d) after exact phone lookup; unknown phones keep plain payload. Frontend api.ts/EnhancedAuth already consumed token+user.
- Pattern: verify the full cross-layer contract (route → middleware JWT claims → frontend consumer) before declaring a payment auth bug fixed; mutation-check regression tests (red without fix, green with).

## 2026-08-29 (Erawan-QSys) — formatRMAligned nbsp leak, PinPadModal stale re-verify, tax invoice numbering reform

### 1. formatRMAligned pads with nbsp — never use for inline prose
**Error**: in "@ RM X per session" hint I called `formatRMAligned(item.unitPriceCents).trim()` thinking `.trim()` would strip padding. `formatRMAligned` returns `\u00A0RM\u00A0\u00A0\u00A0115.46` (9-char monospace pad) — `\u00A0` (nbsp) is NOT stripped by `.trim()` (only ASCII whitespace). Result: `@ RM   115.46` with multiple nbsp spaces visible in POS cart.
**Fix**: use `(cents/100).toFixed(2)` for inline prose hints (single space, no padding). `formatRMAligned` is for FIXED-WIDTH MONO COLUMNS only (thermal receipt right-aligned amounts). Never reuse for inline HTML.
**Prevention**: when a format helper produces a monospace-aligned string for a specific context (thermal column alignment), don't reuse it in a different context (inline prose) even after `.trim()` — the padding character may not be ASCII whitespace. Use a plain formatter or hand-roll.

### 2. PinPadModal stale-PIN re-verify after close — the real queue lock bug
**Error**: FD reported "unable to lock queue back after unlock." I shipped TWO wrong fixes (lock button styling, close button disable) before finding the root cause. The PinPadModal stays MOUNTED when `open=false` (returns null at render but React hooks still execute). After unlock, the full PIN remained in the modal's `input` state. The auto-verify effect depended on `onVerify` (a prop the parent recreates every render — 30s auto-refresh, SSE, toasts). Each re-render re-fired the verify effect with the stale PIN → hash matched → `setQueueLocked(false)` → silently re-unlocked the queue, reverting the FD's relock attempt.
**Fix**: (1) clear `input`/`error`/`verifying` state when `open` transitions to false. (2) Guard the verify effect with `if (!open) return`. (3) Add `open` to the effect's dep array.
**Prevention**: when a modal returns null while mounted (controlled by an `open` prop), its internal hooks STILL RUN. Any effect depending on a callback the parent recreates every render will re-fire after close. Always clear internal state on close and guard effects with the open flag. Test: unlock → wait 35s (past the auto-refresh interval) → verify still locked.

### 3. Tax invoice numbering — jumping because receipts.next called per method line
**Error**: "why is the invoice number jumping?" (e.g. EAK-0000201, 0202, 0203, 0204, gap to 0211). Root cause: `payments.service.ts` checkout called `receipts.next()` INSIDE `paymentLines.map()` — each payment-method line of a split checkout consumed a separate receipt number. A cash+card+voucher sale consumed 3 numbers. The list showed the first (grouped by booking), so the visible sequence jumped by the method count.
**Fix**: call `receipts.next()` ONCE before the loop, share the result across all payment lines. Required a schema migration to DROP the unique constraint on `Payment.receiptNo` (multiple rows now share one number).
**Prevention**: for sequence-number issuance, always issue at the SALE boundary (one checkout = one number), never at the LINE boundary (one payment method = one number). Audit any `.map(async ... receipts.next())` pattern — it's a hidden multi-consume.

### 4. Migration deploy — _prisma_migrations finished_at NULL = stray DDL
**Error**: `prisma migrate deploy` failed with "relation ReceiptSequence_new_pkey already exists" — a previous migration (20260826000000_receipt_sequence_running) had failed mid-run (finished_at NULL), leaving a stray constraint/index in the catalog. Migrate deploy tried to re-run it and hit the leftover.
**Fix**: manually inspect `pg_indexes` + `pg_constraints` for stray objects; DROP them; UPDATE _prisma_migrations set finished_at=NOW() for the failed row; then migrate deploy succeeds.
**Prevention**: when migrate deploy fails with "already exists," check `_prisma_migrations` for rows with `finished_at IS NULL` — those are failed migrations that left DDL behind. Clean the stray objects manually before re-running.

### 5. Root-owned dirs on V2 block opsadmin git pull
**Error**: after a root-run `pnpm build` creates files (e.g. apps/api/src/mail/voucher-email.ts as root), the next `git pull` as opsadmin fails: "unable to create file ... Permission denied." The pull partially applies (some files checked out, others blocked) — leaving the repo in a mixed state.
**Fix**: `sudo chown -R opsadmin:opsadmin apps/api/src` before `git pull`. Or run the pull as root.
**Prevention**: after any root-run build on V2, chown the affected directories back to opsadmin before the next git operation. Or standardize: always build as opsadmin (not root) via `sudo -H -u opsadmin env PATH=... pnpm build`.

### 6. Modal close buttons disabled when busy — trapped user
**Error**: "unable to close the masseur page." Four modals in the masseur page had `disabled={busy}` on their close buttons AND `onClick={busy ? undefined : onClose}` on backdrops. When a fetch hung or network dropped, `busy` stayed true → the user was trapped inside the modal with no escape (X greyed out, backdrop click dead).
**Fix**: all close buttons + backdrop clicks now always fire onClose, regardless of busy state.
**Prevention**: NEVER gate a modal's close path on an async state. The user must always be able to dismiss a modal, even mid-operation. `busy` should disable action buttons, not the escape hatch.

### 7. Payments table: used wrong print-tokens class names
**Error**: settlement thermal print HTML used `.lbl`, `.hr`, `.hr-soft`, `.b` — NONE of which exist in `print-tokens.ts`. The actual classes are `.label`, `.amt`, `<hr class="rule">`, `<hr class="rule-soft">`, `.center`, `.muted`, `.display`, `.page`. The thermal output rendered as plain unaligned text with no dividers.
**Fix**: rewrote with the actual print-tokens classes; row layout via `.row` + `.label` (float left) + `.amt` (float right).
**Prevention**: before writing thermal print HTML that references a shared stylesheet, READ the stylesheet (print-tokens.ts) and use the exact class names defined there. Don't assume class names from memory — verify against the source.

## 2026-09-01 (Stalwart mail) - transcribed passwords from memory, 9/16 wrong in chat+PDF
**Error**: after generating random passwords into a temp JSON + txt sheet, I wrote the chat summary table and built the first PDF by RECALLING the values instead of reading the file. 9 of 11 evolveplayboost passwords in chat/PDF were wrong (only the 2 I actually used in commands — noreply@ for .env, dev@ for tests — were right). User hit 'webmail not showing email' which was actually login failure with wrong password.
**Fix**: regenerated PDF strictly reading from the sheet file; live-login-verified every password (11 EPB + 5 serambi) before presenting. Updated .mail-passwords sheet unchanged (was always correct).
**Prevention**: secrets flow FILE -> artifact, never memory -> artifact. Any artifact containing secrets must be verified against the live system (login test) before handoff. A verify that ran before the divergence is not proof for the artifact.

## 2026-09-01 (evolvepayboost-web) — EPB smoke: two parallel admin product systems, env-file split

**Discovery:** EPB admin has TWO product systems with NO sync: Products tab (Prisma `public.products`) and per-game tabs (raw-SQL game schemas `diablo_4.items/materials/...`). Storefront game pages read ONLY game schemas; catalog API (Prisma) has no price-rendering consumer (formatCatalogPrice dead code). "Admin price update → storefront" only works via per-game tabs.

**Gotchas hit:** (1) tsx auto-loads ROOT `.env`, not `server/.env` — minted admin JWT with server/.env JWT_SECRET failed signature verification; root .env holds the live secret. (2) Admin UI auth needs raw localStorage keys `auth_token`+`evolve_user` (initialize() bypasses zustand persist). (3) Admin products URL is `/admin/games/diablo-4?tab=products`, not `/products`. (4) AdminGuard comment says requireAdmin no-ops in dev — false; JWT always required.

**Reusable rule:** on EPB, before claiming "admin price update visible to customers", identify WHICH tab edited: per-game tab (items/builds/bosses/leveling) → storefront ✓; Products tab → catalog API only (no rendered surface). Materials storefront is 500-broken (schema drift: controller SELECT references columns absent from diablo_4.materials).

## 2026-09-01 (evolvepayboost-web) — EPB fixes: materials migration + legacy route

**Fixes:** (1) materials schema drift: controller mirrors bosses SELECT but no migration ever ran → wrote idempotent all-games migration (ADD COLUMN IF NOT EXISTS × 10 cols + base_price=price backfill), applied via psql + manual `_prisma_migrations` row (sha256 checksum as file hash). (2) legacy admin products.ts PUT/POST sent `price`/`promotionalPrice`/`status`/`subcategoryId`/`heroClass`/`serverRegion`/`successRate`/`boosters` to Prisma — all nonexistent on Product model → 500. Now dual-key (legacy + model names) with explicit-null clearing semantics.

**Gotchas:** (1) RETRACTED same night (see pay/play entry below): the .env flakiness was NOT tsx --watch - it was the pay/play sibling-dir trap; the failing reads pointed at the stale stub dir (no .env there). tsx was innocent. (2) `_prisma_migrations` rows are applied BY HAND in this repo (all existing rows pattern-match manual inserts); runners (run-migration.cjs/run-migrations-pg.ts) point at stale legacy paths — don't use them. (3) `salePrice: null` needs explicit handling — `null ?? x` short-circuits, and Prisma `undefined` = "no change" vs `null` = "set NULL"; distinguish key-absent from key-null.

**Reusable rule:** EPB Prisma migrations = psql the file + INSERT tracking row (uuid, sha256(file), now(), name, NULL, 1, NULL, now()). Pre-migration pg_dump schema+data to backups/ (gitignored) first.

## 2026-09-01 night (evolvepayboost-web) - pay/play sibling-dir trap manufactured phantom "fs flakiness"

**Error:** during the ps1-quarantine/gitignore phase, file ops kept failing (ENOENT on .env reads, Move/Get-ChildItem misses, check-ignore that would not match) - including the paradox "existsSync true but readFileSync ENOENT". I logged it as "tsx --watch reload lock" and "flaky fs tooling". WRONG on both counts.
**Cause:** EvolvePlayBoost root holds two sibling dirs ONE LETTER apart: evolvepayboost-web (evolve-PAY) = REAL repo (git remote nusabyte-my/evolvepayboost-web.git; server/, .env, migrations, the whole app) and evolveplayboost-web (evolve-PLAY) = stale stub (src/pages only, no .git/.env). Hand-typed paths alternated spellings between calls; every "failure" was a correct ENOENT against the stub. Poison sources: MEMORY.md's EPB entry carried the PLAY spelling, and the morning log's disambiguation line typo'd both mentions to PAY.
**Fix:** derive sibling paths programmatically (Test-Path .git = real) - never hand-type. Quarantined the 6 password-bearing mail-test ps1 into backups/mail-test-scripts-20260824 plus backups/ and /*.ps1 gitignore rules (commit 8d8b833). Deleted the spurious .gitignore my wrong-dir append created in the PLAY stub. Corrected MEMORY.md (path PLAY->PAY, SQLite->PostgreSQL) and the morning log line. Retracted the tsx gotcha above.
**Reusable rule:** near-identical sibling dir names in a workspace = treat hand-typed paths as suspect from the FIRST unexplained ENOENT. Echo the failing path next to a programmatically-derived one before debugging anything else. "Flaky filesystem" is almost always "wrong path".
## 2026-09-02 (evolvepayboost prod deploy) — three deploy-session landmines

**1. pm2 "online" while crash-looping (again, but new cause):** evolve-backend restarts showed status "online" with climbing ↺ counts and EMPTY error output in --nostream tails. Real error lived in evolve-backend-error.log (FATAL: missing STRIPE_SECRET_KEY). Diagnosis path that worked: run the exact pm2-wrapped command manually (`NODE_ENV=production npm run server`) — it failed identically, proving the crash was env, not pm2.
**Root cause:** ecosystem.config.cjs sets NODE_ENV=production → validateConfig demands PLAIN STRIPE_SECRET_KEY/STRIPE_WEBHOOK_SECRET — keys that have NEVER existed (.env only carries _TEST/_LIVE suffixed; stripe-config.ts resolves those). The old process only ever ran because it was registered WITHOUT NODE_ENV. Latent since 70942cf.
**Fix used:** replicate the old registration (`pm2 start npm --name evolve-backend --cwd <dir> -- run server`, no NODE_ENV). Proper fix (do later): make config.ts resolve suffixed keys via STRIPE_ACTIVE_MODE.

**2. nginx regex-beats-prefix struck the LIVE vhost too:** /uploads/evolveplayboost/x.jpg 404'd although the file existed and the /uploads/ location root was correct — because `location ~* \.(jpg|...)$ { root .../dist; }` outranked the plain prefix `location /uploads/`. Same trap I had just fixed in the repo copy (b1fcbfd) without knowing live had it too. One-char fix: `^~ /uploads/`.
**Rule:** when a location exists but requests still hit a *different* root, print the full location list (grep -n "location\|root ") and check regex-vs-prefix precedence BEFORE blaming file paths. Also: `access_log off` on the matching locations makes "no log entry" mean nothing — absence of evidence is not evidence.

**3. Prod-vs-local schema inversion:** the materials 13-col "drift" I migrated was LOCAL-ONLY. Prod always had the rich 23-col shape; the local dev db was the stale one. Migration on prod = no-op (idempotent by design, tracked). Reminder: verify which SIDE is behind before calling something "drift" — the fix direction (local pull from prod) may be the actual need.
## 2026-09-16 (.206 / jebat) — watchdog killed llama.cpp mid-load for 3 days; a latent bug became an outage when host steal went 1%→85%

**Error:** `llama.cpp` (`llama-cpp-jebat.service`, `jebat.online` chat route) was dead 3 days 1 hour. `jebat.online` landing, `/webui/`, `/api/status`, `jebat-api`, the `.65` tunnel — ALL returned 200. The public surface was healthy while the model backend had never started even once.

**Root cause (two faults, one masking the other):**
1. `jebat-watchdog.sh` rule 1 killed any process >80% CPU older than 180s. `llama-server` loading a 5GB GGUF CPU-only runs 150–250% CPU for ~4 min. It crossed 180s, got SIGKILLed, restarted (`Restart=always`, `RestartSec=3`), and the watchdog killed it again 5 min later — the timer's `OnUnitActiveSec=5min` matched the load window almost exactly. 871 kills. The unit log had ZERO `server is listening` lines, ever.
2. Host `%steal` went 0.9% (09-08) → 26.2 (09-10) → 72.9 (09-11) → 85.2 (09-16). The VM gets ~15% of its 8 vCPU. Model load went from "finishes in time" to "always killed at 180s". Fault 1 was latent from 2026-09-01; fault 2 detonated it on 09-13.

**Fix:** added `is_protected()` to the watchdog — name allowlist + "is this PID the MainPID of its systemd unit" derived from `/proc/PID/cgroup`. MainPID-scoped on purpose: a blanket "any process in a .service cgroup" would have shielded cron-spawned runaways (`cron.service`). Also fixed an adjacent bug: the memory rule read `$3` (%CPU) from `ps aux --sort=-%mem` where it meant `$4` (%MEM). Verified: `SKIP protected: PID=532871 CPU=186% CMD=llama-server` at 08:17:04Z, then `server is listening` at 08:29:37Z — first successful start since 09-13.

**Same defect, other victims:** clamd 471×, aide 13×, dockerd 3×, postgres 3×, ollama 3×. Any long-CPU-heavy-but-legitimate service on this box was at risk.

**Prevention / reusable rules:**
- **Kill rules must never target systemd-managed services.** systemd owns the lifecycle and declares the restart policy; SIGKILLing a unit's main process mid-startup produces an infinite kill/restart loop that *looks* like a crash loop in `NRestarts` and *looks* healthy at the HTTP layer if a reverse proxy serves something else.
- **"High CPU for N minutes" is not a runaway signal for loaders/scanners/database maintenance.** Model load, AV scan, vacuum, backup compression are all legitimately >80% for minutes. Age-based heuristics need a "known long-running process class" escape.
- **A green public endpoint does not mean the backend is alive.** `jebat.online` → 200 the whole time because nginx/landing/static routes answered while the model route was 503. Probe the *dependency*, not the front door. `llama /v1/models` returning `{"error":{"message":"Loading model"},"code":503}` was the real signal, and it was there on the very first probe.
- **Check `%steal` before blaming guest-side config.** `sar -u -f /var/log/sysstat/saNN` per-day, `top` instantaneous. A guest at 85% steal makes every guest-side timeout look like a bug in the guest. Two "flaky SSH/tooling" moments this session were just a starved host.
- **Bound remote filesystem scans.** My own `grep -rIl ... /opt/` ran 31 min at ~30% CPU and I found it only by accident in `ps`. It added to the load I was diagnosing. Never `grep -r` a large remote path without `timeout` or a narrow scope.

**Verification honesty:** llama listening + 5× HTTP 200 request completions verified in journal. The generated response *body* was not captured — detached curls to `/tmp` returned empty across several attempts, consistent with a 10-token generation at ~1 tok/s under 85% steal. Interactive usability NOT verified; expectation is "up but too slow to use" until steal is fixed. Left a capture at `/root/infer.json` + `/root/infer.meta`.

## 2026-09-17 (CetakTshirt) — four real security defects found by auditing, not by reading

Triggered by "any more security?" — built `web/scripts/audit-auth.mjs`, a script that fires every API route unauthenticated and asserts 401/403, with an explicit public-by-design allowlist. That is what found the bugs; reading the code top-to-bottom had not.

**1. Tracking token used Math.random() — the token IS the credential.**
`trackToken()` returned `Math.random().toString(36).slice(2,12) + Date.now().toString(36)`. Middleware's own comment says "the unguessable token IS the credential" — and it authorizes BOTH reading order data AND writing proof approval (`/api/track/approve` advances prepress->done, print->active). `Math.random()` is a seeded PRNG (xorshift128+ in V8) whose state is recoverable from a few observed outputs, so the "unguessable" premise was false.
**Fix:** new `lib/secrets.ts` with `randomBytes(32).toString("base64url")` (256-bit, 43 chars). Put it in a separate module because `lib/utils.ts` is imported by client components for `cn()` — a `crypto` import there leaks into the browser bundle. Verified: 43 chars, url-safe, no longer `Math.random`-shaped.

**2. `getClientIp()` trusted the LEFTMOST x-forwarded-for — rate-limit bypass.**
`forwarded.split(",")[0]` is the caller-supplied value. Any client could forge a new IP per request and defeat every limiter, including the login brute-force guard. Also the `buckets` Map never evicted, so forged keys grew it unboundedly (OOM vector).
**Fix:** prefer `cf-connecting-ip` (edge-set, client cannot forge); else take the RIGHTMOST x-forwarded-for (appended by the closest trusted proxy). Added bucket eviction at a 10k cap.
**Verified:** 14 requests each with a different forged leftmost XFF -> throttled at the shared limit (5x200 then 429s) instead of unlimited 200s.

**3. `POST /api/tracking` was an unauthenticated, unvalidated, unthrottled DB write.**
Public analytics beacon accepted any `event` string and any `meta` object. Now schema-validated against an explicit event enum + field length caps, and rate-limited 30/min/IP.

**4. `POST /api/track/approve` had no rate limit and no idempotency.**
A replay re-ran the production side-effects, resurrecting a completed job. Added 10/min/IP limit + token schema (min 16 chars) + `approvedAt` guard returning `{alreadyApproved:true}`.

**Bonus functional bug the audit exposed:** `/api/track/approve` returned 401 to EVERYONE. Middleware whitelisted `pathname.startsWith("/api/tracking")` — but `/api/track/approve` is `/api/track/...`, a different segment, so it never matched and fell through to "requires auth". The customer proof sign-off button on the public tracking page was dead. `startsWith` prefix checks silently miss sibling segments — the string looks like a match to a human reader.

**Reusable rules:**
- Build an executable access audit before claiming a codebase is hardened. Reading routes one by one misses exactly the routes nobody thought about.
- A token described as "unguessable" is only unguessable if generated with a CSPRNG. Grep for `Math.random()` anywhere near auth, tokens, IDs, or reset codes.
- Never trust the leftmost XFF. Prefer an edge-set header (`cf-connecting-ip`), else the rightmost entry. Always cap in-memory limiter maps.
- Middleware prefix allowlists: `startsWith("/api/x")` does not cover `/api/x-y`. Enumerate exact sibling paths.
- Any public-by-token endpoint that WRITES must have: rate limit, schema validation, and an idempotency guard on the state it mutates.
## 2026-09-17 (Erawan-QSys) — 4 production incidents resolved: chained service self-collision, cross-guest Pay & Start capture, duplicate receipt reuse, and walk-in chargeable scoping

**1. Chained services self-collided in Pay & Start (#YNUBEK)**
- **Symptom:** Starting a 2-service single-guest booking (`HBS 30m + Foot30 30m`) failed with `Overbooking blocked at 15:51 MYT: Nutty; Room F1`, splitting the session into 15:51 and 18:30.
- **Cause:** `pay-and-add-sheet.tsx` looped through `allItemIds` setting the identical `preferredTime: startTimeIso` on both items. Item 2 collided with Item 1 in Room F1 with Nutty.
- **Fix:** Stagger chained items sequentially: `Item 1 = startTimeIso`, `Item 2 = startTimeIso + duration(Item 1)`. Sequential services can then share the same therapist and room without self-collision.

**2. Pay & Start cross-guest pull (#ND8XQ9)**
- **Symptom:** Paying for Guest 1 pulled Guest 2 into the cart and split Guest 2's session.
- **Cause:** A whole-booking sync step in `pay-and-add-sheet.tsx` auto-aligned sibling items for other guests to start at the same time.
- **Fix:** Strictly isolate Pay & Start to the clicked block's items (`allItemIds`). Each guest in a multi-guest booking has their own schedule and starts individually.

**3. Duplicate receipt reuse across checkouts on same booking (#ND8XQ9 / EAK-0000877)**
- **Symptom:** Two separate checkouts for Guest 2 and Guest 1 both received `EAK-0000877`. The refund modal showed `Receipt: EAK-0000877 + EAK-0000877` totaling RM 346.10, preventing individual refund.
- **Cause:** `existingServiceReceiptNo` searched for any prior payment on the `bookingId` and reused its receipt number across separate checkouts. In addition, `getDetail()` grouped all payments on the booking.
- **Fix:** Every checkout call allocates a fresh receipt number via `this.receipts.next(...)`. `getDetail()` scopes `invoicePayments` strictly to `receiptNo: payment.receiptNo`. `payments-modal.tsx` shows `detail.payment.receiptNo` and refunds the specific transaction individually.

**4. Walk-in multi-guest checkout failed with 400 (#5LLR3Y, #W76OOH, #I54NGT, #NLV46Q)**
- **Symptom:** Walk-in checkouts converted sessions to active, but payment failed with `Capture Failed: All 1 booking(s) failed: At least one booking item is required for checkout.` Sessions ran without payment or receipt numbers.
- **Cause:** Walk-in cart items have no `bookingItemId`. `chargeableBookingItemIds` was empty, sending `bookingItemIds: []` to the API. `assertBookingPaymentWithinBalance` rejected empty arrays.
- **Fix:** Extract real item IDs from `fullBooking.items` filtered by `guestIndex`. On the backend, fall back gracefully to `guestIndex` scoping when `bookingItemIds` is empty or omitted. Added 200ms retry backoff in POS to eliminate the race condition with `convert-consolidated` commits.

## 2026-09-17 (Serambi Tiffin) — Outbound WA Gateway 502 bypass, pg-model constructor trap, and email credentials alignment

**1. Outbound WhatsApp Gateway (wa.nusabyte.my) 502 Bad Gateway bypass:**
- **Error:** Customers attempting registration / OTP verification did not receive messages. Probe to `wa.nusabyte.my` returned `502 Bad Gateway` from Cloudflare because the upstream Baileys process was offline.
- **Root Cause:** Outbound push depends on external daemon uptime, and Meta blocks freeform outbound messages to new numbers outside the 24-hour service window.
- **Fix:** Replaced the fragile outbound dependency with **Inbound 1-Click WhatsApp Verification**:
  1. System generates a random single-use code (`VERIFY <6-digit-code>`).
  2. User taps link: opens WhatsApp with prefilled message to HQ (`+601139481246`).
  3. User taps Send in WhatsApp.
  4. Inbound messages are free on Meta (zero utility charges), never blocked by 24h windows, and 100% authenticate the real sender's mobile.
  5. Frontend auto-polls `/api/whatsapp/inbound-otp/status` every 1.5s, detects arrival, and logs user in automatically.
  6. Added on-screen desktop QR Code (scannable with phone camera) and Mailcow email OTP fallback.

**2. pg-model.ts constructor trap (`User is not a constructor`):**
- **Error:** Calling `new User({...})` or `new UserProfile({...})` threw runtime error: `User is not a constructor`.
- **Root Cause:** In `server/models/pg-model.ts`, models generated by `createPgModel(tableName)` are not Javascript class constructors with `new`. They expose Mongoose-compatible static methods (`Model.create({...})`, `Model.findOne({...})`, `Model.find({...})`).
- **Fix:** Always use `await Model.create({...})`.

**3. Process environment variable precedence with dotenv:**
- **Error:** `EmailService` failed with `535 Authentication credentials invalid` despite updating `server/.env`.
- **Root Cause:** The parent process environment already had stale `MAIL_` variables from a previous shell session. By default, `import 'dotenv/config'` in Node.js refuses to overwrite already-existing `process.env` keys.
- **Fix:** Pass `{ override: true }` in `dotenv.config({ path: ..., override: true })` so file changes take immediate effect.

## 2026-09-19 (JEBAT engine, second pass) — I trusted a sandbox that did not sandbox

**Error:** I "verified" the memory migration against a temp-dir copy, then ran `pytest tests/test_enhanced_memory.py`. The fixture does `monkeypatch.setenv("HOME", str(tmp_path))` before constructing `EnhancedMemorySystem()`. On Windows `Path.home()` resolves `USERPROFILE`, **not** `HOME`, so the `HOME` override did nothing and the instance opened the REAL store — running my `_load()` migration against production memory.

**It happened to be the intended outcome and I proved it clean** (86 → 69 traces, 0 distinct contents lost, `access_count` conserved at 505, 0 dangling links, idempotent, backup taken first). But at the moment it ran it was unintended, and had the migration been wrong it would have silently rewritten the live store.

**Fix:** the migration is correct and stays; the backup (`traces.json.bak-<ts>-pre-migration`) is retained. Boundary noted so it is a decision rather than an accident.

**Reusable rule:** before trusting any "sandboxed" run, assert the sandbox actually redirected — print the resolved path and check it is the temp dir. A test that *looks* isolated is not isolated. Cross-platform trap: `HOME` (POSIX) vs `USERPROFILE` (Windows) vs `Path.home()` which reads both platform-dependently. Same family as the 2026-09-01 pay/play sibling-dir trap: the environment quietly disagreed with my model of it, and every downstream conclusion was wrong until I checked the path itself.

## 2026-09-23 (Erawan-QSys) — Manual SQL insert column assumptions on core tables

**Error:** When constructing surgical inserts for replacement sessions (`Assignment`, `BookingItem`, `Payment`), initial SQL queries failed with `column "createdAt" of relation "Assignment" does not exist`, `column "createdAt" of relation "BookingItem" does not exist`, and `column "serviceTaxCents" of relation "Payment" does not exist`.

**Root Cause:** Assumed conventional timestamp and tax columns existed across all tables without checking exact DDL. In reality:
- `Assignment` and `BookingItem` do not have `createdAt` or `updatedAt` columns.
- `Payment` has `createdAt`, `roundingCents`, `receiptKind`, `receiptNo`, `guestIndex`, `branchId`, `businessDate`, but does NOT have `updatedAt` or `serviceTaxCents`.

**Fix:** Ran `\d "Payment"`, `\d "Assignment"`, `\d "BookingItem"` to inspect exact column definitions, adjusted the insert queries to use only genuine schema fields, and verified execution.

**Prevention:** Never guess table columns when writing manual SQL migrations or surgical patches. Always inspect table schema via `\d "TableName"` or check `schema.prisma` first.

## 2026-09-24 — PerkasaApp-MEV Corrections

1. **Defunct Route `/admin/new-task`:**
   - Issue: Clicking `+ Tugasan` or `Tugasan Baru` navigated to `/admin/new-task` which wasn't registered in `main.tsx`, redirecting admins back to `/`.
   - Correction: Replaced route navigation with a centered modal popup (`showNewTaskModal`) that manages premise selection, driver assignment, and duplicate prevention directly on the dashboard.

2. **Leaflet `tap` Option Deprecation in TypeScript:**
   - Issue: `tsc` build failed with `error TS2353: Object literal may only specify known properties, and 'tap' does not exist in type 'MapOptions'`.
   - Correction: Removed `tap: false` and relied on `dragging: false` and `scrollWheelZoom: false` which are valid and fully supported across modern Leaflet types.

3. **Topbar Horizontal Overflow on 375px Screens:**
   - Issue: Driver topbar links ("Profil", "Baru") duplicated the bottom navigation dock and stretched topbar width to 434px on mobile.
   - Correction: Added `.topbar-desktop-only` class to hide redundant links on mobile screens (`max-width: 768px`).

## 2026-10-01 — ALAND report ship

1. **Duplicate cover metadata (caught in triage, fixed pre-commit):**
   - Issue: the editorial cover's new firm footer printed `Ref:` and `Prepared for <client>` while
     `refLine(refNumber, clientName)` already prints both in the metadata column — the same reference
     stated twice on one page.
   - Correction: removed the footer duplicates, kept the firm identity block, left a comment explaining
     why the fields are not repeated.

2. **Client-name prefix normalization:** users type "Prepared for ACME" into the field while templates add
   their own prefix. Strip the typed prefix at the single point where the value enters `generateCoverPage`
   — never per-template.

3. **Two failed probes in one session:** `studies`/`study_id` (real: `feasibility_studies` / `studyId`) and
   the object form of `setCookies` (real: raw `Cookie:` header). Both were avoidable by reading the schema
   and the tool contract first.

## 2026-10-01 — ALAND LandMarket & Apportionment fixes

1. **Townhouse lot calculation in ApportionmentTable (`DevelopmentSection.tsx` & `development.ts`):**
   - Issue: The table previously divided the townhouse physical lot footprint by 2 (`effectiveLotSizeSF = lotSizeSF / 2`), which cut the $20' \times 60' = 1,200\text{ sf}$ lot size to $600\text{ sf}$ and doubled the physical lot count to $44.88$.
   - Correction: In the Apportionment schedule, Land Size / Unit represents the physical lot footprint ($1,200\text{ sf}$), and Land Lots (No.) calculates the actual land lot count: $\text{apportionSF} / 1200 = 26,927.92 / 1200 = 22.44\text{ lots}$.

2. **Section 2 hidden on listing detail (`LandMarketListing.tsx`):**
   - Issue: Listing 32 on `landmarket.alandfeasi.tech` did not display Section 2 because the card was gated behind `if (listing.nettGDVMillions)` (which is null for listings authored without an attached feasibility study).
   - Correction: Conditioned Section 2 on any populated development parameter (`proposedDevelopment`, `GDV`, `GDC`, `profit`, `densityPerAcre`, `plotRatio`, `totalUnits`). Added `formatMoneyOrMillions` to correctly format both raw RM and shorthand million inputs.

3. **Admin Listings link pointed to non-existent `/marketplace/:id`:**
   - Issue: Admin View button routed to `/marketplace/${listing.id}` (which redirects or 404s).
   - Correction: Updated route to `/landmarket/${listing.id}` in a new tab (`target="_blank"`), and added an `Edit` action pointing to `/marketplace/publish?editId=${listing.id}`.

## 2026-10-01 — WiraSiber AI routing corrections

1. **Stale provider metadata shipped as truth:** constants listed Groq `llama-3.3-70b-versatile` and an Ollama id `ollama-llama3` naming Qwen; `.env` had `OLLAMA_MODEL=llama3.1:8b`. Two of three were models that do not exist on the target accounts/hosts, so the primary provider failed 100% of calls. Rule: when wiring a provider, hit `/v1/models` (Groq) or `/api/tags` (Ollama) with the real credentials before assigning default ids.
2. **Edit rejected: cross-drive path typo** (`M:/jebatcore` instead of `D:/jebatcore`) → File not found on MEMORY.md insert. Re-anchored with the same tag on the correct drive, no content loss.

## 2026-10-02 — NusaByte deploy-pipeline misbelief

1. **Inferred "auto-deploy on push" from a single observation:** the first SEO batch propagated to production ~2 min after my push, and I stored it as a fact ("push triggers automated VPS deploy ~2-3 min"). Wrong causal model — a concurrent session had simply run scripts/deploy-next.ps1 around that time. The quick-wins push sat undeployed for 40+ minutes (18 polls, 404), and the stored fact actively discouraged checking the real trigger. Correction: deploys are manual script runs; SSH from this box works; poll a NEW route to 200 AND check whether the script has run (release dir timestamps on the VPS) before concluding "propagating". Stale memory cc9f0628 flagged for deletion (project_forget needs approval); superseded by c6887874.
2. **First deploy attempt aborted on `tar --force-local`:** the script's run-contract comments encode GNU-tar behavior, but System32 tar on this host is bsdtar, which rejects the flag. The failure then exposed a second bug — the catch handler read `$remoteTouched` unset under Set-StrictMode Latest and threw its own error. Fixed both in 0058e31 (flag-first-then-fallback; initialise before try). Lesson: a script that "worked yesterday" on a shared repo can break on host-tool differences the other committer never hits.

## 2026-10-03 — SME-toolkit audit self-correction

1. **Audit claimed n8n workflows hit dead `/webhook/*` endpoints — wrong.** A `grep` for literal strings `webhook/copywriter|webhook/canvas|webhook/leads` missed that FastAPI declares a *dynamic* route `@webhook_router.post("/{agent_name}")` (app/api/v1/webhooks.py:19). Static-literal grep against path-parameterized routers produces false "missing endpoint" findings. Rule: before declaring an API route dead, check for `{param}` dynamic routes in the router file, not just literal strings.
2. **SME-toolkit "20 project memories" in ~/.jebat traces are cross-project contamination** — Erawan QPOS/booking facts tagged under project name `SME-toolkit`. Recall results for a project must be repo-verified before use as ground truth (the FastAPI/TimescaleDB "stack" fact was stale Erawan; actual stack: React 19 + Vite + FastAPI backend).

## 2026-10-08 - ALAND deploy

1. **VPS .env cannot be shell-sourced** (RESEND_FROM_EMAIL has unquoted <...>): extract DATABASE_URL with grep/cut instead. Drizzle pgTable names are snake_case in Postgres (marketplace_listings), columns stay camelCase quoted - check the pgTable() string before writing ALTER. deploy_to_vps.ps1 does NOT run db:push; apply schema changes by hand (ADD COLUMN IF NOT EXISTS) before deploying.

## 2026-10-08 - GitHub push outage + sidebar

1. **GitHub 'Internal Server Error' on push = transient server-side failure**, not auth/branch protection: it rejected even a brand-new branch, and ls-remote still worked. Correct response: keep the commit safe locally (backup branch), deploy from the local tree (deploy_to_vps.ps1 does not need GitHub), then retry the push after a few minutes. Do not chase auth/config.
2. **Sidebar collapse reset on every ALAND page**: SidebarProvider writes sidebar_state cookie but never reads it back. Fix: initialize useState from the cookie. Sub-app shells that remount per route need cookie/localStorage rehydration, not just writes.
3. Scrapling screenshots land as image attachments this GLM session cannot read - verify UI via code review + user, say so instead of claiming visual QA.

## 2026-10-08 - ALAND local DB sync

1. Local dev uses root .env (postgres://jebat:jebat_password@localhost:5432/aland_feasi), backend .env variant has no password - root .env wins via loadEnv. Local Postgres 17 service, 18 installed but stopped.
2. VPS .env values contain unquoted <...>; safe extraction = grep '^DATABASE_URL=' | cut -d= -f2- | tr -d quotes/CR. pg_dump -Fc 108MB dumps/restores cleanly with --no-owner --no-privileges -j 4.
3. ALAND health endpoints: backend http://localhost:3001/api/health (dev proxy /api verified 200). Windows hidden pwsh + Start-Process is reliable for long-lived dev servers; pwsh Start-Job dies with parent shell.

## 2026-10-08 - ALAND modal extraction pattern

1. To reuse a page as a modal without duplicating UI: rename page component to exported XxxPanel, strip its layout wrapper to a fragment, re-add default export wrapping the panel. Then lazy-import the panel in the modal (static import of a lazy page module kills the chunk split - vite INEFFECTIVE_DYNAMIC_IMPORT warning is the telltale, main bundle +30KB).
2. Content width in Calc is controlled by mx-auto max-w-7xl container in Calc.tsx, not the layout - users expect full-width on study pages.
3. Full-screen modal pattern in this repo: fixed inset-0 z-[80] + top bar with close + flex-1 overflow-y-auto body + Escape handler + body scroll lock.

4. ALAND /calc/:id full-width fix took TWO caps: (a) mx-auto max-w-7xl container in Calc.tsx, (b) mx-auto max-w-7xl in SectionGroupNav.tsx tab strip. When user reports a width problem, grep the whole page tree for max-w-\d, not just the obvious container - sticky nav strips have their own caps.

5. **calc/:id not full width root cause**: CalcLayout's inner <div class=flex min-h-screen> is a flex child of SidebarProvider's wrapper but lacked flex-1 w-full, so the column shrank to content width. DashboardLayout avoided this via shadcn SidebarInset (w-full flex-1 built in). Rule: when hand-rolling a layout beside a SidebarProvider wrapper, the content column needs flex-1 w-full explicitly - removing max-w caps alone cannot fix a shrink-to-fit parent.

6. **Width requirement reversal caught late**: user demanded 'full width' on /calc/:id, then pointed at /admin (max-w-7xl centered) as the CORRECT width. The real ask was consistency with admin console, not infinite stretch. I removed both max-w-7xl caps, then had to restore them (keeping the flex-1 fix). Lesson: when user describes width as wrong, ask what page looks RIGHT before removing caps - 'full page' meant 'fill the column like other pages', not 'no max-width'.

7. **'Button opens page instead of modal' false alarm root cause**: user's SPA tab was loaded BEFORE the modal deploy; old code still navigated to /library in that long-lived tab. Deploys don't reload open SPA tabs. Verified live bundle contained modal (strings in index + KB chunks) before concluding. Remedy: hard refresh; consider deploy-version poll banner for long-lived tabs.

8. ALAND report cover profile infra already had save/apply/merge (settings.ts firmProfile + applyFirmProfile fill-blanks-only). Missing pieces user asked: explicit Save Cover button (autosave existed but invisible) + bulk apply across all owned reports. Bulk pattern: server-side loop over feasibilityStudies by userId, parse reportEdits body 'cover' JSON, applyFirmProfile, upsert via onConflictDoUpdate target [studyId, sectionId]. Confirm() before bulk write.

9. **State normalizer pointed the wrong way (same session)**: built `normalizeStateValue` mapping state NAMES -> slugs for the quiz, before reading `lib/options.ts`, which documents the users-side convention as value === label with FULL names (login/register/profile-edit write names; prod rows hold names) and legacy slugs translated by `findStateLabel`. The helper was deleted and every site re-wired to the documented convention. Lesson: before adding a normalizer, read the file that documents the existing convention; the codebase usually already decided.
10. **Assumed a 'superadmin' tier existed**: investigated "make this account superadmin as well" against a role enum of exactly user|admin — there is no second tier; 'SuperAdmin Login' is just the admin-only impersonation feature, and the real failure was the role-demotion bug. Lesson: when a user names a mechanism ("superadmin"), grep for the term before designing for it.

## 2026-10-09 - jebat-core session (agentix foundry + fleet + REA)

1. **Two stale tests were red since the 2026-10-08 CLI banner refactor**, not from my changes: `test_help_survives_legacy_windows_console_encoding` (asserted a version string in `--help` output the refactor dropped — restored via parser epilog `JEBAT v{__version__}`) and `test_quickwin_fixes.py::test_repl_dispatch_opens_repl_not_llm` (stubbed `banner` as `lambda: None`, but the call now passes `subtitle/version/style` — stub widened to `*a, **k`). Verify-before-blaming: stash the suspect files and run the failing test on HEAD before assuming your change caused it.
2. **"add this in jebat mcp agentic" was ambiguous** — resolved as BOTH legs: register REA in MCP configs AND expose the fleet + the agentix foundry as MCP tools and catalog specialists. If only one leg was intended, the other is additive and verified.
3. **MCP write smoke kept off the live bus** — `fleet_dispatch` was proven on a temp fleet root; the real bus was only read (counts). A live dispatch waits for an actual request.
4. **`pm2 env <id>` returned an empty key during the VPS probe** — the working extraction was the `.env` fallback (`grep '^JEBAT_API_KEY=' /var/www/jebat-core/.env`). Don't conclude a tool is missing from a 401 when the probe key may just be empty (the first probe script carried the fallback; a stripped re-run lost it and misread as "tool absent").
5. **`git push` hit a transient GitHub 406 / "interrupted"** (same class as the 2026-10-08 push failure): the commit is safe locally and deploys do not depend on GitHub — retry the push, don't chase auth.
6. **The "repo rename" was half red herring, half misread**: pushes were broken by the stale `hosts` pin (fixed above), BUT `hermes-agent-jebatcore` (pointed at by `4e5d703` + `jebatcore-new`) **does exist** — it is the **control-room repo** (formerly nusabyte-hermes) recreated + history-merged at ~22:04 on 2026-10-09 and set **private**; the 404 observed was the expected anonymous response for a private repo. **Lesson: verify repo existence with a token (`GET /repos/<owner>/<name>` using the GCM credential) before concluding "doesn't exist" — anonymous 404 proves nothing for private repos.** The jebatcore commit `b95b39a` (install URLs → new repo) was **dropped on 2026-10-10**: decision — repos stay separate (`jebat-core` public = code/install home; `hermes-agent-jebatcore` private = control room). Vault: `vault/decisions/2026-10-10-repo-topology-hermes-agent-jebatcore.md`.

## 2026-10-10 - Live token committed to a PUBLIC repo (jebat-core)

1. **MEMORY.md is a tracked file in a public repo — it is NOT private memory, it is PUBLICATION.** The 2026-10-09 Erawan entry (item 6) carried the live Avenue K print-agent token; the memory-index bookkeeping commit `ad57e91` published it. Caught in review minutes after push. Remediation executed: local + PROD `print_agent_token:avenue-k` rotated (new sha256 `bcfb9166…`, actor `jebat-mcp-rotate-20261010`, 2026-10-09T17:03Z); the Erawan repo's `scripts/print-agent/config.json` updated (that file is gitignored — never leaked); new value handed over via `D:/Jebat/.local-backups/print-agent-token-avenue-k-20261010.txt`; memory entry redacted. The old token remains in git history but is invalid — history rewrite is unnecessary for a rotated credential.
   Rule: never paste tokens/keys into MEMORY.md, daily logs, or any tracked file; record rotation metadata (hash prefix + date + actor) only. Pre-commit check for memory edits: `grep -nE '[0-9a-fA-F]{32,}' MEMORY.md`.
2. **Stale path in MEMORY.md corrected**: Erawan-QSys lives at `E:\AI-Dev\nusabyte-project\Erawan-QSys` (the `C:\Users\shaid\Desktop\nusabyte\...` path in the index was stale — `Desktop\nusabyte\` no longer exists).

## 2026-10-10 — Erawan-QSys VPS performance, B2A room conflict & localhost SW chunk timeout

1. **Nginx SSE rate-limiting dropped live connections on shared outlet IPs**: `location /api/live-matrix/events` carried `limit_req zone=erawan_api burst=10 nodelay`. In retail spa branches where 3-5 devices share one external NAT IP, concurrent refreshes hit 503 Service Temporarily Unavailable, triggering client reconnection storms and polling loops that degraded the entire UI. Rule: SSE event streams are persistent connections and must NEVER carry `limit_req`; general API rate limits must be at least 120r/s with burst=200 for multi-device stores.
2. **Missing Customer indexes caused 8.2B sequential row scans**: `Customer` table had only a primary key on `id`, forcing full table scans on every phone/name search across 8,085 rows (1.7M scans recorded). Added `Customer_phone_idx`, `Customer_name_idx`, `BookingItem_roomId_idx`, `BookingItem_masseurId_idx`, `CommissionEntry_createdAt_idx`, and `RoomStatusEvent_createdAt_idx`. Ran full `vacuumdb -z` (dead tuples dropped from thousands to 0).
3. **Hard-pinned subRoomId in advance bookings blocks physical room assignment**: Fu Chin's advance booking for 17:00 had `subRoomId: sub_nu_b2_a` hard-pinned in PostgreSQL. The backend guard `busySubRoomIds` treated this as an exclusive bed lock, throwing `room_unavailable` when front desk tried to assign B2A. Rule: advance reservations must keep `subRoomId: null` so they float dynamically until physical floor check-in.
4. **Service Worker localhost deadlock on Next.js 15 dev eval chunks**: A stale Service Worker on `localhost:5500` intercepted `_next/static/chunks/app/layout.js` before React mounted, causing a ChunkLoadError timeout that deadlocked the cleanup in `PwaRegistration`'s `useEffect`. Fix: added `<EarlyHeadGuardScript />` directly into `<head>` in `app/layout.tsx` to synchronously unregister all SWs and purge `caches` on localhost before webpack scripts load.
5. **Next build overwriting .next while next dev runs causes 404 on evaluation chunks**: Running `pnpm build` in parallel with an active dev server wipes `.next` and generates production hashes, deleting development chunks (`main-app.js`, `layout.js`, `page.js`). Browser requests on localhost then 404. Fix: terminate the dev process, remove `apps/web/.next`, and restart `next dev` cleanly.
6. **Sub-room selection reverted to parent room code in POS cart**: `openEditAssignModal` and room slot selection set `assignRoom.code = r.code` ("B2") instead of the bed code ("B2A"), causing cart and tickets to obscure the bed location. Fix: flattened all sub-rooms into individual room options and set `assignRoom.code = subRoomCode` directly.

## 2026-10-12 — Erawan-QSys VIP receipt name, duration m unification & notification stacking

1. **VIP Member Name fallback to 'VIP Member'**: In `payments.service.ts` `getDetail()`, resolving stored-value member payments looked up the `VipCard` with its linked `customer`, but the returned `vipTopupData` object omitted `customerName`. When front desk opened or printed the Member Transaction Receipt, `detail.vipData.customerName` was undefined and the booking was keyed as "Walk-in Customer", forcing fallback to "VIP Member". Fix: added `customerName: foundCard.customer?.name ?? topup?.vipCard.customer?.name ?? null` to `vipTopupData`. Andy Lee's name now renders correctly on receipt header and signature line.
2. **Header overflow clipping & modal layer stacking**: `NotificationBell` popup was rendered inside `<header>` which carried `z-40` and `overflow-x-auto`. When modals (`z-50`, `z-[9000]`) were open or on desktop scroll, the dropdown either rendered underneath modals or was clipped vertically by the header height. Fix: moved `overflow-x-auto` to `<nav>`, upgraded `<header>` to `z-[100]`, and rendered the dropdown in `createPortal(..., document.body)` with `fixed` coordinates and `z-[99999]`.
3. **Inconsistent duration abbreviation**: Across the app, duration was displayed inconsistently as `31 min`, `31min`, `31 minutes`, and `31m`. Unified all session durations and elapsed time indicators to terse `m` (e.g. `31m`, `60m`, `90m`).
4. **Transaction Detail tender breakdown count badge**: In `payments-modal.tsx` `TransactionDetailModal`, the tender breakdown card showed an unnecessary `×2` count badge beside the method name when multiple tender lines existed. Removed to keep tender lines clean.
5. **Supervisor PIN 5599 requirement in membership payment flow**: Tendering with membership and another payment method (split tender) triggered a blocking `PinPadModal` requiring supervisor approval code `5599`. Removed the gate and modal so front desk can process membership checkouts and point splits directly.

## 2026-10-12 — ALAND: Conversion & Dev Charge prefill, Industrial subtype priority & Match 10.10.26 cutover

1. **Industrial subtype matching priority in landRefData**: In `CONVERSION_PREMIUM_ROWS` and `DEVELOPMENT_CHARGE_ROWS`, a generic condition `to.includes("Industrial") && r.to.includes("Industrial")` triggered on the very first industrial row (`Light Industrial` at 20%), overriding specific rows like `Medium Industrial` (25%). Fix: introduced `matchSubtypeOrFallback(val, rowVal)` which strictly extracts and requires the specific subtype ("Light", "Medium", "Heavy") if present before falling back to generic matching.
2. **Fail2ban burst cooldown on ALAND VPS**: Port 22 connections on `jebatvps` enforce a ~45s jail after rapid successive connections. Fixed by executing a single binary custom-format dump (`pg_dump -Fc aland_feasi > .local-backups/aland_feasi_vps.dump`) over a single SSH connection and restoring locally with `pg_restore --no-owner --role=jebat`.
3. **Schema-before-deploy ordering invariant**: Drizzle ORM queries select every column from declared tables (`SELECT ... FROM matching_entries`). Deploying backend code before creating new tables or columns in production crashes all related endpoints. DDL table creation (`matching_entries`, `matching_attachments`, `matching_matches`, `matching_role_penalties`, `matching_notifications`) was applied to PostgreSQL on the VPS (`alandfeasi.tech`) before running `./deploy_to_vps.ps1`.
4. **Matching UI horizontal card stacking and zero sparkles**: In Section C ("Your matches"), cards were overhauled from a 3-column vertical grid to responsive horizontal cards (`flex flex-col lg:flex-row items-stretch justify-between gap-5`) with distinct identity, match rationale, and score gauge columns. Sparkle icons were eliminated across cards, badges, and AI tagging spinners in favor of clean institutional badges and standard `Loader2` spinners.
5. **Restoring partner-facing profile in matching flow**: When overhauling the matching screen to the multi-entry client spec, the top-level `UserProfileCard` (photo upload, state badge, industry/designation/company descriptors, inline editable bio, social handles) was integrated directly at the top of Section A so users can curate how they appear to partners alongside granular offers and needs.

## 2026-10-13 — ALAND: PostgreSQL table ownership, Stripe optimistic activation gate & Material Link drawer

1. **PostgreSQL table ownership vs database user**: On VPS `aland_feasi`, tables `matching_*` were created with owner `postgres`, while the application connects as user `jebat`. User `jebat` had zero table grants, causing queries like `select count(*) from matching_entries` and inserts to crash with `500 Internal Server Error (permission denied)`. Fix: executed `ALTER TABLE matching_* OWNER TO jebat; ALTER SEQUENCE matching_* OWNER TO jebat;` and `GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO jebat;`. Rule: whenever running manual DDL on production, always ensure ownership matches the app's `DATABASE_URL` user (`jebat`).
2. **Stripe optimistic activation bypass in embedded registration**: In `packages/backend/server/_core/oauth.ts` at `/api/subscription/confirm-embedded-registration`, when Stripe reported `!verification.isPaid`, the endpoint only warned to console and optimistically activated the user as premium, created the subscription record in DB, and sent the Resend welcome credentials email claiming "Payment Confirmed · RM 499.00". When Tan (`eng.tsetse@gmail.com`) hit the confirmation endpoint on Sep 16, they received the email with password `Aland-pxQYNkQW` despite zero payment processing through Stripe. Fix: hard-gated the endpoint with `if (!verification.isPaid) return res.status(402).json({ error: "Payment has not been completed or verified by Stripe gateway." });`.
3. **Add your material dual-action Link drawer**: User requested that material tiles support both file upload (`+ Add`) and URL attachment (`Link`), opening an inline address bar (`Link to [name]`, `https://...`, `Save link`, `Cancel`) below the tiles. Updated `Matching.tsx` with dual header buttons and interactive inline address drawer saving directly via `addAttachmentMutation`.
4. **Admin Matching Cockpit (10.10.26) cutover**: Rebuilt `AdminMatching.tsx` with 5 institutional sections matching the client PRD spec (1. Member Information, 2. Offers & Seeking with gap analysis, 3. AI Matching Table with formula math, 4. Interested Activity Feed with WhatsApp prefill, 5. Algorithm & PRD reader and downloads) and implemented backend endpoints in `packages/backend/server/routers/matching.ts`.
5. **LandMarket Frontend Pairing**: Added "Deal Matchmaking" navigation links with `AI Match` badges to `LandMarketPublic.tsx` and `LandMarketListing.tsx`, plus hero bridge row and due diligence partner cards on `landmarket.alandfeasi.tech`.
## 2026-10-14 — Erawan-QSys: Multi-session guest receipt grouping, clean receipt logo & centered login overhaul

1. **Multi-session guest receipts printed therapist and session IDs per item**: When a guest had chained services (e.g. Foot 60 + HBS 30) with the same therapist and session code, each item row repeated the therapist and session ID line immediately below the service name, splitting the guest's service list. Fix: updated `ReceiptPreviewModal`, `ReceiptView`, POS `printReceipt`, `payments-modal.tsx`, `receipt-email.ts`, and `receipt-pdf.ts` to list all service lines first, followed by deduplicated `— Therapist: [Code]` and `— Session ID: [Code]` at the bottom of the guest section.
2. **Thermal receipt logo (/erawan-receipt-logo.png) included unwanted "wellness massage" text**: The bottom 20px of the raster image contained "wellness massage" with pixelated anti-aliasing. Sliced off the subtitle and re-rendered the clean 3-headed elephant crest and "Erawan" calligraphy in pure solid jet-black (`RGB(0, 0, 0)`) with smooth alpha anti-aliasing, immediately updating thermal prints, on-screen modals, VIP receipts, and PDF invoices across the entire platform.
3. **Login page (/login) squished logo, typewriter font & uncentered grid**: The login page used a low-res JPEG (`/erawan-wellness-logo.jpg`) with CSS multiply hacks, Courier New monospace headers, and an uncentered layout. Generated high-res 2x Retina master logo (`/erawan-logo-enhanced.png`) from `Erawan LOGO.png` with corrected tracked subtitle, overhauled typography to editorial serif (`Georgia, Cambria, serif`), and center-aligned all grid objects (`place-items: center; align-items: center; max-width: 1440px; margin: 0 auto;`).

## 2026-10-15 — BaanIyaraQPOS: POS category indexing, Products below Facial Essence & VPS dual deployment

1. **POS Category indexing misclassified therapies as products**: In `pos/page.tsx`, `TIER_ORDER` omitted `Bamboo`, `FootScrub`, and `FacialEssence`, defaulting their `tierIndex` to `999`. Because `isProductGroup` tested `tierIndex >= PRODUCT_START_IDX` (where VIP was index 9), all 3 therapies were misclassified as products, hidden from `All Services`, and displayed in the Products section with default sparkles and unspaced names (`FootScrub`). Fix: replaced index arithmetic with explicit `PRODUCT_GROUPS: Record<string, true> = { VIP: true, Voucher: true, Product: true }`, placing all 11 therapy groups strictly under Sessions, ending with `Facial Essence`.
2. **Products section placement below Facial Essence**: Reorganized the sidebar to place the `<p>Products</p>` section header and items (`Retail Products`, `Gift Voucher`, `VIP Membership`) strictly beneath `Facial Essence` (the last session), with dedicated icons (`Leaf`, `Footprints`, `Sparkles`, `Ticket`, `Crown`, `ShoppingBag`).
3. **Baan Iyara VPS deployment on shared Hostinger box**: Deployed `/opt/baaniyaraQPOS` to `erawanhq` (`2a02:4780:5e:20bd::1` / `72.60.42.163`) with complete isolation from Erawan: dedicated ports 4002 (API) and 5502 (Web), isolated PostgreSQL database `baaniyara_qsys` on port 5433, Redis DB index 1, and Nginx vhost `/etc/nginx/sites-available/qpos.baaniyara.com`. Erawan on 4001/5501 remains untouched.

## 2026-10-15 — ALAND: ISF commercial base 0, library admin-only, snapshot overlay

1. **ISF (Commercial or Industrial) charges on every non-residential category.** A landed unit type stored `category: "residential"` for an industrial park (study 99, 27 × 11,000 sf = 297,000 sf) zeroed the commercial charge. The apportionment table only exposed a free-text name — category was unreachable from the live UI. Fix: per-row category select + one shared classifier `RESIDENTIAL_ISF_CATEGORIES` (shared/feasibility/engine/statutory.ts) replacing three hand-written lists. Verify `unitTypes[].category`, never the row name — names lie.
2. **`buildBucket` drops zero-amount lines** (`lines.filter(l => l.amount !== 0)`), so a statutory line that computes 0 vanishes from `bucket.lines`. B2's `getAmt` falls back to 0 and a test must assert the rendered row, not the line object.
3. **KB reference-library mutations were `protectedProcedure`** — any account could edit/delete shared categories and documents. Now `adminProcedure`; UI hides the controls for non-admins rather than surfacing a FORBIDDEN toast.
4. **Native `confirm()` is a silent-failure trap**: after "prevent this page from creating additional dialogs", it returns false with no UI. "Apply to All Reports" looked dead. Use an in-app Dialog.
5. **Lot Explorer reports ready before tiles paint** (`Embed.ready()` at boot). Snapshots taken early bake the loading overlay; poll `__mylot_capture()` instead of DOM-capturing the host card.
6. **Dead components**: `LandedMixTable`, `RiskFlagsPanel`, `AlandGisLotPopup` (unmounted). Don't fix bugs there expecting users to see them.
