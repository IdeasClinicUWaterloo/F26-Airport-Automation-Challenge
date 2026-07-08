# Passenger Monitoring & Processing

## Challenge Overview

Airports process thousands of passengers and bags per hour across multiple checkpoints — check-in, baggage drop, security, boarding, and carousel collection. Each handoff is a potential point of failure: delays, misrouted bags, congestion, and security gaps all have real operational and safety consequences.

This challenge focuses on passenger monitoring and processing in aviation environments. You will have the opportunity to learn about the operational problems airports face and design a solution to address them. You can use the provided tools as a starting point or build an independent solution focused on any aspect of passenger or asset processing.

## Industry Context

Passenger processing systems operate across three layers:

**Sensing:** Cameras, barcode scanners, weight sensors, LiDAR, and biometric readers capture data at each checkpoint.

**Control & Verification:** Systems cross-reference scanned data against flight manifests and passenger records in real time, flagging anomalies and routing passengers or assets accordingly.

**Data & Visualization:** Operator dashboards synthesize live checkpoint data into alerts, flow metrics, and congestion maps that staff use to make operational decisions — opening additional lanes, reallocating staff, or holding a gate.

## Potential Solutions

To jump-start your project, this repository contains a working proof-of-concept you may use, modify, or build on.

### 1: SecureBag — Luggage Visual Verification System

Located in the [securebag](.../securebag) directory, this system addresses a documented security vulnerability: luggage tag switching, where tags are swapped between bags to route contraband onto flights through unsuspecting passengers.

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
