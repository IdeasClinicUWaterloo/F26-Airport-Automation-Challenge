# Baggage Handling System

![alt text](assets/conveyor_system.webp)

## Challenge Overview

Brock Solutions is a global engineering solutions and professional services company that designs, builds, and integrates large-scale automation software for transit, aviation, and industrial logistics. In any high-throughput sorting or material handling environment, multiple disciplines must converge: fast-moving mechanical transport, real-time control logic, edge sensing and vision, and human-in-the-loop situational awareness dashboards.

In a real airport terminal, a baggage handling system is a dynamic, high-volume logistical network. Sorting thousands of bags per hour requires coordinated control, reliable tracking, and clear operational visibility across the airport. This challenge provides a few starting points for approaching that space.

The primary supported direction for this subproblem is **SecureBag**, which frames baggage handling as a visual identity and verification workflow. The secondary supported direction is the **barcode conveyor** environment, which focuses on physical routing with camera-based barcode capture and edge automation. A separate **BHS simulation** environment is also available for teams that want a more software-focused and algorithmic path.

---

## Industry Context

Modern industrial sortation networks are complex ecosystems responsible for moving thousands of assets per hour with zero tracking loss. To achieve this, automated systems rely on an integrated three-layer technology stack:

1. **The Physical/Sensing Layer:** Conveyor tracks, mechanical diverters, photo-eyes, laser arrays, and vision systems that transport items and capture physical operational data at high speeds.

2. **The Control Layer:** High-Level Control (HLC) brains that interpret sensor data in real time, evaluate routing choices, manage traffic density, and instantly actuate physical sorting hardware to steer items safely around system line blocks or mechanical jams.

3. **The Data & Visual Layer:** High-frequency data historians that capture continuous time-series event logs, paired with operator command-center dashboards that synthesize background telemetry into clear, actionable visual alerts and live performance metrics.

A failure or inefficiency in any single layer compromises the entire facility. This challenge provides you with the tools and environments to innovate anywhere across this stack.

---

## Supported Solution Paths

This repository includes a small set of starter environments that can be used as the foundation for a BHS project.

### 1: SecureBag

Located in the [securebag](securebag) directory, this path centers on a visual bag verification workflow. Rather than starting from a conveyor control loop, it focuses on the airport's core operational challenge of confirming that the bag presented at the checkpoint is the same bag that was checked in.

SecureBag provides a practical foundation for exploring how visual evidence, bag metadata, and lightweight operational tooling can be combined to flag suspicious activity before a bag reaches the gate.

**Potential projects:**

- Add a weight-based verification signal
- Improve automation for checkpoint capture and scanning
- Add stronger alerting and staff dashboard workflows
- Expand the system to cover more of the baggage lifecycle

### 2: Barcode Conveyor

Located in the [`barcode-conveyor/`](barcode-conveyor) directory, this path provides a physical hardware and edge-computing setup centered on camera-driven barcode tracking and sorting logic. It is a strong option when a team wants to work more directly with live sensing, industrial hardware, and automation timing.

This path is well suited to teams that want to build around object identification, conveyor control, and device-to-device communication in a more physical execution environment.

**Potential projects:**

- Real-time barcode recognition and validation on the edge
- Timing and state coordination between camera capture and diverter action
- Operational dashboarding or logging built around scanner and routing telemetry

## Optional Independent Paths

### BHS Simulation

Located in the [`bhs-simulation/`](bhs-simulation) directory, this environment offers a software-focused simulation of a larger baggage network. It is intended for teams that want to explore routing, algorithmic optimization, flow control, and dashboard-style analysis in a more abstract, data-driven setting.

This path is available for teams who want a more software-heavy and algorithmic solution they can pursue independently.

**Potential projects:**

- More intelligent pathfinding around congestion and failures
- Performance optimization and network-aware routing strategies
- Dashboard or analytics improvements for operational visibility

### Custom or Hybrid Systems

You are welcome to step outside the provided templates and adapt the solution in your own direction. You may combine approaches, use live hardware input to influence broader network logic, or build a unique prototype that mixes simulation, sensing, and operational dashboards.

---

## Workspace Directory Structure

The repository is organized into a few project directories that represent the supported and some unsupported paths:

```text
baggage-handling-system/
│
├── README.md
│
├── securebag/
│   ├── README.md
│   ├── sample_img/
│   ├── app.py
│   ├── bag_compare.py
│   └── bags.json
│
├── barcode-conveyor/
│   ├── README.md
│   ├── barcode_scanner.py
│   └── Node-Red Guide.docx
│
└── bhs-simulation/
    ├── README.md
    ├── generate_scenario.py
    ├── evaluator.py
    ├── solution.py
    ├── bsd_dashboard.py
    └── data/
        ├── network_layout.json
        └── simulation_scenario.json
```
## Useful Resources

- [IATA Baggage Standards](https://www.iata.org/en/programs/ops-infra/baggage/standards/) — Includes baggage-related Resolutions and Recommended Practices, including Resolution 753 on baggage tracking and Resolution 739 on baggage security control.
- [IATA Baggage Reference Manual (BRM)](https://www.iata.org/en/publications/manuals/baggage-reference-manual/) — The primary industry manual consolidating baggage operations guidance, best practices, and the baggage Resolutions/RPs used across airlines and ground handlers.
- [IATA Baggage Information eXchange (BIX)](https://www.iata.org/en/programs/ops-infra/baggage/baggage-information-exchange-bix/) — Relevant to the data exchange and interoperability side of baggage handling systems, especially where tracking and automation are involved.
- [IATA Technical Peripheral Specifications (ITPS)](https://www.iata.org/en/publications/manuals/iata-technical-peripheral-specifications/) — Covers standard device communications for baggage-related airport systems such as baggage tag printers, self-baggage drop, and common-use devices.
- [ICAO Publications](https://www.icao.int/publications) — Useful for locating ICAO standards and guidance material that shape how airports and aviation stakeholders operate secure, interoperable systems.
- [IABSC](https://www.iabsc.org/) — Industry association content focused on baggage handling technology, system design, operations, and real-world deployment challenges.
- [SITA](https://www.sita.aero/) — Useful for understanding how airlines and airports implement baggage tracking, digital operations, and end-to-end baggage visibility.
- [ACI World](https://aci.aero/) — Provides airport operations context for how baggage systems fit into larger terminal and passenger processing environments.
