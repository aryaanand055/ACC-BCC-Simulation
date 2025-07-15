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
        # Draw roads (as a single horizontal line for now)
        for road in self.roads:
            x1, y1 = 100, 200
            x2, y2 = 1100, 200
            self.create_line(x1, y1, x2, y2, width=8, fill='gray')
            
        # Draw cars sorted by position (lowest pos = rightmost)
        if self.cars:
            sorted_cars = sorted(self.cars, key=lambda c: c.pos)
            l = len(sorted_cars)
            for i in range(l-1, -1, -1):
                car = sorted_cars[i]
                road_length = self.roads[0].length if self.roads else 1000
                # Inverted mapping: lowest pos = rightmost (x2), highest pos = leftmost (x1)
                x = 1100 - (car.pos / road_length) * 1000
                y = 200
                self.create_rectangle(x-car.length/2, y-10, x+car.length/2, y+10, fill=car.color, outline='black')
                self.create_text(x, y-25, text=f"{car.velocity:.1f}")
                mode_label = 'A' if getattr(car, 'mode', 'ACC') == 'ACC' else 'B' if getattr(car, 'mode', 'BCC') == 'BCC' else f"{car.integration_factor:.2f}".split(".")[1] if getattr(car, 'mode', 'INTEGRATED') == 'INTEGRATED' else 'V'
                self.create_text(x, y + 20, text=mode_label, font=("Arial", 8))

   