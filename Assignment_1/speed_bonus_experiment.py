from vi import Agent, Simulation, Config
from pygame.math import Vector2
import random
import pygame as pg
import math
from PIL import Image
import datetime
import sys
import numpy as np
import csv

class AggregationConfig(Config):
    delta_time: float = 0.5
    mass: int = 20
    movement_speed: float = 10
    max_angle_change: float = 120.0
    p_change_direction: float = 0.95
    t_join_base: float = 1.0
    t_join_noise: float = 0.1
    p_base_leaving: float = 0.05
    p_base_joining: float = 0.9
    p_random_stop: float = 0.001
    a: float = 5
    b: float = 4
    time_step_d: int = 5
    time_step_f: int = 20
    site_width: int = 0
    site_height: int = 0
    stopping_duration: float = 75.0
    small_aggregation_threshold: int = 5

class Cockroach(Agent):
    config: AggregationConfig

    def __init__(self, images, simulation, pos=None, move=None):
        super().__init__(images, simulation, pos, move)
        if move is None:
            angle = random.uniform(0, 360)
            self.move = Vector2(self.config.movement_speed, 0).rotate(angle)
        self.state = 'wandering'
        self.timer = 0
        self.stop_timer = 0
        self.current_site_size = 0

    def change_position(self):
        self.there_is_no_escape()

    def obstacle_avoidance(self, next_step):
        while self.is_obstacle(next_step):
            angle_change = random.uniform(-self.config.max_angle_change, self.config.max_angle_change)
            self.move = self.move.rotate(angle_change)
            next_step = self.pos + self.move * self.config.delta_time

    def is_obstacle(self, position):
        return not (0 <= position.x < 750 and 0 <= position.y < 750)

    def wandering(self):
        if random.random() < self.config.p_change_direction:
            angle_change = random.uniform(-self.config.max_angle_change, self.config.max_angle_change)
            self.move = self.move.rotate(angle_change)
        
        self.move = self.move.normalize() * self.config.movement_speed
        next_step = self.pos + self.move * self.config.delta_time
        self.obstacle_avoidance(next_step)
        self.pos += self.move * self.config.delta_time

    def joining(self):
        self.wandering()
        if self.timer > self.t_join:
            self.state = 'still'
            self.current_site_size = self.in_proximity_performance().count()
        else:
            self.timer += self.config.delta_time

    def joiningProbability(self, in_proximity):
        if in_proximity > self.current_site_size:
            return 0.03 + 0.48 * (1 - math.exp(-self.config.a * (in_proximity + 1)))
        else:
            return 0

    def still(self):
        self.freeze_movement()
        in_proximity = self.in_proximity_performance().count()
        self.current_site_size = in_proximity

        if AggregationSimulation.global_delta_time % self.config.time_step_d == 0:
            if random.random() < self.leavingProbability(in_proximity):
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
        if in_proximity <= self.config.small_aggregation_threshold:
            return 1.0 - math.exp(-self.config.b * (in_proximity + 1))
        else:
            return math.exp(-self.config.b * (in_proximity + 1))

    def checkInSite(self):
        return False

    def social_interaction(self):
        in_proximity = self.in_proximity_performance().count()
        if in_proximity > 3:
            if self.state == 'wandering' and random.random() < self.joiningProbability(in_proximity):
                self.t_join = self.config.t_join_base + abs(random.gauss(0, self.config.t_join_noise))
                self.state = 'joining'
                self.timer = 0
            elif self.state == 'still' and random.random() < self.leavingProbability(in_proximity):
                self.state = 'leaving'
                self.continue_movement()

    def update(self):
        self.social_interaction()
        if self.state == 'wandering':
            if random.random() < self.config.p_random_stop:
                self.state = 'stopping'
                self.stop_timer = 0
                self.freeze_movement()
                return
            self.wandering()
            if AggregationSimulation.global_delta_time % self.config.time_step_d == 0:
                if self.checkInSite() and random.random() < self.joiningProbability(self.in_proximity_performance().count()):
                    self.state = 'joining'
                    self.timer = 0
                    self.t_join = self.config.t_join_base + abs(random.gauss(0, self.config.t_join_noise))
        elif self.state == 'joining':
            self.joining()
        elif self.state == 'still':
            self.still()
        elif self.state == 'leaving':
            self.leaving()
        elif self.state == 'stopping':
            self.stop_timer += self.config.delta_time
            if self.stop_timer >= self.config.stopping_duration:
                self.state = 'wandering'
                self.continue_movement()
        return super().update()

class Pheromone(Agent):
    def _init_(self, pos: Vector2, images: pg.Surface, simulation: Simulation, *args, **kwargs):
        super()._init_([images], simulation, *args, **kwargs)
        self.pos = pos

    def change_position(self):
        pass

class AggregationSimulation(Simulation):
    config: AggregationConfig
    init_pos: Vector2 = Vector2(0, 0)
    global_delta_time: int = 0
    global_count: int = 0

    def __init__(self, config, num_roaches):
        super().__init__(config)
        self.site_image_path = "Assignment_0/images/bubble-full.png"
        self.site_image_resized_path = "Assignment_0/images/bubble-full-resized.png"
        self.resize_image(self.site_image_path, self.site_image_resized_path, (100, 100))
        self.site_width, self.site_height = self.get_image_dimensions(self.site_image_resized_path)
        self.config.site_width = self.site_width
        self.config.site_height = self.site_height
        self.simulation_start_time = None
        self.num_roaches = num_roaches

    def spawn_pheromone(self, position: Vector2):
        cube_image = "Assignment_0/images/green.png"
        cube_image = pg.image.load(cube_image).convert_alpha()
        cube = Pheromone(pos=position, images=cube_image, simulation=self)
        self._agents.add(cube)

    def resize_image(self, image_path, output_path, size):
        with Image.open(image_path) as img:
            resized_img = img.resize(size, Image.Resampling.LANCZOS)
            resized_img.save(output_path)

    def get_image_dimensions(self, image_path):
        with Image.open(image_path) as img:
            return img.size

    def before_update(self):
        super().before_update()
        if self.simulation_start_time is None:
            self.simulation_start_time = datetime.datetime.now()

        AggregationSimulation.global_delta_time += 1
        self.global_count = 0

        if AggregationSimulation.global_delta_time % self.config.time_step_d == 0:
            for event in pg.event.get():
                if event.type == pg.KEYDOWN:
                    if event.key == pg.K_m:
                        for agent in self._agents:
                            agent.state = "joining"

        for cockroach in self._agents:
            if cockroach.state == 'still':
                self.global_count += 1

        if self.global_count == self.num_roaches:
            elapsed_time = datetime.datetime.now() - self.simulation_start_time
            with open("dataset_bonus.csv", "a", newline='') as file:
                writer = csv.writer(file)
                elapsed_milliseconds = int(elapsed_time.total_seconds() * 1000)
                writer.writerow([self.num_roaches, elapsed_milliseconds])
            self.stop()

def run_simulation(number_of_roaches):
    AggregationSimulation(
        AggregationConfig(
            fps_limit=0,
            seed=1.5,
            movement_speed=25,
            radius=50,
            image_rotation=True,
        ), number_of_roaches
    ).batch_spawn_agents(number_of_roaches, Cockroach, images=["Assignment_0/images/roach40.png"]).run()

