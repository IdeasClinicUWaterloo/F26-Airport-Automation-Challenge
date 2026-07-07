# SecureBag

A prototype airport bag check-in and re-identification system. A passenger's bag is photographed at check-in; a QR code is generated for that bag; at the security scanner, a second photo is taken and automatically compared against the check-in photo to catch bag swaps or mismatches before they reach the gate.

## How it works

1. **Check-in** (`/`) — passenger details (name, passport, flight, destination, gate, weight) plus a photo of the bag are submitted. A dominant colour is extracted from the photo and a `barcode_id` is generated (`{flight}-{destination}-{random}`). The record, including the photo as base64, is stored in `bags.json`.
2. **QR code** (`/qr/<barcode_id>`) — encodes a URL to the bag's verification page (`/bag/<barcode_id>`) so staff can scan it with a phone.
3. **Verification** (`/verify/<barcode_id>`) — a new photo taken at the scanner is compared against the check-in photo using `bag_compare.py`, returning a verdict of `pass`, `review`, or `flag`.
4. **Action** (`/action/<barcode_id>`) — staff can `confirm`/`resolve` a flagged bag, re-`flag` it, or `collect` (remove) it from the system.

### Comparison pipeline (`bag_compare.py`)

Three independent signals are combined to decide whether two photos show the same bag:

- **Colour** (weight 0.6) — gray-world-balanced, centre-weighted 2D hue/saturation histogram correlation. Ignores brightness (V) to tolerate different lighting between check-in and the scanner.
- **ORB features** (weight 0.4) — ORB keypoint matching with Lowe's ratio test, verified geometrically via RANSAC homography, so repetitive prints/logos don't produce false correspondences.
- **Surface texture** — a rotation-tolerant FFT orientation-histogram comparison of a native-resolution central patch, used only as a veto to catch bags that share colour and shape but have a different surface pattern (e.g. ribbed vs. diamond-faceted hard-shell).

Both photos are first normalized to a consistent scale: a pretrained COCO object detector (`fasterrcnn_mobilenet_v3_large_320_fpn`, via `torchvision`) locates the bag (`suitcase`/`handbag`/`backpack`), falling back to a texture-based foreground detector for items outside those classes (e.g. small pouches).

The colour and ORB scores are combined into a weighted score against `PASS_THRESHOLD` / `FLAG_THRESHOLD`. Any single strong mismatch (colour, ORB, or texture) caps the verdict at `review` even if the combined score alone would pass — a deliberate check against one confident signal masking another that's flatly wrong. Tuning constants live at the top of `bag_compare.py`.

## Tech stack

| Purpose | Library |
|---|---|
| Web server / API | Flask |
| Image decoding/encoding | Pillow, OpenCV (`opencv-python`) |
| Bag detection | PyTorch + torchvision (pretrained Faster R-CNN, COCO weights) |
| Numerical/image processing | NumPy, OpenCV (histograms, ORB, FFT) |
| QR code generation | `qrcode` |
| Storage | TinyDB (`bags.json`, flat-file JSON — no external database) |

Frontend is server-rendered HTML/CSS/JS via Flask's `render_template_string` (no build step, no JS framework).

## Project structure

```
app.py           Flask app: routes, HTML templates, TinyDB wiring
bag_compare.py   Image comparison pipeline (colour / ORB / texture scoring)
bags.json        TinyDB data file — created/updated at runtime (contains PII + images)
sample_img/      Sample bag photo pairs for manual testing
venv/            Local Python virtual environment
```

## Setup

Requires Python 3.9 (matches the committed `venv/`).

```bash
# from the project root
source venv/bin/activate
python app.py
```

The venv is already populated and committed in this repo, so no `pip install` should be necessary. If you need to rebuild it from scratch:

```bash
python3.9 -m venv venv
source venv/bin/activate
pip install flask pillow opencv-python torch torchvision numpy qrcode tinydb
```

The first run downloads the pretrained Faster R-CNN weights (internet access required once; cached afterward by torchvision).

## Running

```bash
python app.py
```

This starts the server on port `5001`, bound to `0.0.0.0` (so it's reachable from other devices on the same network — e.g. a phone scanning the QR code). The console prints both the localhost URL and the LAN URL to open on a phone.

- Check-in UI: `http://localhost:5001/`
- All bags / staff dashboard: `http://localhost:5001/bags`

## API endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/` | Check-in form |
| POST | `/checkin` | Create a bag record (multipart form: `name`, `passport`, `flight`, `destination`, `gate`, `weight`, `image`) |
| GET | `/qr/<barcode_id>` | PNG QR code linking to the bag's verify page |
| GET | `/bag/<barcode_id>` | Verify page for a specific bag |
| POST | `/verify/<barcode_id>` | Submit a scan photo (`image`), returns verdict + score breakdown |
| POST | `/action/<barcode_id>` | JSON `{"action": "flag" \| "resolve" \| "confirm" \| "collect"}` |
| POST | `/clear` | Wipes the entire database |
| GET | `/bags` | Lists all bag records |

## Important considerations

- **This is a prototype, not a production security system.** There is no authentication on any route — anyone on the network can check in bags, verify them, clear the database, or view every passenger's data.
- **PII is stored in plaintext.** `bags.json` stores passenger name, passport number, and the full bag photo (base64) unencrypted. Treat this file as sensitive; do not commit real passenger data. `.gitignore` should probably exclude it if this ever leaves demo use.
- **Debug mode is on** (`app.run(..., debug=True)`), which enables the Werkzeug debugger — this must never be exposed outside a trusted local network, since it allows arbitrary code execution if reached by an attacker.
- **`/clear` has no confirmation or auth** and deletes all records — easy to trigger accidentally.
- **The `venv/` directory is committed to git**, which is unusual and bloats the repo; consider `.gitignore`-ing it and documenting dependencies in a `requirements.txt` instead.
- **The comparison pipeline is heuristic, not cryptographic identity verification** — it is tuned against the sample photos in `sample_img/` and may need re-tuning (`PASS_THRESHOLD`, `FLAG_THRESHOLD`, `ORB_WEIGHT`/`COLOR_WEIGHT`) for different lighting, camera hardware, or bag types.
- **`get_local_ip()`** opens a UDP socket to `8.8.8.8` purely to determine the machine's LAN-facing IP (no packets are actually sent); this will fail or hang on a network with no outbound route.
