# Unified Identity Gateway — Design

## Purpose

Implement the Unified Identity Gateway (UIG) module from the DCS hackathon challenge (see `README.md`): a single check-in flow combining identity verification, document validation, seat confirmation, bag declaration, and boarding pass / bag tag issuance — instead of three separate tools. The system must clearly surface whether a passenger is **cleared**, **blocked**, or **needs manual review**, and why.

## Scope

In scope:
- Full-stack app: REST API + web UI, backed by a persistent Postgres database.
- Deterministic document validation rules engine, including a mock document confidence score.
- Passenger self-service check-in flow and an agent-facing console, switchable via a UI role toggle (no real authentication).
- Agent override of blocked/needs-review status, with a required reason and an audit log.
- Boarding pass and bag tag generation, rendered with a QR code encoding the record id.
- Seeded mock data covering all status paths for demo purposes.

Out of scope (belongs to other DCS modules per README):
- Real-time bag movement tracking (scan events, induction/screening/sorting/loading states) — that's the IoT Baggage Tracker module.
- Load/weight-and-balance estimation across cabin/cargo zones — that's the Predictive Load Controller module.
- Real OCR or biometric face-match — explicitly deferred; document fields are entered as structured data (simulating already-extracted fields), not images.
- Real authentication/session management.

## Architecture

Monorepo using npm workspaces:

```
dcs/
  apps/
    api/   Fastify + TypeScript + Prisma + Postgres
    web/   Vite + React + TypeScript
  docs/superpowers/specs/
```

## Data model (Prisma)

- **Flight**: id, flightNumber, origin, destination, departureTime, aircraftType, maxBagWeightKg
- **Seat**: id, flightId, seatNumber, cabinZone (`front`/`mid`/`rear`), occupied, passengerId (nullable)
- **Passenger**: id, bookingRef, firstName, lastName, flightId, groupId (nullable), checkInStatus (`NOT_STARTED`/`IN_PROGRESS`/`CLEARED`/`BLOCKED`/`NEEDS_REVIEW`), seatId (nullable), declaredBagCount, riskFlags (string array)
- **Document**: id, passengerId, passportNumber, fullName, dob, nationality, expiryDate, confidenceScore (0–100), issues (string array), status
- **Bag**: id, passengerId, flightId, tagId, weightKg, overweight (bool)
- **BoardingPass**: id, passengerId, flightId, seatNumber, qrPayload, issuedAt
- **AuditLog**: id, passengerId, actorRole, action, prevStatus, newStatus, reason, timestamp

## Rules engine

Pure, deterministic functions — no randomness, so every decision is explainable in the demo.

**Hard block → `BLOCKED`:**
- Missing or malformed passport number
- Document expiry date before flight departure date

**Soft flag → `NEEDS_REVIEW`** (only applied if no hard block):
- Name mismatch between booking name and document `fullName` (normalized comparison)
- Destination on a mock "extra checks required" country list
- `confidenceScore` below 60
- Declared bag weight exceeds the flight's `maxBagWeightKg`

**`CLEARED`**: no outstanding hard or soft flags, seat assigned, boarding pass issued.

**Confidence score**: weighted sum of field-completeness and format-validity checks (passport number format, expiry date validity, name presence, etc.), 0–100.

**Agent override**: any status → `CLEARED`, requires a reason string, writes an `AuditLog` row (prevStatus, newStatus, actorRole, reason, timestamp). Overrides are one-directional for v1 (no auto re-evaluation/reversal).

## API (Fastify)

```
GET  /flights
GET  /flights/:id/seatmap
GET  /passengers?flightId=                      agent search
GET  /passengers/lookup?bookingRef=&lastName=   passenger self-lookup
GET  /passengers/:id
POST /passengers/:id/document        submit doc fields -> validate -> status
POST /passengers/:id/seat            confirm/select seat
POST /passengers/:id/bags            declare bags -> tag gen + overweight check
POST /passengers/:id/boarding-pass   issue pass (only if CLEARED) -> QR gen
POST /passengers/:id/override        agent: targetStatus + reason -> audit log
GET  /passengers/:id/audit-log
```

All endpoints return JSON. Status-changing endpoints re-run the rules engine and return the updated `checkInStatus` plus the list of active issues/flags.

## Frontend (React)

Top-level role switcher: **Passenger** / **Agent** (UI-only mode toggle, no auth).

- **Passenger view**: booking reference + last name lookup, then a step wizard (document entry → seat selection → bag declaration → boarding pass / bag tag display). A persistent status badge shows cleared/blocked/needs-review with plain-language reasons pulled from `Document.issues` / `riskFlags`.
- **Agent view**: flight picker → passenger table (status column, filters for blocked/needs-review) → row detail opens the same step view plus an override panel (target status + reason) and the passenger's audit log.

QR codes are rendered client-side from `qrPayload` (a string encoding the boarding pass / bag tag id).

## Seed data

A seed script populates 2 flights with seat maps (3 cabin zones each) and ~18 passengers, covering every status path: clean/cleared, missing passport number, expired document, name mismatch, extra-check destination, overweight bag, and at least one group booking (shared `groupId`).

## Testing

- Vitest unit tests on the rules engine — pure functions, no DB dependency, covers each block/flag condition and the confidence score calculation.
- Light integration smoke tests on 2–3 representative API routes (document submission, override, boarding pass issuance).
- No heavy end-to-end test infrastructure, given hackathon scope.

## Open questions / explicit deferrals

None outstanding — stretch goals (face-match, OCR, real auth, bag movement tracking, load balancing) are explicitly deferred to future iterations or other DCS modules per the scoping decisions above.
