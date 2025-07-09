"""
transportation_painter.py: Visualization for the simulation (using tkinter).
"""

import tkinter as tk

class TransportationPainter(tk.Canvas):
    def __init__(self, master, roads, cars, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.roads = roads
        self.cars = cars
        self.counter = 0

    def set_elements(self, roads, cars):
        self.roads = roads
        self.cars = cars

    def increase_counter(self):
        self.counter += 1

    def init(self):
        self.counter = 0
        self.repaint()

    def repaint(self):
        self.delete('all')
        self.paint()

    def paint(self):
        self.delete('all')
        # Draw roads (one line per lane)
        for road in self.roads:
            for lane_id in range(road.num_lanes):
                x1, y1 = 100, 200 + lane_id * 50  # Offset lanes vertically
                x2, y2 = 1100, 200 + lane_id * 50
                self.create_line(x1, y1, x2, y2, width=8, fill='gray')
                
        # Draw cars sorted by position within each lane
        road_length = self.roads[0].length if self.roads else 1000
        for road in self.roads:
            for lane_id in range(road.num_lanes):
                lane_cars = [car for car in road.get_cars_in_lane(lane_id)]
                sorted_cars = sorted(lane_cars, key=lambda c: c.pos)
                for car in sorted_cars:
                    x = 1100 - (car.pos / road_length) * 1000
                    y = 200 + lane_id * 50  # Offset by lane
                    self.create_rectangle(x - car.length/2, y - 10, x + car.length/2, y + 10, fill=car.color, outline='black')
                    self.create_text(x, y - 25, text=f"{car.velocity:.1f}")