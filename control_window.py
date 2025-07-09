'''
control_window.py: Contains the ControlWindow class for managing the traffic simulation GUI.
'''


import tkinter as tk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import csv
from city import City
from transportation_painter import TransportationPainter

class ControlWindow:
    def __init__(self, master):
        self.master = master

        # Create a scrollable frame inside a canvas
        self.canvas_wrapper = tk.Canvas(master)
        self.scroll_y = tk.Scrollbar(master, orient="vertical", command=self.canvas_wrapper.yview)
        self.scroll_y.pack(side="right", fill="y")
        self.canvas_wrapper.pack(side="left", fill="both", expand=True)

        # This frame will hold all your content
        self.scrollable_frame = tk.Frame(self.canvas_wrapper)

        # Connect canvas to the scrollable frame
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas_wrapper.configure(
                scrollregion=self.canvas_wrapper.bbox("all")
            )
        )

        # Embed the frame inside the canvas
        self.canvas_wrapper.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas_wrapper.configure(yscrollcommand=self.scroll_y.set)

        # Create a panel/frame for parameter entries and buttons
        self.panel = tk.Frame(self.scrollable_frame)
        self.panel.pack()

        # Dictionary to hold entry widgets for parameters
        self.entries = {}

        # Default values for simulation parameters
        default_values = {
            "car_number": 15,
            "kd": 2.3,
            "kv": 1.5,
            "kc": 1.0,
            "v_des": 25.0,
            "max_v": 50.0,
            "min_v": 0.0,
            "min_dis": 25.0,
            "reaction_time": 0.8,
            "max_a": 4.5,
            "min_a": -9.0,
            "min_gap": 2.0,
            "dt": 0.05  
        }
        
        params = [
            ("car_number", "Number of Cars"),
            ("kd", "Gap Control Gain (kd)"),
            ("kv", "Relative Velocity Gain (kv)"),
            ("kc", "Desired Velocity Gain (kc)"),
            ("v_des", "Desired Velocity"),
            ("max_v", "Max Velocity"),
            ("min_v", "Min Velocity"),
            ("min_dis", "Min Distance Between cars (buffer distance)"),
            ("reaction_time", "Reaction Time"),
            ("max_a", "Max Acceleration"),
            ("min_a", "Min Acceleration"),
            ("min_gap", "Minimum Gap Between Cars (for collision check)"),
            ("dt", "Simulation Time Step (dt)")  
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

        # Btn for graphs
        self.plot_button = tk.Button(self.panel, text="Plot Velocity Profiles", command=self.plot_velocities)
        self.plot_button.grid(row=len(params)+2, column=1)
        
        # Create a City instance for ACC 
        self.city_acc = City()
        self.city_bcc = City()

        # Visualization for ACC (top)
        self.painter_acc = TransportationPainter(self.scrollable_frame, self.city_acc.roads, self.city_acc.cars, width=1500, height=300, bg='white')
        self.painter_acc.pack()
        tk.Label(self.scrollable_frame, text="ACC").pack()
        self.energy_label_acc = tk.Label(self.scrollable_frame, text="Total Energy : 0 KwH", font=("Arial", 10, "bold"))
        self.energy_label_acc.pack()

        # # Visualization for BCC (bottom)
        self.painter_bcc = TransportationPainter(self.scrollable_frame, self.city_bcc.roads, self.city_bcc.cars, width=1500, height=300, bg='white')
        self.painter_bcc.pack()
        tk.Label(self.scrollable_frame, text="BCC").pack()
        self.energy_label_bcc = tk.Label(self.scrollable_frame, text="Total Energy : 0 KwH", font=("Arial", 10, "bold"))
        self.energy_label_bcc.pack()

        self.fig_acc = Figure(figsize=(7, 2.5), dpi=100)
        self.ax_acc = self.fig_acc.add_subplot(111)
        self.ax_acc.set_title("ACC Velocity Profiles")
        self.ax_acc.set_xlabel("Time (s)")
        self.ax_acc.set_ylabel("Velocity")

        self.canvas_acc = FigureCanvasTkAgg(self.fig_acc, self.scrollable_frame)
        self.canvas_acc.get_tk_widget().pack()

        self.fig_bcc = Figure(figsize=(7, 2.5), dpi=100)
        self.ax_bcc = self.fig_bcc.add_subplot(111)
        self.ax_bcc.set_title("BCC Velocity Profiles")
        self.ax_bcc.set_xlabel("Time (s)")
        self.ax_bcc.set_ylabel("Velocity")

        self.canvas_bcc = FigureCanvasTkAgg(self.fig_bcc, self.scrollable_frame)
        self.canvas_bcc.get_tk_widget().pack()

        # Timer for simulation updates
        self.timer = None

        # Flags to control leader stop for ACC and BCC
        self.leader_stop_acc = False
        self.leader_stop_bcc = False

        self.dt = default_values["dt"] 

    
    def load_velocity_profile(self, filename="data.csv"):
        self.ego_velocity_profile = []
        with open(filename, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                time = float(row['time'])
                velocity = float(row['velocity'])
                self.ego_velocity_profile.append((time, velocity))
        print("Velocity profile loaded from", filename)


    def run_simulation(self):
       # Get parameter values from entry fields
        args = []
        for key in ["car_number", "kd", "kv", "kc", "v_des", "max_v", "min_v", "min_dis","reaction_time", "max_a", "min_a", "min_gap", "dt"]:
            val = self.entries[key].get()
            try:
                val = float(val) if '.' in val or 'e' in val.lower() else int(val)
            except Exception:
                val = 0
            args.append(val)

        self.dt = args[-1]  # Set self.dt from user input

        self.city_acc = City()
        self.city_bcc = City()

        # Initialize cities with parameters for ACC and BCC models, including dt
        self.city_acc.init(*args[:-1], dt=self.dt, model='ACC')
        self.city_bcc.init(*args[:-1], dt=self.dt, model='BCC')

        # Update painters with new city elements
        self.painter_acc.set_elements(self.city_acc.roads, self.city_acc.cars)
        self.painter_bcc.set_elements(self.city_bcc.roads, self.city_bcc.cars)

        # Reset leader stop flags
        self.leader_stop_acc = False
        self.leader_stop_bcc = False

        # Load velocity profile from CSV file
        # self.load_velocity_profile()
        # self.city_acc.ego_velocity_profile = self.ego_velocity_profile
        # self.city_bcc.ego_velocity_profile = self.ego_velocity_profile

        # Start simulation timer
        self.start_timer()

    def start_timer(self):
        # Cancel previous timer if exists, then start updating simulation
        if self.timer:
            self.master.after_cancel(self.timer)
        self.update_simulation()

    def plot_velocities(self):
        dt = self.dt  # Use the same constant dt

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

        # ACC Plot
        for idx, car in enumerate(self.city_acc.cars):
            time_axis = [dt * i for i in range(len(car.vel_history))]
            ax1.plot(time_axis, car.vel_history, label=f"Car {idx+1}")
        ax1.set_title("ACC Velocity Profiles")
        ax1.set_ylabel("Velocity (units/s)")
        ax1.legend(fontsize="small", loc="upper right")
        ax1.grid(True)

        # BCC Plot
        for idx, car in enumerate(self.city_bcc.cars):
            time_axis = [dt * i for i in range(len(car.vel_history))]
            ax2.plot(time_axis, car.vel_history, label=f"Car {idx+1}")
        ax2.set_title("BCC Velocity Profiles")
        ax2.set_xlabel("Time (s)")
        ax2.set_ylabel("Velocity (units/s)")
        ax2.legend(fontsize="small", loc="upper right")
        ax2.grid(True)

        plt.tight_layout()
        plt.show()

    def update_live_graphs(self):
        dt = self.dt  # Use the same constant dt

        # ACC Graph 
        self.ax_acc.clear()
        self.ax_acc.set_title("ACC Velocity Profiles")
        self.ax_acc.set_xlabel("Time (s)")
        self.ax_acc.set_ylabel("Velocity")

        for idx, car in enumerate(self.city_acc.cars):
            steps = len(car.vel_history)
            time_axis = [dt * i for i in range(steps)]
            self.ax_acc.plot(time_axis, car.vel_history, label=f"Car {idx+1}")

        self.ax_acc.legend(fontsize="xx-small", loc="upper right")
        self.ax_acc.grid(True)
        self.canvas_acc.draw()

        # BCC Graph
        self.ax_bcc.clear()
        self.ax_bcc.set_title("BCC Velocity Profiles")
        self.ax_bcc.set_xlabel("Time (s)")
        self.ax_bcc.set_ylabel("Velocity")

        for idx, car in enumerate(self.city_bcc.cars):
            steps = len(car.vel_history)
            time_axis = [dt * i for i in range(steps)]
            self.ax_bcc.plot(time_axis, car.vel_history, label=f"Car {idx+1}")

        self.ax_bcc.legend(fontsize="xx-small", loc="upper right")
        self.ax_bcc.grid(True)
        self.canvas_bcc.draw()

    def update_simulation(self):
        dt = self.dt 

        # Set leader stop flags for both cities
        self.city_acc.set_leader_stop(self.leader_stop_acc)
        self.city_bcc.set_leader_stop(self.leader_stop_bcc)

        # Run simulation step for both cities with fixed dt
        self.city_acc.run(dt)
        self.city_bcc.run(dt)

        # Update painters with new city elements
        self.painter_acc.set_elements(self.city_acc.roads, self.city_acc.cars)
        self.painter_bcc.set_elements(self.city_bcc.roads, self.city_bcc.cars)

        # Redraw the visualizations
        self.painter_acc.repaint()
        self.painter_bcc.repaint()

        # Update live graphs with velocity profiles
        # Comment the below line to disable live graph and improve simulation performance
        # self.update_live_graphs()
        
        # Calculate total energy
        total_energy_acc = sum(car.energy_used for car in self.city_acc.cars)
        total_energy_bcc = sum(car.energy_used for car in self.city_bcc.cars)
        
        # Update label texts
        self.energy_label_acc.config(text=f"Total Energy : {total_energy_acc:.4f} KwH")
        self.energy_label_bcc.config(text=f"Total Energy : {total_energy_bcc:.4f} KwH")


        # Schedule next update for 0.1 seconds later (100 ms)
        self.timer = self.master.after(int(dt*1000), self.update_simulation)

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
