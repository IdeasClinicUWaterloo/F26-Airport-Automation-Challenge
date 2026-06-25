from flask import Flask, request, jsonify, render_template_string, send_file
import base64, json, requests, uuid, qrcode, socket
from PIL import Image
from io import BytesIO
from datetime import datetime
from tinydb import TinyDB, Query

app = Flask(__name__)
db = TinyDB('bags.json')
Bag = Query()
PORT = 5001

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]
    s.close()
    return ip

def analyze_image(image_file):
    img = Image.open(image_file).convert("RGB")
    buf = BytesIO()
    img.save(buf, format="JPEG")
    image_b64 = base64.b64encode(buf.getvalue()).decode()
    prompt = """Analyze this bag and return ONLY a JSON object, no other text:
{
  "primary_colour": "main colour",
  "shell_type": "hard or soft",
  "size_class": "cabin, medium, or large",
  "wheel_type": "2-wheel, 4-wheel spinner, or none",
  "distinctive_features": ["any stickers, damage, logos"]
}"""
    response = requests.post("http://localhost:11434/api/generate", json={
        "model": "llava",
        "prompt": prompt,
        "images": [image_b64],
        "stream": False
    })
    raw = response.json().get("response", "").strip()
    raw = raw.replace("```json", "").replace("```", "").strip()
    return json.loads(raw), image_b64

# ---------------------------------------------------------------------------
# CHECKIN PAGE
# ---------------------------------------------------------------------------

CHECKIN_HTML = """
<!DOCTYPE html>
<html>
<head>
  <title>SecureBag — Check In</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: system-ui, sans-serif; }
    body { background: #0f172a; min-height: 100vh; padding: 1.5rem; color: white; }
    .container { max-width: 600px; margin: 0 auto; }
    .header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 1.5rem; padding-bottom: 1rem; border-bottom: 1px solid #1e293b; }
    .header h1 { font-size: 1.2rem; font-weight: 600; }
    .header p { font-size: 0.8rem; color: #64748b; }
    .header-actions { display: flex; gap: 8px; align-items: center; }
    .badge { background: #1e40af; color: #93c5fd; font-size: 0.7rem; padding: 2px 8px; border-radius: 20px; font-weight: 600; }
    .btn-small { background: transparent; border: 1px solid #334155; color: #64748b; font-size: 0.7rem; padding: 2px 8px; border-radius: 20px; cursor: pointer; }
    .btn-small:hover { color: white; border-color: #64748b; }
    .btn-link { color: #64748b; font-size: 0.78rem; text-decoration: none; }
    .btn-link:hover { color: white; }
    .card { background: #1e293b; border-radius: 12px; padding: 1.25rem; margin-bottom: 1rem; border: 1px solid #334155; }
    .card h2 { font-size: 0.8rem; font-weight: 600; margin-bottom: 1rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em; }
    .field { margin-bottom: 0.9rem; }
    label { display: block; font-size: 0.78rem; color: #64748b; margin-bottom: 0.3rem; }
    input { width: 100%; padding: 0.6rem 0.8rem; border: 1px solid #334155; border-radius: 8px; font-size: 0.95rem; background: #0f172a; color: white; }
    input:focus { outline: none; border-color: #3b82f6; }
    input::placeholder { color: #475569; }
    .row { display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; }
    .upload-zone { border: 2px dashed #334155; border-radius: 8px; padding: 1.5rem; text-align: center; cursor: pointer; transition: all .2s; }
    .upload-zone:hover { border-color: #3b82f6; }
    .upload-zone p { color: #64748b; font-size: 0.85rem; margin-top: 0.4rem; }
    #preview { width: 100%; border-radius: 8px; margin-top: 1rem; display: none; }
    .btn { width: 100%; padding: 0.85rem; background: #2563eb; color: white; border: none; border-radius: 8px; font-size: 0.95rem; font-weight: 600; cursor: pointer; margin-top: 0.5rem; }
    .btn:hover { background: #1d4ed8; }
    .btn:disabled { background: #1e3a5f; color: #475569; cursor: not-allowed; }
    .result { display: none; background: #0f2d1f; border: 1px solid #166534; border-radius: 12px; padding: 1.25rem; margin-top: 1rem; text-align: center; }
    .result h3 { color: #4ade80; margin-bottom: 0.75rem; }
    .qr { width: 160px; height: 160px; margin: 0 auto 0.75rem; display: block; border-radius: 8px; background: white; padding: 8px; }
    .barcode { font-family: monospace; font-size: 0.8rem; background: #0f172a; padding: 0.5rem 1rem; border-radius: 6px; border: 1px solid #334155; margin-bottom: 0.75rem; word-break: break-all; color: #94a3b8; }
    .tags { display: flex; flex-wrap: wrap; gap: 0.4rem; justify-content: center; }
    .tag { background: #1e3a8a; color: #93c5fd; font-size: 0.78rem; padding: 0.2rem 0.6rem; border-radius: 20px; }
    .loading { display: none; text-align: center; padding: 1rem; color: #64748b; }
    .spinner { display: inline-block; width: 18px; height: 18px; border: 2px solid #334155; border-top-color: #3b82f6; border-radius: 50%; animation: spin .7s linear infinite; vertical-align: middle; margin-right: 0.5rem; }
    @keyframes spin { to { transform: rotate(360deg); } }
  </style>
</head>
<body>
<div class="container">
  <div class="header">
    <div>
      <h1>✈ SecureBag</h1>
      <p>Staff check-in terminal</p>
    </div>
    <div class="header-actions">
      <span class="badge">STAFF ONLY</span>
      <button class="btn-small" onclick="clearDB()">Clear DB</button>
      <a class="btn-link" href="/bags">All bags →</a>
    </div>
  </div>

  <div class="card">
    <h2>Passenger</h2>
    <div class="field"><label>Full name</label><input id="name" placeholder="As on ticket"></div>
    <div class="field"><label>Passport / ID number</label><input id="passport" placeholder="e.g. GB123456789"></div>
  </div>

  <div class="card">
    <h2>Flight</h2>
    <div class="row">
      <div class="field"><label>Flight number</label><input id="flight" placeholder="e.g. BA291"></div>
      <div class="field"><label>Destination</label><input id="dest" placeholder="e.g. Madrid"></div>
    </div>
    <div class="row">
      <div class="field"><label>Gate</label><input id="gate" placeholder="e.g. B14"></div>
      <div class="field"><label>Weight (kg)</label><input id="weight" type="number" placeholder="e.g. 23.4" step="0.1"></div>
    </div>
  </div>

  <div class="card">
    <h2>Bag photo</h2>
    <div class="upload-zone" onclick="document.getElementById('file').click()">
      <div style="font-size:1.8rem">📷</div>
      <p>Tap to photograph bag</p>
    </div>
    <input type="file" id="file" accept="image/*" capture="environment" style="display:none" onchange="previewImage(this)">
    <img id="preview">
  </div>

  <button class="btn" onclick="checkin()">Register bag + generate QR</button>

  <div class="loading" id="loading">
    <span class="spinner"></span> AI analysing bag — please wait...
  </div>

  <div class="result" id="result">
    <h3>✓ Bag registered</h3>
    <p style="font-size:0.8rem;color:#4ade80;margin-bottom:0.75rem">Scan QR to verify at gate</p>
    <img class="qr" id="qr-out" alt="QR Code">
    <div class="barcode" id="barcode-out"></div>
    <div class="tags" id="tags-out"></div>
    <a id="verify-link" href="#" style="display:inline-block;margin-top:0.75rem;font-size:0.8rem;color:#64748b;">Open verify page →</a>
  </div>
</div>

<script>
function previewImage(input) {
  const file = input.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = e => {
    const img = document.getElementById('preview');
    img.src = e.target.result;
    img.style.display = 'block';
  };
  reader.readAsDataURL(file);
}

async function checkin() {
  const name = document.getElementById('name').value;
  const passport = document.getElementById('passport').value;
  const flight = document.getElementById('flight').value;
  const dest = document.getElementById('dest').value;
  const gate = document.getElementById('gate').value;
  const weight = document.getElementById('weight').value;
  const file = document.getElementById('file').files[0];

  if (!name || !passport || !flight || !dest || !file) {
    alert('Please fill in all fields and take a photo.');
    return;
  }

  const formData = new FormData();
  formData.append('name', name);
  formData.append('passport', passport);
  formData.append('flight', flight);
  formData.append('destination', dest);
  formData.append('gate', gate);
  formData.append('weight', weight || 0);
  formData.append('image', file);

  document.querySelector('.btn').disabled = true;
  document.getElementById('loading').style.display = 'block';
  document.getElementById('result').style.display = 'none';

  const resp = await fetch('/checkin', { method: 'POST', body: formData });
  const data = await resp.json();

  document.getElementById('loading').style.display = 'none';
  document.querySelector('.btn').disabled = false;

  if (data.error) { alert('Error: ' + data.error); return; }

  document.getElementById('barcode-out').textContent = data.barcode_id;
  document.getElementById('qr-out').src = '/qr/' + data.barcode_id;
  document.getElementById('verify-link').href = '/bag/' + data.barcode_id;

  const tags = document.getElementById('tags-out');
  tags.innerHTML = '';
  const d = data.descriptors;
  const fields = [d.primary_colour, d.shell_type, d.size_class, d.wheel_type, ...(d.distinctive_features||[])].filter(Boolean);
  fields.forEach(f => {
    const tag = document.createElement('span');
    tag.className = 'tag';
    tag.textContent = f;
    tags.appendChild(tag);
  });
  document.getElementById('result').style.display = 'block';
}

async function clearDB() {
  if (!confirm('Clear all bag records? This cannot be undone.')) return;
  await fetch('/clear', { method: 'POST' });
  alert('Database cleared.');
}
</script>
</body>
</html>
"""

# ---------------------------------------------------------------------------
# ALL BAGS PAGE
# ---------------------------------------------------------------------------

BAGS_HTML = """
<!DOCTYPE html>
<html>
<head>
  <title>SecureBag — All Bags</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: system-ui, sans-serif; }
    body { background: #0f172a; color: white; padding: 1.25rem; }
    .container { max-width: 700px; margin: 0 auto; }
    .header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 1.25rem; padding-bottom: 1rem; border-bottom: 1px solid #1e293b; }
    .header h1 { font-size: 1.2rem; font-weight: 600; }
    .header-actions { display: flex; gap: 10px; align-items: center; }
    .btn-small { background: transparent; border: 1px solid #334155; color: #64748b; font-size: 0.75rem; padding: 4px 10px; border-radius: 6px; cursor: pointer; }
    .btn-small:hover { color: white; border-color: #64748b; }
    .btn-link { color: #64748b; font-size: 0.78rem; text-decoration: none; }
    .btn-link:hover { color: white; }
    .count { font-size: 0.8rem; color: #64748b; margin-bottom: 1rem; }
    .empty { text-align: center; padding: 3rem; color: #334155; }
    .empty p { font-size: 0.9rem; margin-top: 0.5rem; }
    table { width: 100%; border-collapse: collapse; }
    th { font-size: 0.72rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em; padding: 0.5rem 0.75rem; text-align: left; border-bottom: 1px solid #1e293b; }
    td { padding: 0.75rem; border-bottom: 1px solid #1e293b; font-size: 0.85rem; vertical-align: middle; }
    tr:last-child td { border: none; }
    tr:hover td { background: #1e293b; }
    .thumb { width: 44px; height: 44px; object-fit: cover; border-radius: 6px; border: 1px solid #334155; }
    .thumb-placeholder { width: 44px; height: 44px; background: #1e293b; border-radius: 6px; border: 1px solid #334155; display: flex; align-items: center; justify-content: center; font-size: 1.2rem; }
    .status { font-size: 0.72rem; padding: 2px 8px; border-radius: 20px; font-weight: 600; display: inline-block; }
    .status-active { background: #14532d; color: #86efac; }
    .status-flagged { background: #7f1d1d; color: #fca5a5; }
    .tag { background: #1e3a8a; color: #93c5fd; font-size: 0.7rem; padding: 1px 6px; border-radius: 20px; display: inline-block; margin: 1px; }
    .link { color: #3b82f6; text-decoration: none; font-size: 0.78rem; }
    .link:hover { text-decoration: underline; }
  </style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>✈ SecureBag — All Bags</h1>
    <div class="header-actions">
      <button class="btn-small" onclick="location.reload()">↻ Refresh</button>
      <a class="btn-link" href="/">← Check in</a>
    </div>
  </div>

  {% if not bags %}
    <div class="empty">
      <div style="font-size:2.5rem">🧳</div>
      <p>No bags checked in yet.</p>
    </div>
  {% else %}
    <p class="count">{{ bags|length }} bag{{ 's' if bags|length != 1 }} active</p>
    <table>
      <thead>
        <tr>
          <th>Photo</th>
          <th>Passenger</th>
          <th>Flight</th>
          <th>Descriptors</th>
          <th>Weight</th>
          <th>Status</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        {% for bag in bags %}
        <tr>
          <td>
            {% if bag.image_b64 %}
              <img class="thumb" src="data:image/jpeg;base64,{{ bag.image_b64 }}" alt="bag">
            {% else %}
              <div class="thumb-placeholder">🧳</div>
            {% endif %}
          </td>
          <td>
            <div style="font-weight:500;color:#e2e8f0">{{ bag.passenger_name }}</div>
            <div style="font-size:0.75rem;color:#64748b">{{ bag.passport }}</div>
          </td>
          <td>
            <div style="color:#e2e8f0">{{ bag.flight }}</div>
            <div style="font-size:0.75rem;color:#64748b">→ {{ bag.destination }}</div>
            {% if bag.gate %}<div style="font-size:0.75rem;color:#64748b">Gate {{ bag.gate }}</div>{% endif %}
          </td>
          <td>
            <span class="tag">{{ bag.descriptors.primary_colour }}</span>
            <span class="tag">{{ bag.descriptors.shell_type }}</span>
            <span class="tag">{{ bag.descriptors.size_class }}</span>
          </td>
          <td style="color:#94a3b8">{{ bag.weight_kg }} kg</td>
          <td>
            {% if bag.status == 'flagged' %}
              <span class="status status-flagged">⚠ Flagged</span>
            {% else %}
              <span class="status status-active">● Active</span>
            {% endif %}
          </td>
          <td><a class="link" href="/bag/{{ bag.barcode_id }}">Verify →</a></td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  {% endif %}
</div>
</body>
</html>
"""

# ---------------------------------------------------------------------------
# VERIFY PAGE
# ---------------------------------------------------------------------------

VERIFY_HTML = """
<!DOCTYPE html>
<html>
<head>
  <title>SecureBag — Verify</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: system-ui, sans-serif; }
    body { background: #0f172a; color: white; padding: 1.25rem; }
    .container { max-width: 480px; margin: 0 auto; }
    .header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 1.25rem; }
    .header h1 { font-size: 1.1rem; font-weight: 600; }
    .header-actions { display: flex; gap: 10px; align-items: center; }
    .btn-link { color: #64748b; font-size: 0.78rem; text-decoration: none; }
    .btn-link:hover { color: white; }
    .status-badge { font-size: 0.75rem; padding: 3px 10px; border-radius: 20px; font-weight: 600; }
    .status-ok { background: #14532d; color: #86efac; }
    .status-flag { background: #7f1d1d; color: #fca5a5; }
    .card { background: #1e293b; border-radius: 12px; padding: 1.1rem; margin-bottom: 0.9rem; border: 1px solid #334155; }
    .card h2 { font-size: 0.8rem; font-weight: 600; margin-bottom: 0.75rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em; }
    .bag-img { width: 100%; border-radius: 8px; margin-bottom: 0.75rem; max-height: 220px; object-fit: cover; }
    .qr { width: 120px; height: 120px; background: white; padding: 6px; border-radius: 8px; display: block; margin: 0 auto 0.75rem; }
    .tags { display: flex; flex-wrap: wrap; gap: 0.35rem; margin-bottom: 0.75rem; }
    .tag { background: #1e3a8a; color: #93c5fd; font-size: 0.75rem; padding: 0.2rem 0.55rem; border-radius: 20px; }
    .meta { font-size: 0.82rem; color: #64748b; line-height: 1.9; }
    .meta span { color: #e2e8f0; font-weight: 500; }
    .other-bag { display: flex; gap: 0.75rem; align-items: center; padding: 0.6rem 0; border-bottom: 1px solid #334155; }
    .other-bag:last-child { border: none; }
    .other-bag img { width: 52px; height: 52px; object-fit: cover; border-radius: 6px; border: 1px solid #334155; }
    .other-bag-info { font-size: 0.8rem; }
    .other-bag-info strong { display: block; color: #e2e8f0; }
    .other-bag-info span { color: #64748b; font-size: 0.75rem; }
    .actions { display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; margin-bottom: 0.75rem; }
    .btn-confirm { padding: 0.85rem; background: #166534; color: #4ade80; border: 1px solid #22c55e; border-radius: 8px; font-size: 0.95rem; font-weight: 600; cursor: pointer; }
    .btn-flag { padding: 0.85rem; background: #7f1d1d; color: #fca5a5; border: 1px solid #ef4444; border-radius: 8px; font-size: 0.95rem; font-weight: 600; cursor: pointer; }
    .btn-resolve { width: 100%; padding: 0.85rem; background: #1e3a8a; color: #93c5fd; border: 1px solid #3b82f6; border-radius: 8px; font-size: 0.95rem; font-weight: 600; cursor: pointer; margin-bottom: 0.75rem; }
    .btn-collect { width: 100%; padding: 0.85rem; background: #1e293b; color: #64748b; border: 1px solid #334155; border-radius: 8px; font-size: 0.95rem; font-weight: 600; cursor: pointer; }
    .alert-flag { background: #450a0a; border: 1px solid #ef4444; color: #fca5a5; padding: 0.75rem 1rem; border-radius: 8px; font-size: 0.85rem; margin-bottom: 0.9rem; }
    .done-screen { text-align: center; padding: 2rem 1rem; }
    .done-screen .icon { font-size: 3rem; margin-bottom: 0.75rem; }
    .done-screen h2 { font-size: 1.2rem; margin-bottom: 0.5rem; }
    .done-screen p { color: #64748b; font-size: 0.85rem; }
  </style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>✈ SecureBag</h1>
    <div class="header-actions">
      {% if bag %}
        {% if bag.status == 'flagged' %}
          <span class="status-badge status-flag">⚠ FLAGGED</span>
        {% else %}
          <span class="status-badge status-ok">● Active</span>
        {% endif %}
      {% endif %}
      <a class="btn-link" href="/bags">All bags →</a>
    </div>
  </div>

  {% if error %}
    <div class="card"><p style="color:#f87171">{{ error }}</p></div>

  {% else %}

  {% if bag.status == 'flagged' %}
  <div class="alert-flag">⚠ This bag has been flagged. Hold for security inspection.</div>
  {% endif %}

  <div class="card">
    <h2>Bag — {{ bag.barcode_id }}</h2>
    {% if bag.image_b64 %}
      <img class="bag-img" src="data:image/jpeg;base64,{{ bag.image_b64 }}" alt="Bag photo">
    {% endif %}
    <img class="qr" src="/qr/{{ bag.barcode_id }}" alt="QR code">
    <div class="tags">
      {% for f in [bag.descriptors.primary_colour, bag.descriptors.shell_type, bag.descriptors.size_class, bag.descriptors.wheel_type] %}
        {% if f %}<span class="tag">{{ f }}</span>{% endif %}
      {% endfor %}
      {% for f in bag.descriptors.distinctive_features %}
        <span class="tag">{{ f }}</span>
      {% endfor %}
    </div>
    <div class="meta">
      Passenger: <span>{{ bag.passenger_name }}</span><br>
      Passport: <span>{{ bag.passport }}</span><br>
      Flight: <span>{{ bag.flight }} → {{ bag.destination }}</span><br>
      Gate: <span>{{ bag.gate }}</span><br>
      Weight: <span>{{ bag.weight_kg }} kg</span>
    </div>
  </div>

  {% if other_bags %}
  <div class="card">
    <h2>Other bags — same passport</h2>
    {% for ob in other_bags %}
    <div class="other-bag">
      {% if ob.image_b64 %}
        <img src="data:image/jpeg;base64,{{ ob.image_b64 }}" alt="bag">
      {% endif %}
      <div class="other-bag-info">
        <strong>{{ ob.descriptors.primary_colour }} {{ ob.descriptors.shell_type }}-shell, {{ ob.descriptors.size_class }}</strong>
        <span>{{ ob.barcode_id }}</span><br>
        <span>{{ ob.weight_kg }} kg</span>
      </div>
    </div>
    {% endfor %}
  </div>
  {% endif %}

  {% if bag.status == 'flagged' %}
    <button class="btn-resolve" onclick="doAction('resolve')">✓ Resolve flag — return to active</button>
  {% else %}
    <div class="actions">
      <button class="btn-confirm" onclick="doAction('confirm')">✓ Confirm bag</button>
      <button class="btn-flag" onclick="doAction('flag')">⚠ Flag bag</button>
    </div>
  {% endif %}
  <button class="btn-collect" onclick="doAction('collect')">Collected at carousel →</button>

  {% endif %}
</div>

<script>
async function doAction(type) {
  const resp = await fetch('/action/{{ bag.barcode_id }}', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({action: type})
  });
  const data = await resp.json();
  if (!data.ok) { alert('Error: ' + (data.error || 'unknown')); return; }
  if (type === 'collect') {
    document.querySelector('.container').innerHTML = `
      <div class="done-screen">
        <div class="icon">✅</div>
        <h2>Bag checked out</h2>
        <p>Record deleted. Bag collected at carousel.</p>
        <a href="/bags" style="display:inline-block;margin-top:1rem;color:#64748b;font-size:0.85rem;text-decoration:none">← Back to all bags</a>
      </div>`;
  } else {
    location.reload();
  }
}
</script>
</body>
</html>
"""

# ---------------------------------------------------------------------------
# ROUTES
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template_string(CHECKIN_HTML)

@app.route("/checkin", methods=["POST"])
def checkin():
    try:
        name = request.form["name"]
        passport = request.form["passport"]
        flight = request.form["flight"]
        destination = request.form["destination"]
        gate = request.form.get("gate", "")
        weight = float(request.form.get("weight", 0))
        image_file = request.files["image"]
        descriptors, image_b64 = analyze_image(image_file)
        barcode_id = f"{flight}-{destination[:3].upper()}-{uuid.uuid4().hex[:6].upper()}"
        db.insert({
            "barcode_id": barcode_id,
            "passenger_name": name,
            "passport": passport,
            "flight": flight,
            "destination": destination,
            "gate": gate,
            "weight_kg": weight,
            "descriptors": descriptors,
            "image_b64": image_b64,
            "checked_in_at": datetime.now().isoformat(),
            "status": "active"
        })
        return jsonify({"barcode_id": barcode_id, "descriptors": descriptors})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/qr/<barcode_id>")
def qr_code(barcode_id):
    ip = get_local_ip()
    url = f"http://{ip}:{PORT}/bag/{barcode_id}"
    img = qrcode.make(url)
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return send_file(buf, mimetype="image/png")

@app.route("/bag/<barcode_id>")
def verify_page(barcode_id):
    results = db.search(Bag.barcode_id == barcode_id)
    if not results:
        return render_template_string(VERIFY_HTML, error="Bag not found", bag=None, other_bags=[])
    bag = results[0]
    other_bags = [b for b in db.search(Bag.passport == bag["passport"]) if b["barcode_id"] != barcode_id]
    return render_template_string(VERIFY_HTML, bag=bag, other_bags=other_bags, error=None)

@app.route("/action/<barcode_id>", methods=["POST"])
def bag_action(barcode_id):
    action = request.json.get("action")
    results = db.search(Bag.barcode_id == barcode_id)
    if not results:
        return jsonify({"ok": False, "error": "not found"}), 404
    bag = results[0]
    if bag["status"] == "flagged" and action not in ("resolve", "collect"):
        return jsonify({"ok": False, "error": "bag is flagged — resolve or collect only"})
    if action == "flag":
        db.update({"status": "flagged"}, Bag.barcode_id == barcode_id)
    elif action == "resolve":
        db.update({"status": "active"}, Bag.barcode_id == barcode_id)
    elif action == "confirm":
        db.update({"status": "active"}, Bag.barcode_id == barcode_id)
    elif action == "collect":
        db.remove(Bag.barcode_id == barcode_id)
    return jsonify({"ok": True})

@app.route("/clear", methods=["POST"])
def clear_db():
    db.truncate()
    return jsonify({"ok": True})

@app.route("/bags")
def all_bags():
    bags = db.all()
    return render_template_string(BAGS_HTML, bags=bags)

if __name__ == "__main__":
    ip = get_local_ip()
    print(f"\n✓ SecureBag running!")
    print(f"  Local:   http://localhost:{PORT}")
    print(f"  Network: http://{ip}:{PORT}  ← open this on your phone\n")
    app.run(host="0.0.0.0", debug=True, port=PORT)