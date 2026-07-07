from flask import Flask, request, jsonify, render_template_string, send_file
import base64, uuid, qrcode, socket
from PIL import Image
from io import BytesIO
from datetime import datetime
from tinydb import TinyDB, Query
from bag_compare import verify_bags, get_dominant_colour, rgb_to_colour_name

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
    .upload-zone { border: 2px dashed #334155; border-radius: 8px; padding: 1.5rem; text-align: center; cursor: pointer; transition: border-color .2s; }
    .upload-zone:hover { border-color: #3b82f6; }
    .upload-zone p { color: #64748b; font-size: 0.85rem; margin-top: 0.4rem; }
    #preview { width: 100%; border-radius: 8px; margin-top: 1rem; display: none; max-height: 200px; object-fit: cover; }
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
    <span class="spinner"></span> Processing bag...
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
  const name     = document.getElementById('name').value.trim();
  const passport = document.getElementById('passport').value.trim();
  const flight   = document.getElementById('flight').value.trim();
  const dest     = document.getElementById('dest').value.trim();
  const gate     = document.getElementById('gate').value.trim();
  const weight   = document.getElementById('weight').value;
  const file     = document.getElementById('file').files[0];

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
  const tag = document.createElement('span');
  tag.className = 'tag';
  tag.textContent = data.colour_name;
  tags.appendChild(tag);

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
    .status-active  { background: #14532d; color: #86efac; }
    .status-flagged { background: #7f1d1d; color: #fca5a5; }
    .tag { background: #1e3a8a; color: #93c5fd; font-size: 0.7rem; padding: 1px 6px; border-radius: 20px; display: inline-block; margin: 1px; }
    .link { color: #3b82f6; text-decoration: none; font-size: 0.78rem; }
    .link:hover { text-decoration: underline; }
    .btn-resolve-sm { background: #1e3a8a; color: #93c5fd; border: 1px solid #3b82f6; font-size: 0.7rem; padding: 3px 8px; border-radius: 6px; cursor: pointer; margin-top: 5px; display: block; }
    .btn-resolve-sm:hover { background: #2563eb; }
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
          <th>Colour</th>
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
          <td><span class="tag">{{ bag.descriptors.colour_name }}</span></td>
          <td style="color:#94a3b8">{{ bag.weight_kg }} kg</td>
          <td>
            {% if bag.status == 'flagged' %}
              <span class="status status-flagged">⚠ Flagged</span>
            {% else %}
              <span class="status status-active">● Active</span>
            {% endif %}
          </td>
          <td>
            <a class="link" href="/bag/{{ bag.barcode_id }}">Verify →</a>
            {% if bag.status == 'flagged' %}
            <button class="btn-resolve-sm" onclick="resolveFlag('{{ bag.barcode_id }}')">Resolve flag</button>
            {% endif %}
          </td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  {% endif %}
</div>
<script>
async function resolveFlag(barcodeId) {
  if (!confirm('Clear the flag on this bag and return it to active?')) return;
  const resp = await fetch('/action/' + barcodeId, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ action: 'resolve' })
  });
  const data = await resp.json();
  if (data.ok) location.reload();
  else alert('Error: ' + (data.error || 'unknown'));
}
</script>
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
    .header p { font-size: 0.78rem; color: #64748b; }
    .header-actions { display: flex; gap: 8px; align-items: center; }
    .badge { background: #1e40af; color: #93c5fd; font-size: 0.7rem; padding: 2px 8px; border-radius: 20px; font-weight: 600; }
    .btn-link { color: #64748b; font-size: 0.78rem; text-decoration: none; }
    .btn-link:hover { color: white; }
    .status-badge { font-size: 0.75rem; padding: 3px 10px; border-radius: 20px; font-weight: 600; }
    .status-ok   { background: #14532d; color: #86efac; }
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
    .upload-zone { border: 2px dashed #334155; border-radius: 8px; padding: 1.25rem; text-align: center; cursor: pointer; transition: border-color .2s; }
    .upload-zone:hover { border-color: #3b82f6; }
    .upload-zone p { color: #64748b; font-size: 0.85rem; margin-top: 0.35rem; }
    #scan-preview { display: none; width: 100%; border-radius: 8px; margin-top: 0.75rem; max-height: 200px; object-fit: cover; }
    .btn { width: 100%; padding: 0.85rem; background: #2563eb; color: white; border: none; border-radius: 8px; font-size: 0.95rem; font-weight: 600; cursor: pointer; margin-top: 0.75rem; }
    .btn:hover { background: #1d4ed8; }
    .btn:disabled { background: #1e3a5f; color: #475569; cursor: not-allowed; }
    .loading { display: none; text-align: center; padding: 0.75rem; color: #64748b; font-size: 0.85rem; }
    .spinner { display: inline-block; width: 16px; height: 16px; border: 2px solid #334155; border-top-color: #3b82f6; border-radius: 50%; animation: spin .7s linear infinite; vertical-align: middle; margin-right: 0.4rem; }
    @keyframes spin { to { transform: rotate(360deg); } }
    .score-grid { margin-top: 0.75rem; }
    .score-row { display: flex; justify-content: space-between; align-items: center; padding: 0.3rem 0; border-bottom: 1px solid rgba(255,255,255,0.08); font-size: 0.82rem; }
    .score-row:last-child { border: none; }
    .score-val { font-weight: 700; font-size: 0.9rem; }
    .actions { display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; margin-bottom: 0.75rem; }
    .btn-confirm { padding: 0.85rem; background: #166534; color: #4ade80; border: 1px solid #22c55e; border-radius: 8px; font-size: 0.9rem; font-weight: 600; cursor: pointer; }
    .btn-flag    { padding: 0.85rem; background: #7f1d1d; color: #fca5a5; border: 1px solid #ef4444; border-radius: 8px; font-size: 0.9rem; font-weight: 600; cursor: pointer; }
    .btn-resolve { width: 100%; padding: 0.85rem; background: #1e3a8a; color: #93c5fd; border: 1px solid #3b82f6; border-radius: 8px; font-size: 0.9rem; font-weight: 600; cursor: pointer; margin-bottom: 0.75rem; }
    .btn-collect { width: 100%; padding: 0.85rem; background: #1e293b; color: #64748b; border: 1px solid #334155; border-radius: 8px; font-size: 0.9rem; font-weight: 600; cursor: pointer; }
    .alert-flag  { background: #450a0a; border: 1px solid #ef4444; color: #fca5a5; padding: 0.75rem 1rem; border-radius: 8px; font-size: 0.85rem; margin-bottom: 0.9rem; }
    .done-screen { text-align: center; padding: 2rem 1rem; }
    .done-screen .icon { font-size: 3rem; margin-bottom: 0.75rem; }
    .done-screen h2 { font-size: 1.2rem; margin-bottom: 0.5rem; }
    .done-screen p { color: #64748b; font-size: 0.85rem; }
  </style>
</head>
<body>
<div class="container">
  <div class="header">
    <div>
      <h1>✈ SecureBag</h1>
      <p>Bag verification</p>
    </div>
    <div class="header-actions">
      {% if bag %}
        <span id="status-badge" class="status-badge {{ 'status-flag' if bag.status == 'flagged' else 'status-ok' }}">
          {{ '⚠ FLAGGED' if bag.status == 'flagged' else '● Active' }}
        </span>
      {% endif %}
      <span class="badge">STAFF ONLY</span>
      <a class="btn-link" href="/bags">All bags →</a>
    </div>
  </div>

  {% if error %}
    <div class="card"><p style="color:#f87171">{{ error }}</p></div>
  {% else %}

  <div id="flag-alert" class="alert-flag" style="{{ '' if bag.status == 'flagged' else 'display:none' }}">
    ⚠ This bag has been flagged for inspection. Do not release.
  </div>

  <div class="card">
    <h2>Check-in — {{ bag.barcode_id }}</h2>
    {% if bag.image_b64 %}
      <img class="bag-img" src="data:image/jpeg;base64,{{ bag.image_b64 }}" alt="Check-in photo">
    {% endif %}
    <img class="qr" src="/qr/{{ bag.barcode_id }}" alt="QR code">
    <div class="tags">
      <span class="tag">{{ bag.descriptors.colour_name }}</span>
    </div>
    <div class="meta">
      Passenger: <span>{{ bag.passenger_name }}</span><br>
      Passport:  <span>{{ bag.passport }}</span><br>
      Flight:    <span>{{ bag.flight }} → {{ bag.destination }}</span><br>
  {% if bag.gate %}Gate: <span>{{ bag.gate }}</span><br>{% endif %}
      Weight:    <span>{{ bag.weight_kg }} kg</span>
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
        <strong>{{ ob.descriptors.colour_name }}</strong>
        <span>{{ ob.barcode_id }}</span><br>
        <span>{{ ob.weight_kg }} kg</span>
      </div>
    </div>
    {% endfor %}
  </div>
  {% endif %}

  <!-- ── STEP 1: scan form ──────────────────────────────────────────── -->
  <div id="scan-step">
    <div class="card">
      <h2>Scan this bag now</h2>
      <div class="upload-zone" onclick="document.getElementById('scan-file').click()">
        <div style="font-size:1.8rem">📷</div>
        <p>Photograph the bag in front of you</p>
      </div>
      <input type="file" id="scan-file" accept="image/*"
             style="display:none" onchange="previewScan(this)">
      <img id="scan-preview">
      <button class="btn" id="compare-btn" onclick="compareBags()">Compare bags →</button>
      <div class="loading" id="scan-loading">
        <span class="spinner"></span> Comparing bags...
      </div>
    </div>
  </div>

  <!-- ── STEP 2: result (populated by JS) ──────────────────────────── -->
  <div id="result-step" style="display:none"></div>

  <!-- always-visible controls -->
  <button class="btn-collect" onclick="doAction('collect')">Collected at carousel →</button>

  {% endif %}
</div>

<script>
const BARCODE_ID       = '{{ bag.barcode_id if bag else "" }}';
const ALREADY_FLAGGED  = {{ 'true' if bag and bag.status == 'flagged' else 'false' }};

function previewScan(input) {
  const file = input.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = e => {
    const img = document.getElementById('scan-preview');
    img.src = e.target.result;
    img.style.display = 'block';
  };
  reader.readAsDataURL(file);
}

async function compareBags() {
  const file = document.getElementById('scan-file').files[0];
  if (!file) { alert('Please photograph or upload the bag first.'); return; }

  document.getElementById('compare-btn').disabled = true;
  document.getElementById('scan-loading').style.display = 'block';

  const formData = new FormData();
  formData.append('image', file);

  try {
    const resp = await fetch('/verify/' + BARCODE_ID, { method: 'POST', body: formData });
    const data = await resp.json();
    document.getElementById('scan-loading').style.display = 'none';

    if (!data.ok) {
      alert('Error: ' + data.error);
      document.getElementById('compare-btn').disabled = false;
      return;
    }
    document.getElementById('scan-step').style.display = 'none';
    showResult(data);
  } catch (err) {
    document.getElementById('scan-loading').style.display = 'none';
    document.getElementById('compare-btn').disabled = false;
    alert('Error: ' + err.message);
  }
}

function showResult(data) {
  const { verdict, combined_score, flag_reason, breakdown, scan_b64 } = data;

  const cfg = {
    pass:   { bg: '#0f2d1f', border: '#166534', color: '#4ade80', icon: '✓', label: 'PASS',   msg: 'Bag confirmed — consistent with check-in photo' },
    review: { bg: '#1c1500', border: '#d97706', color: '#fbbf24', icon: '⚠', label: 'REVIEW', msg: 'Marginal match — manual visual check required'    },
    flag:   { bg: '#450a0a', border: '#ef4444', color: '#fca5a5', icon: '✕', label: 'FLAG',   msg: 'Bag may have been switched — lock it down'        },
  }[verdict];

  // Update live status badge and alert banner when auto-flagging
  if (verdict === 'flag' && !ALREADY_FLAGGED) {
    const badge = document.getElementById('status-badge');
    if (badge) { badge.textContent = '⚠ FLAGGED'; badge.className = 'status-badge status-flag'; }
    document.getElementById('flag-alert').style.display = 'block';
  }

  const pct = n => (n * 100).toFixed(1) + '%';

  const reasonHtml = flag_reason
    ? `<p style="font-size:0.76rem;opacity:0.75;margin-top:0.5rem">Reason: ${flag_reason}</p>` : '';

  const reviewBtns = verdict === 'review' ? `
    <div class="actions">
      <button class="btn-confirm" onclick="doAction('confirm')">✓ Confirm bag</button>
      <button class="btn-flag"    onclick="doAction('flag')">⚠ Flag bag</button>
    </div>` : '';

  const scanImg = scan_b64
    ? `<img class="bag-img" src="data:image/jpeg;base64,${scan_b64}" alt="Scan photo" style="margin-bottom:0.9rem">` : '';

  document.getElementById('result-step').innerHTML = `
    <div style="background:${cfg.bg};border:1px solid ${cfg.border};color:${cfg.color};
                border-radius:12px;padding:1.25rem;margin-bottom:0.9rem;text-align:center">
      <div style="font-size:2rem;margin-bottom:0.25rem">${cfg.icon}</div>
      <div style="font-size:1rem;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.35rem">
        ${cfg.label}
      </div>
      <div style="font-size:0.82rem;opacity:0.85;margin-bottom:0.9rem">${cfg.msg}</div>
      ${reasonHtml}
      <div class="score-grid">
        <div class="score-row">
          <span>Combined score</span><span class="score-val">${pct(combined_score)}</span>
        </div>
        <div class="score-row">
          <span>ORB features (×0.6)</span><span class="score-val">${pct(breakdown.orb_score)}</span>
        </div>
        <div class="score-row">
          <span>Colour (×0.4)</span><span class="score-val">${pct(breakdown.color_score)}</span>
        </div>
      </div>
    </div>
    ${scanImg}
    ${reviewBtns}
    <p style="text-align:center;margin-bottom:0.75rem">
      <a href="#" onclick="resetScan();return false"
         style="font-size:0.78rem;color:#64748b;text-decoration:none">↩ Scan again</a>
    </p>
  `;
  document.getElementById('result-step').style.display = 'block';
}

function resetScan() {
  const rs = document.getElementById('result-step');
  rs.style.display = 'none';
  rs.innerHTML = '';
  document.getElementById('scan-file').value = '';
  document.getElementById('scan-preview').style.display = 'none';
  document.getElementById('compare-btn').disabled = false;
  document.getElementById('scan-step').style.display = 'block';
}

async function doAction(type) {
  const resp = await fetch('/action/' + BARCODE_ID, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ action: type })
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
        name        = request.form["name"]
        passport    = request.form["passport"]
        flight      = request.form["flight"]
        destination = request.form["destination"]
        gate        = request.form.get("gate", "")
        weight      = float(request.form.get("weight", 0))
        image_file  = request.files["image"]

        img = Image.open(image_file).convert("RGB")
        buf = BytesIO()
        img.save(buf, format="JPEG")
        image_b64 = base64.b64encode(buf.getvalue()).decode()

        r, g, b = get_dominant_colour(image_b64)
        colour_name = rgb_to_colour_name(r, g, b)

        barcode_id = f"{flight}-{destination[:3].upper()}-{uuid.uuid4().hex[:6].upper()}"
        db.insert({
            "barcode_id":     barcode_id,
            "passenger_name": name,
            "passport":       passport,
            "flight":         flight,
            "destination":    destination,
            "gate":           gate,
            "weight_kg":      weight,
            "descriptors":    {"colour_name": colour_name},
            "image_b64":      image_b64,
            "checked_in_at":  datetime.now().isoformat(),
            "status":         "active",
        })
        return jsonify({"barcode_id": barcode_id, "colour_name": colour_name})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/qr/<barcode_id>")
def qr_code(barcode_id):
    ip  = get_local_ip()
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
    bag        = results[0]
    other_bags = [b for b in db.search(Bag.passport == bag["passport"]) if b["barcode_id"] != barcode_id]
    return render_template_string(VERIFY_HTML, bag=bag, other_bags=other_bags, error=None)


@app.route("/verify/<barcode_id>", methods=["POST"])
def verify_bag(barcode_id):
    try:
        results = db.search(Bag.barcode_id == barcode_id)
        if not results:
            return jsonify({"ok": False, "error": "bag not found"}), 404
        bag = results[0]

        image_file = request.files.get("image")
        if not image_file:
            return jsonify({"ok": False, "error": "no scan image provided"}), 400

        img = Image.open(image_file).convert("RGB")
        buf = BytesIO()
        img.save(buf, format="JPEG")
        scan_b64 = base64.b64encode(buf.getvalue()).decode()

        result = verify_bags(bag["image_b64"], scan_b64)

        if result["verdict"] == "flag":
            db.update({"status": "flagged"}, Bag.barcode_id == barcode_id)

        return jsonify({"ok": True, "scan_b64": scan_b64, **result})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/action/<barcode_id>", methods=["POST"])
def bag_action(barcode_id):
    action  = request.json.get("action")
    results = db.search(Bag.barcode_id == barcode_id)
    if not results:
        return jsonify({"ok": False, "error": "not found"}), 404
    bag = results[0]
    if bag["status"] == "flagged" and action not in ("resolve", "collect"):
        return jsonify({"ok": False, "error": "bag is flagged — resolve or collect only"})
    if action == "flag":
        db.update({"status": "flagged"}, Bag.barcode_id == barcode_id)
    elif action in ("resolve", "confirm"):
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
