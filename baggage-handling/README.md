# Baggage Handling System

## Challenge Overview

Brock Solutions is a global engineering solutions and professional services company that develops solutions for many industries, including the airport industry. Brock Solutions provides an array of software solutions for airports known as the SmartSuite. The software packages contained in SmartSuite help with various parts of airport automation, with a heavy focus on Baggage Handling Systems (BHS). Below are the main solutions within SmartSuite that deal with Baggage Handling:

### SmartBag

SmartBag is the Baggage Reconciliation System (BRS) solution in SmartSuite. Its purpose is to track baggage and ensure that baggage is moving to the correct destination. The functionality of SmartBag is as follows: 

* **SmartBag Reconciliation**: Reconciles checked baggage with passengers to provide information about whether baggage can be loaded onto aircrafts. Tracks loading issues and provides baggage handlers with any information needed to locate and offload bags if needed.
* **SmartBag Recovery**: Reflights delayed baggage to be reconnected with passengers at their destinations as efficiently and cost-effectively as possible.
* **SmartBag Tracking**: Scans incoming or outgoing bags to view tracking information about them including inbound flight number, remaining time to connecting flight (with Hot Bag indication), and assigned gate for the bag’s outbound flight.
* **SmartBag Grouping**: Allows bags to be grouped with specific validation rules. Baggage handlers can track, validate, and perform bulk actions as defined on bags to ensure efficient movement and visibility on the ramp and throughout the airport. 
* **Other Functionality**: SmartBag contains multiple other functions that are not within the scope of this challenge, including weight management, notification systems, and agent services. 

### SmartDrop

SmartDrop is a bag drop efficiency solution within the SmartSuite. It provides airports with functionality to streamline the baggage acceptance process by allowing passengers to self-tag their bags at airport kiosks before dropping them off. There are three options for airports to choose from:

* **Agent Bag Drop**: Closest to traditional systems. Allows agents to quickly validate the bags, skipping the tagging step by letting passengers self-tag.
* **Mobile Bag Drop**: Similar to Agent Bag Drop, allows agents to use mobile devices for even quicker validation and acceptance.
* **Auto Bag Drop**: A Self-Service Bag Drop (SSBD) solution that allows passengers to drop their bags off without any agents required.

### SmartSort

SmartSort is the heart of the BHS solutions within SmartSuite. It is a sortation management and High-Level Control (HLC) system used to track bags and report all key performance indicators about them within the airport. This allows airports to identify, implement, and measure operational improvements within the BHS. SmartSort consists of the following sub-systems:

* **Sort Allocation Controller (SAC)**: The main sortation system. Controls conveyor system to transport baggage to their correct destinations. 
* **Data Historian System (DHS)**: Collects and stores time series data from the various sensors and components in the conveyor system. This data is used to monitor components for enhancing efficiency, predicting failures, and other data analysis processes.
* **Manual Encode Console (MEC)**: Allows operators or agents to manually enter bag information when automatic scanners cannot read it. 
* **Bag Status Display (BSD)**: Creates an interative 3D BHS map that shows all the bags moving through the conveyor system.
* **Web Client**: Integrates all sub-systems into a single web client for easy access.

---

# What You Are Building

You will create simplified equivalents of the three SmartSuite solutions outlined in the previous section. The level of detail and breadth is up to the group as long as the Core Requirements are met. 

For SmartBag and SmartSort, you will be given different cases to handle with your solution that will be handled by an evaluator file. SmartDrop will be evaluated by human judges for depth of functionality and user-friendly design.

---

# Core Requirements

The core requirements are separated by solution. The requirements represent the minimum requirements for the group. If time permits, groups can work on more than what is outlined.

### SmartBag

* Implement two (2) of the SmartBag functions
    * **Reconciliation**: You will be given a list of baggage information to be loaded into an aircraft and a list of loaded baggage. For the baggage to be loaded, create a script to check if they are authorized to be loaded onto the aircraft. For the baggage already loaded, create a script to check if all of the baggage is valid, and if not, generate text to send the baggage handler about the invalid baggage's location.
    * **Recovery**: You will be given a list of delayed baggage and flights leaving the airport. Connect baggage to flights in a way that minimizes the overall delay of baggage to their owners. 
    * **Grouping**: You will be given a list of baggage and their information. Create a GUI that visualizes the information associated with the baggage and allows a user to group properties of different baggage together. Evaluated by human judges based on visual design, features, user-friendly functions, etc.
* **SmartBag Tracking** will be integrated with **SmartDrop**. 

### SmartDrop

* There are three levels to this solution. Choose one (1) of these levels to build.
    * **Agent Bag Drop (Level 1)**: You will be given a list of baggage that is to be checked in. Create a self-tag system that checks if all information about the baggage is valid and creates a scannable barcode that encodes the baggage information in it.
    * **Mobile Bag Drop (Level 2)**: Complete level 1. Additionally, create a script that can scan your barcodes and parse the information encoded within. 
    * **Auto Bag Drop (Level 3)**: Complete level 2. Additionally, there is a physical conveyor system in the IDEAS Clinic that you can implement this system on. You will be given access to a platform to program the conveyors. Publish your barcodes to an MQTT broker (will be given) and use the Nvidia Jetson Nanos connected to the the conveyor to run a CV script to scan your barcodes. Based on if a valid barcode is scanned, either engage the diverter or stop the conveyor.

### SmartSort

* Implement one (1) of the SmartSort sub-systems
    * **SAC**: You will be given a conveyor map and list of baggage with their destinations. Create an algorithm to find the optimal path for a piece of baggage to reach its destination. There will be additional rules for paths that must be taken into account.
    * **DHS**: You will be given a sample stream of data from a simplified conveyor system. It will contain information about conveyor failures and number of baggage processed at various junctions. Visualize the data stream into graphs and propose changes to the current system to improve efficiency.
    * **MEC**: Extension for SmartDrop. In real world scenarios, barcodes can be hidden or inaccessible for scanners. Implement a system for an operator to manually enter baggage information in such cases.
    * **BSD**: You will be given a list of time-series information about bags and their current positions. Create a tool to visualize the conveyor system and the status of the bags on it. 


There is variable degree of difficulty to these challenges. Some of the challenges relate to others. Choose a set that you think your group can complete within time. 

---

# Starter Files

---

# Suggested Solution Approaches

There is no unique solution for any of the problems. As long as the Core Requirements are met, feel free to choose any approach. 

---

# Recommended Roadmap

---

# Evaluation

Solutions may be evaluated by evaluator scripts or human judges.  

## Scored Metrics

---

# Deliverables

---
