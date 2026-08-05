# Passenger Monitoring and Processing

Airports process thousands of passengers and bags across check-in, baggage drop, security, boarding, and carousel collection. Each handoff can introduce delays, misrouted bags, congestion, accessibility barriers, or security concerns.

This challenge focuses on passenger monitoring and processing in an aviation environment. You can use the supplied projects as a starting point or build an independent solution for passenger flow, verification, accessibility, baggage reconciliation, or operational awareness.

## Table of Contents

- [Challenge](#challenge)
- [Potential Solutions](#potential-solutions)
- [Getting Started](#getting-started)
- [Resources](#resources)

## Challenge

Design a solution that improves passenger movement, verification, accessibility, or operational awareness at one or more airport checkpoints.

A useful system should make it clear:

- which passenger, bag, queue, or checkpoint state is being tracked;
- how that state changes after each event;
- what staff or passengers need to know next;
- how delays, missing information, and manual-review cases are handled;
- what personal data is collected and how long it is retained;
- how information and controls remain accessible.

You may build software, a simulation, a dashboard, a hardware-assisted prototype, or a tested design demonstration.

### Industry Context

Passenger-processing systems operate across three connected layers.

**Sensing:** Cameras, barcode scanners, weight sensors, LiDAR, and biometric readers can capture information at checkpoints.

**Control and verification:** Systems compare observations with flight manifests, passenger records, baggage records, and security rules. They flag anomalies and route passengers or assets to the next step.

**Data and visualization:** Operator dashboards combine live checkpoint information into alerts, flow measures, and congestion maps. Staff use these views to open another lane, reassign staff, assist a passenger, or hold a gate.

A design should connect sensing to a decision. Collecting data is not useful by itself unless a passenger or staff member can understand and act on the result.

### Regulatory and Safety Context

Passenger-processing systems handle personal information, restricted-area access, baggage screening, passenger rights, and accessibility. A prototype is not expected to implement every legal requirement, but its data and workflow choices should acknowledge the environment in which a real system would operate.

Canadian aviation security and accessibility regulations are developed alongside international aviation standards. Some primary ICAO documents, including Annex 17, Annex 9, and Doc 9984, are restricted publications available through the [ICAO Store](https://store.icao.int/).

| Regulation | Requirements relevant to this challenge | Link |
| --- | --- | --- |
| Canadian Aviation Security Regulations, 2012 | Passengers must be identity-screened and meet the identification requirements before passing a screening checkpoint (s. 8.3). No person may help another person circumvent screening (s. 14). Screening authorities may force open locked checked baggage for screening, must notify the passenger, and must retain a record for at least 180 days (ss. 14.1 and 14.2). A change to a baggage-handling system that may affect screening operations requires CATSA agreement before implementation (ss. 126 and 436). | [Justice Laws website](https://laws-lois.justice.gc.ca/eng/regulations/SOR-2011-318/index.html) |
| Secure Air Travel Regulations | At the boarding gate, carriers must verify a passenger's identity using the identification described in sections 3 and 4. The carrier must compare the boarding-pass name with the identification and, when photo identification is presented, compare the passenger's face with the photograph (s. 4.1). | [Justice Laws website](https://laws-lois.justice.gc.ca/eng/regulations/SOR-2015-181/FullText.html) |
| Air Passenger Protection Regulations | During a tarmac delay, carriers must provide food, water, ventilation, and lavatory access, and must allow passengers to disembark after three hours subject to the regulation's conditions (ss. 8 and 9). For defined delays or cancellations within the carrier's control, passengers must receive information and alternate travel arrangements or a refund when the applicable conditions are met (s. 12). Passenger-rights notices must be visible at check-in desks, self-service kiosks, and boarding gates (s. 7). | [Justice Laws website](https://laws-lois.justice.gc.ca/eng/regulations/SOR-2019-150/index.html) |
| Personal Information Protection and Electronic Documents Act (PIPEDA) | Organizations must identify the purpose of collecting personal information before or at collection and obtain the individual's knowledge and consent (Principles 2 and 3). Collection must be limited to what is needed (Principle 4). Information must be used only for its identified purpose, retained only as long as required, and then destroyed (Principle 5). Reasonable safeguards must protect it against loss, theft, or unauthorized access (Principle 7). | [Justice Laws website](https://laws-lois.justice.gc.ca/eng/acts/P-8.6/index.html) |
| Accessible Transportation for Persons with Disabilities Regulations | Public-facing information must be available in accessible formats, and electronic content must meet the applicable WCAG requirements (s. 9). Departure and safety announcements must be available in audio and visual formats (s. 10). Self-service kiosks must meet accessibility requirements, with staff assistance available on request (ss. 11 to 13). Personnel interacting with passengers must receive training on communication and assistance (s. 16). | [Justice Laws website](https://laws-lois.justice.gc.ca/eng/regulations/SOR-2019-244/index.html) |
| Accessible Canada Act | Federally regulated organizations must publish an accessibility plan, update it regularly, consult people with disabilities while developing it, and publish progress reports on barrier removal. | [Justice Laws website](https://lois.justice.gc.ca/eng/acts/A-0.6/FullText.html) |

Use the linked regulations for design context. A real deployment would still require legal, privacy, accessibility, security, and operational review.

## Potential Solutions

The following directions come from the original challenge material. You may combine them, extend the supplied implementations, or build something different.

### SecureBag: Luggage Visual Verification

The working [`SecureBag`](../../baggage-handling-system/securebag/README.md) proof of concept compares a bag photographed at check-in with the bag seen at a later checkpoint. It explores a weakness in relying only on a detachable luggage tag to identify the physical bag.

Potential projects include:

- improve image-comparison accuracy with another feature detector or model;
- add bag weight as another verification signal;
- connect a Raspberry Pi camera and barcode scanner for checkpoint capture;
- send live alerts to security staff when a bag is flagged;
- extend the staff dashboard with bag location and verification history.

### Passenger Flow and Congestion Monitoring

Airports need real-time visibility into bottlenecks. Staff may otherwise rely on visual observation or delayed reports when deciding whether to open another lane or redirect passenger flow.

Potential projects include:

- simulate passengers moving through terminal checkpoints with agent-based modelling;
- build a dashboard that tracks density or queue length by zone;
- alert staff when a threshold is exceeded and explain the recommended response;
- model staffing decisions using queue length, wait time, and flight schedules.

### Accessible Passenger Processing

Accessibility services are often something passengers must find and request separately. A better system could include accessibility in the normal passenger journey while protecting sensitive information and preserving passenger choice.

Potential projects include:

- create an opt-in accessibility profile linked to a boarding pass;
- show staff which passengers requested assistance at each checkpoint;
- provide targeted wayfinding for passengers with mobility or vision requirements;
- present status and safety announcements in both visual and audio forms;
- evaluate a kiosk or check-in flow for keyboard, screen-reader, and low-vision use.

### Additional Directions

| Direction | What it could do | Related material |
| --- | --- | --- |
| Checkpoint status tracker | Show completed steps and explain why a passenger is cleared, blocked, or waiting. | [Unified Identity Gateway](../unified-identity-gateway/README.md) |
| Document-review workflow | Validate required fields and route uncertain cases to a person. | [Identity validation rules](../unified-identity-gateway/apps/api/src/rules/) |
| Passenger and bag reconciliation | Link accepted bags to passengers and flag missing or unexpected handoffs. | [Baggage Handling System](../../baggage-handling-system/README.md) |
| Operations dashboard | Combine passenger exceptions, queue conditions, baggage state, and flight readiness. | [Departure Control System overview](../README.md) |

## Getting Started

### Run the SecureBag Example

Follow the complete [SecureBag starter workflow](../../baggage-handling-system/securebag/README.md#starter-workflow). From the `passenger-processing/` folder, a local setup looks like this:

```bash
cd ../../baggage-handling-system/securebag
python -m venv .venv
```

Activate the environment on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Or on macOS and Linux:

```bash
source .venv/bin/activate
```

Then install and run the application:

```bash
pip install -r requirements.txt
python app.py
```

Open `http://localhost:5001`. The network address printed in the terminal can also be opened on a phone connected to the same local network.

### Build an Independent Project

1. Identify the passenger, staff member, or operator using the result.
2. Define the event or decision the system must handle.
3. Model the passenger, bag, queue, checkpoint, or flight state required for that decision.
4. Create normal, delayed, missing-data, and manual-review cases.
5. Process those cases and show both the result and the next action.
6. Explain the data, accessibility, safety, and operational assumptions.

A mock event might look like this:

```json
{
  "passenger_id": "P1042",
  "flight_id": "AC101",
  "checkpoint": "security",
  "status": "needs_review",
  "reason": "document_name_mismatch",
  "updated_at": "2026-06-05T10:15:00"
}
```

Do not use real passport numbers, biometric data, medical details, or other sensitive information in the prototype.

### Workspace Structure

```text
F26-Airport-Automation-Challenge/
├── departure-control-system/
│   ├── README.md
│   ├── passenger-processing/
│   │   └── README.md
│   └── unified-identity-gateway/
└── baggage-handling-system/
    └── securebag/
        ├── README.md
        ├── app.py
        ├── bag_compare.py
        ├── requirements.txt
        └── bags.json
```

## Resources

### Challenge Resources

- [Departure Control System overview](../README.md)
- [Unified Identity Gateway example](../unified-identity-gateway/README.md)
- [SecureBag proof of concept](../../baggage-handling-system/securebag/README.md)
- [Baggage Handling System challenge](../../baggage-handling-system/README.md)

### Canadian Safety, Privacy, and Accessibility References

- [Canadian Aviation Security Regulations, 2012](https://laws-lois.justice.gc.ca/eng/regulations/SOR-2011-318/index.html)
- [Secure Air Travel Regulations](https://laws-lois.justice.gc.ca/eng/regulations/SOR-2015-181/FullText.html)
- [Air Passenger Protection Regulations](https://laws-lois.justice.gc.ca/eng/regulations/SOR-2019-150/index.html)
- [Personal Information Protection and Electronic Documents Act](https://laws-lois.justice.gc.ca/eng/acts/P-8.6/index.html)
- [Accessible Transportation for Persons with Disabilities Regulations](https://laws-lois.justice.gc.ca/eng/regulations/SOR-2019-244/index.html)
- [Accessible Canada Act](https://laws-lois.justice.gc.ca/eng/acts/A-0.6/FullText.html)
