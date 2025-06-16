# Traffic Simulation: ACC and BCC Python Code

This project simulates traffic flow using car-following models, specifically Adaptive Cruise Control (ACC) and (optionally) Bilateral Cruise Control (BCC). The simulation is visualized using a Tkinter-based GUI.

## Project Structure
- `car.py`: Defines the `Car` class, representing individual vehicles and their dynamics.
- `road.py`: Defines the `Road` class, representing the road on which cars travel.
- `city.py`: Contains the `City` class, which manages the simulation, including cars, roads, and the main logic for updating vehicle states.
- `control_window.py`: The main GUI controller. Handles user input, simulation parameters, and starts/stops the simulation.
- `transportation_painter.py`: Handles visualization of the simulation using Tkinter.

## How It Works
- The simulation creates a number of cars on a circular road.
- Each car's acceleration is determined by the selected car-following model (ACC by default).
- The simulation updates car positions, velocities, and handles collisions at each time step.
- The GUI allows you to set parameters such as the number of cars, control gains (`kd`, `kv`, `kc`), desired velocity, and more.
- The simulation is visualized in real time, showing car positions and velocities.

## How to Run
1. **Requirements**: Python 3.x. No external libraries are required beyond Tkinter (included with standard Python).
2. **Start the Simulation**:
   - Run `control_window.py`:
     ```sh
     python control_window.py
     ```
   - This opens a window where you can set simulation parameters and control the simulation.
3. **Controls**:
   - **Run**: Starts the simulation with the current parameters.
   - **Stop ACC**: Stops the lead (ego) car in the ACC model.
   - **Resume ACC**: Resumes the lead car's movement.
   - You can adjust parameters such as number of cars, control gains, desired velocity, etc., before running the simulation.

## Key Parameters
- **kd**: Gap control gain (how strongly a car reacts to the distance to the car in front).
- **kv**: Relative velocity gain (how strongly a car reacts to the speed difference with the car in front).
- **kc**: Desired velocity gain (how strongly a car tries to reach the desired speed).
- **v_des**: Desired velocity for all cars.
- **reaction_time**: Time delay in driver response.
- **max_a / min_a**: Maximum and minimum allowed acceleration.

## Notes
- The BCC (Bilateral Cruise Control) model is still being worked on and will soon be published.
- The simulation uses a circular road, so cars wrap around when reaching the end.
- Visualization shows each car as a rectangle, with the lead car in red and others in blue.

## Customization
- You can modify the car-following logic in `city.py` to experiment with different traffic models.
- Adjust the visualization in `transportation_painter.py` as needed.

---
For any questions or further customization, reach out to me
