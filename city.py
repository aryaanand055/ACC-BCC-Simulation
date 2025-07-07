'''
City .py: Contains the City class for managing the traffic simulation.
'''

from car import Car
from road import Road

class City:
    def __init__(self):
        self.cars = []
        self.roads = []
        self.step_count = 0
        self.model = 'ACC'  
        self.min_gap = 5.0 
        self.dt = 0.1 

    def init(self, car_number, kd, kv, kc, v_des, max_v, min_v, min_dis, reaction_time, max_a, min_a, min_gap=5.0, dt=0.1, model='ACC'):
        # Reset simulation state
        self.cars.clear()
        self.roads.clear()
        self.step_count = 0
        self.model = model
        self.dt = dt

        # Create a single straight road for simplicity
        road = Road(1000, 0, 0, 1, 0)
        self.roads.append(road)

        # Place cars at intervals along the road
        for i in range(int(car_number)):
            # Initial velocity, position, and sizeof each car
            velocity = 0
            car_length = 5
            headway = min_dis + velocity * reaction_time
            pos = i * (car_length + headway) 
            if i == 0:
                color = 'red'  
            elif i == car_number - 1:
                color = 'green'
            else:
                color = 'blue'
            car = Car(length=car_length, color=color, pos=pos,min_dis=min_dis, velocity=velocity, acceleration=0, current_road=road)
            car.original_color = color  
            car.collision_timer = 0
            self.cars.append(car)
            road.enter_road(car)

        # Store model parameters
        self.kd = kd
        self.kv = kv
        self.kc = kc
        self.v_des = v_des
        self.max_v = max_v
        self.min_v = min_v
        self.reaction_time = reaction_time
        self.max_a = max_a
        self.min_a = min_a
        self.min_dis = min_dis
        self.min_gap = min_gap

    def run(self, dt=None):
        # Run one simulation step with real dt
        if dt is None:
            dt = self.dt
        self.driver_decision()
        self.move_forward(dt)
        self.step_count += 1

    def set_leader_stop(self, leader_stop):
        self.leader_stop = leader_stop

    # Main code to calculate acclerattion
    def driver_decision(self):
        road_length = self.roads[0].length if self.roads else 1000
        dt = self.dt
        car_states = [(c.pos, c.velocity) for c in self.cars]

        for idx, car in enumerate(self.cars):
            if idx == 0 and hasattr(self, 'leader_stop') and self.leader_stop:
                # Ego vehicle: decelerate to stop if leader_stop is set
                acc = self.min_a
                car.acceleration = acc
                if car.velocity + acc * dt < 0:
                    car.velocity = 0
                    car.acceleration = 0
                continue
            if idx == 0:
                if hasattr(self, 'ego_velocity_profile') and self.ego_velocity_profile:
                    time = round(self.step_count * dt, 3)
                    for i in range(len(self.ego_velocity_profile)-1):
                        t1,v1 = self.ego_velocity_profile[i]
                        t2, v2 = self.ego_velocity_profile[i+1]
                        if t1 <= time <= t2:
                            alpha = (time - t1) / (t2 - t1)
                            target_velocity = v1 + alpha * (v2 - v1)
                            current_velocity = car.velocity
                            acc = (target_velocity - current_velocity) / dt
                            car.acceleration = max(self.min_a, min(self.max_a, acc))
                            break
                    else:
                        # If time exceeds profile, maintain last velocity
                        t1, v1 = self.ego_velocity_profile[-1]
                        target_velocity = v1
                        current_velocity = car.velocity
                        acc = (target_velocity - current_velocity) / dt
                        acc = max(self.min_a, min(self.max_a, acc))
                        car.acceleration = acc
                else:
                    # Ego vehicle: try to reach desired velocity
                    acc = self.kc * (self.v_des - car.velocity)
                    acc = max(self.min_a, min(self.max_a, acc))
                    car.acceleration = acc
                continue

            # Find the car ahead and behind on the same road (circular road)
            
            cars_same_road = [c for c in self.cars if c.current_road == car.current_road and c != car]

            def gap_to(other):
                return (car.pos - other.pos) % road_length
            
            front_car = min(cars_same_road, key=gap_to, default=None) if cars_same_road else None

            def gap_from(other):
                return (other.pos - car.pos) % road_length
            
            back_car = min(cars_same_road, key=gap_from, default=None) if cars_same_road else None

            if self.model == 'ACC':
                # Active Cruise Control: only consider the car in front
                if front_car:
                    car_pos, car_vel = car_states[idx]
                    front_idx = self.cars.index(front_car)
                    front_car_pos, front_car_vel = car_states[front_idx]

                    gap = (car_pos - front_car_pos - car.length ) % road_length
                    rel_v = front_car_vel - car_vel
                    desired_gap = self.min_dis + car_vel * self.reaction_time
                    acc = 0.5 * self.kd * (gap - desired_gap) + 0.5 * self.kv * rel_v
                    acc = max(self.min_a, min(self.max_a, acc))
                    car.acceleration = acc
                else:
                    # No car ahead: accelerate towards desired velocity
                    acc = self.kc * (self.v_des - car.velocity)
                    acc = max(self.min_a, min(self.max_a, acc))
                    car.acceleration = acc
            elif self.model == 'BCC':
                # For the last car, use ACC logic
                if idx == len(self.cars) - 1:
                    if front_car:
                        car_pos, car_vel = car_states[idx]
                        front_idx = self.cars.index(front_car)
                        front_car_pos, front_car_vel = car_states[front_idx]
                        gap = (car_pos - front_car_pos - car.length ) % road_length
                        rel_v = front_car_vel - car_vel
                        desired_gap = self.min_dis + car_vel * self.reaction_time
                        acc = 0.5 * self.kd * (gap - desired_gap) + 0.5 * self.kv * rel_v
                        acc = max(self.min_a, min(self.max_a, acc))
                        car.acceleration = acc
                    else:
                        acc = self.kc * (self.v_des - car.velocity)
                        acc = max(self.min_a, min(self.max_a, acc))
                        car.acceleration = acc
                # Otherwise, use BCC logic
                elif front_car and back_car:
                    car_pos, car_vel = car_states[idx]
                    front_idx = self.cars.index(front_car)
                    front_car_pos, front_car_vel = car_states[front_idx]
                    back_idx = self.cars.index(back_car)
                    back_car_pos, back_car_vel = car_states[back_idx]

                    desired_gap = self.min_dis + car_vel * self.reaction_time

                    front_gap = abs((car_pos - front_car_pos - front_car.length) % road_length)
                    back_gap = abs((back_car_pos - car_pos - car.length) % road_length)

                    gap_factor = 0.5 * self.kd * (front_gap - desired_gap) + 0.5 * self.kd * (desired_gap - back_gap)
                    velocity_factor = 0.5 * self.kv * (front_car_vel - car_vel) + 0.5 * self.kv * (back_car_vel - car_vel)

                    acc = velocity_factor + gap_factor
                    acc = max(self.min_a, min(self.max_a, acc))
                    car.acceleration = acc
                else:
                    acc = self.kc * (self.v_des - car.velocity)
                    acc = max(self.min_a, min(self.max_a, acc))
                    car.acceleration = acc
                    


       
    def move_forward(self, dt=None):
        if dt is None:
            dt = self.dt
        # Move all cars forward based on their velocity and acceleration
        for car in self.cars:
            car.update(dt)
            # Clamp velocity to not exceed max_v
            car.velocity = max(self.min_v, min(car.velocity, self.max_v))

            # Fade collision color if timer is active
            if hasattr(car, 'collision_timer') and car.collision_timer > 0:
                car.collision_timer -= 1
                if car.collision_timer == 0:
                    car.color = car.original_color
        # Handle any collisions that may have occurred
        self.handle_collisions()

    def handle_collisions(self):
        # Sort cars by position to check for overlaps (circular road)
        road_length = self.roads[0].length if self.roads else 1000
        sorted_cars = sorted(self.cars, key=lambda c: c.pos)
        for i, car in enumerate(sorted_cars):
            next_car = sorted_cars[(i + 1) % len(sorted_cars)]

            # Calculate gap considering circular road
            gap = (next_car.pos - car.pos - car.length) % road_length
            min_gap = self.min_gap  # Use instance parameter
            if gap < car.length :
                # Prevent overlap: set next_car just behind car, match velocities
                next_car.pos = (car.pos + car.length + min_gap) % road_length
                avg_v = (car.velocity + next_car.velocity) / 2
                car.velocity = avg_v
                next_car.velocity = avg_v
                
                # Change color to indicate collision and start timer
                car.color = 'orange'
                next_car.color = 'orange'
                car.collision_timer = 40  # 40 steps * 0.1s = 4 seconds
                next_car.collision_timer = 40
