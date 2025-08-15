# Traffic Simulation: ACC and BCC Python Code

This project simulates traffic flow using car-following models, including Adaptive Cruise Control (ACC), Bilateral Cruise Control (BCC), and an advanced integrated model of ACC + BCC. The simulation is designed to be highly realistic, using established formulas for vehicle dynamics and energy consumption. It can be run with a Tkinter-based GUI for real-time visualization or in a headless command-line mode for in-depth analysis.

-----

## Project Structure

  - `car.py`: Defines the `Car` class, representing individual vehicles. It contains the core physics for movement and energy consumption.
  - `city.py`: Contains the `City` class, which manages the entire simulation. It implements the logic for the three car-following models (ACC, BCC, and the integrated ACC+BCC model).
  - `control_window.py`: The main GUI controller. It allows for user input of simulation parameters and provides real-time, side-by-side visualization of all three models.
  - `run_headless.py`: A new script for running the simulation without a GUI, specifically for data analysis and plotting.
  - `road.py`: Defines the `Road` class, representing the circular road on which cars travel.
  - `transportation_painter.py`: Handles the visualization of the simulation in the GUI.
  - `data.csv`, `data1.csv`, `data2.csv`, `data (km - hr).csv`: Optional files used for providing custom velocity profiles for the lead and follower cars.

-----

## How It Works

The simulation places a number of cars on a circular road. Each car's movement is calculated at each time step using standard kinematic formulas: `S = ut + 0.5at^2` for displacement and `v = u + at` for velocity.

### Car-Following Models

The core of the simulation is in the car-following models, which determine each car's acceleration.

  - **Adaptive Cruise Control (ACC)**: The car's acceleration is a function of the gap to the car in front and the relative velocity between the two cars.
  - **Bilateral Cruise Control (BCC)**: This model considers both the car in front and the car behind. It aims to maintain an equal gap between both vehicles by adjusting acceleration based on both front and rear gaps and relative velocities. The last car in the chain always defaults to the ACC model for stability.
  - **ACC+BCC Integration**: This advanced model dynamically calculates an "integration factor" based on multiple factors like gaps, relative speeds, and the rear car's braking behavior. This factor smoothly transitions a car's behavior between ACC and BCC logic to adapt to different traffic conditions.

### Energy Consumption

Energy consumption is calculated using a formula that accounts for the total forces acting on the car, including:

  - **Inertia Force**: `mass * acceleration`
  - **Rolling Resistance Force**: `Cr * mass * gravity`
  - **Drag Force**: `0.5 * Cd * air_density * frontal_area * velocity^2`

The total energy used in kWh is accumulated over the simulation run.

### Collision Detection

A crash is indicated by the car turning **orange**, and the simulation handles the collision by adjusting the positions and velocities of the involved cars based on a coefficient of restitution.

-----

## How to Run

1.  **Requirements**: Python 3.x. The GUI version requires `tkinter` (included with standard Python). The headless version requires `matplotlib`, `numpy`, and `pandas`.
2.  **Start the Simulation with GUI**:
    ```sh
    python control_window.py
    ```
    This opens a window where you can set simulation parameters and control the simulation. The three models are visualized side-by-side.
3.  **Run Headless Simulation**:
    ```sh
    python run_headless.py
    ```
    This will run a 60-second simulation with default parameters and generate plots and statistics upon completion.

-----

## Plots and Data Analysis

The simulation provides various data points and plots to analyze the performance of the different car-following models.

### Plots

  - **Velocity and Acceleration Profiles**: Both the GUI and the headless script can generate plots showing the velocity and acceleration history of each car over the duration of the simulation. This is crucial for comparing the stability and responsiveness of the ACC, BCC, and integrated models.
  - **Energy Consumption Bar Chart**: The headless script generates a bar graph comparing the total energy consumption of the three models.

### Data Obtained

  - **Real-time Energy**: The GUI displays the total energy consumption for each model in real-time.
  - **Inter-vehicular Gap Statistics**: The headless script provides a detailed statistical summary of the gaps between cars throughout the simulation. This includes:
      - Minimum, average, and maximum distances.
      - Key percentiles (p5, p25, median, p75, p95).
      - Standard deviation and variance of the gaps.
