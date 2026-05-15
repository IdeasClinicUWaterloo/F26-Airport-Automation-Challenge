"""
TEST SOLUTION FILE
assigns flight to first available gate regardless of compatibility (for testing purposes only)
"""

HOME = "YYZ"
INTERNATIONAL_DESTINATIONS = ["LHR", "CDG", "FRA", "NRT", "DXB"]

def decide(observation):
    assignments = []
    reassignments = []
    
    waiting_flights = observation["waiting_flights"]
    gates = observation["gates"]
    gate_assignments = observation.get("gate_assignments", {})
    aircraft_info = observation["ac_info"]
    
    for flight_id, flight in waiting_flights.items():
        legs = flight["legs"]
        aircraft_type = legs[0]["aircraftType"]
        wingspan = aircraft_info[aircraft_type]["wingspan"]
        jetbridge_required = aircraft_info[aircraft_type]["jetbridge_required"]
        
        # Determine if flight is international
        is_international = any(
            leg["arrivalStation"] in INTERNATIONAL_DESTINATIONS or 
            leg["departureStation"] in INTERNATIONAL_DESTINATIONS 
            for leg in legs
        )
        
        for gate_id, gate in gates.items():
            assignments.append((flight_id, gate_id))
            break   

        else:
            print(f"ERROR: No Compatible Gates found for {flight_id}")

    return {"assignments": assignments, "reassignments": reassignments}