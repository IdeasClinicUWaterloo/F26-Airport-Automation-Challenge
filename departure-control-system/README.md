# Departure Control System Automation

## Challenge overview

A Departure Control System (DCS) runs the departure side of an airline operation: check-in, identity and document verification, baggage acceptance, boarding pass issuance, boarding control, and weight and balance.

It answers questions like:

- Is this passenger correctly identified, with valid documents for the destination?
- How many bags should we expect from this passenger or group?
- Is the aircraft load balanced across cabin and cargo?
- Has a bag moved from check-in through screening, sorting, and loading?
- Can check-in, baggage, identity, and boarding all be seen from one place?

This challenge is a scaled-down version of that problem. Pick a piece of it and build a real solution - see [Challenge summary](#challenge-summary).

## Industry context

Airline departure operations run on systems that must stay in sync - passenger records, schedules, seat maps, aircraft configuration, baggage data, document checks, boarding status, load constraints - all changing right up to departure.

A DCS sits at the center: it takes in passenger and booking data, runs check-in, accepts bags, validates documents, issues boarding passes, tracks boarding, and feeds load control, continuously.

The industry is shifting from rule-based, manually supervised processing toward predictive, AI-assisted processing: estimating bag counts, spotting group patterns, flagging no-show risk, recommending load adjustments before problems show up at the gate.

**Real systems that solve this problem:** Brock Solutions SmartSuite Enterprise, SITA Horizon DCS, Amadeus Altéa Departure Control. Yours will be much smaller, but the underlying ideas are the same.

## The pipeline

1. Load passenger, booking, flight, and aircraft data
2. Passenger checks in and verifies identity
3. Documents are validated; issues flagged for review
4. Bags are accepted, tagged, linked to the passenger
5. Bag scans update live baggage state
6. Load is estimated across aircraft zones
7. System recommends seat, bag, or review actions
8. Operational view shows departure readiness

Focus on clear data flow and decisions, not handling every edge case.

## How this maps to real systems

| Hackathon concept | Industry analogue |
|---|---|
| Check-in flow | DCS check-in processing |
| ID/document upload | Passport/visa/identity verification |
| Boarding pass generation | Departure control passenger acceptance |
| Bag tag creation | Baggage acceptance and reconciliation |
| Scan events | Baggage handling system tracking |
| Bag status dashboard | Baggage operations monitoring |
| Predicted bag count | Passenger behavior / load forecasting |
| Seat/load recommendation | Aircraft load control |
| Manual review flags | Agent intervention, exception handling |
| Unified ops dashboard | Departure readiness control |

## Challenge summary

The problem space is anything inside a DCS - check-in, identity/document verification, baggage tracking, load balancing, boarding control, or the dashboard tying it together. There's no fixed feature list: pick a piece and build a real solution to it. Narrow and complete beats broad and shallow.

This repo includes two implemented examples, covering different slices of the DCS pipeline. They're here to show expected scope and depth, not to define the required shape of your submission:

- **[Unified Identity Gateway](unified-identity-gateway/)** - identity verification, document checks, and boarding pass issuance as a single check-in flow that clearly shows whether a passenger is cleared, blocked, or needs manual review.
- **[Load Control](load-control/)** - the "load is estimated across aircraft zones" step of the pipeline: a MILP-based weight-and-balance optimizer (`load.py`) that assigns cargo and passenger load to aircraft bays/zones to hit a target center-of-gravity within structural and zero-fuel-weight limits, plus a small Flask app (`weight_balancer_app/`) exposing it as a live tool.

## Basic vs. advanced

**Basic:** a deterministic workflow on mock data - clean modeling, obvious rule-based checks, a readable UI.

**Advanced:** a predictive decision-support system - estimate what's likely to happen and recommend action before all the data is in.

## State to track

Model whatever your problem needs, clearly enough that state changes are traceable. Typical entities: **passenger** (ID, booking, flight, seat, document status, boarding status), **baggage** (tag ID, passenger, location/status, weight, exceptions), **flight** (aircraft type, seat map, zones, load, readiness).

## Inputs

Mock data - passenger lists, bookings, seat maps, aircraft layouts, baggage records, scan events, document fields, schedules. Expect it messy: missing fields, late updates, conflicting counts, inconsistent scans.

## Expected outputs

Whatever your solution produces should make departure readiness legible: status, decisions made, exceptions flagged, and why.

## Evaluation

- **Workflow completeness** - realistic, end-to-end flow?
- **Data modeling** - clearly represented state?
- **Decision quality** - are recommendations/flags actually useful?
- **Exception handling** - does it catch messy or inconsistent data?
- **Dashboard clarity** - can an operator tell readiness at a glance?
- **Code quality** - modular, readable, maintainable?
- **Demo quality** - does it make the case for why this matters?

## Suggested milestones

1. **Mock data and core models** - the entities your solution needs. *Demo: show them for one flight.*
2. **Core flow working end-to-end** - the main thing your solution does, deterministically. *Demo: walk through one passenger/bag/decision.*
3. **Exception handling** - flag the messy cases. *Demo: show a blocked/flagged case and why.*
4. **Predictive/decision logic** - if applicable, add a smarter layer on top of the deterministic baseline. *Demo: explain a recommendation.*
5. **Dashboard** - a single view of state and readiness. *Demo: an operator can see at a glance.*
6. **Polish** - better test data, edge cases, a clean demo script.

## Optional stretch goals

Push any part of your solution from basic to advanced: richer data, smarter predictions, sharper UI, an audit log for overrides.

## Final goal

By the end, your system should make it clear: what's the state of the problem you picked, what needs attention, and why.

That's the same question real DCS platforms answer for airlines every day before the aircraft pushes back.

## Safety & Policy Resources

- [IATA Resolution 753](https://www.iata.org/contentassets/5c4aa8b8b3b1432697d2bf3301450684/reso753-implementation-guide---2023_issue-4.02.pdf) - requires airlines to scan a bag at each handoff
- [ICAO Doc 9303](https://www.icao.int/publications/pages/publication.aspx?docnum=9303) - the standard for machine-readable passports and ID docs
- [ICAO Annex 9](https://www.icao.int/facilitation-programmes/Annex9) - border and document control rules
- [ICAO Annex 6, Part I / IATA Weight and Balance Manual](https://www.icao.int/sites/default/files/sp-files/SAM/Documents/2008/RPEO03/Anexo%206%20ParteII%20Just%20Cambios.pdf) - weight and balance rules (see `load-control/`)
