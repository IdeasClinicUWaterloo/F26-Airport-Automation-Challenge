# Unified Identity Gateway

<div align="center">
  <img width="328" height="65" alt="Unified Identity Gateway project banner" src="https://github.com/user-attachments/assets/94cde17a-04b2-47f6-bf4e-9e7f6566ccbb" />
</div>

The Unified Identity Gateway is a working example for the [Departure Control System challenge](../README.md). It combines booking lookup, document checks, seat selection, bag declaration, boarding-pass issuance, agent review, and audit logging in one check-in flow.

The project demonstrates how several small decisions contribute to one passenger status: `NOT_STARTED`, `IN_PROGRESS`, `CLEARED`, `BLOCKED`, or `NEEDS_REVIEW`. That status is derived from the underlying document, seat, bag, and boarding-pass state.

This is a learning prototype. The role switcher is not real authentication, and the identity checks are not suitable for production use.

## Table of Contents

- [Challenge](#challenge)
- [Potential Solutions](#potential-solutions)
- [Getting Started](#getting-started)
- [Resources](#resources)

## Challenge

Build or extend a check-in experience that makes passenger readiness clear to passengers and staff.

The supplied implementation supports three views:

- **Passenger:** Look up a booking, submit document information, choose a seat, declare bags, and receive a boarding pass when cleared.
- **Agent:** View passengers by status, help complete check-in, override a blocked or review status with a reason, and inspect the audit log.
- **Admin:** Add flights and passenger bookings for testing.

The role switcher in the header stands in for signing in as a passenger, agent, or operations administrator. Each view stays mounted when you switch roles, so work in one view is not reset when you inspect another.

Successful improvements should consider:

- clear reasons for blocked and review states
- safe manual overrides with an audit trail
- atomic seat assignment so two passengers cannot book the same seat
- passenger privacy and minimal data collection
- accessible forms, status messages, and error feedback
- normal, blocked, and exceptional test cases

### How It Works

#### Passenger Check-In Flow

A passenger looks up a booking using a booking reference and last name, then completes four steps:

1. **Document:** Enter passport number, name, date of birth, nationality, and expiry date. The rules engine calculates a confidence score and identifies missing or inconsistent information. Some issues block check-in, while others require manual review.
2. **Seat:** Choose from the flight's actual seat inventory, grouped into front, middle, and rear cabin zones. Occupied seats are disabled, and booking is handled atomically to prevent two passengers from receiving the same seat.
3. **Bags:** Declare the bag count and weight of each bag. A bag above the flight's configured maximum weight sends the passenger to review rather than blocking the entire process automatically.
4. **Boarding pass:** Once cleared, issue a QR-coded boarding pass and one QR-coded tag for each declared bag.

The overall status is derived from document, seat, bag, and boarding-pass state. It moves through `NOT_STARTED`, `IN_PROGRESS`, `CLEARED`, `BLOCKED`, or `NEEDS_REVIEW`; it is not a value set independently of the underlying records.

[Watch the passenger self-check-in flow](https://github.com/user-attachments/assets/d017b474-5400-4cbd-ab1d-dfd5042acbbf).

#### Agent View

An agent selects a flight and sees every passenger's current status. The table can be filtered to passengers who are `BLOCKED` or `NEEDS_REVIEW`. Selecting a passenger opens the same check-in wizard so an agent can help in person.

The override panel lets an agent clear a blocked or review status only after entering a reason. The system records who performed the override, when it happened, the previous status, the new status, and the reason. That history is available from the same panel.

#### Admin View

An administrator can add a flight with its flight number, route, departure time, aircraft type, and maximum bag weight. The application also generates the flight's seat map using the same three-zone layout as the seed data.

An administrator can add a passenger booking to an existing flight with a booking reference, name, and optional group ID. The new booking becomes available immediately in the passenger and agent views.

[Watch the admin flow and live agent update](https://github.com/user-attachments/assets/eedf8dd8-e2ce-4810-ae7a-5ad2735c157f).

#### Rules Engine

The logic in [`apps/api/src/rules/`](apps/api/src/rules/) is dependency-free and tested separately from the API:

- `confidenceScore.ts` scores document completeness and format from 0 to 100.
- `validateDocument.ts` turns document fields into blocking and review issues.
- `status.ts` derives the overall check-in status from document, seat, bag, override, and boarding-pass state.

Boarding-pass issuance is sticky. Resubmitting a document or bag record after a pass is issued does not silently revoke it.

## Potential Solutions

The working application can be used as a base for several focused projects.

| Potential solution | Description | Starting point |
| --- | --- | --- |
| Better document checks | Add clear validation rules and tests without pretending uncertain checks are definitive. | [`apps/api/src/rules/`](apps/api/src/rules/) |
| Accessible check-in | Improve keyboard navigation, labels, focus handling, status announcements, and readable error messages. | [`apps/web/src/components/CheckInWizard.tsx`](apps/web/src/components/CheckInWizard.tsx) |
| Agent decision support | Prioritize passengers needing review and explain the next useful action. | [`apps/web/src/components/AgentView.tsx`](apps/web/src/components/AgentView.tsx) |
| Stronger audit history | Make overrides easier to review by passenger, agent, flight, or reason. | [`apps/api/src/routes/override.ts`](apps/api/src/routes/override.ts) |
| Bag exception handling | Add configurable limits, clearer review reasons, or links to bag-tracking events. | [`apps/api/src/routes/bags.ts`](apps/api/src/routes/bags.ts) |
| Privacy controls | Add retention, redaction, consent, or role-based data visibility. | [`apps/api/prisma/schema.prisma`](apps/api/prisma/schema.prisma) |
| Operations summary | Show check-in completion, blocked passengers, review queues, and flight readiness in one view. | [`apps/web/src/components/AgentView.tsx`](apps/web/src/components/AgentView.tsx) |

## Getting Started

Run commands from the `departure-control-system/unified-identity-gateway` folder.

You need Node.js, npm, and either Docker or a local PostgreSQL 16 installation.

### 1. Start PostgreSQL

With Docker:

```bash
docker compose up -d postgres
```

### 2. Start the API

On macOS or Linux:

```bash
cd apps/api
cp .env.example .env
npm install
npx prisma migrate deploy
npx tsx prisma/seed.ts
npm run dev
```

On Windows PowerShell:

Windows PowerShell 5.1 does not support `&&` command chaining, so run each command on its own line.

```powershell
cd apps\api
copy .env.example .env
npm install
npx prisma migrate deploy
npx tsx prisma/seed.ts
npm run dev
```

The API runs on `http://localhost:3001`.

Check it before starting the web app:

```powershell
Invoke-WebRequest http://localhost:3001/health
```

The response should contain `{"status":"ok"}`.

If the request hangs or is refused, the API is not listening. Check the terminal running `npm run dev` before debugging a "failed to fetch" message in the browser.

### 3. Start the Web App

Open a second terminal in the Unified Identity Gateway folder.

On macOS or Linux:

```bash
cd apps/web
cp .env.example .env
npm install
npm run dev
```

On Windows PowerShell:

```powershell
cd apps\web
copy .env.example .env
npm install
npm run dev
```

Open the Vite address printed in the terminal, usually `http://localhost:5173`.

### 4. Try the Seeded Examples

| Booking | Last name | Expected case |
| --- | --- | --- |
| `CLEAN1` | `Doe` | Clean check-in flow |
| `NOPASS` | `Lee` | Missing passport number and blocked status |
| `EXPIRD` | `Khan` | Expired document and blocked status |
| `NAMEMM` | `Smith` | Name mismatch and blocked status |
| `OVRWGT` | `Patel` | Overweight bag and manual review |
| `GROUP1` | `Nguyen` | Passenger in a shared booking group |
| `GROUP2` | `Nguyen` | Second passenger in the same booking group |
| `XCHECK` | `Chen` | Passenger on the second seeded flight |

Switch to the agent view to review a blocked passenger, enter an override reason, and inspect the audit history.

All examples except `XCHECK` are on flight `DC101` from JFK to LHR. `XCHECK` is on flight `DC202` from JFK to DXB.

### 5. Run Tests

With PostgreSQL running and migrated:

```bash
cd apps/api
npx vitest run
```

## Resources

### Project Structure

| Location | Purpose |
| --- | --- |
| [`apps/api/src/routes/`](apps/api/src/routes/) | Fastify API routes for passengers, documents, seats, bags, boarding passes, overrides, and flights |
| [`apps/api/src/rules/`](apps/api/src/rules/) | Dependency-free confidence, validation, and status logic |
| [`apps/api/prisma/`](apps/api/prisma/) | PostgreSQL data model, migrations, and seed data |
| [`apps/api/tests/`](apps/api/tests/) | Rule tests and end-to-end API smoke test |
| [`apps/web/src/components/`](apps/web/src/components/) | Passenger, agent, admin, seat, override, and boarding-pass interfaces |
| [`apps/web/src/api.ts`](apps/web/src/api.ts) | Typed web client for the API |
| [`docs/challenge-spec.md`](docs/challenge-spec.md) | Original challenge specification |

The main source tree is organized as follows:

```text
apps/
  api/
    src/
      routes/       passengers, documents, seats, bags, passes, overrides, and flights
      rules/        confidence scoring, validation, and status derivation
    prisma/
      schema.prisma PostgreSQL data model
      seed.ts       flights, seat maps, and passengers covering each status
    tests/
      rules/        isolated rules-engine tests
      api.smoke.test.ts
  web/
    src/
      components/   passenger, agent, admin, seat, override, and pass interfaces
      api.ts        typed API client
      types.ts      shared frontend types
docs/
  challenge-spec.md
```

### Technology

- **API:** Fastify 4 with TypeScript, Prisma 5, Zod validation, and Vitest tests
- **Web:** React 19 with TypeScript and Vite, using project-specific components and CSS
- **Database:** PostgreSQL, run through Docker or a compatible local installation

- [Fastify documentation](https://fastify.dev/docs/latest/)
- [Prisma documentation](https://www.prisma.io/docs)
- [React documentation](https://react.dev/)
- [Vite documentation](https://vite.dev/guide/)
- [Vitest documentation](https://vitest.dev/guide/)

### Safety and Privacy

- [Secure Air Travel Regulations](https://laws-lois.justice.gc.ca/eng/regulations/SOR-2015-181/FullText.html)
- [Personal Information Protection and Electronic Documents Act](https://laws-lois.justice.gc.ca/eng/acts/P-8.6/index.html)
- [Accessible Transportation for Persons with Disabilities Regulations](https://laws-lois.justice.gc.ca/eng/regulations/SOR-2019-244/index.html)

Do not use real passenger, passport, biometric, or medical information in this prototype.
