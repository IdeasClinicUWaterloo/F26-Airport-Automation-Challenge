# Baggage Sortation and Analytics System

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

This challenge presents a simplified version of this industrial architecture.

### Real Software Solutions

Brock Solutions' **SmartSort** platform coordinates these tasks simultaneously by breaking the architecture into specialized subsystems:

* **Sort Allocation Controller (SAC)**: The "brain" that calculates paths and manages conveyor routing.
* **Data Historian System (DHS)**: The system that processes time-series logs and tracks physical performance.
* **Bag Status Display (BSD)**: The visual user interface that maps the state of the network into a scannable operational view.

---

## What You Are Building

You will build a simulation-driven baggage sortation and monitoring application. Your system must read a live stream of airport operational data and execute real-time routing decisions while feeding an analytics pipeline and user interface.

Your solution will implement simplified versions of three core SmartSort components:

1. **The SAC (Backend)**: The algorithmic core of your system. This component handles real-time pathfinding decisions for baggage at choice points across the network, adjusting routes based on line congestion and active system faults.
2. **The DHS (Analytics)**: A tracking tool that captures continuous event streams from the simulation loop. It aggregates time-series data to compute system latency, track mechanical error statistics, and establish systemic performance baselines.
3. **The BSD (Frontend)**: A 2D graphical user interface that visualizes the conveyor grid, actively tracks moving baggage, and plots operational KPIs.

---

## Core Simulation Mechanics

To evaluate your software fairly and reliably, this challenge utilizes a **Time-Step (Tick-Based) Simulation Framework**.

Time in the simulator progresses in uniform steps called ticks (where 1 simulation tick represents 1 second of airport operational time). Your software does not manage the main execution loop; the evaluator runs the physics of the environment and triggers reactive API calls to your code when an item requires a routing decision.

---

### Conveyor Network Geography

The airport infrastructure is represented as a directed graph composed of Nodes and Edges:

* Nodes act as fixed structural milestones, categorized as Intake Ports (where baggage enters the system), Junctions (routing intersections), Spines (high-speed transit trunks), and Gates (terminal flight destinations).

* Edges represent physical, directed conveyor belts connecting the nodes. Every edge carries a structural Base Travel Cost measured in ticks, representing the length of the belt.

### Dynamic Events

Various dynamic effects will occur throughout the simulation that can affect your routing times:

* Conveyor belts do not have fixed speeds; their transit times fluctuate depending on how crowded they are. The travel time required for a bag to cross an edge scales dynamically based on the volume of active baggage currently occupying that specific conveyor line. Your routing logic must account for these fluid weights, as a physically direct route may become slower than a clear outer detour path during peak traffic.
* The evaluator simulates real-world hardware disruptions. Conveyor lines can experience mechanical breakdowns, transitioning to a JAMMED state. When a line is jammed, any baggage currently on that edge freezes in place, and its traversal countdown halts. Your routing logic must detect active faults across the network and dynamically guide incoming bags around broken infrastructure.
* Conveyor belts degrade over time based on the cumulative volume of freight they process. Exceeding a line's operational usage threshold will trigger automated mechanical overloads, causing unexpected structural breakdowns that temporarily halt the line.

---

## Technical Specifications

Your team must write a unified Python program. The evaluator will look for a file named `solution.py` containing an implementation of your routing module.

### 1. Sort Allocation Controller (SAC) API Requirement

Your `solution.py` file must expose the following entry-point function signature exactly:

```python
def route_bag(bag_id, current_node, destination_gate, active_faults, edge_occupancy):
    """
    Executes real-time routing decisions for a single baggage item reaching a junction.
    
    Parameters:
    -----------
    bag_id : str
        The unique identification string of the baggage item (e.g., 'B0014')
    current_node : str
        The ID of the node junction the bag has just reached (e.g., 'JA3')
    destination_gate : str
        The target gate where the bag must be delivered (e.g., 'GA2')
    active_faults : list of str
        A list of specific edge IDs currently experiencing active jams (e.g., ['e_JA2_S2'])
    edge_occupancy : dict
        A map of edge IDs to integers representing the exact count of active bags on that belt
        
    Returns:
    --------
    str
        The node ID of the next consecutive junction or gate to steer the bag toward.
    """
    # Your pathfinding and optimization logic here
    return next_node_id

```

### 2. Data Historian System (DHS) Specifications

Your analytics module must process the continuous time-series logging stream produced by the evaluator (`live_telemetry.csv`). It must aggregate this historical data to calculate and export the following metrics:

* **Conveyor Utilization Rates**: Historical tracking of structural bottlenecks, identifying lines consistently experiencing peak volume.
* **System Misroute Statistics**: The count of high-priority priority bags that failed to reach their target gate prior to their assigned flight deadlines.
* **Mean Transit Efficiency**: The average tick duration required for completed baggage items to navigate from an intake point to a destination gate.

You may also process the telemetry data to optimize your pathfinding algorithm.

## Baseline Data

The system evaluator reads its parameters from your project's `data/` directory:

* `network_layout.json`: Contains the layout definitions of the terminal infrastructure, mapping node classes, edge connections, base travel costs, and structural wear thresholds.
* `simulation_scenario.json`: Outlines a complex 3,600-tick (1 hour) operational schedule. This file dictates exactly when specific bags spawn, their designated target gates, optional strict flight arrival deadlines, and a timeline of scheduled terminal maintenance jams.

---

## Evaluation and Scoring

Your submission will be scored through automated code evaluation.

### Hard Failures

The following events will result in severe point deductions or simulation failure:

* **Invalid Routing**: Sending a bag to a node or gate not connected to its current position via a valid edge.
* **Uncaught Exceptions**: Unhandled logic crashes occurring when the simulator introduces an unexpected or unannounced mechanical fault event.
* **Illegal Teleportation**: Returning node skips or attempting to bypass the time-step increments of intermediate conveyor tracks.

### Scored Metrics

Solutions will be scored based on these performance criteria:

* **Total Misrouted Bags**: The count of bags that arrived at their gate after their designated flight departure tick.
* **Mean Transit Latency**: The average travel time across all successfully delivered inventory.
