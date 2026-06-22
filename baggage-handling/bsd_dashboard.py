import tkinter as tk
from tkinter import ttk
import csv
import os
import sys

# 2D Canvas Coordinate Map for the 28 Airport Nodes
NODE_COORDINATES = {
    # Terminal A (Top Half)
    "IA1": (80, 140),  "IA2": (80, 240),
    "JA1": (220, 140), "JA2": (380, 140), "JA3": (540, 140), "JA4": (700, 140), "JA5": (460, 60),
    "GA1": (220, 40),  "GA2": (380, 40),  "GA3": (540, 40),  "GA4": (700, 40),

    # Main Center Spine Corridors
    "S1": (220, 360),  "S2": (380, 360),  "S3": (540, 360),
    "S4": (700, 360),  "S5": (860, 360),  "S6": (540, 480),

    # Terminal B (Bottom Half)
    "IB1": (80, 580),  "IB2": (80, 480),
    "JB1": (220, 580), "JB2": (380, 580), "JB3": (540, 580), "JB4": (700, 580), "JB5": (460, 660),
    "GB1": (860, 140), "GB2": (860, 240), "GB3": (860, 480), "GB4": (860, 580)
}

class BSDDashboard:
    def __init__(self, root, telemetry_path="live_telemetry.csv"):
        self.root = root
        self.root.title("Brock Solutions - SmartSuite: Bag Status Display (BSD)")
        self.root.geometry("1100x820")
        self.root.configure(bg="#1e1e24")

        self.telemetry_path = telemetry_path
        self.current_tick = 1
        self.max_ticks = 1
        self.is_playing = False
        self.playback_speed = 100 #ms per tick
        self.history = {}

        self._load_telemetry_data()
        self._build_ui_layout()
        self._draw_static_network()
        self._update_display()

    def _load_telemetry_data(self):
        """Parses the telemetry CSV file and structures rows by simulation tick."""
        if not os.path.exists(self.telemetry_path):
            print(f"Error: Target data file '{self.telemetry_path}' not found. Run evaluator first.")
            sys.exit(1)

        print("Parsing simulation telemetry dataset...")
        with open(self.telemetry_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                t = int(row["tick"])
                edge_id = row["edge_id"]
                
                if t not in self.history:
                    self.history[t] = {}
                    
                self.history[t][edge_id] = {
                    "status": row["status"],
                    "fault_reason": row["fault_reason"],
                    "active_bags": int(row["active_bags"]),
                    "volume": int(row["cumulative_volume"])
                }
                self.max_ticks = max(self.max_ticks, t)

    def _build_ui_layout(self):
        """Constructs widgets, media player toolbars, and canvas properties."""
        # Top Heading Frame
        header = tk.Frame(self.root, bg="#0f0f12", height=60)
        header.pack(fill=tk.X, side=tk.TOP)
        
        lbl_title = tk.Label(header, text="SmartSort Operational Playback Command Center", 
                             font=("Helvetica", 14, "bold"), fg="#ffffff", bg="#0f0f12")
        lbl_title.pack(side=tk.LEFT, padx=20, pady=15)

        # Control Panel Frame (Bottom Toolbar)
        controls = tk.Frame(self.root, bg="#0f0f12", height=70)
        controls.pack(fill=tk.X, side=tk.BOTTOM)

        self.btn_play = tk.Button(controls, text="▶ Play", width=10, bg="#28a745", fg="white", 
                                  font=("Helvetica", 10, "bold"), command=self._toggle_playback)
        self.btn_play.pack(side=tk.LEFT, padx=15, pady=15)

        # Step controls
        btn_prev = tk.Button(controls, text="⏮ Back", bg="#3a3a43", fg="white", command=self._prev_tick)
        btn_prev.pack(side=tk.LEFT, padx=5, pady=15)
        btn_next = tk.Button(controls, text="Next ⏭", bg="#3a3a43", fg="white", command=self._next_tick)
        btn_next.pack(side=tk.LEFT, padx=5, pady=15)

        # Live Performance KPIs Side/Bottom Displays
        self.lbl_tick_counter = tk.Label(controls, text="Tick: 0000 / 3600", font=("Courier", 12, "bold"), 
                                         fg="#00ffcc", bg="#0f0f12")
        self.lbl_tick_counter.pack(side=tk.LEFT, padx=30)

        # Live Surcharge Delay Meter
        self.lbl_active_jams = tk.Label(controls, text="Active Blockages: 0", font=("Helvetica", 11, "bold"), 
                                        fg="#ff3333", bg="#0f0f12")
        self.lbl_active_jams.pack(side=tk.RIGHT, padx=30)

        # Main Central Simulation Matrix Canvas
        self.canvas = tk.Canvas(self.root, bg="#151518", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def _draw_static_network(self):
        """Renders static geographical system markers onto the coordinate plane."""
        # Draw background node landmarks to define spatial zones
        for node_id, (x, y) in NODE_COORDINATES.items():
            # Determine color template based on specific node naming types
            if node_id.startswith("I"):   color, label_color = "#007bff", "white" # Intake Ports
            elif node_id.startswith("G"): color, label_color = "#28a745", "white" # Destination Gates
            elif node_id.startswith("S"): color, label_color = "#ffc107", "black" # High-Speed Spine Trunks
            else:                         color, label_color = "#6c757d", "white" # Junction Junctions

            # Render physical circular terminal ports
            r = 16
            self.canvas.create_oval(x-r, y-r, x+r, y+r, fill=color, outline="#ffffff", width=1)
            self.canvas.create_text(x, y, text=node_id, font=("Helvetica", 8, "bold"), fill=label_color)

    def _update_display(self):
        """Clears transient visual artifacts and updates edges, metrics, and logs."""
        # Remove old dynamic line layers and numeric indicators
        self.canvas.delete("dynamic_overlay")
        
        tick_data = self.history.get(self.current_tick, {})
        active_jams_count = 0

        # Sync visual properties across mapped conveyor connections
        for edge_id, edge in tick_data.items():
            # Deconstruct baseline ID tags to map endpoints
            base_clean_id = edge_id.replace("_FWD", "").replace("_REV", "")
            
            # Find edge object mapping coordinates dynamically from dataset layout patterns
            # Safe fallbacks mapped dynamically to trace lines cleanly
            parts = base_clean_id.split("_")
            if len(parts) != 3: continue
            _, u, v = parts # Formatted as e_NodeU_NodeV
            
            # If line flag was reversed, flip coordinates to maintain accurate direction paths
            if edge_id.endswith("_REV"):
                u, v = v, u

            if u not in NODE_COORDINATES or v not in NODE_COORDINATES:
                continue

            x1, y1 = NODE_COORDINATES[u]
            x2, y2 = NODE_COORDINATES[v]

            # Enforce Line Color Gradients based on System Telemetry
            bags_count = edge["active_bags"]
            is_jammed = edge["status"] == "JAMMED"
            
            if is_jammed:
                line_color = "#dc3545" # Faulted Blockage: Crimson Red
                line_width = 4
                active_jams_count += 1
            elif bags_count > 0:
                line_color = "#fd7e14" # Occupied Cargo Line: Safety Orange
                line_width = 3
            else:
                line_color = "#343a40" # Idle Unused Conveyor: Charcoal Dark Gray
                line_width = 1.5

            # Draw directional conveyor track
            self.canvas.create_line(x1, y1, x2, y2, fill=line_color, width=line_width, 
                                    arrow=tk.LAST, arrowshape=(10,12,4), tags="dynamic_overlay")

            # Draw numeric load indicator bubbles over high-volume lanes
            if bags_count > 0:
                mx, my = (x1 + x2) / 2, (y1 + y2) / 2
                # Slid offset bubble upwards slightly for overlapping parallel fields
                if edge_id.endswith("_REV"): my += 12 
                else: my -= 12
                
                self.canvas.create_rectangle(mx-9, my-7, mx+9, my+7, fill="#fd7e14", outline="white", tags="dynamic_overlay")
                self.canvas.create_text(mx, my, text=str(bags_count), font=("Courier", 8, "bold"), fill="white", tags="dynamic_overlay")

        # Refresh global dashboard dashboard metrics
        self.lbl_tick_counter.config(text=f"Tick: {self.current_tick:04d} / {self.max_ticks:04d}")
        self.lbl_active_jams.config(text=f"Active Blockages: {active_jams_count}")

    def _toggle_playback(self):
        """Controls media frame execution transitions."""
        if self.is_playing:
            self.is_playing = False
            self.btn_play.config(text="▶ Play", bg="#28a745")
        else:
            self.is_playing = True
            self.btn_play.config(text="⏸ Pause", bg="#ffc107")
            self._playback_loop()

    def _playback_loop(self):
        """Automated timeline thread ticking algorithm."""
        if not self.is_playing:
            return
        if self.current_tick < self.max_ticks:
            self.current_tick += 1
            self._update_display()
            self.root.after(self.playback_speed, self._playback_loop)
        else:
            self.is_playing = False
            self.btn_play.config(text="▶ Play", bg="#28a745")

    def _next_tick(self):
        if self.current_tick < self.max_ticks:
            self.current_tick += 1
            self._update_display()

    def _prev_tick(self):
        if self.current_tick > 1:
            self.current_tick -= 1
            self._update_display()

if __name__ == "__main__":
    root = tk.Tk()
    # Path configuration maps straight out of repository specifications
    csv_file = "baggage-handling/live_telemetry.csv" if os.path.exists("baggage-handling/live_telemetry.csv") else "live_telemetry.csv"
    app = BSDDashboard(root, telemetry_path=csv_file)
    root.mainloop()