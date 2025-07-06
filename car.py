"""
car.py: Contains the Car class for the traffic simulation.
"""

class Car:
    def __init__(self, length, color, pos,min_dis, velocity, acceleration, current_road):
        self.length = length
        self.color = color
        self.pos = pos
        self.min_dis = min_dis
        self.velocity = velocity
        self.acceleration = acceleration
        self.current_road = current_road
        self.pos_history = []
        self.vel_history = []

    def get_length(self):
        return self.length

    def get_color(self):
        return self.color

    def get_pos(self):
        return self.pos

    def get_velocity(self):
        return self.velocity

    def get_acceleration(self):
        return self.acceleration

    def get_current_road(self):
        return self.current_road

    def get_pos_history(self):
        return self.pos_history

    def update(self, dt):
        # Invert position update for inverted mapping (move right as forward)
        # S = ut + 0.5at^2
        # v = u + at
        displacement = self.velocity * dt - 0.5 * self.acceleration * dt**2
        self.pos -= displacement

        self.velocity += self.acceleration * dt

        if self.velocity < 0:
            self.velocity = 0

        road_length = self.current_road.length if hasattr(self, 'current_road') else 1000
        if self.pos < 0:
            self.pos += road_length
        elif self.pos >= road_length:
            self.pos -= road_length
        self.pos_history.append(self.pos)
        self.vel_history.append(self.velocity)