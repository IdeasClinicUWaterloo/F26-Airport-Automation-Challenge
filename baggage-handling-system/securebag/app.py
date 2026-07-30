from flask import Flask, request, jsonify, render_template, send_file
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
# ROUTES
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("checkin.html")


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
        return render_template("verify.html", error="Bag not found", bag=None, other_bags=[])
    bag        = results[0]
    other_bags = [b for b in db.search(Bag.passport == bag["passport"]) if b["barcode_id"] != barcode_id]
    return render_template("verify.html", bag=bag, other_bags=other_bags, error=None)


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
    return render_template("bags.html", bags=bags)


if __name__ == "__main__":
    ip = get_local_ip()
    print(f"\n✓ SecureBag running!")
    print(f"  Local:   http://localhost:{PORT}")
    print(f"  Network: http://{ip}:{PORT}  ← open this on your phone\n")
    app.run(host="0.0.0.0", debug=True, port=PORT)
