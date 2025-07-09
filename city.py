'''
city.py: Contains the City class for managing the traffic simulation.
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
        self.ego_lane = 0  # Ego vehicle starts in lane 0

    def init(self, car_number, kd, kv, kc, v_des, max_v, min_v, min_dis, reaction_time, max_a, min_a, min_gap=5.0, dt=0.1, model='ACC'):
        # Reset simulation state
        self.cars.clear()
        self.roads.clear()
        self.step_count = 0
        self.model = model
        self.dt = dt
        self.min_gap = min_gap

        # Create a road with 2 lanes
        road = Road(1000, 0, 0, 1, 0, num_lanes=2)
        self.roads.append(road)

        # Place cars at intervals, alternating lanes
        for i in range(int(car_number)):
            velocity = 0
            car_length = 5
            headway = min_dis + velocity * reaction_time
            pos = i * (car_length + headway)
            lane_id = 0 if i % 2 == 0 else 1  # Alternate lanes
            color = 'red' if i == 0 else 'green' if i == car_number - 1 else 'blue'
            car = Car(length=car_length, color=color, pos=pos, min_dis=min_dis, velocity=velocity, acceleration=0, current_road=road)
            car.original_color = color
            car.collision_timer = 0
            car.lane_id = lane_id
            self.cars.append(car)
            road.enter_road(car, lane_id)

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

    def calculate_front_gap(self, v_e, v_l):
        a_e = self.max_a
        t_r = self.reaction_time
        l_buffer = 3.0
        k_mix = 1.5
        term1 = v_e * t_r
        term2 = 0 if v_e <= v_l else (v_e - v_l)**2 / (2 * a_e)
        return (term1 + term2 + l_buffer) * k_mix

    def calculate_rear_gap(self, v_f, v_e):
        a_f = 2.5
        t_r = self.reaction_time
        l_buffer = 3.0
        k_mix = 1.5
        term1 = v_f * t_r
        term2 = 0 if v_f <= v_e else (v_f - v_e)**2 / (2 * a_f)
        return (term1 + term2 + l_buffer) * k_mix

    def calculate_total_required_gap(self, v_e, v_l, v_f):
        g_front_min = self.calculate_front_gap(v_e, v_l)
        g_rear_min = self.calculate_rear_gap(v_f, v_e)
        l_e = self.cars[0].length
        return g_front_min + l_e + g_rear_min

    def get_practical_gaps(self, ego_car, target_lane_id):
        road_length = self.roads[0].length
        target_lane_cars = self.roads[0].get_cars_in_lane(target_lane_id)
        
        if not target_lane_cars:
            return float('inf'), float('inf'), float('inf'), None, None
        
        def gap_to(other):
            return (ego_car.pos - other.pos) % road_length
        
        def gap_from(other):
            return (other.pos - ego_car.pos) % road_length
        
        front_car = min(target_lane_cars, key=gap_to, default=None) if target_lane_cars else None
        back_car = min(target_lane_cars, key=gap_from, default=None) if target_lane_cars else None
        
        g_lead = float('inf') if not front_car else (ego_car.pos - front_car.pos - ego_car.length) % road_length
        g_follow = float('inf') if not back_car else (back_car.pos - ego_car.pos - back_car.length) % road_length
        g_available = float('inf') if not (front_car and back_car) else (front_car.pos - back_car.pos) % road_length
        
        return g_lead, g_follow, g_available, front_car, back_car

    def check_lane_change(self, car, target_lane_id):
        v_e = car.velocity
        target_lane_cars = self.roads[0].get_cars_in_lane(target_lane_id)
        
        if not target_lane_cars:
            return True, {'feasible': True, 'g_front_min': 0, 'g_rear_min': 0, 'g_required': 0, 'g_lead': float('inf'), 'g_follow': float('inf'), 'g_available': float('inf')}
        
        g_lead, g_follow, g_available, front_car, back_car = self.get_practical_gaps(car, target_lane_id)
        v_l = front_car.velocity if front_car else v_e
        v_f = back_car.velocity if back_car else v_e
        
        g_front_min = self.calculate_front_gap(v_e, v_l)
        g_rear_min = self.calculate_rear_gap(v_f, v_e)
        g_required = self.calculate_total_required_gap(v_e, v_l, v_f)
        
        front_ok = g_lead >= g_front_min
        rear_ok = g_follow >= g_rear_min
        total_ok = g_available >= g_required
        
        result = {
            'feasible': front_ok and rear_ok and total_ok,
            'g_front_min': g_front_min,
            'g_rear_min': g_rear_min,
            'g_required': g_required,
            'g_lead': g_lead,
            'g_follow': g_follow,
            'g_available': g_available
        }
        return result['feasible'], result

    def perform_lane_change(self, car, target_lane_id):
        current_lane_id = car.lane_id
        car.lane_id = target_lane_id
        self.roads[0].exit_road(car, current_lane_id)
        self.roads[0].enter_road(car, target_lane_id)

    def log_gaps(self, car_idx, gap_data):
        with open("gap_log.csv", "a") as f:
            if f.tell() == 0:
                f.write("step,car_idx,g_front_min,g_rear_min,g_required,g_lead,g_follow,g_available,feasible\n")
            f.write(f"{self.step_count},{car_idx},{gap_data['g_front_min']:.1f},"
                    f"{gap_data['g_rear_min']:.1f},{gap_data['g_required']:.1f},"
                    f"{gap_data['g_lead']:.1f},{gap_data['g_follow']:.1f},"
                    f"{gap_data['g_available']:.1f},{gap_data['feasible']}\n")

    def run(self, dt=None):
        if dt is None:
            dt = self.dt
        self.driver_decision()
        
        # Check lane change for all cars
        for idx, car in enumerate(self.cars):
            target_lane_id = 1 if car.lane_id == 0 else 0
            if self.step_count % 100 == 0:  # Attempt lane change every 100 steps
                feasible, gap_data = self.check_lane_change(car, target_lane_id)
                self.log_gaps(idx, gap_data)
                if feasible:
                    # self.perform_lane_change(car, target_lane_id)
                    print(f"Step {self.step_count}: Car {idx} changed to lane {target_lane_id}, Gaps: {gap_data}")
                else:
                    print(f"Step {self.step_count}: Car {idx} lane change not feasible, Gaps: {gap_data}")
        
        self.move_forward(dt)
        self.step_count += 1

    def set_leader_stop(self, leader_stop):
        self.leader_stop = leader_stop

    def driver_decision(self):
        road_length = self.roads[0].length if self.roads else 1000
        dt = self.dt
        car_states = [(c.pos, c.velocity, c.lane_id) for c in self.cars]

        for idx, car in enumerate(self.cars):
            # Check if car is the first in its lane
            lane_cars = [c for c in self.cars if c.lane_id == car.lane_id and c != car]
            is_first_in_lane = True
            if lane_cars:
                for other in lane_cars:
                    gap = (car.pos - other.pos) % road_length
                    if gap < road_length / 2:  # Other car is ahead
                        is_first_in_lane = False
                        break

            if is_first_in_lane:
                # First car in lane follows v_des (or ego velocity profile for car 0)
                if idx == 0 and hasattr(self, 'ego_velocity_profile') and self.ego_velocity_profile:
                    time = round(self.step_count * dt, 3)
                    for i in range(len(self.ego_velocity_profile)-1):
                        t1, v1 = self.ego_velocity_profile[i]
                        t2, v2 = self.ego_velocity_profile[i+1]
                        if t1 <= time <= t2:
                            alpha = (time - t1) / (t2 - t1)
                            target_velocity = v1 + alpha * (v2 - v1)
                            current_velocity = car.velocity
                            acc = (target_velocity - current_velocity) / dt
                            car.acceleration = max(self.min_a, min(self.max_a, acc))
                            break
                    else:
                        t1, v1 = self.ego_velocity_profile[-1]
                        target_velocity = v1
                        current_velocity = car.velocity
                        acc = (target_velocity - current_velocity) / dt
                        car.acceleration = max(self.min_a, min(self.max_a, acc))
                else:
                    v_des = 0 if (getattr(self, 'leader_stop', False) and idx == 0) else self.initial_v_des
                    acc = self.kc * (v_des - car.velocity)
                    car.acceleration = max(self.min_a, min(self.max_a, acc))
                continue

            # Find the car ahead and behind in the same lane
            cars_same_lane = [c for c in self.cars if c.lane_id == car.lane_id and c != car]
            
            def gap_to(other):
                return (car.pos - other.pos) % road_length
            
            front_car = min(cars_same_lane, key=gap_to, default=None) if cars_same_lane else None

            def gap_from(other):
                return (other.pos - car.pos) % road_length
            
            back_car = min(cars_same_lane, key=gap_from, default=None) if cars_same_lane else None

            if self.model == 'ACC' or (self.model == 'BCC' and idx == len(self.cars) - 1):
                # ACC: Consider only the car in front
                car_pos, car_vel, _ = car_states[idx]
                if front_car:
                    front_idx = self.cars.index(front_car)
                    front_car_pos, front_car_vel, _ = car_states[front_idx]
                    gap = (car_pos - front_car_pos - car.length) % road_length
                    rel_v = front_car_vel - car_vel
                    desired_gap = self.min_dis + car_vel * self.reaction_time
                    acc = 0.5 * self.kd * (gap - desired_gap) + 0.5 * self.kv * rel_v
                    car.acceleration = max(self.min_a, min(self.max_a, acc))
                else:
                    acc = self.kc * (self.initial_v_des - car.velocity)
                    car.acceleration = max(self.min_a, min(self.max_a, acc))
            elif self.model == 'BCC':
                car_pos, car_vel, _ = car_states[idx]
                if front_car and back_car:
                    front_idx =  self.cars.index(front_car)
                    back_idx = self.cars.index(back_car)
                    front_car_pos, front_car_vel, _ = car_states[front_idx]
                    back_car_pos, back_car_vel, _ = car_states[back_idx]
                    desired_gap = self.min_dis + car_vel * self.reaction_time
                    front_gap = abs((car_pos - front_car_pos - front_car.length) % road_length)
                    back_gap = abs((back_car_pos - car_pos - car.length) % road_length)
                    gap_factor = 0.5 * self.kd * (front_gap - desired_gap) + 0.5 * self.kd * (desired_gap - back_gap)
                    velocity_factor = 0.5 * self.kv * (front_car_vel - car_vel) + 0.5 * self.kv * (back_car_vel - car_vel)
                    acc = velocity_factor + gap_factor
                    car.acceleration = max(self.min_a, min(self.max_a, acc))
                elif front_car:
                    front_idx = self.cars.index(front_car)
                    front_car_pos, front_car_vel, _ = car_states[front_idx]
                    gap = (car_pos - front_car_pos - car.length) % road_length
                    rel_v = front_car_vel - car_vel
                    desired_gap = self.min_dis + car_vel * self.reaction_time
                    acc = 0.5 * self.kd * (gap - desired_gap) + 0.5 * self.kv * rel_v
                    car.acceleration = max(self.min_a, min(self.max_a, acc))
                else:
                    acc = self.kc * (self.initial_v_des - car.velocity)
                    car.acceleration = max(self.min_a, min(self.max_a, acc))

    def move_forward(self, dt=None):
        if dt is None:
            dt = self.dt
        for car in self.cars:
            car.update(dt)
            car.velocity = max(self.min_v, min(car.velocity, self.max_v))
            if hasattr(car, 'collision_timer') and car.collision_timer > 0:
                car.collision_timer -= 1
                if car.collision_timer == 0:
                    car.color = car.original_color
        self.handle_collisions()

    def handle_collisions(self):
        road_length = self.roads[0].length if self.roads else 1000
        for lane_id in range(self.roads[0].num_lanes):
            lane_cars = sorted(self.roads[0].get_cars_in_lane(lane_id), key=lambda c: c.pos)
            for i, car in enumerate(lane_cars):
                next_car = lane_cars[(i + 1) % len(lane_cars)] if len(lane_cars) > 1 else None
                if next_car and car != next_car:
                    hasCollided = ((next_car.pos - car.pos) % road_length) <= car.length
                    if hasCollided:
                        v1 = car.velocity
                        v2 = next_car.velocity
                        e = car.CoR if hasattr(car, 'CoR') else 0.3
                        car.velocity = ((1 - e) * v1 + (1 + e) * v2) / 2
                        next_car.velocity = ((1 - e) * v2 + (1 + e) * v1) / 2
                        next_car.pos = (car.pos + car.length + self.min_gap) % road_length
                        car.color = 'orange'
                        next_car.color = 'orange'
                        car.collision_timer = 40
                        next_car.collision_timer = 40