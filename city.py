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
        self.mode = 'BCC'
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
            car_length = 4
            headway = min_dis + velocity * reaction_time
            pos = 1000 - (car_number - 1 -i) * (car_length + headway) 
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
        self.initial_v_des = v_des
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

    def set_follower_stop(self, follower_stop):
        self.follower_stop = follower_stop

    # Main code to calculate acclerattion
    def driver_decision(self):
        road_length = self.roads[0].length if self.roads else 1000
        dt = self.dt
        car_states = [(c.pos, c.velocity) for c in self.cars]

        for idx, car in enumerate(self.cars):
            self.v_des = 0 if (getattr(self, 'follower_stop', False) and idx == 2) else self.initial_v_des
          

            if idx == 0:
                if getattr(self, 'leader_stop', False):
                    acc = self.kc * (0 - car.velocity)
                    acc = max(self.min_a, min(self.max_a, acc))
                    car.acceleration = acc
                    continue

                if hasattr(self, 'lead_velocity_profile') and self.lead_velocity_profile:
                    time = round(self.step_count * dt, 3)
                    for i in range(len(self.lead_velocity_profile)-1):
                        t1,v1 = self.lead_velocity_profile[i]
                        t2, v2 = self.lead_velocity_profile[i+1]
                        if t1 <= time <= t2:
                            alpha = (time - t1) / (t2 - t1)
                            target_velocity = v1 + alpha * (v2 - v1)
                            current_velocity = car.velocity
                            acc = (target_velocity - current_velocity) / dt
                            car.acceleration = max(self.min_a, min(self.max_a, acc))
                            break
                    else:
                        # If time exceeds profile, maintain last velocity
                        t1, v1 = self.lead_velocity_profile[-1]
                        target_velocity = v1
                        current_velocity = car.velocity
                        acc = (target_velocity - current_velocity) / dt
                        acc = max(self.min_a, min(self.max_a, acc))
                        car.acceleration = acc
                else:
                    # Try to reach v_des if no velocity profile
                    acc = self.kc * (self.v_des - car.velocity)
                    acc = max(self.min_a, min(self.max_a, acc))
                    car.acceleration = acc
                continue
            if idx == 2:
                if getattr(self, 'follower_stop', False):
                    acc = self.kc * (0 - car.velocity)
                    acc = max(self.min_a, min(self.max_a, acc))
                    car.acceleration = acc
                    car.mode = "VEL"
                    continue
                
                if hasattr(self, 'lead_velocity_profile') and self.lead_velocity_profile:
                    time = round(self.step_count * dt, 3)
                    for i in range(len(self.follower_velocity_profile)-1):
                        t1,v1 = self.follower_velocity_profile[i]
                        t2, v2 = self.follower_velocity_profile[i+1]
                        if t1 <= time <= t2:
                            alpha = (time - t1) / (t2 - t1)
                            target_velocity = v1 + alpha * (v2 - v1)
                            current_velocity = car.velocity
                            acc = (target_velocity - current_velocity) / dt
                            car.acceleration = max(self.min_a, min(self.max_a, acc))
                            break
                    else:
                        # If time exceeds profile, maintain last velocity
                        t1, v1 = self.follower_velocity_profile[-1]
                        target_velocity = v1
                        current_velocity = car.velocity
                        acc = (target_velocity - current_velocity) / dt
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

            if self.model == 'ACC' or (self.model == 'BCC' and idx == len(self.cars) - 1):
                car.mode = 'ACC'
                # Active Cruise Control: only consider the car in front
                car_pos, car_vel = car_states[idx]
                front_idx = self.cars.index(front_car)
                front_car_pos, front_car_vel = car_states[front_idx]
                gap = (car_pos - front_car_pos - car.length ) % road_length
                rel_v = front_car_vel - car_vel
                desired_gap = self.min_dis + car_vel * self.reaction_time
                acc = 0.5 * self.kd * (gap - desired_gap) + 0.5 * self.kv * rel_v
                acc = max(self.min_a, min(self.max_a, acc))
                car.acceleration = acc
            elif self.model == 'BCC':        
                car.mode = 'BCC'        
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

            elif self.model == 'ACC+BCC':
                self.mode = "INTEGRATED"
                ve = car.velocity
                vl = front_car.velocity
                vf = back_car.velocity
                ae = abs(self.min_a)
                af = ae * 0.7  
                Tr = self.reaction_time
                Le = car.length
                Lb = self.min_gap

                Gfront_min = ve * Tr + ((ve - vl) ** 2) / (2 * ae) + Lb
                Grear_min = vf * Tr + ((vf - ve) ** 2) / (2 * af) + Lb

                X = Gfront_min + Le + Grear_min

                car_pos, car_vel = car_states[idx]
                front_idx = self.cars.index(front_car)
                front_car_pos, front_car_vel = car_states[front_idx]
                back_idx = self.cars.index(back_car)
                back_car_pos, back_car_vel = car_states[back_idx]

                front_gap = abs((car_pos - front_car_pos - front_car.length) % road_length)
                back_gap = abs((back_car_pos - car_pos - car.length) % road_length)


                car.integration_factor = self.calculate_integration_factor(front_gap, back_gap, X, car, front_car,back_car)
                iF = car.integration_factor
                # print(f"IF: {iF:.2f}")
                desired_gap = self.min_dis + car_vel * self.reaction_time

                front_gap = abs((car_pos - front_car_pos - front_car.length) % road_length)
                back_gap = abs((back_car_pos - car_pos - car.length) % road_length)

                gap_factor = 0.5 * self.kd * (front_gap - desired_gap) + iF * 0.5 * self.kd * (desired_gap - back_gap)
                velocity_factor =  0.5 * self.kv * (front_car_vel - car_vel) + iF * 0.5 * self.kv * (back_car_vel - car_vel)
                
                acc = velocity_factor + gap_factor
                acc = max(self.min_a, min(self.max_a, acc))
                car.acceleration = acc
                   

    def calculate_integration_factor(self, front_gap, back_gap, X, car, front_car, rear_car):
        """
        Advanced integration factor:
          - More factors: gaps, relative speeds, rear car behavior
          - Smooth hysteresis
        """
        # 1) Gap ratios
        back_ratio = (back_gap - X) / X
        front_ratio = (front_gap - X) / X

        # 2) Rear deceleration factor
        # If rear car is braking hard → push towards BCC
        rear_brake_ratio = 0.0
        if rear_car.acceleration < 0:
            # Normalize braking: say -2 m/s2 is strong
            rear_brake_ratio = min(1, rear_car.acceleration / 2.0)

        # 3) Relative velocity factor
        # If closing on front car fast → push towards ACC
        rel_vel_front = car.velocity - front_car.velocity 
        closing_ratio = max(0, min(1, rel_vel_front / 10.0))  
        
        # 4) Weighted sum
        w_back = 0.3
        w_front = 0.3
        w_rear_brake = 0.3
        w_closing = 0.1
        raw_iF = (
            - w_back * back_ratio
            - w_front * front_ratio
            - w_rear_brake * rear_brake_ratio
            - w_closing * closing_ratio
        )  

        # 5) Clamp to [0, 1]
        raw_iF = max(0, min(1, raw_iF))

        # 5) Smooth with hysteresis
        old_iF = getattr(car, 'integration_factor', 0)
        alpha = self.dt / (0.5 + self.dt)
        smoothed_iF = (1 - alpha) * old_iF + alpha * raw_iF
        car.integration_factor = smoothed_iF
        print(f"back_ratio: {back_ratio:.2f}, front_ratio: {front_ratio:.2f}, rear_brake_ratio: {rear_brake_ratio:.2f}, closing_ratio: {closing_ratio:.2f}, IF: {car.integration_factor:.2f}")

        # 6) Mode switch for visualization
        if smoothed_iF < 0.2:
            car.mode = 'ACC'
        elif smoothed_iF > 0.8:
            car.mode = 'BCC'
        else:
            car.mode = 'INTEGRATED'
        return smoothed_iF

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
            if car == next_car:
                continue
            min_gap = self.min_gap  # Use instance parameter

            # Calculate gap considering circular road
            hasCollided = ((next_car.pos - car.pos) % road_length) <= car.length
            if hasCollided:
                v1 = car.velocity
                v2 = next_car.velocity
                e = car.CoR if hasattr(car, 'CoR') else 0.3

                # Prevent overlap: set next_car just behind car with an addition of min_gap
                car.velocity = ((1 - e) * v1 + (1 + e) * v2) / 2
                next_car.velocity = ((1 - e) * v2 + (1 + e) * v1) / 2

                next_car.pos = (car.pos + car.length + min_gap) % road_length

                # Change color to indicate collision and start timer
                car.color = 'orange'
                next_car.color = 'orange'
                car.collision_timer = 40  # 40 steps * 0.1s = 4 seconds
                next_car.collision_timer = 40
    
     