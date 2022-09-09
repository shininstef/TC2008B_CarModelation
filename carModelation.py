import pygame
from pygame import gfxdraw
from scipy.spatial import distance
from copy import deepcopy
from collections import deque
import json

import numpy as np

#copy to json 
d = { "agents": [
    {
      "agentId": 0,
      "type": 0 # Vehicle
    }
  ],
     "steps": [
         {
            "StepInfo": {
            "agentId": 0, # Vehicle.
            "stepIndex": 0, # Integer number of sequence order.
            "time": 0, # Elapsed time ms.
            "state": 0, # For example 0: Stoped, 1: Moving.
            "positionX": 0,
            "positionY": 0,
            "positionZ": 0,
            }
        }
    ]
}

class Window:
    def __init__(self, sim, config={}):
        # Simulation to draw
        self.sim = sim

        # Set default configurations
        self.set_default_config()

        # Update configurations
        for attr, val in config.items():
            setattr(self, attr, val)

    def set_default_config(self):
        """Set default configuration"""
        self.width = 600
        self.height = 600
        self.bg_color = (250, 250, 250)

        self.fps = 60
        self.zoom = 2
        self.offset = (0, 0)

        self.mouse_last = (0, 0)
        self.mouse_down = False

        self.pos = 0
        self.pos2 = -5
        self.step_size = 1/5
        self.step_size2 = 1/5
        self.currentIndex = 0
        self.currentIndex2 = 0
        self.step = 1;

        self.tfstate = [(0,0,0),(0,0,0)]
        self.tfstateJSON = [0,0]

    def loop(self, loop=None):
        """Shows a window visualizing the simulation and runs the loop function."""

        # Create a pygame window
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.flip()

        # Fixed fps
        clock = pygame.time.Clock()

        # To draw text
        pygame.font.init()
        self.text_font = pygame.font.SysFont('Lucida Console', 16)

        # Draw loop
        running = True
        while running and self.step<3000: #3000 quits the program 
            # Update simulation
            if loop:
                loop(self.sim)

            # Draw simulation
            self.draw()

            # Update window
            pygame.display.update()
            clock.tick(self.fps)

            # Handle all events
            for event in pygame.event.get():
                # Quit program if window is closed
                if event.type == pygame.QUIT:
                    running = False
            self.step = self.step + 1
            #print(self.step)
        pygame.quit()

    def run(self, steps_per_update=1):
        """Runs the simulation by updating in every loop."""
        def loop(sim):
            sim.run(steps_per_update)
        self.loop(loop)

    def convert(self, x, y=None):
        """Converts simulation coordinates to screen coordinates"""
        if isinstance(x, list):
            return [self.convert(e[0], e[1]) for e in x]
        if isinstance(x, tuple):
            return self.convert(*x)
        return (
            int(self.width/2 + (x + self.offset[0])*self.zoom),
            int(self.height/2 + (y + self.offset[1])*self.zoom)
        )

    def inverse_convert(self, x, y=None):
        """Converts screen coordinates to simulation coordinates"""
        if isinstance(x, list):
            return [self.convert(e[0], e[1]) for e in x]
        if isinstance(x, tuple):
            return self.convert(*x)
        return (
            int(-self.offset[0] + (x - self.width/2)/self.zoom),
            int(-self.offset[1] + (y - self.height/2)/self.zoom)
        )

    def background(self, r, g, b):
        """Fills screen with one color."""
        self.screen.fill((r, g, b))

    def line(self, start_pos, end_pos, color):
        """Draws a line."""
        gfxdraw.line(
            self.screen,
            *start_pos,
            *end_pos,
            color
        )

    def rect(self, pos, size, color):
        """Draws a rectangle."""
        gfxdraw.rectangle(self.screen, (*pos, *size), color)

    def box(self, pos, size, color):
        """Draws a rectangle."""
        gfxdraw.box(self.screen, (*pos, *size), color)

    def circle(self, pos, radius, color, filled=True):
        gfxdraw.aacircle(self.screen, *pos, radius, color)
        if filled:
            gfxdraw.filled_circle(self.screen, *pos, radius, color)

    def polygon(self, vertices, color, filled=True):
        gfxdraw.aapolygon(self.screen, vertices, color)
        if filled:
            gfxdraw.filled_polygon(self.screen, vertices, color)

    def rotated_box(self, pos, size, angle=None, cos=None, sin=None, centered=True, color=(0, 0, 255), filled=True):
        """Draws a rectangle center at *pos* with size *size* rotated anti-clockwise by *angle*."""
        x, y = pos
        l, h = size

        if angle:
            cos, sin = np.cos(angle), np.sin(angle)

        def vertex(e1, e2): return (
            x + (e1*l*cos + e2*h*sin)/2,
            y + (e1*l*sin - e2*h*cos)/2
        )

        if centered:
            vertices = self.convert(
                [vertex(*e) for e in [(-1, -1), (-1, 1), (1, 1), (1, -1)]]
            )
        else:
            vertices = self.convert(
                [vertex(*e) for e in [(0, -1), (0, 1), (2, 1), (2, -1)]]
            )

        self.polygon(vertices, color, filled=filled)

    def rotated_rect(self, pos, size, angle=None, cos=None, sin=None, centered=True, color=(0, 0, 255)):
        self.rotated_box(pos, size, angle=angle, cos=cos, sin=sin,
                         centered=centered, color=color, filled=False)

    def arrow(self, pos, size, angle=None, cos=None, sin=None, color=(150, 150, 190)):
        if angle:
            cos, sin = np.cos(angle), np.sin(angle)

        self.rotated_box(
            pos,
            size,
            cos=(cos - sin) / np.sqrt(2),
            sin=(cos + sin) / np.sqrt(2),
            color=color,
            centered=False
        )

        self.rotated_box(
            pos,
            size,
            cos=(cos + sin) / np.sqrt(2),
            sin=(sin - cos) / np.sqrt(2),
            color=color,
            centered=False
        )

    def draw_axes(self, color=(100, 100, 100)):
        x_start, y_start = self.inverse_convert(0, 0)
        x_end, y_end = self.inverse_convert(self.width, self.height)
        self.line(
            self.convert((0, y_start)),
            self.convert((0, y_end)),
            color
        )
        self.line(
            self.convert((x_start, 0)),
            self.convert((x_end, 0)),
            color
        )

    def draw_grid(self, unit=50, color=(150, 150, 150)):
        x_start, y_start = self.inverse_convert(0, 0)
        x_end, y_end = self.inverse_convert(self.width, self.height)

        n_x = int(x_start / unit)
        n_y = int(y_start / unit)
        m_x = int(x_end / unit)+1
        m_y = int(y_end / unit)+1

        for i in range(n_x, m_x):
            self.line(
                self.convert((unit*i, y_start)),
                self.convert((unit*i, y_end)),
                color
            )
        for i in range(n_y, m_y):
            self.line(
                self.convert((x_start, unit*i)),
                self.convert((x_end, unit*i)),
                color
            )

    def draw_roads(self):
        for road in self.sim.roads:
            # Draw road background
            self.rotated_box(
                road.start,
                (road.length, 3.7),
                cos=road.angle_cos,
                sin=road.angle_sin,
                color=(180, 180, 220),
                centered=False
            )

            # Draw road arrow
            if road.length > 5:
                for i in np.arange(-0.5*road.length, 0.5*road.length, 10):
                    pos = (
                        road.start[0] + (road.length/2 + i +
                                         3) * road.angle_cos,
                        road.start[1] + (road.length/2 + i +
                                         3) * road.angle_sin
                    )

                    self.arrow(
                        pos,
                        (-1.25, 0.2),
                        cos=road.angle_cos,
                        sin=road.angle_sin
                    )

    def draw_traffic_lights(self):
        i = 0
        for light in self.sim.lights:
            self.circle(light.position, 4, light.state)
            self.tfstate[i] = light.state
            if(self.tfstate[i] == (0, 255, 0)):
                self.tfstateJSON[i] = 2
            elif (self.tfstate[i] == (255, 255, 0)):
                self.tfstateJSON[i] = 1
            elif (self.tfstate[i] == (255, 0, 0)):
                self.tfstateJSON[i] = 0
            
            #print("Semaforo1")
            #print(self.tfstateJSON[0])
            i += 1
            
            #colors = [(0, 255, 0), (255, 255, 0), (255, 0, 0)]  # GREEN, YELLOW, RED, RED
            #colorsJSON = [2, 1, 0] # GREEN, YELLOW, RED, RED

    def draw_status(self):
        text_fps = self.text_font.render(
            f't={self.sim.t:.5}', False, (0, 0, 0))
        text_frc = self.text_font.render(
            f'n={self.sim.frame_count}', False, (0, 0, 0))

        self.screen.blit(text_fps, (0, 0))
        self.screen.blit(text_frc, (100, 0))

    def checkLights(self, path, currentIndex, position, length):
        pace = 1/5

        if(path[currentIndex] == 0 and position > length - 50):
            if (self.tfstate[0] == (255, 255, 0) and position > length - 20):
                pace = 1/10
            elif (self.tfstate[0] == (255,0,0) and position > length - 10):
                pace = 0
            elif (self.tfstate[0] == (255,0,0) and position > length - 20):
                pace = 1/15
            else:
                pace = 1/5
    
        if(path[currentIndex] == 10 and position > length - 50):
            if (self.tfstate[1] == (255, 255, 0) and position > length - 20):
                pace = 1/10
            elif (self.tfstate[1] == (255,0,0) and position > length - 10):
                pace = 0
            elif (self.tfstate[1] == (255,0,0) and position > length - 20):
                pace = 1/15
            else:
                pace = 1/5
        
        return pace;

    def draw(self):
        # Fill background
        self.background(*self.bg_color)

        self.draw_roads()
        self.draw_traffic_lights()

        # Draw status info
        self.draw_status()

        path = [1,2,4,5,6,7,8,9,0,3,6,7,10,11]
        # path = [0,3,6,7,10,11,4,5,6,7,8,9,1,2]
        path2 = [0,3,6,7,10,11,4,5,6,7,8,9,1,2]
        longitud = self.sim.roads[path[self.currentIndex]].length

        #Check Traffic Light Color, If its red stop, if its yellow reduce the speed, if its green dont do nothing.
        self.step_size = self.checkLights(path, self.currentIndex, self.pos, longitud);
        self.step_size2 = self.checkLights(path2, self.currentIndex2, self.pos2, longitud);

        if(path[self.currentIndex] == path2[self.currentIndex2]):
            if(self.pos2 > self.pos - 5):
                self.step_size2 = 0
            elif(self.pos2 > self.pos - 10):
                self.step_size2 = 1/20
            else:
                self.step_size2 = 1/5
            
        #Change Position form to the next street
        #Blue Car
        if (self.pos > longitud):
            self.pos = 0
            self.currentIndex += 1

        #Red Car
        if (self.pos2 > longitud):
            self.pos2 = 0
            self.currentIndex2 += 1

        #Blue Car
        sin, cos = self.sim.roads[path[self.currentIndex]].angle_sin, self.sim.roads[path[self.currentIndex]].angle_cos
        h = 3
        l = 3
        x = self.sim.roads[path[self.currentIndex]].start[0] + cos * self.pos
        y = self.sim.roads[path[self.currentIndex]].start[1] + sin * self.pos
        self.rotated_box((x, y), (l, h), cos=cos, sin=sin, centered=True)
        self.pos = self.pos + self.step_size

        #Red Car
        sin2, cos2 = self.sim.roads[path2[self.currentIndex2]].angle_sin, self.sim.roads[path2[self.currentIndex2]].angle_cos
        h = 3
        l = 3
        x2 = self.sim.roads[path2[self.currentIndex2]].start[0] + cos2 * self.pos2
        y2 = self.sim.roads[path2[self.currentIndex2]].start[1] + sin2 * self.pos2
        self.rotated_box((x2, y2), (l, h), cos=cos2, sin=sin2, centered=True, color=(255, 0, 0))
        self.pos2 = self.pos2 + self.step_size2


        #info car 1 (blue)
 
        agent = {
          "StepInfo": {
            "agentId": 0, # Vehicle.
            "stepIndex": self.step, # Integer number of sequence order.
            "time": self.sim.t, # Elapsed time ms.
            "state": 0, # For example 0: Stoped, 1: Moving.
            "positionX": x,
            "positionY": y,
            "positionZ": 0,
          }
        }
        
        #info car 2 (red)
        agent2 = {
          "StepInfo": {
            "agentId": 1, # Vehicle.
            "stepIndex": self.step, # Integer number of sequence order.
            "time": self.sim.t, # Elapsed time ms.
            "state": 0, # For example 0: Stoped, 1: Moving.
            "positionX": x2,
            "positionY": y2,
            "positionZ": 0,
          }
        }

        agent3 = {
          "StepInfo": {
            "agentId": 3, # Vehicle.
            "stepIndex": self.step, # Integer number of sequence order.
            "time": self.sim.t, # Elapsed time ms.
            "state": self.tfstateJSON[0], 
            "positionX": 300,
            "positionY": 290,
            "positionZ": 0,
          }
        }
        
        agent4 = {
          "StepInfo": {
            "agentId": 4, # Vehicle.
            "stepIndex": self.step, # Integer number of sequence order.
            "time": self.sim.t, # Elapsed time ms.
            "state": self.tfstateJSON[1],
            "positionX": 290,
            "positionY": 300,
            "positionZ": 0,
          }
        }
        
        with open ('data_file.json', "r+") as data_file:
            data = json.load(data_file)
            
            data["steps"].append(agent)
            data["steps"].append(agent2)
            data["steps"].append(agent3)
            data["steps"].append(agent4)
            data_file.seek(0)
            json.dump(data, data_file, indent = 4)  #append 1 json
            
            
             
     
class Simulation:
    def __init__(self, config={}):
        # Set default configuration
        self.set_default_config()

        # Update configuration
        for attr, val in config.items():
            setattr(self, attr, val)

    def set_default_config(self):
        self.t = 0.0            # Time keeping
        self.frame_count = 0    # Frame count keeping
        self.dt = 1/60          # Simulation time step
        self.roads = []         # Array to store roads
        self.lights = []        # Array to store traffic lights

    def create_road(self, start, end):
        road = Road(start, end)
        self.roads.append(road)
        return road

    def create_roads(self, road_list):
        for road in road_list:
            self.create_road(*road)

    def create_traffic_lights(self, light_list):
        for light in light_list:
            self.lights.append(TrafficLight(*light))

    def update(self):
        # Update every road
        for road in self.roads:
            road.update(self.dt)

        for light in self.lights:
            light.update(self.t)

        # Increment time
        self.t += self.dt
        self.frame_count += 1

    def run(self, steps):
        for _ in range(steps):
            self.update()


class Road:
    def __init__(self, start, end):
        self.start = start
        self.end = end

        self.vehicles = deque()

        self.init_properties()

    def init_properties(self):
        self.length = distance.euclidean(self.start, self.end)
        self.angle_sin = (self.end[1]-self.start[1]) / self.length
        self.angle_cos = (self.end[0]-self.start[0]) / self.length

    def update(self, dt):
        n = len(self.vehicles)

class TrafficLight:
    def __init__(self, position, route):
        self.cicle = cicles[route]  # Actual Cicle
        self.index = 0  # Index in array
        # The index on the colors array
        self.stateIndex = self.cicle[self.index]
        self.state = colors[self.stateIndex]  # The State's Color
        self.time = 0
        self.position = position

    def checkState(self):
        if (self.time != 0 and self.time % 20 < 0.01666666666674388):
            self.index += 1
            self.stateIndex = self.cicle[self.index]
            self.state = colors[self.stateIndex]
            if (self.index == 4):
                self.index = 0

    def getState(self):
        return self.state

    def update(self, t):
        self.time = t
        self.checkState()


cicles = [
    [0, 0, 1, 2, 2],
    [2, 2, 2, 0, 1]
]  # Posible Cicles 1 - GREEN, 2 - YELLOW, 3 - RED
colors = [(0, 255, 0), (255, 255, 0), (255, 0, 0)]  # GREEN, YELLOW, RED, RED
colorsJSON = [2, 1, 0] # GREEN, YELLOW, RED, RED
# 0 - Rojo
# 1 - Amarillo
# 2 - Verde
sim = Simulation()

# Add multiple roads
sim.create_roads([
    ((0, -100), (0, 0)),
    ((0, -100), (100, -100)),
    ((100, -100), (100, 0)),
    ((0, 0),  (0, 100)),
    ((100, 0), (100, 100)),
    ((100, 100), (0, 100)),
    ((0, 100), (-100, 100)),
    ((-100, 100), (-100, 0)),
    ((-100, 0), (-100, -100)),
    ((-100, -100), (0, -100)),
    ((-100, 0), (0, 0)),
    ((0, 0),  (100, 0)),
])

# Add multiple traffic lights
sim.create_traffic_lights([
    ((300, 290), 0),
    ((290, 300), 1)
])

# Start simulation
win = Window(sim)
win.offset = (0, 0)
win.run(steps_per_update=5)