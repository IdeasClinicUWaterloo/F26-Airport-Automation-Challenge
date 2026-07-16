# Passenger Monitoring & Processing

## Challenge Overview

Airports process thousands of passengers and bags per hour across multiple checkpoints — check-in, baggage drop, security, boarding, and carousel collection. Each handoff is a potential point of failure: delays, misrouted bags, congestion, and security gaps all have real operational and safety consequences.

This challenge focuses on passenger monitoring and processing in aviation environments. You will have the opportunity to learn about the operational problems airports face and design a solution to address them. You can use the provided tools as a starting point or build an independent solution focused on any aspect of passenger or asset processing.

## Industry Context

Passenger processing systems operate across three layers:

**Sensing:** Cameras, barcode scanners, weight sensors, LiDAR, and biometric readers capture data at each checkpoint.

**Control & Verification:** Systems cross-reference scanned data against flight manifests and passenger records in real time, flagging anomalies and routing passengers or assets accordingly.

**Data & Visualization:** Operator dashboards synthesize live checkpoint data into alerts, flow metrics, and congestion maps that staff use to make operational decisions — opening additional lanes, reallocating staff, or holding a gate.

## Regulatory & Safety Context

Passenger processing systems operate in a heavily regulated environment — handling personal data, managing access to restricted areas, and directly affecting passenger safety and rights. A system that stores passport numbers without a retention policy, or a flow monitoring tool that contributes to a missed boarding, has real legal obligations. Knowing which regulations govern this space is useful both for making sound design decisions and for the Safety and Security judging category.

Solutions developed in this challenge that involve passenger data, baggage handling, or airport operations should be designed with the following Canadian regulations in mind. Canada's aviation security and accessibility regulations are developed in alignment with ICAO international standards, though the primary ICAO documents (Annex 17, Annex 9, Doc 9984) are restricted publications available for purchase through the [ICAO Store](https://store.icao.int).

| Regulation | Key requirements relevant to this challenge | Link |
|---|---|---|
| *Canadian Aviation Security Regulations, 2012* (SOR/2011-318) | Passengers must be identity-screened before passing a screening checkpoint — name on boarding pass must match photo ID (s.8.3). No person may help another circumvent screening (s.14). Screening authorities may force open locked checked baggage for screening and must notify the passenger and keep a record for at least 180 days when they do (s.14.1–14.2). Any change to a baggage handling system that may affect screening operations requires CATSA agreement before implementation (s.126/436). | [laws-lois.justice.gc.ca](https://laws-lois.justice.gc.ca/eng/regulations/SOR-2011-318/index.html) |
| *Secure Air Travel Regulations* (SOR/2015-181) | At the boarding gate, carriers must verify that the name on the boarding pass matches the passenger's government-issued photo ID, and compare the passenger's face to the photo on their ID (s.3–4). | [laws-lois.justice.gc.ca](https://laws-lois.justice.gc.ca/eng/regulations/SOR-2015-181/FullText.html) |
| *Air Passenger Protection Regulations* (SOR/2019-150) | If a flight is delayed on the tarmac, carriers must provide food, water, ventilation, and access to lavatories, and must allow passengers to disembark after three hours (s.8–9). If a delay or cancellation is within the carrier's control, passengers must be informed and offered alternate travel arrangements or a refund if the delay reaches three hours or more (s.12). Carriers must display passenger rights notices visibly at check-in desks, self-service kiosks, and boarding gates (s.7). | [laws-lois.justice.gc.ca](https://laws-lois.justice.gc.ca/eng/regulations/SOR-2019-150/index.html) |
| *Personal Information Protection and Electronic Documents Act* (PIPEDA) | Organizations must identify the purpose of collecting personal information before or at the time of collection, and must obtain the individual's knowledge and consent (Principles 2–3). Collection must be limited to what is needed for the identified purpose (Principle 4). Information must only be used or disclosed for the purpose it was collected, kept only as long as needed, and then destroyed (Principle 5). Reasonable safeguards must be in place to protect personal information from loss, theft, or unauthorized access (Principle 7). | [laws-lois.justice.gc.ca](https://laws-lois.justice.gc.ca/eng/acts/P-8.6/index.html) |
| *Accessible Transportation for Persons with Disabilities Regulations* (SOR/2019-244) | All public-facing information must be available in accessible formats — electronic content must meet WCAG 2.0 Level AA (s.9). Departure and safety announcements must be made in both audio and visual formats (s.10). Self-service kiosks must meet accessibility standards and staff must assist passengers with disabilities in using them on request (s.11–13). Personnel who interact with passengers must be trained on communicating with persons with disabilities and on the types of assistance available (s.16). | [laws-lois.justice.gc.ca](https://laws-lois.justice.gc.ca/eng/regulations/SOR-2019-244/index.html) |
| *Accessible Canada Act* | Federally regulated organizations must publish an accessibility plan, update it regularly, and consult persons with disabilities in developing it. They must also publish progress reports on barrier removal. | [laws-lois.justice.gc.ca](https://lois.justice.gc.ca/eng/acts/A-0.6/FullText.html) |
## Potential Solutions

To jump-start your project, this repository contains a working proof-of-concept you may use, modify, or build on.

### 1: SecureBag — Luggage Visual Verification System

Located in the [securebag](securebag) directory, this system addresses a documented security vulnerability: luggage tag switching, where tags are swapped between bags to route contraband onto flights through unsuspecting passengers.

**Potential projects:**

- Improve comparison accuracy using SIFT instead of ORB, or add bag weight as a third verification signal
- Connect to a Raspberry Pi camera and barcode scanner to automate photo capture at each checkpoint
- Build a live alert pipeline that notifies security staff when a bag is flagged
- Extend the staff dashboard to show bag location across the handling system in real time

### 2: Passenger Flow & Congestion Monitoring

Airports need real-time visibility into where passengers are and where bottlenecks are forming. Staff currently rely on visual observation or lagged reports to decide when to open additional lanes or redirect flow.

**Potential projects:**

- Simulate passenger flow across terminal checkpoints using agent-based modelling
- Build a dashboard that tracks density per zone and alerts when thresholds are exceeded
- Model staff allocation decisions based on live congestion data

### 3: Accessible Passenger Processing

Accessibility services are currently something passengers must seek out rather than being integrated into the processing system. Airports have limited data on where passengers with disabilities experience delays or difficulties.

**Potential projects:**

- Design an opt-in accessibility profile tied to a passenger's boarding pass
- Build a staff-facing view showing which passengers need assistance at each checkpoint
- Prototype targeted wayfinding notifications for passengers with mobility or vision requirements

## Getting Started

```bash
git clone https://github.com/your-username/securebag.git
cd securebag
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 app.py
```

Open `http://localhost:5001`. The network URL printed in the terminal can be opened on any phone on the same WiFi.

## Workspace Directory Structure

```
repository-root/
│
├── README.md
│
└── securebag/
    ├── README.md
    ├── app.py
    ├── bag_compare.py
    ├── requirements.txt
    └── bags.json
```
