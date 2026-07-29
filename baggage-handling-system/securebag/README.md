# SecureBag

SecureBag is a prototype airport bag check-in and re-identification system. It helps staff check whether a bag photographed later in its journey appears to be the same bag that the passenger originally checked in—not one that was swapped or mixed up.

> **Important:** SecureBag is a learning and hackathon prototype. It is not a certified aviation-security or passenger-identification system.

## How it works

1. **Check-in:** Staff enter the passenger's name, passport number, flight, destination, gate, and bag weight, then take a photo of the bag.
2. **Bag ID and QR code:** The app stores the record in `bags.json`, creates an ID such as `AC123-YYZ-8F2A3C`, and generates a QR code linked to that bag's verification page.
3. **Verification:** At a later checkpoint, staff scan the QR code and take a new photo. The app compares it with the check-in photo.
4. **Decision:** The comparison returns `pass`, `review`, or `flag`.
5. **Staff action:** Staff can confirm an active bag, manually flag it, resolve a flagged bag, or collect it. Collecting a bag removes its record from the database.

The automated result is decision support only. A person should review uncertain or flagged results.

## What students can learn

This project is a starting point for experimenting with:

- Flask routes and a server-rendered web interface
- Image uploads, encoding, and processing
- QR-code generation and phone-based workflows
- Classical computer-vision features and similarity scoring
- Pretrained object-detection models
- Human review and status-management workflows
- Privacy, security, and reliability trade-offs in prototypes

## Project structure

| File or folder | Purpose |
|---|---|
| `app.py` | Flask application, inline HTML/CSS/JavaScript, routes, and TinyDB integration |
| `bag_compare.py` | Bag detection and photo-comparison pipeline |
| `requirements.txt` | Python dependencies |
| `bags.json` | TinyDB data file containing bag records and base64-encoded images |
| `sample_img/` | Sample bag-photo pairs for manual testing |

The frontend is rendered directly by Flask with `render_template_string`; there is no JavaScript framework or frontend build step.

## Tech stack

| Purpose | Technology |
|---|---|
| Web application and API | Flask |
| Image decoding and processing | Pillow and OpenCV |
| Bag detection | PyTorch and torchvision |
| Numerical processing | NumPy |
| QR-code generation | `qrcode` |
| Storage | TinyDB using `bags.json` |

## Setup

The source uses Python 3.9+ syntax. Python 3.10 or 3.11 is recommended for the smoothest package compatibility.

Open a terminal in `baggage-handling-system/securebag`, then create and activate a virtual environment.

### Windows

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

### macOS or Linux

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open `http://localhost:5001` after the server starts.

The installation includes PyTorch and torchvision, so it can take several minutes and use substantial disk space. On the first comparison, torchvision may also download pretrained Faster R-CNN weights. Those weights are cached for later runs.

### Windows long-path errors

If installation fails with a "filename too long" error, create the virtual environment in a shorter location:

```powershell
python -m venv C:\venv-securebag
C:\venv-securebag\Scripts\activate
pip install -r requirements.txt
python app.py
```

Run the final two commands from the `securebag` project folder.

## Using the app

- `http://localhost:5001/` — register a bag and generate its QR code
- `http://localhost:5001/bags` — view the staff dashboard

The server binds to `0.0.0.0`, and the console prints a LAN address for testing from another device on the same network. The QR code uses that LAN address.

The current `get_local_ip()` helper determines the address by opening a UDP socket to `8.8.8.8`. On a restricted or fully offline network, startup or QR generation may fail even when the model weights are already cached.

## How photo comparison works

`bag_compare.py` combines three visual signals:

- **Colour:** A centre-weighted hue/saturation histogram checks whether the bags have similar overall colours while reducing the effect of brightness changes.
- **Visual features:** ORB keypoints look for matching details such as logos, patterns, corners, and scuffs. RANSAC checks whether those matches align geometrically.
- **Surface texture:** An FFT-based orientation comparison helps distinguish similarly coloured bags with different surface patterns or materials.

For the main colour and ORB comparison, each image is cropped with a texture-based foreground detector and normalized to a fixed canvas. For the surface-texture check, a pretrained COCO Faster R-CNN model attempts to locate a `suitcase`, `handbag`, or `backpack`; if it cannot find one, the code falls back to the foreground detector.

Colour and ORB scores are combined and compared with `PASS_THRESHOLD` and `FLAG_THRESHOLD`. A strong mismatch in colour, ORB features, or texture can reduce an apparent pass to `review`. Tuning constants are near the top of `bag_compare.py`.

The pipeline is heuristic: lighting, camera angle, background, image quality, and bag type can all affect the result.

## API routes

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/` | Display the check-in form |
| `POST` | `/checkin` | Create a bag record from `name`, `passport`, `flight`, `destination`, `gate`, `weight`, and `image` |
| `GET` | `/qr/<barcode_id>` | Return a PNG QR code linked to the bag's verification page |
| `GET` | `/bag/<barcode_id>` | Display the verification page for one bag |
| `POST` | `/verify/<barcode_id>` | Compare an uploaded `image` with the check-in image |
| `POST` | `/action/<barcode_id>` | Apply `flag`, `resolve`, `confirm`, or `collect` |
| `POST` | `/clear` | Delete every bag record |
| `GET` | `/bags` | Display all bag records |

Example action request:

```json
{
  "action": "confirm"
}
```

## Important limitations

- **No authentication or authorization:** Anyone who can reach the server can view passenger data, register bags, change bag status, or clear the database.
- **Plaintext passenger data:** `bags.json` stores names, passport numbers, and full bag photos without encryption. Use fictional passenger information only.
- **Bundled test data:** The repository currently tracks `bags.json`. Clearing or adding records changes a tracked file.
- **Destructive clear action:** `/clear` deletes all records without server-side authentication or confirmation.
- **Debug server exposed to the LAN:** The app runs Flask with `debug=True` while listening on `0.0.0.0`. Only run it on a trusted network. Disable debug mode before any wider deployment.
- **Unrestricted uploads:** The server does not currently enforce an upload-size limit or validate the image format before processing it.
- **Unpinned dependencies:** `requirements.txt` does not specify versions, so installations may behave differently over time.
- **Heuristic matching:** A pass is not proof that two photos show the same physical bag. The sample images are not a complete validation dataset.
- **Prototype storage:** TinyDB is convenient for a demo but is not designed for sensitive data or a concurrent production workload.

Do not enter real passport information or expose this application to the public internet.

## Extension ideas

- Compare bag weight at check-in and later checkpoints
- Add staff accounts and role-based permissions
- Add a confirmation step before clearing records
- Record an audit trail without deleting collected bags
- Improve the mobile check-in and scanning experience
- Separate HTML templates, styles, and scripts from `app.py`
- Add input validation, upload limits, and clearer error messages
- Pin dependency versions and add automated tests
- Evaluate thresholds on a larger labelled image dataset
- Store sensitive data in an encrypted production database
- Make LAN-address detection work on restricted or offline networks

## Disclaimer

SecureBag is an experimental teaching prototype. It must not replace approved baggage-screening procedures, trained staff, or certified aviation-security systems.
