# Unified Identity Gateway Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the Unified Identity Gateway — a full-stack check-in app (document validation, seat confirmation, bag declaration, boarding pass/tag issuance, agent override) per `docs/superpowers/specs/2026-06-30-unified-identity-gateway-design.md`.

**Architecture:** npm-workspaces monorepo. `apps/api` = Fastify + TypeScript + Prisma + Postgres exposing the REST API and a pure, unit-tested rules engine. `apps/web` = Vite + React + TypeScript, role-switched UI (Passenger / Agent) calling the API directly via fetch.

**Tech Stack:** Fastify 4, Prisma 5, Postgres 16 (via docker-compose), Zod (request validation), Vitest, React 18, Vite, qrcode.react.

---

## File Structure

```
dcs/
  docker-compose.yml
  package.json                          (workspace root)
  .gitignore
  apps/
    api/
      package.json
      tsconfig.json
      .env.example
      prisma/
        schema.prisma
        seed.ts
      src/
        server.ts                       Fastify app bootstrap
        db.ts                           Prisma client singleton
        rules/
          confidenceScore.ts
          validateDocument.ts
          status.ts
        routes/
          flights.ts
          passengers.ts
          document.ts
          seat.ts
          bags.ts
          boardingPass.ts
          override.ts
      tests/
        rules/
          confidenceScore.test.ts
          validateDocument.test.ts
          status.test.ts
        api.smoke.test.ts
    web/
      package.json
      tsconfig.json
      vite.config.ts
      index.html
      .env.example
      src/
        main.tsx
        App.tsx
        api.ts
        types.ts
        styles.css
        components/
          RoleSwitcher.tsx
          StatusBadge.tsx
          PassengerView.tsx
          AgentView.tsx
          CheckInWizard.tsx
          OverridePanel.tsx
          BoardingPassCard.tsx
```

---

## Task 1: Monorepo scaffold

**Files:**
- Create: `package.json`
- Create: `.gitignore`
- Create: `docker-compose.yml`

- [ ] **Step 1: Create root package.json**

```json
{
  "name": "dcs-uig",
  "private": true,
  "workspaces": ["apps/*"]
}
```

- [ ] **Step 2: Create .gitignore**

```
node_modules/
dist/
.env
*.log
```

- [ ] **Step 3: Create docker-compose.yml for Postgres**

```yaml
services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_USER: dcs
      POSTGRES_PASSWORD: dcs
      POSTGRES_DB: dcs
    ports:
      - "5432:5432"
    volumes:
      - dcs_pg_data:/var/lib/postgresql/data

volumes:
  dcs_pg_data:
```

- [ ] **Step 4: Commit**

```bash
git add package.json .gitignore docker-compose.yml
git commit -m "chore: scaffold monorepo root"
```

---

## Task 2: API package scaffold

**Files:**
- Create: `apps/api/package.json`
- Create: `apps/api/tsconfig.json`
- Create: `apps/api/.env.example`
- Create: `apps/api/src/db.ts`
- Create: `apps/api/src/server.ts`

- [ ] **Step 1: Init package and install deps**

```bash
mkdir -p apps/api/src apps/api/tests
cd apps/api
npm init -y
npm install fastify @fastify/cors zod @prisma/client
npm install -D typescript tsx vitest @types/node prisma
cd ../..
```

- [ ] **Step 2: Write apps/api/package.json scripts (merge into generated file)**

```json
{
  "name": "@dcs/api",
  "version": "0.0.1",
  "type": "module",
  "scripts": {
    "dev": "tsx watch src/server.ts",
    "build": "tsc -p tsconfig.json",
    "start": "node dist/server.js",
    "test": "vitest run",
    "prisma:migrate": "prisma migrate dev",
    "prisma:seed": "tsx prisma/seed.ts"
  },
  "dependencies": {
    "@fastify/cors": "^9.0.0",
    "@prisma/client": "^5.0.0",
    "fastify": "^4.0.0",
    "zod": "^3.0.0"
  },
  "devDependencies": {
    "@types/node": "^20.0.0",
    "prisma": "^5.0.0",
    "tsx": "^4.0.0",
    "typescript": "^5.0.0",
    "vitest": "^1.0.0"
  }
}
```

- [ ] **Step 3: Create apps/api/tsconfig.json**

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "Bundler",
    "outDir": "dist",
    "rootDir": "src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "resolveJsonModule": true
  },
  "include": ["src"]
}
```

- [ ] **Step 4: Create apps/api/.env.example**

```
DATABASE_URL="postgresql://dcs:dcs@localhost:5432/dcs"
PORT=3001
```

- [ ] **Step 5: Create apps/api/src/db.ts**

```typescript
import { PrismaClient } from '@prisma/client';

export const prisma = new PrismaClient();
```

- [ ] **Step 6: Create apps/api/src/server.ts with a health route**

```typescript
import Fastify from 'fastify';
import cors from '@fastify/cors';

export function buildServer() {
  const app = Fastify({ logger: true });
  app.register(cors, { origin: true });

  app.get('/health', async () => ({ status: 'ok' }));

  return app;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const app = buildServer();
  const port = Number(process.env.PORT) || 3001;
  app.listen({ port, host: '0.0.0.0' }).catch((err) => {
    app.log.error(err);
    process.exit(1);
  });
}
```

- [ ] **Step 7: Copy .env.example to .env, start Postgres, verify server boots**

```bash
cp apps/api/.env.example apps/api/.env
docker compose up -d postgres
cd apps/api && npm run dev &
sleep 2
curl -s http://localhost:3001/health
```

Expected: `{"status":"ok"}`. Stop the dev server (`kill %1` or Ctrl+C) before continuing.

- [ ] **Step 8: Commit**

```bash
git add apps/api/package.json apps/api/tsconfig.json apps/api/.env.example apps/api/src/db.ts apps/api/src/server.ts apps/api/package-lock.json
git commit -m "feat(api): scaffold fastify server with health route"
```

---

## Task 3: Rules engine — confidence score (TDD)

**Files:**
- Create: `apps/api/src/rules/confidenceScore.ts`
- Test: `apps/api/tests/rules/confidenceScore.test.ts`

- [ ] **Step 1: Write failing test**

```typescript
import { describe, it, expect } from 'vitest';
import { calculateConfidenceScore } from '../../src/rules/confidenceScore';

const validDoc = {
  passportNumber: 'X1234567',
  fullName: 'Jane Doe',
  dob: '1990-05-01',
  nationality: 'US',
  expiryDate: '2030-01-01',
};

describe('calculateConfidenceScore', () => {
  it('returns 100 for a fully valid document', () => {
    expect(calculateConfidenceScore(validDoc)).toBe(100);
  });

  it('deducts 40 for malformed passport number', () => {
    expect(calculateConfidenceScore({ ...validDoc, passportNumber: '12' })).toBe(60);
  });

  it('deducts 20 for missing full name', () => {
    expect(calculateConfidenceScore({ ...validDoc, fullName: '' })).toBe(80);
  });

  it('deducts 20 for invalid dob', () => {
    expect(calculateConfidenceScore({ ...validDoc, dob: 'not-a-date' })).toBe(80);
  });

  it('deducts 20 for invalid expiry date', () => {
    expect(calculateConfidenceScore({ ...validDoc, expiryDate: 'not-a-date' })).toBe(80);
  });

  it('clamps at 0 when everything is wrong', () => {
    expect(
      calculateConfidenceScore({ passportNumber: '', fullName: '', dob: '', expiryDate: '', nationality: '' })
    ).toBe(0);
  });
});
```

- [ ] **Step 2: Run test, verify it fails**

```bash
cd apps/api && npx vitest run tests/rules/confidenceScore.test.ts
```

Expected: FAIL — `Cannot find module '../../src/rules/confidenceScore'`.

- [ ] **Step 3: Implement**

```typescript
export interface DocumentInput {
  passportNumber: string;
  fullName: string;
  dob: string;
  nationality: string;
  expiryDate: string;
}

const PASSPORT_FORMAT = /^[A-Z0-9]{6,9}$/;

function isValidDate(value: string): boolean {
  return value.length > 0 && !Number.isNaN(Date.parse(value));
}

export function calculateConfidenceScore(doc: DocumentInput): number {
  let score = 100;

  if (!PASSPORT_FORMAT.test(doc.passportNumber)) score -= 40;
  if (!doc.fullName || doc.fullName.trim().length < 2) score -= 20;
  if (!isValidDate(doc.dob)) score -= 20;
  if (!isValidDate(doc.expiryDate)) score -= 20;

  return Math.max(0, Math.min(100, score));
}
```

- [ ] **Step 4: Run test, verify it passes**

```bash
cd apps/api && npx vitest run tests/rules/confidenceScore.test.ts
```

Expected: PASS, 6 tests.

- [ ] **Step 5: Commit**

```bash
git add apps/api/src/rules/confidenceScore.ts apps/api/tests/rules/confidenceScore.test.ts
git commit -m "feat(api): add document confidence score rule"
```

---

## Task 4: Rules engine — document validation (TDD)

**Files:**
- Create: `apps/api/src/rules/validateDocument.ts`
- Test: `apps/api/tests/rules/validateDocument.test.ts`

- [ ] **Step 1: Write failing test**

```typescript
import { describe, it, expect } from 'vitest';
import { validateDocument } from '../../src/rules/validateDocument';

const baseDoc = {
  passportNumber: 'X1234567',
  fullName: 'Jane Doe',
  dob: '1990-05-01',
  nationality: 'US',
  expiryDate: '2030-01-01',
};

const departureTime = '2026-08-01T10:00:00.000Z';

describe('validateDocument', () => {
  it('returns VALID for a clean document, normal destination', () => {
    const result = validateDocument(baseDoc, 'Jane Doe', 'LHR', departureTime, ['DXB']);
    expect(result.status).toBe('VALID');
    expect(result.issues).toEqual([]);
  });

  it('blocks on missing/malformed passport number', () => {
    const result = validateDocument({ ...baseDoc, passportNumber: '' }, 'Jane Doe', 'LHR', departureTime, []);
    expect(result.status).toBe('BLOCKED');
    expect(result.issues).toContain('missing_or_invalid_passport_number');
  });

  it('blocks on expired document', () => {
    const result = validateDocument(
      { ...baseDoc, expiryDate: '2026-01-01' },
      'Jane Doe',
      'LHR',
      departureTime,
      []
    );
    expect(result.status).toBe('BLOCKED');
    expect(result.issues).toContain('document_expired');
  });

  it('flags name mismatch as needs review (not blocked)', () => {
    const result = validateDocument(baseDoc, 'John Smith', 'LHR', departureTime, []);
    expect(result.status).toBe('NEEDS_REVIEW');
    expect(result.issues).toContain('name_mismatch');
  });

  it('name match is order/case/punctuation insensitive', () => {
    const result = validateDocument(baseDoc, 'doe, jane', 'LHR', departureTime, []);
    expect(result.issues).not.toContain('name_mismatch');
  });

  it('flags extra-check destination as needs review', () => {
    const result = validateDocument(baseDoc, 'Jane Doe', 'DXB', departureTime, ['DXB']);
    expect(result.status).toBe('NEEDS_REVIEW');
    expect(result.issues).toContain('extra_checks_required_destination');
  });

  it('flags low confidence score as needs review', () => {
    const result = validateDocument(
      { ...baseDoc, fullName: '', dob: 'bad', expiryDate: 'bad' },
      '',
      'LHR',
      departureTime,
      []
    );
    expect(result.issues).toContain('low_document_confidence');
  });

  it('hard block wins over soft flags', () => {
    const result = validateDocument(
      { ...baseDoc, passportNumber: '' },
      'John Smith',
      'DXB',
      departureTime,
      ['DXB']
    );
    expect(result.status).toBe('BLOCKED');
  });
});
```

- [ ] **Step 2: Run test, verify it fails**

```bash
cd apps/api && npx vitest run tests/rules/validateDocument.test.ts
```

Expected: FAIL — module not found.

- [ ] **Step 3: Implement**

```typescript
import { calculateConfidenceScore, DocumentInput } from './confidenceScore';

export interface DocumentValidationResult {
  status: 'VALID' | 'BLOCKED' | 'NEEDS_REVIEW';
  issues: string[];
  confidenceScore: number;
}

const PASSPORT_FORMAT = /^[A-Z0-9]{6,9}$/;

function normalizeName(name: string): string[] {
  return name
    .toLowerCase()
    .replace(/[^a-z\s]/g, ' ')
    .split(/\s+/)
    .filter(Boolean)
    .sort();
}

function namesMatch(bookingName: string, docFullName: string): boolean {
  const a = normalizeName(bookingName);
  const b = normalizeName(docFullName);
  return a.length === b.length && a.every((token, i) => token === b[i]);
}

export function validateDocument(
  doc: DocumentInput,
  bookingFullName: string,
  destination: string,
  departureTimeIso: string,
  extraCheckDestinations: string[]
): DocumentValidationResult {
  const hardIssues: string[] = [];
  const softIssues: string[] = [];

  if (!PASSPORT_FORMAT.test(doc.passportNumber)) {
    hardIssues.push('missing_or_invalid_passport_number');
  }

  const expiry = Date.parse(doc.expiryDate);
  const departure = Date.parse(departureTimeIso);
  if (Number.isNaN(expiry) || expiry <= departure) {
    hardIssues.push('document_expired');
  }

  const confidenceScore = calculateConfidenceScore(doc);

  if (hardIssues.length === 0) {
    if (!namesMatch(bookingFullName, doc.fullName)) {
      softIssues.push('name_mismatch');
    }
    if (extraCheckDestinations.includes(destination)) {
      softIssues.push('extra_checks_required_destination');
    }
    if (confidenceScore < 60) {
      softIssues.push('low_document_confidence');
    }
  }

  const status = hardIssues.length > 0 ? 'BLOCKED' : softIssues.length > 0 ? 'NEEDS_REVIEW' : 'VALID';

  return { status, issues: [...hardIssues, ...softIssues], confidenceScore };
}
```

- [ ] **Step 4: Run test, verify it passes**

```bash
cd apps/api && npx vitest run tests/rules/validateDocument.test.ts
```

Expected: PASS, 8 tests.

- [ ] **Step 5: Commit**

```bash
git add apps/api/src/rules/validateDocument.ts apps/api/tests/rules/validateDocument.test.ts
git commit -m "feat(api): add document validation rule engine"
```

---

## Task 5: Rules engine — overall status + bag weight (TDD)

**Files:**
- Create: `apps/api/src/rules/status.ts`
- Test: `apps/api/tests/rules/status.test.ts`

- [ ] **Step 1: Write failing test**

```typescript
import { describe, it, expect } from 'vitest';
import { determineOverallStatus, checkBagWeight } from '../../src/rules/status';

describe('determineOverallStatus', () => {
  it('is NOT_STARTED with no document', () => {
    expect(
      determineOverallStatus({ documentStatus: null, anyBagOverweight: false, boardingPassIssued: false })
    ).toBe('NOT_STARTED');
  });

  it('is IN_PROGRESS once document is VALID', () => {
    expect(
      determineOverallStatus({ documentStatus: 'VALID', anyBagOverweight: false, boardingPassIssued: false })
    ).toBe('IN_PROGRESS');
  });

  it('is BLOCKED when document is BLOCKED, regardless of bags', () => {
    expect(
      determineOverallStatus({ documentStatus: 'BLOCKED', anyBagOverweight: false, boardingPassIssued: false })
    ).toBe('BLOCKED');
  });

  it('is NEEDS_REVIEW when document needs review', () => {
    expect(
      determineOverallStatus({ documentStatus: 'NEEDS_REVIEW', anyBagOverweight: false, boardingPassIssued: false })
    ).toBe('NEEDS_REVIEW');
  });

  it('is NEEDS_REVIEW when a bag is overweight even if document is valid', () => {
    expect(
      determineOverallStatus({ documentStatus: 'VALID', anyBagOverweight: true, boardingPassIssued: false })
    ).toBe('NEEDS_REVIEW');
  });

  it('is CLEARED once boarding pass is issued', () => {
    expect(
      determineOverallStatus({ documentStatus: 'VALID', anyBagOverweight: false, boardingPassIssued: true })
    ).toBe('CLEARED');
  });
});

describe('checkBagWeight', () => {
  it('flags overweight when weight exceeds max', () => {
    expect(checkBagWeight(25, 23)).toBe(true);
  });

  it('does not flag when weight is within max', () => {
    expect(checkBagWeight(20, 23)).toBe(false);
  });

  it('does not flag when weight equals max', () => {
    expect(checkBagWeight(23, 23)).toBe(false);
  });
});
```

- [ ] **Step 2: Run test, verify it fails**

```bash
cd apps/api && npx vitest run tests/rules/status.test.ts
```

Expected: FAIL — module not found.

- [ ] **Step 3: Implement**

```typescript
export type CheckInStatus = 'NOT_STARTED' | 'IN_PROGRESS' | 'CLEARED' | 'BLOCKED' | 'NEEDS_REVIEW';
export type DocumentStatus = 'VALID' | 'BLOCKED' | 'NEEDS_REVIEW' | null;

export function determineOverallStatus(params: {
  documentStatus: DocumentStatus;
  anyBagOverweight: boolean;
  boardingPassIssued: boolean;
}): CheckInStatus {
  if (params.boardingPassIssued) return 'CLEARED';
  if (params.documentStatus === 'BLOCKED') return 'BLOCKED';
  if (params.documentStatus === 'NEEDS_REVIEW' || params.anyBagOverweight) return 'NEEDS_REVIEW';
  if (params.documentStatus === 'VALID') return 'IN_PROGRESS';
  return 'NOT_STARTED';
}

export function checkBagWeight(weightKg: number, maxBagWeightKg: number): boolean {
  return weightKg > maxBagWeightKg;
}
```

- [ ] **Step 4: Run test, verify it passes**

```bash
cd apps/api && npx vitest run tests/rules/status.test.ts
```

Expected: PASS, 9 tests.

- [ ] **Step 5: Commit**

```bash
git add apps/api/src/rules/status.ts apps/api/tests/rules/status.test.ts
git commit -m "feat(api): add overall status and bag weight rules"
```

---

## Task 6: Prisma schema + migration

**Files:**
- Create: `apps/api/prisma/schema.prisma`

- [ ] **Step 1: Write schema**

```prisma
generator client {
  provider = "prisma-client-js"
}

datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

enum CheckInStatus {
  NOT_STARTED
  IN_PROGRESS
  CLEARED
  BLOCKED
  NEEDS_REVIEW
}

enum CabinZone {
  FRONT
  MID
  REAR
}

model Flight {
  id             String         @id @default(uuid())
  flightNumber   String
  origin         String
  destination    String
  departureTime  DateTime
  aircraftType   String
  maxBagWeightKg Float
  seats          Seat[]
  passengers     Passenger[]
  bags           Bag[]
  boardingPasses BoardingPass[]
}

model Seat {
  id          String     @id @default(uuid())
  flightId    String
  flight      Flight     @relation(fields: [flightId], references: [id])
  seatNumber  String
  cabinZone   CabinZone
  occupied    Boolean    @default(false)
  passengerId String?    @unique
  passenger   Passenger? @relation(fields: [passengerId], references: [id])

  @@unique([flightId, seatNumber])
}

model Passenger {
  id               String        @id @default(uuid())
  bookingRef       String
  firstName        String
  lastName         String
  flightId         String
  flight           Flight        @relation(fields: [flightId], references: [id])
  groupId          String?
  checkInStatus    CheckInStatus @default(NOT_STARTED)
  declaredBagCount Int           @default(0)
  riskFlags        String[]      @default([])
  seat             Seat?
  document         Document?
  bags             Bag[]
  boardingPass     BoardingPass?
  auditLogs        AuditLog[]

  @@unique([flightId, bookingRef])
}

model Document {
  id              String    @id @default(uuid())
  passengerId     String    @unique
  passenger       Passenger @relation(fields: [passengerId], references: [id])
  passportNumber  String
  fullName        String
  dob             DateTime
  nationality     String
  expiryDate      DateTime
  confidenceScore Int
  issues          String[]  @default([])
  status          String
}

model Bag {
  id          String    @id @default(uuid())
  passengerId String
  passenger   Passenger @relation(fields: [passengerId], references: [id])
  flightId    String
  flight      Flight    @relation(fields: [flightId], references: [id])
  tagId       String    @unique
  weightKg    Float
  overweight  Boolean   @default(false)
}

model BoardingPass {
  id          String    @id @default(uuid())
  passengerId String    @unique
  passenger   Passenger @relation(fields: [passengerId], references: [id])
  flightId    String
  flight      Flight    @relation(fields: [flightId], references: [id])
  seatNumber  String
  qrPayload   String
  issuedAt    DateTime  @default(now())
}

model AuditLog {
  id          String    @id @default(uuid())
  passengerId String
  passenger   Passenger @relation(fields: [passengerId], references: [id])
  actorRole   String
  action      String
  prevStatus  String
  newStatus   String
  reason      String
  timestamp   DateTime  @default(now())
}
```

- [ ] **Step 2: Run migration against local Postgres**

```bash
docker compose up -d postgres
cd apps/api
npx prisma migrate dev --name init
```

Expected: migration created under `apps/api/prisma/migrations/`, Prisma Client generated, no errors.

- [ ] **Step 3: Commit**

```bash
git add apps/api/prisma
git commit -m "feat(api): add prisma schema and initial migration"
```

---

## Task 7: Seed script

**Files:**
- Create: `apps/api/prisma/seed.ts`

- [ ] **Step 1: Write seed.ts**

```typescript
import { PrismaClient, CabinZone } from '@prisma/client';

const prisma = new PrismaClient();

async function main() {
  await prisma.auditLog.deleteMany();
  await prisma.boardingPass.deleteMany();
  await prisma.bag.deleteMany();
  await prisma.document.deleteMany();
  await prisma.seat.deleteMany();
  await prisma.passenger.deleteMany();
  await prisma.flight.deleteMany();

  const flight1 = await prisma.flight.create({
    data: {
      flightNumber: 'DC101',
      origin: 'JFK',
      destination: 'LHR',
      departureTime: new Date('2026-08-01T10:00:00.000Z'),
      aircraftType: 'A320',
      maxBagWeightKg: 23,
    },
  });

  const flight2 = await prisma.flight.create({
    data: {
      flightNumber: 'DC202',
      origin: 'JFK',
      destination: 'DXB',
      departureTime: new Date('2026-08-02T14:00:00.000Z'),
      aircraftType: 'B777',
      maxBagWeightKg: 23,
    },
  });

  async function makeSeats(flightId: string) {
    const zones: { letters: string[]; zone: CabinZone; rows: number[] }[] = [
      { letters: ['A', 'B', 'C'], zone: 'FRONT', rows: [1, 2, 3] },
      { letters: ['A', 'B', 'C'], zone: 'MID', rows: [10, 11, 12] },
      { letters: ['A', 'B', 'C'], zone: 'REAR', rows: [20, 21, 22] },
    ];
    for (const { letters, zone, rows } of zones) {
      for (const row of rows) {
        for (const letter of letters) {
          await prisma.seat.create({
            data: { flightId, seatNumber: `${row}${letter}`, cabinZone: zone },
          });
        }
      }
    }
  }

  await makeSeats(flight1.id);
  await makeSeats(flight2.id);

  await prisma.passenger.create({
    data: { bookingRef: 'CLEAN1', firstName: 'Jane', lastName: 'Doe', flightId: flight1.id },
  });
  await prisma.passenger.create({
    data: { bookingRef: 'NOPASS', firstName: 'Marcus', lastName: 'Lee', flightId: flight1.id },
  });
  await prisma.passenger.create({
    data: { bookingRef: 'EXPIRD', firstName: 'Aisha', lastName: 'Khan', flightId: flight1.id },
  });
  await prisma.passenger.create({
    data: { bookingRef: 'NAMEMM', firstName: 'Robert', lastName: 'Smith', flightId: flight1.id },
  });
  await prisma.passenger.create({
    data: { bookingRef: 'XCHECK', firstName: 'Wei', lastName: 'Chen', flightId: flight2.id },
  });
  await prisma.passenger.create({
    data: { bookingRef: 'OVRWGT', firstName: 'Priya', lastName: 'Patel', flightId: flight1.id },
  });
  const groupId = 'GRP-FAMILY-1';
  await prisma.passenger.create({
    data: { bookingRef: 'GROUP1', firstName: 'Tom', lastName: 'Nguyen', flightId: flight1.id, groupId },
  });
  await prisma.passenger.create({
    data: { bookingRef: 'GROUP2', firstName: 'Lily', lastName: 'Nguyen', flightId: flight1.id, groupId },
  });

  console.log('Seed complete:', { flight1: flight1.id, flight2: flight2.id });
}

main()
  .catch((err) => {
    console.error(err);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
```

- [ ] **Step 2: Run seed, verify data**

```bash
cd apps/api && npx tsx prisma/seed.ts
npx prisma studio &
```

Expected: console prints `Seed complete: {...}`; Prisma Studio (manually check, then close) shows 2 flights, 54 seats, 8 passengers.

- [ ] **Step 3: Commit**

```bash
git add apps/api/prisma/seed.ts
git commit -m "feat(api): add seed script with mock passengers covering all status paths"
```

---

## Task 8: Flights routes

**Files:**
- Create: `apps/api/src/routes/flights.ts`
- Modify: `apps/api/src/server.ts`

- [ ] **Step 1: Write apps/api/src/routes/flights.ts**

```typescript
import { FastifyInstance } from 'fastify';
import { prisma } from '../db';

export async function flightRoutes(app: FastifyInstance) {
  app.get('/flights', async () => {
    return prisma.flight.findMany({ orderBy: { departureTime: 'asc' } });
  });

  app.get<{ Params: { id: string } }>('/flights/:id/seatmap', async (req, reply) => {
    const flight = await prisma.flight.findUnique({ where: { id: req.params.id } });
    if (!flight) return reply.code(404).send({ error: 'flight_not_found' });

    const seats = await prisma.seat.findMany({
      where: { flightId: req.params.id },
      include: { passenger: { select: { id: true, firstName: true, lastName: true } } },
      orderBy: [{ cabinZone: 'asc' }, { seatNumber: 'asc' }],
    });
    return { flight, seats };
  });
}
```

- [ ] **Step 2: Register route in server.ts**

```typescript
import Fastify from 'fastify';
import cors from '@fastify/cors';
import { flightRoutes } from './routes/flights';

export function buildServer() {
  const app = Fastify({ logger: true });
  app.register(cors, { origin: true });

  app.get('/health', async () => ({ status: 'ok' }));
  app.register(flightRoutes);

  return app;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const app = buildServer();
  const port = Number(process.env.PORT) || 3001;
  app.listen({ port, host: '0.0.0.0' }).catch((err) => {
    app.log.error(err);
    process.exit(1);
  });
}
```

- [ ] **Step 3: Manual verify**

```bash
cd apps/api && npm run dev &
sleep 2
curl -s http://localhost:3001/flights | head -c 300
kill %1
```

Expected: JSON array of 2 flights.

- [ ] **Step 4: Commit**

```bash
git add apps/api/src/routes/flights.ts apps/api/src/server.ts
git commit -m "feat(api): add flights and seatmap routes"
```

---

## Task 9: Passenger lookup/search routes

**Files:**
- Create: `apps/api/src/routes/passengers.ts`
- Modify: `apps/api/src/server.ts`

- [ ] **Step 1: Write apps/api/src/routes/passengers.ts**

```typescript
import { FastifyInstance } from 'fastify';
import { prisma } from '../db';

const passengerInclude = {
  flight: true,
  seat: true,
  document: true,
  bags: true,
  boardingPass: true,
} as const;

export async function passengerRoutes(app: FastifyInstance) {
  app.get<{ Querystring: { flightId?: string } }>('/passengers', async (req) => {
    return prisma.passenger.findMany({
      where: req.query.flightId ? { flightId: req.query.flightId } : undefined,
      include: passengerInclude,
      orderBy: [{ lastName: 'asc' }],
    });
  });

  app.get<{ Querystring: { bookingRef?: string; lastName?: string } }>('/passengers/lookup', async (req, reply) => {
    const { bookingRef, lastName } = req.query;
    if (!bookingRef || !lastName) {
      return reply.code(400).send({ error: 'bookingRef_and_lastName_required' });
    }
    const passenger = await prisma.passenger.findFirst({
      where: { bookingRef, lastName: { equals: lastName, mode: 'insensitive' } },
      include: passengerInclude,
    });
    if (!passenger) return reply.code(404).send({ error: 'passenger_not_found' });
    return passenger;
  });

  app.get<{ Params: { id: string } }>('/passengers/:id', async (req, reply) => {
    const passenger = await prisma.passenger.findUnique({
      where: { id: req.params.id },
      include: passengerInclude,
    });
    if (!passenger) return reply.code(404).send({ error: 'passenger_not_found' });
    return passenger;
  });
}
```

- [ ] **Step 2: Register route in server.ts**

Add `import { passengerRoutes } from './routes/passengers';` and `app.register(passengerRoutes);` below the flight routes registration in `apps/api/src/server.ts`.

- [ ] **Step 3: Manual verify**

```bash
cd apps/api && npm run dev &
sleep 2
curl -s "http://localhost:3001/passengers/lookup?bookingRef=CLEAN1&lastName=Doe" | head -c 300
kill %1
```

Expected: JSON of the Jane Doe passenger record.

- [ ] **Step 4: Commit**

```bash
git add apps/api/src/routes/passengers.ts apps/api/src/server.ts
git commit -m "feat(api): add passenger search and lookup routes"
```

---

## Task 10: Document submission route

**Files:**
- Create: `apps/api/src/routes/document.ts`
- Modify: `apps/api/src/server.ts`

- [ ] **Step 1: Write apps/api/src/routes/document.ts**

```typescript
import { FastifyInstance } from 'fastify';
import { z } from 'zod';
import { prisma } from '../db';
import { validateDocument } from '../rules/validateDocument';
import { determineOverallStatus } from '../rules/status';

const EXTRA_CHECK_DESTINATIONS = ['DXB', 'PEK'];

const documentSchema = z.object({
  passportNumber: z.string(),
  fullName: z.string(),
  dob: z.string(),
  nationality: z.string(),
  expiryDate: z.string(),
});

export async function documentRoutes(app: FastifyInstance) {
  app.post<{ Params: { id: string }; Body: unknown }>('/passengers/:id/document', async (req, reply) => {
    const parsed = documentSchema.safeParse(req.body);
    if (!parsed.success) return reply.code(400).send({ error: 'invalid_body', details: parsed.error.flatten() });

    const passenger = await prisma.passenger.findUnique({
      where: { id: req.params.id },
      include: { flight: true, bags: true },
    });
    if (!passenger) return reply.code(404).send({ error: 'passenger_not_found' });

    const result = validateDocument(
      parsed.data,
      `${passenger.firstName} ${passenger.lastName}`,
      passenger.flight.destination,
      passenger.flight.departureTime.toISOString(),
      EXTRA_CHECK_DESTINATIONS
    );

    await prisma.document.upsert({
      where: { passengerId: passenger.id },
      create: {
        passengerId: passenger.id,
        passportNumber: parsed.data.passportNumber,
        fullName: parsed.data.fullName,
        dob: new Date(parsed.data.dob),
        nationality: parsed.data.nationality,
        expiryDate: new Date(parsed.data.expiryDate),
        confidenceScore: result.confidenceScore,
        issues: result.issues,
        status: result.status,
      },
      update: {
        passportNumber: parsed.data.passportNumber,
        fullName: parsed.data.fullName,
        dob: new Date(parsed.data.dob),
        nationality: parsed.data.nationality,
        expiryDate: new Date(parsed.data.expiryDate),
        confidenceScore: result.confidenceScore,
        issues: result.issues,
        status: result.status,
      },
    });

    const anyBagOverweight = passenger.bags.some((b) => b.overweight);
    const newStatus = determineOverallStatus({
      documentStatus: result.status,
      anyBagOverweight,
      boardingPassIssued: false,
    });

    const updated = await prisma.passenger.update({
      where: { id: passenger.id },
      data: { checkInStatus: newStatus },
      include: { flight: true, seat: true, document: true, bags: true, boardingPass: true },
    });

    return updated;
  });
}
```

- [ ] **Step 2: Register route in server.ts**

Add `import { documentRoutes } from './routes/document';` and `app.register(documentRoutes);`.

- [ ] **Step 3: Manual verify against seeded BLOCKED case**

```bash
cd apps/api && npm run dev &
sleep 2
PID=$(curl -s "http://localhost:3001/passengers/lookup?bookingRef=NOPASS&lastName=Lee" | node -e "process.stdin.on('data',d=>console.log(JSON.parse(d).id))")
curl -s -X POST "http://localhost:3001/passengers/$PID/document" \
  -H 'Content-Type: application/json' \
  -d '{"passportNumber":"","fullName":"Marcus Lee","dob":"1985-01-01","nationality":"US","expiryDate":"2030-01-01"}'
kill %1
```

Expected: response `checkInStatus: "BLOCKED"`, `document.issues` includes `"missing_or_invalid_passport_number"`.

- [ ] **Step 4: Commit**

```bash
git add apps/api/src/routes/document.ts apps/api/src/server.ts
git commit -m "feat(api): add document submission route wired to rules engine"
```

---

## Task 11: Seat confirmation route

**Files:**
- Create: `apps/api/src/routes/seat.ts`
- Modify: `apps/api/src/server.ts`

- [ ] **Step 1: Write apps/api/src/routes/seat.ts**

```typescript
import { FastifyInstance } from 'fastify';
import { z } from 'zod';
import { prisma } from '../db';

const seatSchema = z.object({ seatId: z.string() });

export async function seatRoutes(app: FastifyInstance) {
  app.post<{ Params: { id: string }; Body: unknown }>('/passengers/:id/seat', async (req, reply) => {
    const parsed = seatSchema.safeParse(req.body);
    if (!parsed.success) return reply.code(400).send({ error: 'invalid_body' });

    const passenger = await prisma.passenger.findUnique({
      where: { id: req.params.id },
      include: { seat: true },
    });
    if (!passenger) return reply.code(404).send({ error: 'passenger_not_found' });

    const seat = await prisma.seat.findUnique({ where: { id: parsed.data.seatId } });
    if (!seat || seat.flightId !== passenger.flightId) {
      return reply.code(400).send({ error: 'seat_not_on_flight' });
    }
    if (seat.occupied && seat.passengerId !== passenger.id) {
      return reply.code(409).send({ error: 'seat_occupied' });
    }

    if (passenger.seat?.id) {
      await prisma.seat.update({ where: { id: passenger.seat.id }, data: { occupied: false, passengerId: null } });
    }

    await prisma.seat.update({ where: { id: seat.id }, data: { occupied: true, passengerId: passenger.id } });

    return prisma.passenger.findUnique({
      where: { id: passenger.id },
      include: { flight: true, seat: true, document: true, bags: true, boardingPass: true },
    });
  });
}
```

- [ ] **Step 2: Register route in server.ts**

Add `import { seatRoutes } from './routes/seat';` and `app.register(seatRoutes);`.

- [ ] **Step 3: Manual verify**

```bash
cd apps/api && npm run dev &
sleep 2
FID=$(curl -s http://localhost:3001/flights | node -e "process.stdin.on('data',d=>console.log(JSON.parse(d)[0].id))")
PID=$(curl -s "http://localhost:3001/passengers/lookup?bookingRef=CLEAN1&lastName=Doe" | node -e "process.stdin.on('data',d=>console.log(JSON.parse(d).id))")
SID=$(curl -s "http://localhost:3001/flights/$FID/seatmap" | node -e "process.stdin.on('data',d=>console.log(JSON.parse(d).seats[0].id))")
curl -s -X POST "http://localhost:3001/passengers/$PID/seat" -H 'Content-Type: application/json' -d "{\"seatId\":\"$SID\"}"
kill %1
```

Expected: response includes `seat` object matching the chosen seat.

- [ ] **Step 4: Commit**

```bash
git add apps/api/src/routes/seat.ts apps/api/src/server.ts
git commit -m "feat(api): add seat confirmation route"
```

---

## Task 12: Bag declaration route

**Files:**
- Create: `apps/api/src/routes/bags.ts`
- Modify: `apps/api/src/server.ts`

- [ ] **Step 1: Write apps/api/src/routes/bags.ts**

```typescript
import { FastifyInstance } from 'fastify';
import { randomUUID } from 'crypto';
import { z } from 'zod';
import { prisma } from '../db';
import { checkBagWeight, determineOverallStatus } from '../rules/status';

const bagsSchema = z.object({ bags: z.array(z.object({ weightKg: z.number().positive() })) });

export async function bagRoutes(app: FastifyInstance) {
  app.post<{ Params: { id: string }; Body: unknown }>('/passengers/:id/bags', async (req, reply) => {
    const parsed = bagsSchema.safeParse(req.body);
    if (!parsed.success) return reply.code(400).send({ error: 'invalid_body' });

    const passenger = await prisma.passenger.findUnique({
      where: { id: req.params.id },
      include: { flight: true, document: true },
    });
    if (!passenger) return reply.code(404).send({ error: 'passenger_not_found' });

    await prisma.bag.deleteMany({ where: { passengerId: passenger.id } });

    for (const bag of parsed.data.bags) {
      const overweight = checkBagWeight(bag.weightKg, passenger.flight.maxBagWeightKg);
      await prisma.bag.create({
        data: {
          passengerId: passenger.id,
          flightId: passenger.flightId,
          tagId: `BAG-${randomUUID().slice(0, 8).toUpperCase()}`,
          weightKg: bag.weightKg,
          overweight,
        },
      });
    }

    const bags = await prisma.bag.findMany({ where: { passengerId: passenger.id } });
    const anyBagOverweight = bags.some((b) => b.overweight);

    const newStatus = determineOverallStatus({
      documentStatus: (passenger.document?.status as 'VALID' | 'BLOCKED' | 'NEEDS_REVIEW' | undefined) ?? null,
      anyBagOverweight,
      boardingPassIssued: false,
    });

    return prisma.passenger.update({
      where: { id: passenger.id },
      data: { checkInStatus: newStatus, declaredBagCount: bags.length },
      include: { flight: true, seat: true, document: true, bags: true, boardingPass: true },
    });
  });
}
```

- [ ] **Step 2: Register route in server.ts**

Add `import { bagRoutes } from './routes/bags';` and `app.register(bagRoutes);`.

- [ ] **Step 3: Manual verify overweight case**

```bash
cd apps/api && npm run dev &
sleep 2
PID=$(curl -s "http://localhost:3001/passengers/lookup?bookingRef=OVRWGT&lastName=Patel" | node -e "process.stdin.on('data',d=>console.log(JSON.parse(d).id))")
curl -s -X POST "http://localhost:3001/passengers/$PID/bags" -H 'Content-Type: application/json' -d '{"bags":[{"weightKg":30}]}'
kill %1
```

Expected: `bags[0].overweight: true`, `checkInStatus: "NEEDS_REVIEW"`.

- [ ] **Step 4: Commit**

```bash
git add apps/api/src/routes/bags.ts apps/api/src/server.ts
git commit -m "feat(api): add bag declaration route with overweight detection"
```

---

## Task 13: Boarding pass issuance route

**Files:**
- Create: `apps/api/src/routes/boardingPass.ts`
- Modify: `apps/api/src/server.ts`

- [ ] **Step 1: Write apps/api/src/routes/boardingPass.ts**

```typescript
import { FastifyInstance } from 'fastify';
import { randomUUID } from 'crypto';
import { prisma } from '../db';
import { determineOverallStatus } from '../rules/status';

export async function boardingPassRoutes(app: FastifyInstance) {
  app.post<{ Params: { id: string } }>('/passengers/:id/boarding-pass', async (req, reply) => {
    const passenger = await prisma.passenger.findUnique({
      where: { id: req.params.id },
      include: { document: true, seat: true, bags: true },
    });
    if (!passenger) return reply.code(404).send({ error: 'passenger_not_found' });

    if (!passenger.document || passenger.document.status !== 'VALID') {
      return reply.code(409).send({ error: 'document_not_cleared' });
    }
    if (!passenger.seat) {
      return reply.code(409).send({ error: 'seat_not_assigned' });
    }
    if (passenger.bags.some((b) => b.overweight)) {
      return reply.code(409).send({ error: 'overweight_bag_unresolved' });
    }

    const id = randomUUID();
    const boardingPass = await prisma.boardingPass.create({
      data: {
        id,
        passengerId: passenger.id,
        flightId: passenger.flightId,
        seatNumber: passenger.seat.seatNumber,
        qrPayload: `UIG-PASS-${id}`,
      },
    });

    const newStatus = determineOverallStatus({
      documentStatus: 'VALID',
      anyBagOverweight: false,
      boardingPassIssued: true,
    });

    const updated = await prisma.passenger.update({
      where: { id: passenger.id },
      data: { checkInStatus: newStatus },
      include: { flight: true, seat: true, document: true, bags: true, boardingPass: true },
    });

    return { passenger: updated, boardingPass };
  });
}
```

- [ ] **Step 2: Register route in server.ts**

Add `import { boardingPassRoutes } from './routes/boardingPass';` and `app.register(boardingPassRoutes);`.

- [ ] **Step 3: Manual verify happy path (Jane Doe, after doc + seat steps from Tasks 10–11)**

```bash
cd apps/api && npm run dev &
sleep 2
PID=$(curl -s "http://localhost:3001/passengers/lookup?bookingRef=CLEAN1&lastName=Doe" | node -e "process.stdin.on('data',d=>console.log(JSON.parse(d).id))")
curl -s -X POST "http://localhost:3001/passengers/$PID/document" -H 'Content-Type: application/json' -d '{"passportNumber":"Y7654321","fullName":"Jane Doe","dob":"1990-01-01","nationality":"US","expiryDate":"2030-01-01"}' > /dev/null
FID=$(curl -s http://localhost:3001/flights | node -e "process.stdin.on('data',d=>console.log(JSON.parse(d)[0].id))")
SID=$(curl -s "http://localhost:3001/flights/$FID/seatmap" | node -e "process.stdin.on('data',d=>console.log(JSON.parse(d).seats[1].id))")
curl -s -X POST "http://localhost:3001/passengers/$PID/seat" -H 'Content-Type: application/json' -d "{\"seatId\":\"$SID\"}" > /dev/null
curl -s -X POST "http://localhost:3001/passengers/$PID/boarding-pass"
kill %1
```

Expected: 200, `passenger.checkInStatus: "CLEARED"`, `boardingPass.qrPayload` starting with `UIG-PASS-`.

- [ ] **Step 4: Commit**

```bash
git add apps/api/src/routes/boardingPass.ts apps/api/src/server.ts
git commit -m "feat(api): add boarding pass issuance route"
```

---

## Task 14: Override + audit log routes

**Files:**
- Create: `apps/api/src/routes/override.ts`
- Modify: `apps/api/src/server.ts`

- [ ] **Step 1: Write apps/api/src/routes/override.ts**

```typescript
import { FastifyInstance } from 'fastify';
import { z } from 'zod';
import { prisma } from '../db';

const overrideSchema = z.object({ reason: z.string().min(3) });

export async function overrideRoutes(app: FastifyInstance) {
  app.post<{ Params: { id: string }; Body: unknown }>('/passengers/:id/override', async (req, reply) => {
    const parsed = overrideSchema.safeParse(req.body);
    if (!parsed.success) return reply.code(400).send({ error: 'reason_required' });

    const passenger = await prisma.passenger.findUnique({ where: { id: req.params.id } });
    if (!passenger) return reply.code(404).send({ error: 'passenger_not_found' });

    if (passenger.checkInStatus !== 'BLOCKED' && passenger.checkInStatus !== 'NEEDS_REVIEW') {
      return reply.code(409).send({ error: 'override_not_applicable' });
    }

    await prisma.auditLog.create({
      data: {
        passengerId: passenger.id,
        actorRole: 'AGENT',
        action: 'OVERRIDE_TO_CLEARED',
        prevStatus: passenger.checkInStatus,
        newStatus: 'CLEARED',
        reason: parsed.data.reason,
      },
    });

    return prisma.passenger.update({
      where: { id: passenger.id },
      data: { checkInStatus: 'CLEARED' },
      include: { flight: true, seat: true, document: true, bags: true, boardingPass: true },
    });
  });

  app.get<{ Params: { id: string } }>('/passengers/:id/audit-log', async (req) => {
    return prisma.auditLog.findMany({
      where: { passengerId: req.params.id },
      orderBy: { timestamp: 'desc' },
    });
  });
}
```

- [ ] **Step 2: Register route in server.ts**

Add `import { overrideRoutes } from './routes/override';` and `app.register(overrideRoutes);`.

- [ ] **Step 3: Manual verify on the seeded BLOCKED case from Task 10**

```bash
cd apps/api && npm run dev &
sleep 2
PID=$(curl -s "http://localhost:3001/passengers/lookup?bookingRef=NOPASS&lastName=Lee" | node -e "process.stdin.on('data',d=>console.log(JSON.parse(d).id))")
curl -s -X POST "http://localhost:3001/passengers/$PID/document" -H 'Content-Type: application/json' -d '{"passportNumber":"","fullName":"Marcus Lee","dob":"1985-01-01","nationality":"US","expiryDate":"2030-01-01"}' > /dev/null
curl -s -X POST "http://localhost:3001/passengers/$PID/override" -H 'Content-Type: application/json' -d '{"reason":"Manual ID check by supervisor"}'
curl -s "http://localhost:3001/passengers/$PID/audit-log"
kill %1
```

Expected: passenger `checkInStatus: "CLEARED"`; audit-log has one entry with `prevStatus: "BLOCKED"`, `newStatus: "CLEARED"`.

- [ ] **Step 4: Commit**

```bash
git add apps/api/src/routes/override.ts apps/api/src/server.ts
git commit -m "feat(api): add agent override route with audit logging"
```

---

## Task 15: API smoke test

**Files:**
- Create: `apps/api/tests/api.smoke.test.ts`

- [ ] **Step 1: Write smoke test covering the full document -> bag -> seat -> boarding-pass -> override paths**

```typescript
import { describe, it, expect, beforeAll, afterAll } from 'vitest';
import { buildServer } from '../src/server';
import { prisma } from '../src/db';

describe('UIG API smoke test', () => {
  const app = buildServer();
  let flightId: string;
  let passengerId: string;
  let seatId: string;

  beforeAll(async () => {
    await app.ready();
    const flight = await prisma.flight.create({
      data: {
        flightNumber: 'TST001',
        origin: 'JFK',
        destination: 'LHR',
        departureTime: new Date('2030-01-01T00:00:00.000Z'),
        aircraftType: 'A320',
        maxBagWeightKg: 23,
      },
    });
    flightId = flight.id;
    const seat = await prisma.seat.create({
      data: { flightId, seatNumber: '1A', cabinZone: 'FRONT' },
    });
    seatId = seat.id;
    const passenger = await prisma.passenger.create({
      data: { bookingRef: 'SMOKE1', firstName: 'Test', lastName: 'Smoke', flightId },
    });
    passengerId = passenger.id;
  });

  afterAll(async () => {
    await prisma.auditLog.deleteMany({ where: { passengerId } });
    await prisma.boardingPass.deleteMany({ where: { passengerId } });
    await prisma.bag.deleteMany({ where: { passengerId } });
    await prisma.document.deleteMany({ where: { passengerId } });
    await prisma.seat.deleteMany({ where: { flightId } });
    await prisma.passenger.deleteMany({ where: { flightId } });
    await prisma.flight.deleteMany({ where: { id: flightId } });
    await app.close();
    await prisma.$disconnect();
  });

  it('clears a clean passenger end to end', async () => {
    const docRes = await app.inject({
      method: 'POST',
      url: `/passengers/${passengerId}/document`,
      payload: {
        passportNumber: 'A1234567',
        fullName: 'Test Smoke',
        dob: '1990-01-01',
        nationality: 'US',
        expiryDate: '2035-01-01',
      },
    });
    expect(docRes.statusCode).toBe(200);
    expect(docRes.json().checkInStatus).toBe('IN_PROGRESS');

    const seatRes = await app.inject({
      method: 'POST',
      url: `/passengers/${passengerId}/seat`,
      payload: { seatId },
    });
    expect(seatRes.statusCode).toBe(200);

    const bagRes = await app.inject({
      method: 'POST',
      url: `/passengers/${passengerId}/bags`,
      payload: { bags: [{ weightKg: 18 }] },
    });
    expect(bagRes.statusCode).toBe(200);
    expect(bagRes.json().checkInStatus).toBe('IN_PROGRESS');

    const passRes = await app.inject({ method: 'POST', url: `/passengers/${passengerId}/boarding-pass` });
    expect(passRes.statusCode).toBe(200);
    expect(passRes.json().passenger.checkInStatus).toBe('CLEARED');
  });

  it('blocks then overrides a passenger with a bad passport', async () => {
    const docRes = await app.inject({
      method: 'POST',
      url: `/passengers/${passengerId}/document`,
      payload: {
        passportNumber: '',
        fullName: 'Test Smoke',
        dob: '1990-01-01',
        nationality: 'US',
        expiryDate: '2035-01-01',
      },
    });
    expect(docRes.json().checkInStatus).toBe('BLOCKED');

    const overrideRes = await app.inject({
      method: 'POST',
      url: `/passengers/${passengerId}/override`,
      payload: { reason: 'Verified manually against printed passport' },
    });
    expect(overrideRes.statusCode).toBe(200);
    expect(overrideRes.json().checkInStatus).toBe('CLEARED');

    const auditRes = await app.inject({ method: 'GET', url: `/passengers/${passengerId}/audit-log` });
    expect(auditRes.json()).toHaveLength(1);
  });
});
```

- [ ] **Step 2: Run full API test suite**

```bash
cd apps/api && npx vitest run
```

Expected: all rule tests + smoke test PASS (requires Postgres running and migrated).

- [ ] **Step 3: Commit**

```bash
git add apps/api/tests/api.smoke.test.ts
git commit -m "test(api): add end-to-end smoke test for check-in and override flows"
```

---

## Task 16: Web scaffold

**Files:**
- Create: `apps/web/package.json`, `apps/web/tsconfig.json`, `apps/web/vite.config.ts`, `apps/web/index.html`, `apps/web/.env.example`
- Create: `apps/web/src/main.tsx`, `apps/web/src/types.ts`, `apps/web/src/api.ts`, `apps/web/src/styles.css`

- [ ] **Step 1: Scaffold with Vite and install deps**

```bash
cd apps
npm create vite@latest web -- --template react-ts
cd web
npm install qrcode.react
cd ../..
```

- [ ] **Step 2: Create apps/web/.env.example**

```
VITE_API_URL=http://localhost:3001
```

```bash
cp apps/web/.env.example apps/web/.env
```

- [ ] **Step 3: Create apps/web/src/types.ts**

```typescript
export type CheckInStatus = 'NOT_STARTED' | 'IN_PROGRESS' | 'CLEARED' | 'BLOCKED' | 'NEEDS_REVIEW';

export interface Flight {
  id: string;
  flightNumber: string;
  origin: string;
  destination: string;
  departureTime: string;
  aircraftType: string;
  maxBagWeightKg: number;
}

export interface Seat {
  id: string;
  flightId: string;
  seatNumber: string;
  cabinZone: 'FRONT' | 'MID' | 'REAR';
  occupied: boolean;
  passengerId: string | null;
}

export interface Document {
  id: string;
  passportNumber: string;
  fullName: string;
  dob: string;
  nationality: string;
  expiryDate: string;
  confidenceScore: number;
  issues: string[];
  status: string;
}

export interface Bag {
  id: string;
  tagId: string;
  weightKg: number;
  overweight: boolean;
}

export interface BoardingPass {
  id: string;
  seatNumber: string;
  qrPayload: string;
  issuedAt: string;
}

export interface Passenger {
  id: string;
  bookingRef: string;
  firstName: string;
  lastName: string;
  flightId: string;
  groupId: string | null;
  checkInStatus: CheckInStatus;
  declaredBagCount: number;
  riskFlags: string[];
  flight: Flight;
  seat: Seat | null;
  document: Document | null;
  bags: Bag[];
  boardingPass: BoardingPass | null;
}

export interface AuditLogEntry {
  id: string;
  actorRole: string;
  action: string;
  prevStatus: string;
  newStatus: string;
  reason: string;
  timestamp: string;
}
```

- [ ] **Step 4: Create apps/web/src/api.ts**

```typescript
import type { AuditLogEntry, Flight, Passenger, Seat } from './types';

const BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:3001';

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...(init?.headers ?? {}) },
  });
  const body = await res.json();
  if (!res.ok) throw new Error(body.error ?? `request_failed_${res.status}`);
  return body as T;
}

export const api = {
  listFlights: () => request<Flight[]>('/flights'),
  getSeatmap: (flightId: string) => request<{ flight: Flight; seats: Seat[] }>(`/flights/${flightId}/seatmap`),
  listPassengers: (flightId: string) => request<Passenger[]>(`/passengers?flightId=${flightId}`),
  lookupPassenger: (bookingRef: string, lastName: string) =>
    request<Passenger>(`/passengers/lookup?bookingRef=${encodeURIComponent(bookingRef)}&lastName=${encodeURIComponent(lastName)}`),
  getPassenger: (id: string) => request<Passenger>(`/passengers/${id}`),
  submitDocument: (id: string, doc: { passportNumber: string; fullName: string; dob: string; nationality: string; expiryDate: string }) =>
    request<Passenger>(`/passengers/${id}/document`, { method: 'POST', body: JSON.stringify(doc) }),
  confirmSeat: (id: string, seatId: string) =>
    request<Passenger>(`/passengers/${id}/seat`, { method: 'POST', body: JSON.stringify({ seatId }) }),
  declareBags: (id: string, bags: { weightKg: number }[]) =>
    request<Passenger>(`/passengers/${id}/bags`, { method: 'POST', body: JSON.stringify({ bags }) }),
  issueBoardingPass: (id: string) =>
    request<{ passenger: Passenger; boardingPass: Passenger['boardingPass'] }>(`/passengers/${id}/boarding-pass`, { method: 'POST' }),
  override: (id: string, reason: string) =>
    request<Passenger>(`/passengers/${id}/override`, { method: 'POST', body: JSON.stringify({ reason }) }),
  getAuditLog: (id: string) => request<AuditLogEntry[]>(`/passengers/${id}/audit-log`),
};
```

- [ ] **Step 5: Replace apps/web/src/styles.css with minimal layout styles**

```css
body { font-family: system-ui, sans-serif; margin: 0; background: #f5f6f8; color: #1a1a1a; }
.app { max-width: 960px; margin: 0 auto; padding: 16px; }
.role-switcher { display: flex; gap: 8px; margin-bottom: 16px; }
.role-switcher button { padding: 8px 16px; border: 1px solid #333; background: white; cursor: pointer; }
.role-switcher button.active { background: #1a1a1a; color: white; }
.card { background: white; border: 1px solid #ddd; border-radius: 6px; padding: 16px; margin-bottom: 16px; }
.status-badge { display: inline-block; padding: 4px 10px; border-radius: 12px; font-weight: 600; font-size: 0.85rem; }
.status-CLEARED { background: #d4f7dc; color: #15703a; }
.status-BLOCKED { background: #fbd5d5; color: #8a1c1c; }
.status-NEEDS_REVIEW { background: #fff1c2; color: #8a6d00; }
.status-IN_PROGRESS, .status-NOT_STARTED { background: #e2e6ea; color: #444; }
.issue-list { color: #8a1c1c; font-size: 0.9rem; }
table { width: 100%; border-collapse: collapse; }
th, td { text-align: left; padding: 8px; border-bottom: 1px solid #eee; }
tr:hover { background: #fafafa; cursor: pointer; }
form.step { display: flex; flex-direction: column; gap: 8px; max-width: 400px; }
form.step input, form.step select, form.step textarea { padding: 6px; }
```

- [ ] **Step 6: Commit**

```bash
git add apps/web/package.json apps/web/package-lock.json apps/web/tsconfig*.json apps/web/vite.config.ts apps/web/index.html apps/web/.env.example apps/web/src/types.ts apps/web/src/api.ts apps/web/src/styles.css apps/web/src/main.tsx
git commit -m "chore(web): scaffold vite react app with api client and types"
```

---

## Task 17: Role switcher + StatusBadge + App shell

**Files:**
- Create: `apps/web/src/components/RoleSwitcher.tsx`
- Create: `apps/web/src/components/StatusBadge.tsx`
- Modify: `apps/web/src/App.tsx`

- [ ] **Step 1: Create apps/web/src/components/StatusBadge.tsx**

```tsx
import type { CheckInStatus } from '../types';

export function StatusBadge({ status }: { status: CheckInStatus }) {
  return <span className={`status-badge status-${status}`}>{status.replace('_', ' ')}</span>;
}
```

- [ ] **Step 2: Create apps/web/src/components/RoleSwitcher.tsx**

```tsx
export type Role = 'PASSENGER' | 'AGENT';

export function RoleSwitcher({ role, onChange }: { role: Role; onChange: (role: Role) => void }) {
  return (
    <div className="role-switcher">
      <button className={role === 'PASSENGER' ? 'active' : ''} onClick={() => onChange('PASSENGER')}>
        Passenger
      </button>
      <button className={role === 'AGENT' ? 'active' : ''} onClick={() => onChange('AGENT')}>
        Agent
      </button>
    </div>
  );
}
```

- [ ] **Step 3: Replace apps/web/src/App.tsx**

```tsx
import { useState } from 'react';
import { RoleSwitcher, Role } from './components/RoleSwitcher';
import { PassengerView } from './components/PassengerView';
import { AgentView } from './components/AgentView';
import './styles.css';

export default function App() {
  const [role, setRole] = useState<Role>('PASSENGER');

  return (
    <div className="app">
      <h1>Unified Identity Gateway</h1>
      <RoleSwitcher role={role} onChange={setRole} />
      {role === 'PASSENGER' ? <PassengerView /> : <AgentView />}
    </div>
  );
}
```

- [ ] **Step 4: Commit**

```bash
git add apps/web/src/components/RoleSwitcher.tsx apps/web/src/components/StatusBadge.tsx apps/web/src/App.tsx
git commit -m "feat(web): add role switcher and app shell"
```

(This task references `PassengerView` and `AgentView`, created in Tasks 18–19; the app will not compile until those land — commit is still made here per plan order, build is verified at the end of Task 19.)

---

## Task 18: CheckInWizard + BoardingPassCard + PassengerView

**Files:**
- Create: `apps/web/src/components/BoardingPassCard.tsx`
- Create: `apps/web/src/components/CheckInWizard.tsx`
- Create: `apps/web/src/components/PassengerView.tsx`

- [ ] **Step 1: Create apps/web/src/components/BoardingPassCard.tsx**

```tsx
import { QRCodeSVG } from 'qrcode.react';
import type { Passenger } from '../types';

export function BoardingPassCard({ passenger }: { passenger: Passenger }) {
  if (!passenger.boardingPass) return null;
  return (
    <div className="card">
      <h3>Boarding Pass</h3>
      <p>
        {passenger.firstName} {passenger.lastName} — {passenger.flight.flightNumber} ({passenger.flight.origin} →{' '}
        {passenger.flight.destination})
      </p>
      <p>Seat: {passenger.boardingPass.seatNumber}</p>
      <QRCodeSVG value={passenger.boardingPass.qrPayload} size={120} />
      {passenger.bags.map((bag) => (
        <div key={bag.id} style={{ marginTop: 12 }}>
          <p>
            Bag tag {bag.tagId} — {bag.weightKg}kg {bag.overweight ? '(OVERWEIGHT)' : ''}
          </p>
          <QRCodeSVG value={bag.tagId} size={80} />
        </div>
      ))}
    </div>
  );
}
```

- [ ] **Step 2: Create apps/web/src/components/CheckInWizard.tsx**

```tsx
import { useState } from 'react';
import { api } from '../api';
import { StatusBadge } from './StatusBadge';
import { BoardingPassCard } from './BoardingPassCard';
import type { Passenger, Seat } from '../types';

export function CheckInWizard({ passenger: initial }: { passenger: Passenger }) {
  const [passenger, setPassenger] = useState(initial);
  const [seats, setSeats] = useState<Seat[] | null>(null);
  const [bagCount, setBagCount] = useState(1);
  const [bagWeights, setBagWeights] = useState<number[]>([20]);
  const [error, setError] = useState<string | null>(null);
  const [doc, setDoc] = useState({
    passportNumber: '',
    fullName: `${initial.firstName} ${initial.lastName}`,
    dob: '',
    nationality: '',
    expiryDate: '',
  });

  async function refresh(id: string) {
    setPassenger(await api.getPassenger(id));
  }

  async function submitDocument(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      const updated = await api.submitDocument(passenger.id, doc);
      setPassenger(updated);
    } catch (err) {
      setError((err as Error).message);
    }
  }

  async function loadSeats() {
    const { seats } = await api.getSeatmap(passenger.flightId);
    setSeats(seats);
  }

  async function chooseSeat(seatId: string) {
    setError(null);
    try {
      const updated = await api.confirmSeat(passenger.id, seatId);
      setPassenger(updated);
    } catch (err) {
      setError((err as Error).message);
    }
  }

  async function submitBags(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      const bags = bagWeights.slice(0, bagCount).map((weightKg) => ({ weightKg }));
      const updated = await api.declareBags(passenger.id, bags);
      setPassenger(updated);
    } catch (err) {
      setError((err as Error).message);
    }
  }

  async function issuePass() {
    setError(null);
    try {
      const { passenger: updated } = await api.issueBoardingPass(passenger.id);
      setPassenger(updated);
    } catch (err) {
      setError((err as Error).message);
    }
  }

  return (
    <div className="card">
      <h2>
        {passenger.firstName} {passenger.lastName} — {passenger.bookingRef}
      </h2>
      <StatusBadge status={passenger.checkInStatus} />
      {passenger.document && passenger.document.issues.length > 0 && (
        <ul className="issue-list">
          {passenger.document.issues.map((issue) => (
            <li key={issue}>{issue.replace(/_/g, ' ')}</li>
          ))}
        </ul>
      )}
      {error && <p className="issue-list">{error}</p>}

      <h3>1. Document</h3>
      <form className="step" onSubmit={submitDocument}>
        <input
          placeholder="Passport number"
          value={doc.passportNumber}
          onChange={(e) => setDoc({ ...doc, passportNumber: e.target.value })}
        />
        <input placeholder="Full name on document" value={doc.fullName} onChange={(e) => setDoc({ ...doc, fullName: e.target.value })} />
        <input type="date" value={doc.dob} onChange={(e) => setDoc({ ...doc, dob: e.target.value })} />
        <input placeholder="Nationality" value={doc.nationality} onChange={(e) => setDoc({ ...doc, nationality: e.target.value })} />
        <input type="date" value={doc.expiryDate} onChange={(e) => setDoc({ ...doc, expiryDate: e.target.value })} />
        <button type="submit">Submit document</button>
      </form>

      <h3>2. Seat</h3>
      {passenger.seat ? (
        <p>Assigned: {passenger.seat.seatNumber}</p>
      ) : (
        <>
          <button onClick={loadSeats}>Load seat map</button>
          {seats && (
            <select onChange={(e) => chooseSeat(e.target.value)} defaultValue="">
              <option value="" disabled>
                Choose a seat
              </option>
              {seats
                .filter((s) => !s.occupied)
                .map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.seatNumber} ({s.cabinZone})
                  </option>
                ))}
            </select>
          )}
        </>
      )}

      <h3>3. Bags</h3>
      <form className="step" onSubmit={submitBags}>
        <label>
          Bag count:
          <input
            type="number"
            min={0}
            max={5}
            value={bagCount}
            onChange={(e) => {
              const n = Number(e.target.value);
              setBagCount(n);
              setBagWeights((w) => Array.from({ length: n }, (_, i) => w[i] ?? 20));
            }}
          />
        </label>
        {Array.from({ length: bagCount }).map((_, i) => (
          <input
            key={i}
            type="number"
            placeholder={`Bag ${i + 1} weight (kg)`}
            value={bagWeights[i] ?? 20}
            onChange={(e) => {
              const next = [...bagWeights];
              next[i] = Number(e.target.value);
              setBagWeights(next);
            }}
          />
        ))}
        <button type="submit">Declare bags</button>
      </form>

      <h3>4. Boarding pass</h3>
      {passenger.boardingPass ? (
        <BoardingPassCard passenger={passenger} />
      ) : (
        <button onClick={issuePass} disabled={passenger.checkInStatus === 'BLOCKED' || passenger.checkInStatus === 'NEEDS_REVIEW'}>
          Issue boarding pass
        </button>
      )}

      <button style={{ marginTop: 12 }} onClick={() => refresh(passenger.id)}>
        Refresh
      </button>
    </div>
  );
}
```

- [ ] **Step 3: Create apps/web/src/components/PassengerView.tsx**

```tsx
import { useState } from 'react';
import { api } from '../api';
import { CheckInWizard } from './CheckInWizard';
import type { Passenger } from '../types';

export function PassengerView() {
  const [bookingRef, setBookingRef] = useState('');
  const [lastName, setLastName] = useState('');
  const [passenger, setPassenger] = useState<Passenger | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function lookup(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      setPassenger(await api.lookupPassenger(bookingRef, lastName));
    } catch (err) {
      setError((err as Error).message);
    }
  }

  if (passenger) return <CheckInWizard passenger={passenger} />;

  return (
    <div className="card">
      <h2>Find your booking</h2>
      <form className="step" onSubmit={lookup}>
        <input placeholder="Booking reference" value={bookingRef} onChange={(e) => setBookingRef(e.target.value)} />
        <input placeholder="Last name" value={lastName} onChange={(e) => setLastName(e.target.value)} />
        <button type="submit">Find booking</button>
      </form>
      {error && <p className="issue-list">{error}</p>}
    </div>
  );
}
```

- [ ] **Step 4: Commit**

```bash
git add apps/web/src/components/BoardingPassCard.tsx apps/web/src/components/CheckInWizard.tsx apps/web/src/components/PassengerView.tsx
git commit -m "feat(web): add check-in wizard, boarding pass card, and passenger view"
```

---

## Task 19: AgentView + OverridePanel, final wiring, README, end-to-end check

**Files:**
- Create: `apps/web/src/components/OverridePanel.tsx`
- Create: `apps/web/src/components/AgentView.tsx`
- Modify: `README.md`

- [ ] **Step 1: Create apps/web/src/components/OverridePanel.tsx**

```tsx
import { useState } from 'react';
import { api } from '../api';
import type { AuditLogEntry, Passenger } from '../types';

export function OverridePanel({ passenger, onUpdated }: { passenger: Passenger; onUpdated: (p: Passenger) => void }) {
  const [reason, setReason] = useState('');
  const [auditLog, setAuditLog] = useState<AuditLogEntry[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const canOverride = passenger.checkInStatus === 'BLOCKED' || passenger.checkInStatus === 'NEEDS_REVIEW';

  async function submitOverride(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      const updated = await api.override(passenger.id, reason);
      onUpdated(updated);
      setReason('');
    } catch (err) {
      setError((err as Error).message);
    }
  }

  async function loadAuditLog() {
    setAuditLog(await api.getAuditLog(passenger.id));
  }

  return (
    <div className="card">
      <h3>Agent override</h3>
      {canOverride ? (
        <form className="step" onSubmit={submitOverride}>
          <textarea placeholder="Reason for override" value={reason} onChange={(e) => setReason(e.target.value)} required />
          <button type="submit">Override to CLEARED</button>
        </form>
      ) : (
        <p>No override needed — passenger is not blocked or flagged.</p>
      )}
      {error && <p className="issue-list">{error}</p>}
      <button onClick={loadAuditLog}>Load audit log</button>
      {auditLog && (
        <ul>
          {auditLog.map((entry) => (
            <li key={entry.id}>
              {new Date(entry.timestamp).toLocaleString()} — {entry.prevStatus} → {entry.newStatus}: {entry.reason}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Create apps/web/src/components/AgentView.tsx**

```tsx
import { useEffect, useState } from 'react';
import { api } from '../api';
import { StatusBadge } from './StatusBadge';
import { CheckInWizard } from './CheckInWizard';
import { OverridePanel } from './OverridePanel';
import type { Flight, Passenger } from '../types';

export function AgentView() {
  const [flights, setFlights] = useState<Flight[]>([]);
  const [flightId, setFlightId] = useState('');
  const [passengers, setPassengers] = useState<Passenger[]>([]);
  const [selected, setSelected] = useState<Passenger | null>(null);
  const [filter, setFilter] = useState<'ALL' | 'BLOCKED' | 'NEEDS_REVIEW'>('ALL');

  useEffect(() => {
    api.listFlights().then((fs) => {
      setFlights(fs);
      if (fs[0]) setFlightId(fs[0].id);
    });
  }, []);

  useEffect(() => {
    if (flightId) api.listPassengers(flightId).then(setPassengers);
  }, [flightId]);

  const visible = passengers.filter((p) => filter === 'ALL' || p.checkInStatus === filter);

  function handleUpdated(updated: Passenger) {
    setSelected(updated);
    setPassengers((prev) => prev.map((p) => (p.id === updated.id ? updated : p)));
  }

  return (
    <div>
      <div className="card">
        <label>
          Flight:
          <select value={flightId} onChange={(e) => setFlightId(e.target.value)}>
            {flights.map((f) => (
              <option key={f.id} value={f.id}>
                {f.flightNumber} ({f.origin} → {f.destination})
              </option>
            ))}
          </select>
        </label>
        <label style={{ marginLeft: 12 }}>
          Filter:
          <select value={filter} onChange={(e) => setFilter(e.target.value as typeof filter)}>
            <option value="ALL">All</option>
            <option value="BLOCKED">Blocked</option>
            <option value="NEEDS_REVIEW">Needs review</option>
          </select>
        </label>
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Booking</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {visible.map((p) => (
              <tr key={p.id} onClick={() => setSelected(p)}>
                <td>
                  {p.firstName} {p.lastName}
                </td>
                <td>{p.bookingRef}</td>
                <td>
                  <StatusBadge status={p.checkInStatus} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {selected && (
        <>
          <CheckInWizard passenger={selected} />
          <OverridePanel passenger={selected} onUpdated={handleUpdated} />
        </>
      )}
    </div>
  );
}
```

- [ ] **Step 3: Update README.md run instructions**

Append to the end of `README.md`:

```markdown
## Running locally

```bash
docker compose up -d postgres
cd apps/api && cp .env.example .env && npm install && npx prisma migrate dev --name init && npx tsx prisma/seed.ts && npm run dev
# in a second terminal
cd apps/web && cp .env.example .env && npm install && npm run dev
```

API on `http://localhost:3001`, web UI on the Vite dev URL printed in the terminal (typically `http://localhost:5173`).

Run API tests: `cd apps/api && npx vitest run` (requires Postgres running and migrated).
```

- [ ] **Step 4: Full end-to-end manual check**

```bash
docker compose up -d postgres
cd apps/api && npx prisma migrate deploy && npx tsx prisma/seed.ts && npm run dev &
cd ../web && npm run dev &
sleep 3
curl -s http://localhost:3001/flights | head -c 200
```

Open the printed Vite URL in a browser. Switch to Agent, pick a flight, click the `NOPASS` passenger, confirm status shows BLOCKED with `missing_or_invalid_passport_number`, use the override panel to clear it, confirm audit log entry appears. Switch to Passenger, look up `CLEAN1` / `Doe`, walk through document → seat → bags → boarding pass, confirm a QR code renders. Stop both dev servers when done.

- [ ] **Step 5: Commit**

```bash
git add apps/web/src/components/OverridePanel.tsx apps/web/src/components/AgentView.tsx README.md
git commit -m "feat(web): add agent view with override panel and audit log; document run instructions"
```

---

## Spec Coverage Check

- Passenger lookup, doc upload/validate, seat confirm, bag declare, tag+pass gen, ready-for-boarding → Tasks 9–13, 18–19.
- Cleared/blocked/needs-review with reasons → Tasks 3–5 (rules engine), surfaced via `StatusBadge` + `issue-list` in Task 18.
- Document confidence score → Task 3.
- Agent override + audit log → Task 14, 19.
- Role switcher, no auth → Task 17.
- QR-rendered boarding pass/bag tag → Task 18.
- Seed data covering all status paths → Task 7.
- Rules engine unit tests + light API smoke test, no heavy e2e → Tasks 3–5, 15.
