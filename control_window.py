import tkinter as tk
from city import City
from transportation_painter import TransportationPainter

class ControlWindow:
    def __init__(self, master):
        self.master = master

        # Create a panel/frame for parameter entries and buttons
        self.panel = tk.Frame(master)
        self.panel.pack()

        # Dictionary to hold entry widgets for parameters
        self.entries = {}

        # Default values for simulation parameters
        default_values = {
            "car_number": 15,
            "kd": 0.5,
            "kv": 0.5,
            "kc": 0.5,
            "v_des": 30.0,
            "max_v": 44.0,
            "min_v": 0.0,
            "min_dis": 15.0,
            "reaction_time": 1.0,
            "max_a": 3.0,
            "min_a": -3.0,
            # "ttc_inverse": 10.0,
            "min_gap": 5.0
        }
        
        params = [
            ("car_number", "Number of Cars"),
            ("kd", "Gap Control Gain (kd)"),
            ("kv", "Relative Velocity Gain (kv)"),
            ("kc", "Desired Velocity Gain (kc)"),
            ("v_des", "Desired Velocity"),
            ("max_v", "Max Velocity"),
            ("min_v", "Min Velocity"),
            ("min_dis", "Min Distance"),
            ("reaction_time", "Reaction Time"),
            ("max_a", "Max Acceleration"),
            ("min_a", "Min Acceleration"),
            ("min_gap", "Minimum Gap Between Cars (min_gap)")
        ]

        # Create label and entry for each parameter
        for i, (key, label) in enumerate(params):
            tk.Label(self.panel, text=label).grid(row=i, column=0)
            entry = tk.Entry(self.panel)
            entry.grid(row=i, column=1)
            entry.insert(0, str(default_values.get(key, "")))
            self.entries[key] = entry

        # Buttons for running, stopping, and resuming simulations
        self.run_button = tk.Button(self.panel, text="Run", command=self.run_simulation)
        self.run_button.grid(row=len(params), column=0)
        self.stop_button_acc = tk.Button(self.panel, text="Stop Ego", command=lambda: self.stop_simulation())
        self.stop_button_acc.grid(row=len(params), column=1)
        self.resume_button_acc = tk.Button(self.panel, text="Resume Ego", command=lambda: self.resume_simulation())
        self.resume_button_acc.grid(row=len(params), column=2)
        # self.stop_button_bcc = tk.Button(self.panel, text="Stop BCC", command=lambda: self.stop_simulation('BCC'))
        # self.stop_button_bcc.grid(row=len(params)+1, column=1)
        # self.resume_button_bcc = tk.Button(self.panel, text="Resume BCC", command=lambda: self.resume_simulation('BCC'))
        # self.resume_button_bcc.grid(row=len(params)+1, column=2)

        # Create a City instance for ACC 
        self.city_acc = City()
        self.city_bcc = City()

        # Visualization for ACC (top)
        self.painter_acc = TransportationPainter(master, self.city_acc.roads, self.city_acc.cars, width=1500, height=300, bg='white')
        self.painter_acc.pack()
        tk.Label(master, text="ACC").pack()

        # # Visualization for BCC (bottom)
        self.painter_bcc = TransportationPainter(master, self.city_bcc.roads, self.city_bcc.cars, width=1500, height=300, bg='white')
        self.painter_bcc.pack()
        tk.Label(master, text="BCC").pack()
        
        # Timer for simulation updates
        self.timer = None

        # Flags to control leader stop for ACC and BCC
        self.leader_stop_acc = False
        self.leader_stop_bcc = False

    def run_simulation(self):
        # Get parameter values from entry fields
        args = []
        for key in ["car_number", "kd", "kv", "kc", "v_des", "max_v", "min_v", "min_dis","reaction_time", "max_a", "min_a", "min_gap"]:
            val = self.entries[key].get()
            try:
                val = float(val) if '.' in val or 'e' in val.lower() else int(val)
            except Exception:
                val = 0
            args.append(val)

    
        
        self.city_acc = City()
        self.city_bcc = City()

        # Initialize cities with parameters for ACC and BCC models
        self.city_acc.init(*args, model='ACC')
        self.city_bcc.init(*args, model='BCC')

        # Update painters with new city elements
        self.painter_acc.set_elements(self.city_acc.roads, self.city_acc.cars)
        self.painter_bcc.set_elements(self.city_bcc.roads, self.city_bcc.cars)

        # Reset leader stop flags
        self.leader_stop_acc = False
        self.leader_stop_bcc = False

        # Start simulation timer
        self.start_timer()

    def start_timer(self):
        # Cancel previous timer if exists, then start updating simulation
        if self.timer:
            self.master.after_cancel(self.timer)
        self.update_simulation()

    def update_simulation(self):
        # Set leader stop flags for both cities
        self.city_acc.set_leader_stop(self.leader_stop_acc)
        self.city_bcc.set_leader_stop(self.leader_stop_bcc)

        # Run simulation step for both cities
        self.city_acc.run()
        self.city_bcc.run()

        # Update painters with new city elements
        self.painter_acc.set_elements(self.city_acc.roads, self.city_acc.cars)
        self.painter_bcc.set_elements(self.city_bcc.roads, self.city_bcc.cars)

        # Redraw the visualizations
        self.painter_acc.repaint()
        self.painter_bcc.repaint()

        # Schedule next update
        self.timer = self.master.after(50, self.update_simulation)

    def stop_simulation(self):
        self.leader_stop_acc = True
        self.leader_stop_bcc = True

    def resume_simulation(self):
        self.leader_stop_acc = False
        self.leader_stop_bcc = False

if __name__ == "__main__":
    # Create main window and start the application
    root = tk.Tk()
    root.title("Traffic Simulation Control Window")
    app = ControlWindow(root)
    root.mainloop()
