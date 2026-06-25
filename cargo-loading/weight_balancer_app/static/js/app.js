// Initial seed manifest cargo inventory database
let cargoDatabase = [
    {"id": "CRG-001", "weight": 2800, "desc": "Heavy Machinery Parts"},
    {"id": "CRG-002", "weight": 2400, "desc": "Industrial Valves"},
    {"id": "CRG-011", "weight": 4000, "desc": "Generator Unit (Overload)"}, 
    {"id": "CRG-012", "weight": 3500, "desc": "Steel Piping (Overload)"},  
    {"id": "CRG-003", "weight": 1800, "desc": "E-Commerce Pallet A"},
    {"id": "CRG-004", "weight": 1500, "desc": "E-Commerce Pallet B"},
    {"id": "CRG-005", "weight": 1100, "desc": "Perishable Foods"},
    {"id": "CRG-006", "weight": 950,  "desc": "Medical Equipment"},
    {"id": "CRG-007", "weight": 800,  "desc": "Aircraft Spare Parts"},
    {"id": "CRG-008", "weight": 550,  "desc": "Mail Sacks"},
    {"id": "CRG-009", "weight": 400,  "desc": "Diplomatic Cargo"},
    {"id": "CRG-010", "weight": 200,  "desc": "Lithium Batteries"},
];

function renderCargoTable() {
    const tbody = document.getElementById('cargoTableBody');
    tbody.innerHTML = '';
    cargoDatabase.forEach((item, index) => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td><strong>${item.id}</strong></td>
            <td>${parseInt(item.weight).toLocaleString()} lbs</td>
            <td><small>${item.desc}</small></td>
            <td><button class="btn-danger" style="padding: 0.2rem 0.4rem; font-size: 0.75rem;" onclick="deleteCargoItem(${index})">Delete</button></td>
        `;
        tbody.appendChild(row);
    });
}

function addCargoItem() {
    const id = document.getElementById('newId').value.trim();
    const weight = parseInt(document.getElementById('newWeight').value);
    const desc = document.getElementById('newDesc').value.trim();
    
    if(!id || isNaN(weight) || !desc) {
        alert("Please ensure all entry input fields contain valid metrics.");
        return;
    }
    cargoDatabase.push({id, weight, desc});
    renderCargoTable();
    
    document.getElementById('newId').value = '';
    document.getElementById('newWeight').value = '';
    document.getElementById('newDesc').value = '';
}

function deleteCargoItem(index) {
    cargoDatabase.splice(index, 1);
    renderCargoTable();
}

async function runBackendOptimization() {
    // Collect variables from UI
    const aircraft_params = {
        oew: parseFloat(document.getElementById('oew').value),
        oew_arm: parseFloat(document.getElementById('oew_arm').value),
        max_zfw: parseFloat(document.getElementById('max_zfw').value),
        target_cg: parseFloat(document.getElementById('target_cg').value),
        bays: {
            FWD_HOLD: {
                arm: parseFloat(document.getElementById('fwd_arm').value),
                max_weight: parseFloat(document.getElementById('fwd_max').value)
            },
            AFT_HOLD: {
                arm: parseFloat(document.getElementById('aft_arm').value),
                max_weight: parseFloat(document.getElementById('aft_max').value)
            }
        }
    };

    const statusBox = document.getElementById('mStatusBox');
    const statusVal = document.getElementById('mStatus');
    statusVal.innerText = "Computing...";
    statusBox.className = "metric-box";

    try {
        const response = await fetch('/api/optimize', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ cargo_database: cargoDatabase, aircraft_params: aircraft_params })
        });

        if (!response.ok) throw new Error("Server communication fault event.");
        const plan = await response.json();

        // Check if solver found optimal bounds
        if (plan.status !== "Optimal") {
            statusVal.innerText = plan.status;
            statusBox.className = "metric-box status-infeasible";
            alert("Solver could not reach an optimal WAB solution matching structural requirements.");
            return;
        }

        // Render validation text fields
        statusVal.innerText = "Optimal";
        statusBox.className = "metric-box status-optimal";
        document.getElementById('mWeight').innerText = `${plan.metrics.total_weight.toLocaleString()} lbs`;
        document.getElementById('mCG').innerText = `${plan.metrics.final_cg.toFixed(2)}"`;
        document.getElementById('mDev').innerText = `${plan.metrics.deviation_inches.toFixed(4)}"`;

        // Clear layout maps
        const manifestFwd = document.getElementById('manifestFwd');
        const manifestAft = document.getElementById('manifestAft');
        const unassignedContainer = document.getElementById('unassignedContainer');

        manifestFwd.innerHTML = '';
        manifestAft.innerHTML = '';
        unassignedContainer.innerHTML = '';

        // Style the hold visual boxes depending on output state weights
        const fwdBox = document.getElementById('visualFwdHold');
        const aftBox = document.getElementById('visualAftHold');
        
        if (plan.bay_totals.FWD_HOLD.weight > 0) fwdBox.classList.add('active-load'); else fwdBox.classList.remove('active-load');
        if (plan.bay_totals.AFT_HOLD.weight > 0) aftBox.classList.add('active-load'); else aftBox.classList.remove('active-load');

        // Populate Forward items
        plan.assignments.FWD_HOLD.forEach(item => {
            const el = document.createElement('div'); el.className = 'bay-tag';
            el.innerHTML = `<span>${item.id}</span><strong>${item.weight} lb</strong>`;
            manifestFwd.appendChild(el);
        });

        // Populate Aft items
        plan.assignments.AFT_HOLD.forEach(item => {
            const el = document.createElement('div'); el.className = 'bay-tag';
            el.innerHTML = `<span>${item.id}</span><strong>${item.weight} lb</strong>`;
            manifestAft.appendChild(el);
        });

        // Populate left behind item array array lists
        if (plan.unassigned.length === 0) {
            unassignedContainer.innerHTML = '<p class="placeholder-text" style="color:var(--success); font-style:normal; font-weight:600;">✓ All inventory items successfully containerized.</p>';
        } else {
            plan.unassigned.forEach(item => {
                const el = document.createElement('div'); el.className = 'unassigned-item';
                el.innerText = `${item.id}: ${item.weight} lbs`;
                unassignedContainer.appendChild(el);
            });
        }

        // Assign status metric readings
        document.getElementById('statsFwd').innerText = `${plan.bay_totals.FWD_HOLD.weight.toLocaleString()} / ${aircraft_params.bays.FWD_HOLD.max_weight.toLocaleString()} lbs`;
        document.getElementById('statsAft').innerText = `${plan.bay_totals.AFT_HOLD.weight.toLocaleString()} / ${aircraft_params.bays.AFT_HOLD.max_weight.toLocaleString()} lbs`;

        // Render graphical physical CG vector crosshair placement along fuselage bounding map
        const cgMarker = document.getElementById('cgMarkerVisual');
        cgMarker.style.display = 'block';
        
        const minArm = aircraft_params.bays.FWD_HOLD.arm - 50; 
        const maxArm = aircraft_params.bays.AFT_HOLD.arm + 50;
        const scalePct = ((plan.metrics.final_cg - minArm) / (maxArm - minArm)) * 100;
        cgMarker.style.left = `${Math.min(Math.max(scalePct, 5), 95)}%`;

    } catch (err) {
        console.error(err);
        statusVal.innerText = "Error";
        statusBox.className = "metric-box status-infeasible";
    }
}

// Global initialization window hook
window.onload = () => {
    renderCargoTable();
    runBackendOptimization();
};
