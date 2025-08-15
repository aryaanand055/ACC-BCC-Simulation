import matplotlib.pyplot as plt
import csv
from city import City
import numpy as numpy
import pandas as pd

def load_velocity_profiles(city_acc, city_bcc, city_accbcc):
    """Loads the velocity profiles from data files and assigns them to the cities."""
    ego_velocity_profile = []
    ego_velocity_profile_1 = []
    try:
        with open("data.csv", 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                time = float(row['time'])
                velocity = float(row['velocity'])
                ego_velocity_profile.append((time, velocity))

        # with open("data2.csv", 'r') as f:
        #     reader = csv.DictReader(f)
        #     for row in reader:
        #         time = float(row['time'])
        #         velocity = float(row['velocity'])
        #         ego_velocity_profile_1.append((time, velocity))
        
        print("Velocity profiles loaded from data1.csv")

        # Assign profiles to all city models
        city_acc.lead_velocity_profile = ego_velocity_profile
        city_acc.follower_velocity_profile = ego_velocity_profile_1

        city_bcc.lead_velocity_profile = ego_velocity_profile
        city_bcc.follower_velocity_profile = ego_velocity_profile_1

        city_accbcc.lead_velocity_profile = ego_velocity_profile
        city_accbcc.follower_velocity_profile = ego_velocity_profile_1

    except FileNotFoundError:
        print("Warning: data1.csv or data2.csv not found. Running without velocity profiles.")
        city_acc.lead_velocity_profile = []
        city_acc.follower_velocity_profile = []
        city_bcc.lead_velocity_profile = []
        city_bcc.follower_velocity_profile = []
        city_accbcc.lead_velocity_profile = []
        city_accbcc.follower_velocity_profile = []


def plot_results(city_acc, city_bcc, city_accbcc, dt, use_profiles):
    """Plots the velocity and acceleration profiles for all three models."""
    fig, axes = plt.subplots(3, 2, figsize=(18, 12), sharex='col')
    fig.suptitle('Simulation Results', fontsize=16)

    # --- Plotting function for a single model ---
    def plot_model(ax_vel, ax_acc, city, model_name):
        num_cars = len(city.cars)
        
        # Plot follower cars first
        for idx, car in enumerate(city.cars):
            if idx == 0:
                continue # Skip lead car, we'll plot it last

            time_axis = [dt * i for i in range(len(car.vel_history))]
            
            color = 'gray'
            linewidth = 0.8

            # Color car 2 green ONLY if velocity profiles are active
            if use_profiles and idx == 2:
                color = 'green'
                linewidth = 1.5

            ax_vel.plot(time_axis, car.vel_history, color=color, linewidth=linewidth)
            ax_acc.plot(time_axis, car.acc_history, color=color, linewidth=linewidth)

        # Plot the lead car (car 0) last to ensure it's on top
        if num_cars > 0:
            lead_car = city.cars[0]
            time_axis = [dt * i for i in range(len(lead_car.vel_history))]
            ax_vel.plot(time_axis, lead_car.vel_history, color='red', linewidth=1.5)
            ax_acc.plot(time_axis, lead_car.acc_history, color='red', linewidth=1.5)


        ax_vel.set_title(f"{model_name} Velocity")
        ax_vel.set_ylabel("Velocity (m/s)")
        ax_vel.grid(True)

        ax_acc.set_title(f"{model_name} Acceleration")
        ax_acc.set_ylabel("Acceleration (m/s^2)")
        ax_acc.grid(True)



    # --- Plot each model ---
    plot_model(axes[0, 0], axes[0, 1], city_acc, "ACC")
    plot_model(axes[1, 0], axes[1, 1], city_bcc, "BCC")
    plot_model(axes[2, 0], axes[2, 1], city_accbcc, "ACC + BCC Integration")

    # Set common X-axis labels
    axes[2, 0].set_xlabel("Time (s)")
    axes[2, 1].set_xlabel("Time (s)")

    plt.tight_layout(rect=[0.025, 0.025, 0.975, 0.975])
    plt.show()

def plot_energy_consumption(city_acc, city_bcc, city_accbcc):
    """Plots the total energy consumption for each model as a bar graph."""
    total_energy_acc = sum(car.energy_used for car in city_acc.cars)
    total_energy_bcc = sum(car.energy_used for car in city_bcc.cars)
    total_energy_accbcc = sum(car.energy_used for car in city_accbcc.cars)

    models = ['ACC', 'BCC', 'ACC+BCC']
    energy_values = [total_energy_acc, total_energy_bcc, total_energy_accbcc]

    plt.figure(figsize=(5.5, 6))
    bars = plt.bar(models, energy_values, color=['lightblue'], width = 0.5)
    plt.ylabel('Energy Consumption (KwH)')
    plt.title('Total Energy Consumption per Model')

    # for bar in bars:
    #     yval = bar.get_height()
    #     plt.text(bar.get_x() + bar.get_width()/4.0, yval, f'{yval:.4f}', va='bottom') # va: vertical alignment

    plt.show()

def display_gap_statistics(city_acc, city_bcc, city_accbcc):
    """Calculates and prints the final gap statistics for each model."""

    # --- ACC ---
    min_gap_acc = city_acc.overall_min_gap
    max_gap_acc = city_acc.overall_max_gap
    avg_gap_acc = sum(city_acc.all_gaps) / len(city_acc.all_gaps) if city_acc.all_gaps else 0

    # --- BCC ---
    min_gap_bcc = city_bcc.overall_min_gap
    max_gap_bcc = city_bcc.overall_max_gap
    avg_gap_bcc = sum(city_bcc.all_gaps) / len(city_bcc.all_gaps) if city_bcc.all_gaps else 0

    # --- ACC+BCC ---
    min_gap_accbcc = city_accbcc.overall_min_gap
    max_gap_accbcc = city_accbcc.overall_max_gap
    avg_gap_accbcc = sum(city_accbcc.all_gaps) / len(city_accbcc.all_gaps) if city_accbcc.all_gaps else 0
    print("Lenght: ", len(city_accbcc.all_gaps))
    print("\n--- Inter-vehicular Distance Statistics ---")
    print(f"ACC Model:")
    print(f"  - Minimum Distance: {min_gap_acc:.2f} m")
    print(f"  - Average Distance: {avg_gap_acc:.2f} m")
    print(f"  - Maximum Distance: {max_gap_acc:.2f} m")
    print("-" * 20)
    print(f"BCC Model:")
    print(f"  - Minimum Distance: {min_gap_bcc:.2f} m")
    print(f"  - Average Distance: {avg_gap_bcc:.2f} m")
    print(f"  - Maximum Distance: {max_gap_bcc:.2f} m")
    print("-" * 20)
    print(f"ACC+BCC Model:")
    print(f"  - Minimum Distance: {min_gap_accbcc:.2f} m")
    print(f"  - Average Distance: {avg_gap_accbcc:.2f} m")
    print(f"  - Maximum Distance: {max_gap_accbcc:.2f} m")
    print("-------------------------------------------\n")

import numpy as np

def get_gap_statistics(gaps):
    gaps = np.array(gaps)

    stats = {
        "min": np.min(gaps),
        "p5": np.percentile(gaps, 5),
        "p25": np.percentile(gaps, 25),
        "median": np.median(gaps),
        "mean": np.mean(gaps),
        "p75": np.percentile(gaps, 75),
        "p95": np.percentile(gaps, 95),
        "max": np.max(gaps),
        "std": np.std(gaps, ddof=1),  # sample std deviation
        "variance": np.var(gaps, ddof=1)  # sample variance
    }
    df = pd.DataFrame.from_dict(stats, orient="index", columns=["Value"])
    df.index.name = "Statistic"
    print(df.to_string(float_format="%.4f"))
    # return stats


def main():
    """Main function to run the simulation without GUI."""

    # --- Control Flag ---
    # Set this to True to use data1.csv and data2.csv, False to run without them.
    USE_VELOCITY_PROFILES = True
    
    # --- Simulation Parameters ---
    simulation_duration = 60  # Run for 60 seconds
    params = {
        "car_number": 15,
        "kd": 0.9,
        "kv": 0.6,
        "kc": 0.4,
        "v_des": 30.0,
        "max_v": 50.0,
        "min_v": 0.0,
        "min_dis": 6.0,
        "reaction_time": 0.8,
        "headway_time": 2.0,
        "max_a": 4.0,
        "min_a": -5.0,
        "min_gap": 2.0,
        "dt": 0.1
    }
    dt = params["dt"]
    num_steps = int(simulation_duration / dt)

    # --- Initialize City Models ---
    city_acc = City()
    city_bcc = City()
    city_accbcc = City()

    # Unpack params dictionary to pass as arguments
    init_args = [params[k] for k in ["car_number", "kd", "kv", "kc", "v_des", "max_v", "min_v", "min_dis", "reaction_time", "headway_time", "max_a", "min_a", "min_gap"]]

    city_acc.init(*init_args, dt=dt, model='ACC')
    city_bcc.init(*init_args, dt=dt, model='BCC')
    city_accbcc.init(*init_args, dt=dt, model='ACC+BCC')

    # --- Load Velocity Profiles (Conditional) ---
    if USE_VELOCITY_PROFILES:
        # This is crucial to replicate the scenario from the GUI
        load_velocity_profiles(city_acc, city_bcc, city_accbcc)

    # --- Run Simulation Loop ---
    print(f"Running simulation for {simulation_duration} seconds ({num_steps} steps)...")
    for step in range(num_steps):
        # Print progress every 10%
        if (step + 1) % (num_steps // 10) == 0:
            print(f"  ...Progress: {int(((step + 1) / num_steps) * 100)}%")
            
        city_acc.run(dt)
        city_bcc.run(dt)
        city_accbcc.run(dt)
    
    print("Simulation complete.")

    # --- Plot Final Results ---
    print("Generating plots...")
    plot_results(city_acc, city_bcc, city_accbcc, dt, USE_VELOCITY_PROFILES)
    plot_energy_consumption(city_acc, city_bcc, city_accbcc)
    display_gap_statistics(city_acc, city_bcc, city_accbcc)
    acc_stats = get_gap_statistics(city_acc.all_gaps)
    bcc_stats = get_gap_statistics(city_bcc.all_gaps)
    int_stats = get_gap_statistics(city_accbcc.all_gaps)

    print("ACC Stats:", acc_stats)
    print("BCC Stats:", bcc_stats)
    print("Integrated Stats:", int_stats)



if __name__ == "__main__":
    main()
