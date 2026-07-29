# Solution Backup

This folder preserves the earlier version of the tracker. It is separate from the main `starter-kit/` and has its own copies of the route data and scenarios.

Run it from the repository root:

```bash
pip install -r air-traffic-control/starter-kit/requirements.txt
python air-traffic-control/solution-backup/stream.py
```

The backup reads from its local `data/` and `scenarios/` folders and writes its map to `output/`.
