# Baggage Handling System

![alt text](assets/smart_suite.png)

## Challenge Overview

Brock Solutions is a global engineering solutions and professional services company that designs, builds, and integrates large-scale automation software for transit, aviation, and industrial logistics. In any high-throughput sorting or material handling environment (such as an airport baggage handling system or a fulfillment center), multiple disciplines must converge: fast-moving mechanical transport, real-time control logic, edge sensor/vision tracking, and human-in-the-loop situational awareness dashboards.

In a real airport terminal, a baggage conveyor system is a dynamic, high-volume logistical network. Sorting thousands of bags per hour requires real-time adaptations to handle distruptions like mechanical conveyor jams, variable line speeds, routing bottlenecks, and shifting flight gates.

This challenge focuses on the workings of **Baggage Handling Systems (BHS)**. You will have the opportunity to learn about the challenges that BHS systems deal with and design a solution to address them. You can use the provided tools to develop your solution or create a completely independent solution that focuses on BHS.

---

## Industry Context

Modern industrial sortation networks are complex ecosystems responsible for moving thousands of assets per hour with zero tracking loss. To achieve this, automated systems rely on an integrated three-layer technology stack:

1. **The Physical/Sensing Layer:** Conveyor tracks, mechanical diverters, photo-eyes, laser arrays, and vision systems that transport items and capture physical operational data at high speeds.

2. **The Control Layer:** High-Level Control (HLC) brains that interpret sensor data in real time, evaluate routing choices, manage traffic density, and instantly actuate physical sorting hardware to steer items safely around system line blocks or mechanical jams.

3. **The Data & Visual Layer:** High-frequency data historians that capture continuous time-series event logs, paired with operator command-center dashboards that synthesize background telemetry into clear, actionable visual alerts and live performance metrics.

A failure or inefficiency in any single layer compromises the entire facility. This challenge provides you with the tools and environments to innovate anywhere across this stack.

---

## Potential Solutions

To jump-start your project, this repository contains some potential solutions and solution paths that you may use. You are free to modify, expand, strip down, or combine these resources as you see fit.

### 1: The SmartSort Digital Twin & Simulation Sandbox

Located in the [`bhs-simulation/`](/baggage-handling/bhs-simulation/) directory, this toolset provides a fully operational software-driven simulation environment modeling a complex 28-node airport baggage handling system across a multi-phase, 3,600-tick operational stress scenario. The environment simulates real-world complexities like dynamic conveyor line traffic congestion, unexpected mechanical breakdowns (jams), and strict delivery deadlines.

* **Provided Assets:**
    * `evaluator.py`: The master simulation engine that runs the physics, tracking, and fault-injection loops of the conveyor network.
    * `solution.py`: A functional, baseline graph-routing controller to guide baggage to destination gates.
    * `bsd_dashboard.py`: A native 2D desktop application that parses simulation logs to provide smooth, tick-by-tick animated operational playbacks and interactive time scrubbing.

* **Potential Projects:**
    * **Algorithmic Pathfinding Optimization:** Replace the baseline script with a more intelligent algorithm that monitors live network telemetry to actively guide inventory around active jams and high-traffic bottlenecks to maximize on-time delivery.
    * **Dashboard UI/UX & Analytical Overhaul:** Fork the pre-built visual dashboard or build an entirely new visual stack (using React, Dash, Pygame, etc.). Design a better dashboard that enhances operator visibility, tracks key performance indicators, predicts systemic wear-and-tear, or optimizes maintenance deployment.


### 2: The Physical Vision-Guided Conveyor Testbed

Located in the [`barcode-conveyor/`](/baggage-handling/barcode-conveyor/) directory, this setup offers a hands-on hardware integration experience leveraging a physical sorting platform. The workspace models an industrial inspection and routing lane using a single conveyor loop, an adjustable mechanical diverter mechanism, and an overhead camera sensor.

* **Provided Assets:**
    * An NVIDIA Jetson Nano edge computing platform connected directly to the camera and sorting actuators, capable of executing standalone Python scripts.
    * Baseline hardware interface access protocols, setup guides, and operational tutorials.

* **Potential Projects:**
    * **Computer Vision & Asset Tracking:** Develop real-time edge processing scripts on the Jetson Nano to capture video frames, isolate passing freight, and dynamically decode tracking barcodes or structural labels under varying operational speeds.
    * **Hardware-Software Coordination:** Implement precise state-tracking tracking arrays and timing loops to accurately synchronize the delay window between a camera scan event and the physical firing of the downstream diverter mechanism.
    * **Logistical Edge Networking:** Design an logging framework that cross-references scanned data against sorting manifests, tracks scanner reliability data, or pipes live field sensor events upstream to an analytical logger.


### Avenue 3: Completely Custom & Hybrid Systems

Your team is welcome to step entirely outside the provided templates:

* Build hybrid systems that bridge both environments (e.g., using physical input data streams from the conveyor hardware to drive or influence variables within the broader simulated network map).
* Integrate alternative software suites, automation platforms, or protocols (such as Node-RED flow architectures, MQTT messaging brokers, or predictive maintenance databases).
* Engineer a unique Industrial Internet of Things (IIoT), supply chain, or warehouse management prototype tailored around your own vision.   

---

## Workspace Directory Structure

The repository is organized into distinct project directories containing the baseline tools for your exploration:

```text
repository-root/
│
├── README.md                           # Overview (This Document)
│
├── bhs-simulation/                # Simulation & Dashboard Tools
│   ├── README.md                   # Simulation Engine & API Specifications
│   ├── generate_scenario.py                # Seeded Random Scenario Generator
│   ├── evaluator.py                    # Master Simulation Physics Loop
│   ├── solution.py                     # Baseline Routing Script
│   ├── bsd_dashboard.py                # 2D Desktop Playback Application
│   └── data/
│       ├── network_layout.json         # Network Geography Configuration
│       └── simulation_scenario.json    # 3,600-tick Wave and Jam Timeline
│
└── barcode-conveyor/              # Physical Conveyor Tools
    ├── README.md              # Hardware Tutorial and Setup Specifications
    ├── barcode_scanner.py              # Code used on Jetson Nano
    └── Node-Red Guide.docx              # Guide for Node-Red access and usage

```
## Evaluation

Because this challenge is open-ended, projects are evaluated on a case-by-case basis. Judges will use their professional discretion to evaluate how your team approaches the complexities of industrial systems engineering. 

Use these guiding principles to direct your design and innovation process:

### 1. Ideation & Value Proposition
* **Relevance & Reasonability:** How effectively does your concept address real-world industrial automation bottlenecks, and how sound is your engineering approach?
* **Stakeholder Impact:** Does your design offer clear operational advantages? Consider how your solution reduces system friction or assists baggage handlers, airport operators, and maintenance crews.

### 2. Technical Feasibility & System Reliability
* **Practicality & Factory Integration:** Can your software architecture or hardware integration scale smoothly if deployed in a real-world industrial or factory environment? 
* **Reliability & Downtime Mitigation:** How resilient is your system? Your solution should be robust against data anomalies, unexpected hardware faults (such as simulated conveyor jams or physical vision lighting issues), and maintain minimum downtime.
* **Operational ROI:** Does your solution provide a clear return on implementation? (e.g., a massive drop in misrouted assets, a significant increase in sorting speed, or high system efficiency relative to computational/hardware complexity).

### 3. Prototype Execution
* **Core Functionality:** At the time of judging, how functional is your prototype? Does your code run to completion, process input telemetry seamlessly, or actuate physical components successfully?

### 4. Demo, Pitch, & Technical Depth
* **Technical Explanation & Depth:** How thoroughly does your team understand the system you built? Be prepared to justify your algorithmic choices, state-tracking designs, data structures, or hardware wiring decisions.
* **Impact of the Demonstration:** How effectively does your demonstration show off what you accomplished? Use data visualizations, live metrics tracking, or a clear physical run to visibly prove your system's performance.