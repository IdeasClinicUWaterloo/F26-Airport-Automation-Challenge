from flask import Flask, render_template, request, jsonify
import pulp

app = Flask(__name__)

def solve_cargo_loading_plan(cargo_database, aircraft_params, unassigned_penalty_factor=1000.0):
    """
    Solves for optimal cargo distribution to meet WAB using MILP (PuLP)
    """
    # Initialize optimization problem
    prob = pulp.LpProblem("Aircraft_Cargo_WAB", pulp.LpMinimize)

    # Get structural limits
    bays = aircraft_params['bays']
    oew = float(aircraft_params['oew'])
    oew_arm = float(aircraft_params['oew_arm'])
    max_zfw = float(aircraft_params['max_zfw'])
    target_cg = float(aircraft_params['target_cg'])

    num_items = len(cargo_database)
    bay_ids = list(bays.keys())

    if num_items == 0:
        return {
            'status': 'Optimal',
            'assignments': {j: [] for j in bay_ids},
            'bay_totals': {j: {'weight': 0, 'items': 0} for j in bay_ids},
            'unassigned': [],
            'metrics': {
                'total_weight': oew,
                'final_cg': oew_arm,
                'target_cg': target_cg,
                'deviation_inches': abs(oew_arm - target_cg)
            }
        }

    # Decision variables
    z = pulp.LpVariable.dicts("assign", ((i, j) for i in range(num_items) for j in bay_ids), cat='Binary')

    # Continuous variables for absolute deviation from target moment
    dev_pos = pulp.LpVariable("Moment_Dev_Pos", lowBound=0, cat='Continuous')
    dev_neg = pulp.LpVariable("Moment_Dev_Neg", lowBound=0, cat='Continuous')

    # Objective Function
    unassigned_weight_penalty = pulp.lpSum(
        (1 - pulp.lpSum(z[i, j] for j in bay_ids)) * float(cargo_database[i]['weight']) * unassigned_penalty_factor
        for i in range(num_items)
    )
    prob += dev_pos + dev_neg + unassigned_weight_penalty, "Minimize_CG_Deviation_and_Unassigned_Cargo"

    # CONSTRAINT A: Max one bay per cargo item
    for i in range(num_items):
        prob += pulp.lpSum(z[i, j] for j in bay_ids) <= 1, f"Max_One_Bay_Item_{i}"

    # CONSTRAINT B: Compartment weight limits
    for j in bay_ids:
        prob += pulp.lpSum(z[i, j] * float(cargo_database[i]['weight']) for i in range(num_items)) <= float(bays[j]['max_weight']), f"Weight_Cap_Bay_{j}"

    # CONSTRAINT C: Max Zero Fuel Weight
    total_cargo_weight = pulp.lpSum(z[i, j] * float(cargo_database[i]['weight']) for i in range(num_items) for j in bay_ids)
    prob += (oew + total_cargo_weight) <= max_zfw, "Max_Zero_Fuel_Weight"

    # CONSTRAINT D: Linearized absolute value calculation for CG deviation
    # FIX: Moment = Weight * Arm (Multiplication corrected from original addition bug)
    oew_moment = oew * oew_arm 
    cargo_moment = pulp.lpSum(z[i, j] * float(cargo_database[i]['weight']) * float(bays[j]['arm']) for i in range(num_items) for j in bay_ids)
    
    total_weight = oew + total_cargo_weight
    total_moment = oew_moment + cargo_moment

    prob += total_moment - (total_weight * target_cg) == dev_pos - dev_neg, "Linearized_CG_Deviation"

    # Solve optimization problem cleanly
    solver = pulp.PULP_CBC_CMD(msg=False)
    status = prob.solve(solver)

    results = {
        'status': pulp.LpStatus[status],
        'assignments': {j: [] for j in bay_ids},
        'bay_totals': {j: {'weight': 0, 'items': 0} for j in bay_ids},
        'unassigned': []
    }

    if pulp.LpStatus[status] == "Optimal":
        for i in range(num_items):
            assigned = False
            for j in bay_ids:
                if pulp.value(z[i, j]) == 1:
                    results['assignments'][j].append(cargo_database[i])
                    results['bay_totals'][j]['weight'] += int(cargo_database[i]['weight'])
                    results['bay_totals'][j]['items'] += 1
                    assigned = True
                    break
            if not assigned:
                results['unassigned'].append(cargo_database[i])

        final_cargo_weight = sum(results['bay_totals'][j]['weight'] for j in bay_ids)
        final_cargo_moment = sum(results['bay_totals'][j]['weight'] * float(bays[j]['arm']) for j in bay_ids)
        
        actual_total_weight = oew + final_cargo_weight
        actual_final_cg = (oew_moment + final_cargo_moment) / actual_total_weight if actual_total_weight > 0 else 0

        results['metrics'] = {
            'total_weight': actual_total_weight,
            'final_cg': actual_final_cg,
            'target_cg': target_cg,
            'deviation_inches': abs(actual_final_cg - target_cg)
        }
    
    return results

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/optimize', methods=['POST'])
def optimize():
    data = request.json
    cargo_database = data.get('cargo_database', [])
    aircraft_params = data.get('aircraft_params', {})
    
    result = solve_cargo_loading_plan(cargo_database, aircraft_params)
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
