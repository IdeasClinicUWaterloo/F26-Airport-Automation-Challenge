# Baggage Handling System

![alt text](assets/smart_suite.png)

## Challenge Overview

Brock Solutions is a global engineering solutions and professional services company that develops automation software for various industries, including the airport industry. Brock Solutions provides an array of software packages known as the **SmartSuite** to streamline airport operations. One of the solutions within SmartSuite is **SmartSort**, a high-level control (HLC) and sortation management system used to route baggage, track system telemetry, and report operational key performance indicators (KPIs).

In a real airport terminal, a baggage conveyor system is a dynamic, high-volume logistical network. Sorting thousands of bags per hour requires real-time adaptations to handle distruptions like mechanical conveyor jams, variable line speeds, routing bottlenecks, and shifting flight gates.

This challenge aims to capture the architecture of a modern Baggage Handling System (BHS). You will build a simplified equivalent of the SmartSort platform, integrating real features that are available in the software used by many international airports.

---

## Industry Context

### High-Level Control and Telemetry in Airport Logistics

Modern airport baggage systems are highly complex behind the scenes. Bags are tracked via barcodes or RFID tags as they pass physical laser arrays and diverters along long stretches of interconnected conveyor belts. Controlling this hardware requires software that can process real-time events, calculate optimal travel paths instantly, and isolate mechanical failures before they cause gridlock across the entire terminal.

In an enterprise environment, this data pipeline is split into distinctive layers that communicate with one another:

* **The Routing Layer** executes the automation logic, directing physical diverters to send bags down specific paths.
* **The Data Historian Layer** collects high-frequency sensor telemetry to predict component failures and evaluate system efficiency.
* **The Visualization Layer** translates raw data into a unified command center interface, allowing terminal operators to spot bottlenecks and deploy maintenance teams instantly.

### Real Software Solutions

Brock Solutions' **SmartSort** platform coordinates these tasks simultaneously by breaking the architecture into specialized subsystems:

* **Sort Allocation Controller (SAC)**: The "brain" that calculates paths and manages conveyor routing.
* **Data Historian System (DHS)**: The system that processes time-series logs and tracks physical performance.
* **Bag Status Display (BSD)**: The visual user interface that maps the state of the network into a scannable operational view.

---

## What You Are Building

You will build a simulation-driven baggage sortation and monitoring application. Your system must read a live stream of airport operational data and execute real-time routing decisions while feeding an analytics pipeline and user interface.

Your solution will implement simplified versions of three core SmartSort components:

1. **The SAC (Backend)**: A dynamic pathfinding script that routes baggage through a conveyor network graph.
2. **The DHS (Analytics)**: A data processing utility that captures telemetry logs from the simulation loop to calculate real-time system performance metrics.
3. **The BSD (Frontend)**: A 2D graphical user interface that visualizes the conveyor grid, actively tracks moving baggage, and plots operational KPIs.

---

## Core Simulation Mechanics

To accurately evaluate your software without the limitations of real-world "wall-clock" time, this challenge utilizes a **Discrete Tick-Based Simulation Framework**.

Time in the simulator progresses in discrete iterations called **ticks** (where 1 simulation tick represents 1 second of operational airport time). The evaluator manages the physics of the environment and communicates with your software via reactive API calls at every tick.

---

### Conveyor Network Geography

The airport conveyor layout is provided as a directed graph consisting of **Nodes** (intake points, routing junctions, and destination gates) and **Edges** (the physical conveyor belts connecting them). Every conveyor belt has a designated **Base Travel Cost** measured in ticks, representing the physical length of the belt.

### Dynamic Events

To mirror real airport conveyor systems, dynamic events will occur randomly or based on the route allocation for pieces of baggage. The shortest path may not always be the quickest path, and your algorithm must be able to reroute baggage based on real time faults or junction closures.

---

## Starter Files

Apart from inputs from the evaluator, there will be additional files to provide a starting point for some of the Core Requirements.

* `historical_data.csv`: Provides a full log of a previous day's operation. Analyze this data to find patterns which can be used to further optimize your pathfinding algorithm.
* `bsd_starter.py`: Provides a boilerplate map of the conveyor system that you can add BSD features to.

---

## Core Requirements

### 1. Sort Allocation Controller (SAC)

* Implement a dynamic pathfinding algorithm that maps a bag's route from its intake node to its assigned flight gate.
* Routing decisions must be evaluated at every junction; a pre-calculated path from the start may not reach the destination if there are jams

### 2. Data Historian System (DHS)

* Aggregate and compute operational metrics over time, including:
    * **Conveyor Utilization**: Identifying the most heavily congested belts and junctions.
    * **System Misroute Rate**: Tracking bags that missed their flight windows due to delays or pathfinding inefficiencies.
    * **Mean Transit Time**: Calculating the average duration a bag takes to reach its gate from intake.
* Use the historical CSV to map out inherent structural flaws in the airport network before the simulation begins.
* Optionally, process live telemetry to dynamically route bags for further optimization.

### 3. Bag Status Display (BSD)

* Use the provided conveyor map to add BSD functionality.
* Highlight operational nodes, destination gates, and active jam points.
* Render real-time positions or numbers of bags moving along the network edges.
* Integrate a dedicated analytics panel that pulls from your DHS layer to display updating line graphs or charts of system KPIs.

---

## Inputs and Expected Outputs

### Inputs

The evaluator will supply your application with the following data sources:

* `network_layout.json`: Defines the conveyor graph structure, including node IDs, edge connections, base travel costs, and target gate locations.
* `simulation_scenario.json`: A time-step schedule defining the events that occur at each tick (baggage loading, jams, etc.).

### Expected Outputs

At the end of the simulation execution, your system must export:

* A standardized tracking log file recording the exact tick history of every bag's path through the network.
* An analytics report summarizing the final system-wide metrics calculated by your DHS module.
* A running instance of the BSD graphical dashboard during evaluation.

---

## Evaluation and Scoring

Your submission will be scored through automated code evaluation combined with a human review of your user interface.

### Hard Failures

The following events will result in severe point deductions or simulation failure:

* **Invalid Routing**: Sending a bag to a node or gate not connected to its current position via a valid edge.
* **Deadlocks**: Allowing a bag to remain trapped on an active loop indefinitely due to recursive pathfinding logic.
* **Script Crashes**: Unhandled exceptions occurring when a sudden conveyor jam is introduced by the evaluator.

### Scored Metrics

Solutions will be graded based on these performance criteria:

* **Total Misrouted Bags**: The count of bags that arrived at their gate after their designated flight departure tick.
* **Network Efficiency**: The cumulative travel time across all baggage items; lower total scores higher.
* **Dashboard Usability (BSD)**: Evaluated by human judges based on design clarity, visual layout of the conveyor topology, scannability of alerts, and the effectiveness of KPI visualizations.