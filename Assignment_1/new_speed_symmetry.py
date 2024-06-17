from vi import Agent, Simulation, Config
from pygame.math import Vector2
import random
import pygame as pg
import math
from PIL import Image
import datetime
import csv  # Add this import at the beginning of your file

class AggregationConfig(Config):
    delta_time: float = 0.5
    mass: int = 20
    movement_speed: float = 50  # Further increased movement speed
    max_angle_change: float = 45.0  # Further reduced max angle change
    p_change_direction: float = 0.99  # Slightly increased probability of changing direction
    t_join_base: float = 0.3  # Further reduced base time before joining
    t_join_noise: float = 0.03  # Further reduced noise for faster joining
    p_base_leaving: float = 0.05
    p_base_joining: float = 0.85  # Further increased base joining probability
    a: float = 5.0  # Further increased joining probability factor
    b: float = 4.0  # Further increased leaving probability factor
    time_step_d: int = 1  # Further reduced time steps for sampling join/leave probability
    site_width: int = 0
    site_height: int = 0

class Cockroach(Agent):
    config: AggregationConfig

    def __init__(self, images, simulation, pos=None, move=None):
        super().__init__(images, simulation, pos, move)
        if move is None:
            angle = random.uniform(0, 360)
            self.move = Vector2(self.config.movement_speed, 0).rotate(angle)
        self.state = 'wandering'
        self.timer = 0

    def change_position(self):
        self.there_is_no_escape()

    def obstacle_avoidance(self, next_step):
        while self.is_obstacle(next_step):
            angle_change = random.uniform(-self.config.max_angle_change, self.config.max_angle_change)
            self.move = self.move.rotate(angle_change)
            next_step = self.pos + self.move * self.config.delta_time
        return next_step

    def is_obstacle(self, position):
        if position.x < 0 or position.x >= 750 or position.y < 0 or position.y >= 750:
            return True
        return False

    def wandering(self):
        if random.random() < self.config.p_change_direction:
            angle_change = random.uniform(-self.config.max_angle_change, self.config.max_angle_change)
            self.move = self.move.rotate(angle_change)
        self.move = self.move.normalize() * self.config.movement_speed
        next_step = self.pos + self.move * self.config.delta_time
        self.pos = self.obstacle_avoidance(next_step)

    def joining(self):
        self.wandering()
        if self.timer > self.t_join:
            self.state = 'still'
        else:
            self.timer += self.config.delta_time

    def joiningProbability(self, in_proximity):
        p_stay = 0.03 + 0.48 * (1 - math.exp(-self.config.a * (in_proximity + 1)))
        return p_stay

    def still(self):
        if not self.checkInSite():
            self.state = 'wandering'
            return
        self.freeze_movement()
        rand = random.random()
        in_proximity = self.in_proximity_performance().count()
        if AggregationSimulation.global_delta_time % self.config.time_step_d == 0:
            if rand < self.leavingProbability(in_proximity):
                self.state = 'leaving'
                self.continue_movement()

    def leaving(self):
        if self.checkInSite():
            if random.random() < self.config.p_change_direction:
                angle_change = random.uniform(-self.config.max_angle_change, self.config.max_angle_change)
                self.move = self.move.rotate(angle_change)
            self.move = self.move.normalize() * self.config.movement_speed
            self.pos += self.move * self.config.delta_time
        else:
            self.state = 'wandering'

    def leavingProbability(self, in_proximity):
        return math.exp(-self.config.b * (in_proximity + 1))

    def checkInSite(self):
        sites = [
            (250, 375, self.config.site_width, self.config.site_width),
            (500, 375, 100, 100)
        ]
        for site in sites:
            site_x, site_y, site_width, site_height = site
            half_width, half_height = site_width / 2, site_height / 2
            if (site_x - half_width <= self.pos.x <= site_x + half_width and
                site_y - half_height <= self.pos.y <= site_y + half_height):
                return True
        return False

    def update(self):
        if self.state == 'wandering':
            self.wandering()
            if AggregationSimulation.global_delta_time % self.config.time_step_d == 0:
                if self.checkInSite() and random.random() < self.joiningProbability(self.in_proximity_performance().count()):
                    self.state = 'joining'
                    self.timer = 0
                    self.t_join = self.config.t_join_base + abs(random.gauss(0, self.config.t_join_noise))
        elif self.state == 'joining':
            self.joining()
        elif self.state == 'still':
            if not self.checkInSite():
                self.state = 'wandering'
            else:
                self.still()
        elif self.state == 'leaving':
            self.leaving()

        return super().update()

class AggregationSimulation(Simulation):
    config: AggregationConfig
    init_pos: Vector2 = Vector2(0, 0)
    global_delta_time: int = 0

    def __init__(self, config, nr_roaches = 1):
        super().__init__(config)
        self.site_image_path = "Assignment_0/images/bubble-full.png"
        self.site_image_resized_path = "Assignment_0/images/bubble-full-resized.png"
        self.site_dimensions = self.resize_image(self.site_image_path, self.site_image_resized_path, (100, 100))
        self.config.site_width, self.config.site_height = self.site_dimensions
        self.num_of_roaches = nr_roaches
        self.simulation_start_time = None

    def resize_image(self, image_path, output_path, size):
        with Image.open(image_path) as img:
            resized_img = img.resize(size)
            resized_img.save(output_path)
            return resized_img.size

    def before_update(self):
        super().before_update()
        
        if self.simulation_start_time is None:
            self.simulation_start_time = datetime.datetime.now()

        AggregationSimulation.global_delta_time += 1
        for event in pg.event.get():
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_m:
                    for agent in self._agents:
                        agent.state = "joining"

        self.global_count = 0
        for cockroach in self._agents:
            if cockroach.state == 'still':
                self.global_count += 1

        elapsed_time = datetime.datetime.now() - self.simulation_start_time
        
        if self.global_count == self.num_of_roaches:
            with open("dataset_symmetric.csv", "a", newline='') as file:
                writer = csv.writer(file)
                elapsed_milliseconds = int(elapsed_time.total_seconds() * 1000)
                writer.writerow([self.num_of_roaches, elapsed_milliseconds])
            self.stop()


def run_simulation(nr_roaches):
# Define and run the simulation
    AggregationSimulation(
        AggregationConfig(
            fps_limit=0,
            seed=1.5,
            movement_speed=25,  # Further increased movement speed
            radius=50,
            duration=20_000  # Increased duration for more time
    ), nr_roaches
).batch_spawn_agents(nr_roaches, Cockroach, images=["Assignment_0/images/roach40.png"]
                    ).spawn_site("Assignment_0/images/bubble-full.png", x=250, y=375
                                 ).spawn_site("Assignment_0/images/bubble-full.png", x=500, y=375
                                              ).run()