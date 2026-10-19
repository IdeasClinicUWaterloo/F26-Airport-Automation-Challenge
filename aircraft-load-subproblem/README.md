# Aircraft Load Subproblem
## Table of Contents

- [The Problem](#the-problem)
- [The Challenge](#the-challenge)
- [Potential Solutions](#potential-solutions)
- [Resources](#resources)

## The Problem
A mechanical issue causes the airline to replace the originally scheduled aircraft with a smaller aircraft shortly before departure. The new aircraft has different seating, baggage capacity and weight-and-balance limits. 

Passengers have already checked in, seats have been assigned, and baggage is being prepared for loading. Because the new aircraft has less capacity and different loading constraints, the existing passenger and baggage plan can no longer be used directly. Staff must quickly assess how the existing passenger seating arrangement affects the new aircraft's weight and balance, while determining how to adjust baggage and cargo loading to meet the new constraints. Any necessary passenger reseating or boarding decisions are handled separately by the airline.

## The Challenge
Your challenge is to develop a solution that quickly evaluates the passenger and baggage load for the replacement aircraft, optimizes baggage and cargo distribution, and maintains safe weight-and-balance limits while minimizing operational disruption.  

To do this, you can either create your own solution or build off and improve the existing aircraft load control program. 

## Potential Solutions

A possible scope below. You can extend one or build something else entirely.

| Potential solution | Description | Starting point |
| --- | --- | --- |
| Aircraft load control | Assign passenger and cargo load to aircraft zones while respecting weight and balance limits. | [`load-control/`](load-control/) |
| Aircraft-swap replanning tool | Reassign passengers, seats, baggage, and cargo after an aircraft change. | 
| Weight-and-balance dashboard | Show aircraft loading, zone weights, limits, and potential violations. |
| Load-plan optimization tool | Find a safe loading arrangement while minimizing passenger or baggage disruptions. |

## Resources

### Industry Solutions

- [Brock Solutions SmartLoad](https://www.brocksolutions.com/smartload/): A real-world cargo management solution that tracks aircraft loading and validates loads against weight-and-balance plans.
- [JetBlue SmartLoad Case Study](https://www.brocksolutions.com/jetblue-is-loading-their-aircrafts-smarter-with-help-from-brock-solutions-and-smartload/): An example of how an airline uses automated loading verification and real-time weight-and-balance information.

### Technical References

- [SKYbrary – Loading Aircraft with Cargo](https://skybrary.aero/articles/loading-aircraft-cargo): Background information on aircraft cargo loading and operational safety.
- [FAA – Weight and Balance Handbook](https://www.faa.gov/sites/faa.gov/files/2023-09/Weight_Balance_Handbook.pdf): Explains aircraft weight limits, centre of gravity, and safe loading calculations.
- [FAA – Aircraft Weight and Balance Control](https://www.faa.gov/regulations_policies/advisory_circulars/index.cfm/go/document.information/documentID/1035868?pubDate=20260114): Guidance on aircraft weight-and-balance control programs.
- [FAA – Pilot's Handbook, Chapter 10: Weight and Balance](https://www.faa.gov/regulationspolicies/handbooksmanuals/aviation/phak/chapter-10-weight-and-balance): An introductory explanation of aircraft loading, weight distribution, and balance.

