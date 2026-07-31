# Baggage Handling System

Brock Solutions is a global engineering solutions and professional services company that designs, builds, and integrates large-scale automation software for transit, aviation, and industrial logistics. In any high-throughput sorting or material handling environment, multiple disciplines must converge: fast-moving mechanical transport, real-time control logic, edge sensing and vision, and human-in-the-loop situational awareness dashboards.

In a real airport terminal, a baggage handling system (BHS) is a dynamic, high-volume logistical network. Sorting thousands of bags per hour requires coordinated control across an integrated three-layer technology stack:
- **Physical/Sensing Layer:** Conveyors, diverters, photo-eyes, and vision systems capturing physical operational data at high speeds.
- **Control Layer:** High-Level Control (HLC) brains evaluating routing choices, managing traffic density, and actuating physical sorting hardware.
- **Data & Visual Layer:** High-frequency data historians capturing continuous time-series event logs paired with operator command-center dashboards.

---

## Table of Contents

- [Challenge](#challenge)
- [Potential Solutions](#potential-solutions)
  - [Supported Solution Paths](#supported-solution-paths)
  - [Optional Independent Paths](#optional-independent-paths)
- [Resources](#resources)

---

## Challenge

Your goal is to develop solutions that address baggage tracking, visual verification, conveyor automation, network pathfinding, and operational visibility in industrial logistics environments.

Teams are encouraged to explore solutions such as:

- Software applications (e.g., visual verification workflows, checkpoint capture tools, operator dashboards)
- Hardware prototypes (e.g., camera-driven barcode capture setups, conveyor timing and diverter control loops)
- Data analysis approaches (e.g., time-series event log telemetry, tracking data historians)
- Optimization methods (e.g., network pathfinding algorithms to reroute bags around congestion or component failures)
- Research-based solutions (e.g., hardware-in-the-loop sensor integration, standardized airport data exchange strategies)

---

## Potential Solutions

The ideas below are examples to help teams explore possible directions. They are not the only possible solutions.

Teams are encouraged to combine ideas, explore new approaches, and develop creative solutions.

### Supported Solution Paths

| Potential Solution | Description | Resources |
| ------------------ | ----------- | --------- |
| **SecureBag (Visual Verification Workflow)** | Focuses on visual bag verification workflows to confirm that bags presented at checkpoints match checked-in records. Ideas include adding weight-based verification, improving checkpoint scanning automation, and building alert dashboards. | [SecureBag Workspace](securebag/) |
| **Barcode Conveyor (Physical Hardware & Edge)** | Focuses on physical hardware and edge-computing setups centered on camera-driven barcode tracking, diverter actuation timing, and real-time scanner/routing logging. | [Barcode Conveyor Workspace](barcode-conveyor/) |

### Optional Independent Paths

| Potential Solution | Description | Resources |
| ------------------ | ----------- | --------- |
| **BHS Simulation (Network & Algorithmic Optimization)** | A software-focused simulation environment for exploring intelligent network pathfinding around congestion and failures, flow control optimization, and dashboard analytics. | [BHS Simulation Workspace](bhs-simulation/) |
| **Custom or Hybrid Systems** | A custom approach stepping outside provided templates to combine live hardware inputs, simulation logic, and unique operational dashboarding. | Look through any workspaces or online resources. |

---

## Resources

The following resources may help teams better understand the problem and develop solutions.

### Background Information

- **IATA Baggage Standards:** [Resolutions & Recommended Practices (e.g., Resolution 753 on tracking and Resolution 739 on security control)](https://www.iata.org/en/programs/ops-infra/baggage/standards/)
- **IATA Baggage Reference Manual (BRM):** [Consolidated industry operational guidelines and best practices](https://www.iata.org/en/publications/manuals/baggage-reference-manual/)
- **ACI World:** [Airport Operations & Terminal Processing Context](https://aci.aero/)
- **ICAO Publications:** [Global Standards for Secure & Interoperable Aviation Systems](https://www.icao.int/publications)

### Technical Resources

- **IATA Technical Peripheral Specifications (ITPS):** [Standard Device Communications for Printers, Self-Bag Drop, and Hardware](https://www.iata.org/en/publications/manuals/iata-technical-peripheral-specifications/)
- **IATA Baggage Information eXchange (BIX):** [Data Exchange & Interoperability Standards for Tracking](https://www.iata.org/en/programs/ops-infra/baggage/baggage-information-exchange-bix/)
- **Node-RED Guide:** [Node-RED Integration Guide](barcode-conveyor/Node-Red%20Guide.docx)
- **Barcode Recognition Script:** [Python Camera Barcode Tracking Script](barcode-conveyor/barcode_scanner.py)

### Data Sources

- **SecureBag Verification Dataset:** Sample images and bag metadata in [`securebag/sample_img/`](securebag/sample_img/) and [`securebag/bags.json`](securebag/bags.json)
- **BHS Simulation Scenarios:** Topology and scenario datasets in [`bhs-simulation/data/network_layout.json`](bhs-simulation/data/network_layout.json) and [`simulation_scenario.json`](bhs-simulation/data/simulation_scenario.json)

### Additional References

- **IABSC:** [International Association of Baggage System Companies (BHS technology and deployment)](https://www.iabsc.org/)
- **SITA Airport Solutions:** [Insights on End-to-End Baggage Tracking & Digital Operations](https://www.sita.aero/)
- **Brock Solutions:** [Industrial Logistics & Automation Integration Overview](https://www.brocksolutions.com/)