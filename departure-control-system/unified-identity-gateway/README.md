# Unified Identity Gateway

A working implementation of the **Unified Identity Gateway** module from the [Departure Control System Automation challenge](docs/challenge-spec.md): passenger lookup, document verification, seat selection, bag declaration, and boarding pass issuance in a single check-in flow, plus an agent-facing view with override and audit logging.

There's no real authentication — a role switcher in the header toggles between the passenger self-service view, the agent view, and an admin view, standing in for "logged in as a passenger" vs. "logged in as a gate agent" vs. "logged in as ops staff." Switching roles doesn't reset whatever you were doing in the other views — each stays mounted in the background.

## How it works

### Check-in flow

A passenger looks up their booking by reference + last name, then works through four steps:

1. **Document** — passport number, name, date of birth, nationality, expiry date. A rules engine (`apps/api/src/rules/`) scores a confidence value and flags issues: empty passport number, expired document, name mismatch against the booking, etc. Some issues hard-block check-in; others just flag the passenger for manual review.
2. **Seat** — an actual seat map (`apps/web/src/components/SeatMap.tsx`), grouped by cabin zone (front/mid/rear), rendered from the flight's real seat inventory. Occupied seats are visibly disabled; picking an available seat books it atomically (no double-booking race).
3. **Bags** — declare a bag count and a weight per bag. Any bag over the flight's configured max weight flags the passenger for review instead of hard-blocking.
4. **Boarding pass** — once cleared, issue a boarding pass with a QR code (and one QR-coded bag tag per declared bag).

At every step the passenger's overall status (`NOT_STARTED` → `IN_PROGRESS` → `CLEARED` / `BLOCKED` / `NEEDS_REVIEW`) is recomputed from document + seat + bag state — it isn't a flag you set directly, it's derived.

### Agent view

An agent picks a flight, sees every passenger's live status in a table, and can filter to `BLOCKED` / `NEEDS_REVIEW`. Selecting a passenger opens the same check-in wizard (so an agent can walk someone through check-in in person) plus an **override panel**: if a passenger is blocked or flagged, an agent can clear them with a typed reason, which is written to an audit log. The audit log for a passenger (who overrode what, when, and why) is viewable from the same panel.

### Admin view

An admin can add a new flight (flight number, route, departure time, aircraft type, max bag weight) — this also generates that flight's seat map (3 zones × 3 rows × 3 seats, same layout the seed data uses). An admin can also add a passenger booking to any existing flight (booking reference, name, optional group ID), which immediately becomes look-up-able from the passenger view.

### Rules engine

`apps/api/src/rules/` is pure, dependency-free logic, unit-tested in isolation:

- `confidenceScore.ts` — scores a submitted document 0–100 based on field completeness and format validity.
- `validateDocument.ts` — turns document fields into a list of issues (some hard-blocking, some soft).
- `status.ts` — derives a passenger's overall `CheckInStatus` from their document, seat, and bag state, plus whether a boarding pass already exists (issuance is sticky — resubmitting a document or bags after a pass is issued doesn't silently revoke it).

## Tech stack

- **API**: Fastify 4 + TypeScript, Prisma 5 over Postgres, Zod for request validation, Vitest for tests.
- **Web**: React 19 + TypeScript (Vite), no UI framework — hand-rolled components and CSS.
- **DB**: Postgres. No Docker required — works against a local Postgres install (see below). If on mac, ensure you have docker installed and implement using docker.

## Project structure

```
apps/
  api/
    src/
      routes/     one file per resource (passengers, document, seat, bags, boardingPass, override, flights)
      rules/       pure check-in rules engine (confidence scoring, validation, status derivation)
    prisma/
      schema.prisma  data model (Flight, Seat, Passenger, Document, Bag, BoardingPass, AuditLog)
      seed.ts         seeds two flights, a seat map each, and ~8 passengers covering every status
    tests/
      api.smoke.test.ts   end-to-end flow through the live API
      rules/               unit tests for the rules engine
  web/
    src/
      components/  CheckInWizard, SeatMap, AgentView, PassengerView, AdminView, OverridePanel, BoardingPassCard, ...
      api.ts       typed fetch client
      types.ts     shared frontend types
docs/
  challenge-spec.md   the original hackathon brief this module was built from
```

## Running locally

```bash
docker compose up -d postgres   # or `brew services start postgresql@16` if you're not using Docker
cd apps/api && cp .env.example .env && npm install && npx prisma migrate deploy && npx tsx prisma/seed.ts && npm run dev
# in a second terminal
cd apps/web && cp .env.example .env && npm install && npm run dev
```

API on `http://localhost:3001`, web UI on the Vite dev URL printed in the terminal (typically `http://localhost:5173`).

Run API tests: `cd apps/api && npx vitest run` (requires Postgres running and migrated).

### Windows (PowerShell)

Windows PowerShell 5.1 (VS Code's default terminal) doesn't support `&&` chaining, so run each line separately:

```powershell
docker compose up -d postgres
cd apps\api
copy .env.example .env
npm install
npx prisma migrate deploy
npx tsx prisma/seed.ts
npm run dev
```

```powershell
# in a second terminal
cd apps\web
copy .env.example .env
npm install
npm run dev
```

Before moving to the web UI, confirm the API actually started by hitting the health check — a silently hung/crashed API is what produces "failed to fetch" in the browser with no other clue:

```powershell
Invoke-WebRequest http://localhost:3001/health
```

It should return `{"status":"ok"}`. If it hangs or refuses, the API process isn't listening — check the terminal running `npm run dev` for errors before debugging the frontend.

### Demo walkthrough

- **Passenger view**: look up booking `CLEAN1` / last name `Doe`, walk through document → seat → bags → boarding pass. Try `NOPASS` / `Lee` with an empty passport number to see a blocked status with an explanation.
- **Agent view**: pick a flight, click a passenger with a `BLOCKED` or `NEEDS_REVIEW` status, use the override panel to clear them with a reason, then load the audit log to see the recorded override.

Seeded bookings (all on flight `DC101` JFK→LHR unless noted): `CLEAN1`/Doe (clean), `NOPASS`/Lee (missing passport number → blocked), `EXPIRD`/Khan (expired document → blocked), `NAMEMM`/Smith (name mismatch → blocked), `OVRWGT`/Patel (overweight bag once declared → needs review), `GROUP1`/Nguyen and `GROUP2`/Nguyen (same `groupId`), `XCHECK`/Chen (on flight `DC202` JFK→DXB).
