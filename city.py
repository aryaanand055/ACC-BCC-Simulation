from car import Car
from road import Road

class City:
    def __init__(self):
        self.cars = []
        self.roads = []
        self.step_count = 0
        self.model = 'ACC'  
        self.min_gap = 5.0  # Default value

    def init(self, car_number, kd, kv, kc, v_des, max_v, min_v, min_dis, reaction_time, max_a, min_a, min_gap=5.0, model='ACC'):
        # Reset simulation state
        self.cars.clear()
        self.roads.clear()
        self.step_count = 0
        self.model = model

        # Create a single straight road for simplicity
        road = Road(None, None, None, None, 1000, 0, 0, 1, 0)
        self.roads.append(road)

        # Place cars at intervals along the road
        for i in range(int(car_number)):
            initial_car_spacing = 50  # Initial spacing between cars
            pos = i * initial_car_spacing + 10  # Space cars 50 units apart
            velocity = v_des  # Initial velocity of each car
            if i == 0:
                color = 'red'  # First car is red (ego)
            elif i == car_number - 1:
                color = 'green'  # Last car is green
            else:
                color = 'blue'  # Others are blue
            car_length = 5  # If the car is a point object, its length is 0
            car = Car(length=car_length, color=color, pos=pos,min_dis=min_dis, velocity=velocity, acceleration=0, current_road=road)
            car.original_color = color  # Store original color
            car.collision_timer = 0     # Timer for collision color
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
        self.min_gap = min_gap

    def run(self):
        # Run one simulation step
        self.driver_decision()
        self.move_forward()
        self.step_count += 1

    def set_leader_stop(self, leader_stop):
        self.leader_stop = leader_stop

    # Main code to calculate acclerattion
    def driver_decision(self):
        # Decide acceleration for each car based on the selected model
        road_length = self.roads[0].length if self.roads else 1000
        for idx, car in enumerate(self.cars):
            if idx == 0 and hasattr(self, 'leader_stop') and self.leader_stop:
                # Ego vehicle: decelerate to stop if leader_stop is set
                acc = self.min_a
                car.acceleration = acc
                if car.velocity + acc * 0.1 < 0:
                    car.velocity = 0
                    car.acceleration = 0
                continue
            if idx == 0:
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
                    gap = (car.pos - front_car.pos -  car.length) % road_length
                    rel_v = front_car.velocity - car.velocity
                    min_dis = 20
                    desired_gap = min_dis + car.velocity * self.reaction_time
                    # Below is the formula for acceleration
                    acc = self.kd * (gap - desired_gap) + self.kv * rel_v
                    # print(f"Car {idx} - Velocity {car.velocity} - Gap: {gap}, Relative Velocity: {rel_v}, Desired Gap: {desired_gap}, Acceleration: {acc}")
                    acc = max(self.min_a, min(self.max_a, acc))
                    car.acceleration = acc
                else:
                    # No car ahead: accelerate towards desired velocity
                    acc = self.kc * (self.v_des - car.velocity)
                    acc = max(self.min_a, min(self.max_a, acc))
                    car.acceleration = acc
            elif self.model == 'BCC':
            #    BCC Logic here
                car.acceleration = 0

       
    def move_forward(self):
        # Move all cars forward based on their velocity and acceleration
        dt = 0.1
        for car in self.cars:
            car.update(dt)
            # Clamp velocity to not exceed max_v
            if car.velocity > self.max_v:
                car.velocity = self.max_v
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
