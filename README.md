# IELPS — final correction pass, 19 August 2026

Executed against the *Response to Anirudha — Final Pre-Deployment Corrections
(Revised Pip Rule)*, 19 August 2026. This is the §12 sequence carried out in
order, and the exact candidate frozen at the end of it.

**Production is unchanged.** Nothing here has been deployed. Deployment requires
a systemd unit change and remains the Administrator's to execute.

---

## 1. Release identity

| | |
| --- | --- |
| Commit | `83cc0600a04503d6013aaebc04b03e7618dc31f4` |
| Supersedes | `64a91d27077433c44615a3bc08a92f87202bed46` |
| Build ID | `dIPGS5KhNncuyyiVFyVkx` |
| Source files | 120 |
| Manifest SHA-256 | `5d61956bb2ff4d39cf92b60b2b872366255ec8d4958f2ffa97a503edc0884421` |
| TypeScript / lint / build | 0 / 0 / 0 |
| Functional | 48 / 48 |
| PiP settled-state | 91 resting positions, 0 controls blocked |
| Chip → backend audit | 87 declared, 87 matched, 0 unmatched |
| Repo / branch | `10495109/v0-ielps-platform-h4`, `visual-direction-20260815` |

On the file count: the 18 August manifest listed 118. This one lists 120. One is
the genuinely new file, `components/pip/use-pip-settle.ts`; the other is
`.gitignore`, which the previous manifest happened to omit. No file was deleted
and none was added beyond the hook.

## 2. Changed files

Eight files, one of them new.

| File | § | What changed |
| --- | --- | --- |
| `components/pip/use-pip-settle.ts` | 5, 6, 7 | **New.** The settled-state collision rule: measure on scroll-stop, move only if the approved anchor covers a control. |
| `components/pip/pip-agent.tsx` | 5, 6 | Consumes the hook; publishes its own state as `data-pip-motion` / `data-pip-placement` / `data-pip-obstructed`. |
| `app/globals.css` | 5 | Presentation for the two adapted states. The anchored state is untouched. |
| `lib/ielps-data.ts` | 4 | School roster chip corrected to the real route, with a truthful `parameter-required` state on the `Endpoint` type. |
| `components/pathways-section.tsx` | 4 | Renders that state under the chip strip. |
| `lib/apps/studio.ts` | 8, 9 | AI Governance reorganised to the creator / Administrator / Teacher-School boundary; new prepared AI Credits screen. |
| `lib/apps/types.ts` | 8 | `note` panels can carry bullets, for boundaries that a paragraph would bury. |
| `components/app/panel.tsx` | 8 | Renders those bullets. |

Nothing else moved. The CEFR retirement, the restored API chips, the level band
and the Public Landing are all byte-identical to `64a91d2`.

---

## 3. §12.1 — School roster card

The chip previously read `GET /api/roster/providers`, which is not a registered
route. §4 made this a semantic question with two different right answers, so the
first job was deciding which thing the card actually means.

It means **this organisation's configured connections**, not a global provider
catalogue. Two reasons. The card's other two chips are
`/api/school/admin/overview` and `/api/billing/subscription`, both scoped to one
organisation. And the card's own copy describes bulk rostering *at organisation
scale* — a specific institution's integrations, not a marketing list of what
IELPS supports.

So the chip is now:

```
GET /api/roster/organizations/:id/connections     PARAMETER REQUIRED
Organisation id comes from signed-in School context.
```

That route is real: `roster_provider.js` registers it under the `/api/roster`
mount, and it is line 101 of `backend-routes-19aug.txt`. The organisation id is
not available to a signed-out Access Panel card, so the card says
PARAMETER REQUIRED rather than implying a call that is ready to fire.

No provider-list route was invented. The card was not removed. Nothing was
renamed or duplicated. Screenshot: `schools-card-parameter-required.png`.

## 4. §12.2, §12.3 — the revised Pip rule

### What the implementation does

While the page is moving, **nothing happens**. PiP keeps its approved anchor and
its approved size and floats over whatever is beneath it. That is the permitted
transient overlap and it is not measured.

180ms after the last scroll or resize event, PiP asks one question: *is my
approved resting position covering something the learner needs to press?* The
answer is no on most surfaces, and in that case **nothing changes at all** —
same position, same size, same appearance that was approved.

Where the answer is yes, PiP adapts, in this order:

1. **Shrink and move.** It becomes a compact circle (52px desktop and tablet,
   44px mobile) and walks the right edge from the bottom upward, then the left
   edge, taking the first position that covers nothing.
2. **Tuck.** Where neither edge has a clear square — the real case is a stacked
   full-width card list at 390px, where the only clear channel is the page's
   16px gutter — PiP keeps its full hit area but slides most of itself past the
   edge of the screen, leaving a handle in that gutter. The handle covers
   nothing and one tap brings PiP back.
3. **Report.** If even the tuck is covered, PiP takes the least-obstructive
   position and sets `data-pip-obstructed`. Nothing in this build reaches that
   branch; it exists so that a future screen that does is visible rather than
   silent.

The permissions in §5 that were used: resize, reposition, movement and settling
behaviour, and desktop and tablet as well as mobile. The permissions that were
**not** used: recolour, Reading typography, answer-card visual design. None of
those turned out to be needed, and §5 says these are permissions rather than
requirements, so the approved appearance is left alone.

### What was measured

`pip_settled_19aug.py` walks **11 surfaces × 3 widths**, stopping at every
viewport step and waiting past the idle threshold before measuring — so every
number is a settled-state number, never a mid-motion one. At each stop PiP's
rectangle is compared against every reachable `a[href]`, `button`, `input`,
`select`, `textarea` and button/link/tab/checkbox/radio role on screen. A card
that is itself a link counts, because that link is the card's Open action.

```
stops measured at rest:                       91
stops where a control was blocked at rest:     0
```

Full per-stop record in `pip-settled-19aug.json`.

### §12.3 — the 390px Reading case specifically

This was the one genuine failure reported on 18 August: PiP covered the right
end of the second and third answer options. At rest, PiP now moves clear and all
three options are fully tappable. `reading-answers-mobile-settled.png` and
`reading-answers-mobile-bottom.png` show the full scroll range.

**Stated plainly:** this is measured on `/preview/lesson-interactions/`. The real
lesson player is entitlement-gated and unlocking it is a live $3 Stripe charge,
which §10 says not to make. The preview harness renders the same reading
activity component and the same answer buttons, but it is a harness, and I am
not claiming the gated player was tested.

### §7 — the Adult mini-app overlap, reclassified

Reclassified as instructed: mid-scroll overlap is permitted, the settled state is
what matters. On that page at tablet and mobile, every card runs the full width,
so at rest PiP tucks into the 16px gutter and covers nothing.
`adult-index-mobile-tucked.png`, `adult-index-tablet-tucked.png`,
`adult-index-desktop-cleared.png`.

### Two things the tuck must not break

Both checked rather than assumed (`pip_tuck_check.py`):

| Surface | Placement | Handle visible | Horizontal page overflow | Opens on tap |
| --- | --- | --- | --- | --- |
| `/app/adult/` at 390 | tucked | 16px | 0px | yes |
| `/app/adult/` at 900 | tucked | 16px | 0px | yes |
| `/preview/lesson-interactions/` at 390 | anchored | 74px | 0px | yes |

A fixed element parked partly past the right edge could have added horizontal
scroll to the page, which would have been a worse bug than the one it fixes. It
does not.

### One honest limitation

A 16px handle is discreet — a learner glancing at that page might not notice PiP
in the settled state. It becomes fully visible again the moment they scroll, and
it is only ever this small on a page that leaves no room. If you would rather it
stayed prominent and accepted the card overlap on that one surface instead, that
is a one-line change and your call to make.

Collision avoidance runs for the closed launcher only. An open panel is an
interaction the learner just started and carries its own close button, so it
stays where it was approved.

## 5. §12.4 — Studio AI Governance role separation

The screen previously read as one undifferentiated governance surface, which put
learner moderation and administrator prompt control in front of a creator as
though both were theirs. It now follows §8's table.

**A creator's, and shown as theirs:**

| Panel | Endpoint |
| --- | --- |
| Your AI allowance and usage | `GET /api/studio/ai/governance` |
| AI service readiness | `GET /api/studio/ai/governance` |
| Generated content awaiting your review | `GET /api/studio/ai/governance` |
| Human review before publication | (statement, no endpoint) |

The third of those was previously titled "Moderation queues", which read as
learner moderation. It is generated-content review, and now says so.

**Not a creator's, and named as such** rather than silently missing — a "Governed
elsewhere" panel states that global prompt versions, activation, evaluation runs
and platform AI policy are Administrator AI Governance, and that learner
activity, practice and checkpoint moderation and learner speaking and writing
certificate evidence belong to the Teacher and School assessment workflow.

The administrator panel `GET /api/tutor/admin/prompts` remains on the page and
remains administrator-gated. Verified by driving the response status directly
(`role_states_19aug.py`):

| Server answer | What the creator is shown |
| --- | --- |
| `401` | Sign in to load this account data. |
| `402` | An active lesson or subscription entitlement is required. |
| `403` + administrator message | **An administrator role is required to view these records.** |
| `403` other | This account does not have permission to view these records. |

4 / 4. No permission was loosened and no administrator payload is rendered.

## 6. §12.5 — AI Credits, prepared only

`/app/studio/credits/` states the approved model and nothing beyond it:
subscription → included monthly allowance → billable generation consumes credits
→ optional top-ups where enabled. Governance is stated as free to open. Projects,
existing generations, manual editing, review and preview are stated as free.
Credits are the creator-facing unit. The server is stated as the sole authority
on balance and events. Failed provider work is stated as not leaving a charge.

Checked by test, not by eye:

- no `$`, `€` or `£` followed by a digit anywhere on the screen;
- no "*n* credits" figure anywhere;
- **no endpoint chip at all**, because the credit routes do not exist and a chip
  for an unregistered route is exactly what the API rule forbids;
- "Live top-up billing is not enabled" stated on the page.

The balance panel deliberately shows no number. It says in words that it will
read the figure once the endpoint is built, rather than showing an example one.

The server half — credit-event flow, exact billing changes, exact database
changes, proposed routes and permissions — is written up in
**`AI-CREDITS-IMPLEMENTATION-NOTE.md`**. Nothing in it has been applied: no
migration run, no route added, no Stripe object created. It ends with four things
I need from you before any of it can be built, three of which are commercial
values that are not mine to choose.

## 7. §12.6 — what was preserved

Untouched, and verified untouched:

- The CEFR retirement. `/access/` and all six `/levels/*` still 404
  (checked at both `:4879` and through the harness).
- All CEFR content: codes, descriptors, IELPS names, the six definitions, real
  course titles and counts, `Continue with {LEVEL}`, the A1–C2 selector and the
  selected-level band. `lib/cefr-levels.ts` is byte-identical.
- Selected level only. No six-level catalogue, no Basic / Independent /
  Proficient grouping carried into the Access Panel.
- The unused grouping field in `lib/cefr-levels.ts` is **left alone**, per §2.
- The restored GET/POST chips and the three route corrections from 18 August.
- The Public Landing. Not touched in any way.
- The Adult mini-app. Byte-identical to approved.

## 8. §12.7, §12.8 — build and audit

```
TypeScript   0 errors
ESLint       0 problems
next build   succeeded, 19 static pages
Functional   48 / 48   (functional-19a.json)
```

The 28 checks from 18 August all still pass; 20 new ones cover this pass.

The backend route table was **re-extracted from the running server today**
rather than reused: 33 mounts, 266 routes (`backend-routes-19aug.txt`). It is
identical to yesterday's table, so nothing on the backend moved under us.

```
declared chips: 87   matched: 87   unmatched: 0
```

Full per-chip record in `chip-audit-19aug.json`. The one endpoint I stopped on
yesterday is now resolved and matched.

Worth repeating, because it is why this is read from source and not probed: every
router calls `authRequired` before any route matches, so an unauthenticated
request to a path that **does not exist** returns 401, not 404. A probe cannot
tell you a route is real.

## 9. §12.9 — role states and browser network evidence

`role-network-19aug.json` records every `/api` request each surface makes as it
loads, with the status the live backend returned. Signed out, so:

| Surface | API calls | Statuses |
| --- | --- | --- |
| Access Panel home | `/api/auth/me`, `/api/auth/pathways` | 401, 200 |
| Adult dashboard | `/api/auth/me`, `/api/curriculum/deep-summary`, `/api/engine/schedule`, `/api/progress` | 401, 200, 401, 401 |
| Parent dashboard | `/api/auth/me`, `/api/school/parent/dashboard` | 401, 401 |
| School roster | `/api/auth/me`, `/api/school/classes` | 401, 401 |
| School admin overview | `/api/auth/me`, `/api/integrations/status`, `/api/school/admin/overview` | 401, 200, 401 |
| Studio AI governance | `/api/auth/me`, `/api/studio/ai/governance`, `/api/tutor/admin/prompts` | 401, 401, 401 |
| Studio AI Credits | `/api/auth/me` | 401 |

Every request goes to the path its chip declares. No surface requests anything
it does not label, and no surface labels anything it does not request.

**One artefact you will see in that file, and it is mine, not the product's.**
Each page also shows `POST /api/auth/refresh → 308` followed by
`POST /api/auth/refresh/ → 404`. My evidence proxy forwards only `GET` to the
live server — deliberately, so nothing can be written to production while
testing — so the `POST` falls through to the Next.js server and gets a
trailing-slash redirect. Against real production the same call answers correctly:

```
POST https://eilps.com/api/auth/refresh  →  401
```

`POST /api/auth/refresh` is a registered route (`backend-routes-19aug.txt`).

**What is *not* evidenced:** the signed-in branches. This account is signed out,
so 401 is the only server-produced role state here. The other three mappings are
verified against the classifier by driving the status directly, which proves what
a learner is shown for each answer but not that the server produces that answer
for a given role. Saying otherwise would overstate it.

## 10. §12.10 — visual, no-clutter and interaction at three widths

Captures at 1280 / 900 / 390 for nine surfaces, viewport-sized only:
`desktop__*.png`, `tablet__*.png`, `mobile__*.png`.

Density, characters of visible text per 1000px of page height, against
`64a91d2`:

| Surface | 64a91d2 | 83cc060 | |
| --- | ---: | ---: | --- |
| Access Panel home | 982 | 998 | +16, the PARAMETER REQUIRED line |
| Home with level chosen | 985 | 999 | same line |
| Adult mini-app index | 696 | 687 | unchanged content |
| Adult dashboard | 811 | 811 | unchanged |
| Parent dashboard | 718 | 718 | unchanged |
| School roster | 474 | 474 | unchanged |
| Lesson interactions (harness) | 1384 | 1384 | unchanged |
| **Studio AI governance** | 980 | **1292** | the role boundaries are now on the page |
| **Studio AI Credits** | — | **1473** | new screen |

The two Studio numbers went up and I am not going to bury that. Governance rose
because §8 asked for the role separation to be *rendered*, which means words on
the page; the screen grew from 800px to 1291px. Credits is 1473, the densest
surface in the build, because it is entirely explanatory prose — that is what a
policy screen is. Neither is a learner surface. If you want either condensed,
say so and I will condense it.

## 11. §13 — acceptance gate

| Area | Status |
| --- | --- |
| CEFR | PASS — retired and preserved exactly as before |
| Access Panel level band | PASS — selected level only, canonical hierarchy |
| API chips | PASS — 87/87 truthful to the actual backend contract |
| School roster | PASS — real route, PARAMETER REQUIRED, nothing invented |
| Pip interaction | PASS — 91 resting positions, 0 controls blocked |
| Reading answers | PASS — all three options fully usable at rest at 390px |
| Adult mini-app | PASS — settled-state controls reachable at all three widths |
| Studio governance | PASS — creator / Administrator / Teacher-School separated |
| AI Credits | Prepared to scope. No pricing, no live top-up, no chip for an unbuilt route |
| Lesson Player gated test | **SIGNED-IN TEST OUTSTANDING** — no safe entitlement exists; no live charge made |
| Public Landing | UNCHANGED |
| Build / TS / lint | PASS |
| Final exact identity | Fresh SHA, build ID, manifest, inventory, changed-file list, Administrator pack |

## 12. Administrator pack

Deployment is a systemd unit change and is the Administrator's to execute. I have
not run any of this.

**Current unit, verbatim** (`/etc/systemd/system/eilps-learner.service`):

```ini
[Unit]
Description=IELPS immutable A1-C2 learner experience
After=network.target eilps-web.service
Wants=eilps-web.service

[Service]
Type=simple
User=anirudhat
Group=anirudhat
WorkingDirectory=/home/anirudhat/eilps/releases/ielps-a1-c2-learner-20260805-r4-discovery
Environment=NODE_ENV=production
Environment=PORT=4302
Environment=DIST=/home/anirudhat/eilps/releases/ielps-a1-c2-learner-20260805-r4-discovery/out
ExecStart=/usr/bin/node /home/anirudhat/eilps/releases/ielps-a1-c2-learner-20260805-r4-discovery/runtime/learner-server.mjs
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

The live release is a **static export** served from `out/` by a bundled runtime
script. This candidate is a **Next.js standalone build** that runs its own
server. That is the whole reason a unit change is unavoidable and the whole
reason this is not something I can do.

**Four lines change, one is removed:**

```ini
WorkingDirectory=/home/anirudhat/eilps/releases/ielps-learner-20260819-83cc060
Environment=PORT=4302
Environment=HOSTNAME=127.0.0.1
ExecStart=/usr/bin/node /home/anirudhat/eilps/releases/ielps-learner-20260819-83cc060/server.js
# Environment=DIST=...   ← delete this line, standalone does not use it
```

**Steps:**

1. Unpack the release to
   `/home/anirudhat/eilps/releases/ielps-learner-20260819-83cc060/`.
   It must contain `server.js`, `.next/`, and `public/`.
2. Edit the unit as above.
3. `systemctl daemon-reload`
4. `systemctl restart eilps-learner`
5. Run the six health checks below.

**Expected interruption:** a few seconds while the service restarts. `/learner/`
will be briefly unavailable. Nothing else on the box is affected — `eilps-web`
and the API on 4300 are untouched.

**Six health checks, against real URLs:**

| # | Check | Expected |
| --- | --- | --- |
| 1 | `curl -s -o /dev/null -w '%{http_code}' https://eilps.com/learner/` | `200` |
| 2 | `curl -s https://eilps.com/learner/ \| grep -c 'Your chosen level'` | `0` (no band without `?level`) |
| 3 | `curl -s -o /dev/null -w '%{http_code}' https://eilps.com/learner/access/` | `404` |
| 4 | `curl -s -o /dev/null -w '%{http_code}' https://eilps.com/learner/levels/a1/` | `404` |
| 5 | `curl -s https://eilps.com/learner/app/adult/ \| grep -c 'ielps-pip'` | `≥1` |
| 6 | `curl -s https://eilps.com/learner/app/studio/credits/ \| grep -c 'AI Credits'` | `≥1` |

**Rollback:** restore the four lines to the values in the verbatim block above,
`systemctl daemon-reload`, `systemctl restart eilps-learner`. The current release
directory is left in place and untouched, so rollback is a unit edit and a
restart — no file restore, no data change.

## 13. Evidence index

| File | What it is |
| --- | --- |
| `SOURCE-SHA256-19aug.txt` | Per-file SHA-256, 120 files |
| `backend-routes-19aug.txt` | 266 routes re-extracted from the running backend today |
| `chip-audit-19aug.json` | Every declared chip against that table, 87/87 |
| `functional-19a.json` | 48 functional checks |
| `pip-settled-19aug.json` | Every settled-state measurement, 91 stops |
| `role-network-19aug.json` | Per-surface API calls and statuses, plus the four role-state mappings |
| `density.json` | No-clutter density at 1280 |
| `AI-CREDITS-IMPLEMENTATION-NOTE.md` | §9 server-side proposal |
| `pip_settled_19aug.py` | The settled-state acceptance test |
| `pip_tuck_check.py` | Overflow and tappability of the tucked handle |
| `functional19a.py` · `verify_chips.py` · `role_states_19aug.py` · `capture19a.py` · `capture19b.py` | The rest of the harness |
| `*.png` | Captures at 1280 / 900 / 390 |

## 14. Still open

1. **Deployment.** NOT YET DEPLOY APPROVED. Production stays as it is until you
   approve this SHA.
2. **AI Credits.** Four questions at the end of the implementation note; three
   are commercial values that are yours to set.
3. **Lesson Player.** SIGNED-IN TEST OUTSTANDING. If an authorised non-charging
   QA entitlement exists, point me at it and I will turn this green properly. I
   am not making a live charge to do it.
4. **The 16px Pip handle.** Discreet by design. Say the word if you would rather
   it stayed prominent on that one surface.
