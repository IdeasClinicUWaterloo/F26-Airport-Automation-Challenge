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

| Regulation / Standard | What it says | Link |
|---|---|---|
| *Canadian Aviation Security Regulations, 2012* (SOR/2011-318) | All checked baggage must be screened before being loaded, and access to restricted areas such as baggage handling zones must be limited to authorized personnel | [laws-lois.justice.gc.ca](https://laws-lois.justice.gc.ca/eng/regulations/SOR-2011-318/index.html) |
| ICAO Annex 17 — Aviation Security | A bag must not be loaded onto a flight if the passenger it belongs to is not on board, unless the bag has been individually identified and screened | [icao.int](https://www.icao.int/aviation-security-policy-section/Annex17) |
| *Secure Air Travel Regulations* (SOR/2015-181) | Before a passenger boards, the carrier must confirm that the name on their boarding pass matches a valid government-issued photo ID | [laws-lois.justice.gc.ca](https://laws-lois.justice.gc.ca/eng/regulations/SOR-2015-181/FullText.html) |
| *Air Passenger Protection Regulations* (SOR/2019-150) | If a flight is delayed or cancelled, or a passenger is denied boarding, the carrier must communicate the reason, provide care such as meals or hotels where applicable, and pay compensation based on the length of delay | [laws-lois.justice.gc.ca](https://laws-lois.justice.gc.ca/eng/regulations/SOR-2019-150/index.html) |
| *Personal Information Protection and Electronic Documents Act* (PIPEDA) | Organizations must tell passengers what personal information they are collecting and why, collect only what they need, keep it secure, and delete it when it is no longer needed | [laws-lois.justice.gc.ca](https://laws-lois.justice.gc.ca/eng/acts/P-8.6/index.html) |
| *Accessible Transportation for Persons with Disabilities Regulations* (SOR/2019-244) | Airports, airlines, CATSA, and CBSA must provide assistance to passengers with disabilities at every stage of their journey, including check-in, security, boarding, and baggage collection | [laws-lois.justice.gc.ca](https://laws-lois.justice.gc.ca/eng/regulations/SOR-2019-244/index.html) |
| *Accessible Canada Act* | Federally regulated organizations must publish accessibility plans, consult people with disabilities in developing them, and actively work to remove barriers, not just respond when someone asks for help | [laws-lois.justice.gc.ca](https://lois.justice.gc.ca/eng/acts/A-0.6/FullText.html)|

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
