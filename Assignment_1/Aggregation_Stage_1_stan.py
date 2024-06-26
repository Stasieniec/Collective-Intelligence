from vi import Agent, Simulation, Config
from pygame.math import Vector2
import random
import pygame as pg
import math
from PIL import Image
import polars as pl
import seaborn as sns
import matplotlib.pyplot as plt
import datetime
import sys


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
    a: float = 3.0
    b: float = 2.5
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
        # Initialise the movement direction with a random angle
        if move is None:                            
            angle = random.uniform(0, 360)
            self.move = Vector2(self.config.movement_speed, 0).rotate(angle)
        # Initialise the state of the agent to be wandering
        self.state = 'wandering'
        self.timer = 0

    def change_position(self):
        self.there_is_no_escape()

    def obstacle_avoidance(self, next_step):
        '''
        Checks whether the next step is colliding with an obstacle
        '''
        while self.is_obstacle(next_step):
            angle_change = random.uniform(-self.config.max_angle_change, self.config.max_angle_change)
            self.move = self.move.rotate(angle_change)
            next_step = self.pos + self.move * self.config.delta_time

    def is_obstacle(self, position):
        if position.x < 0 or position.x >= 750 or position.y < 0 or position.y >= 750:
            return True
        return False

    def wandering(self):
        '''
        Elicits a random walking behaviour of the Agent
        by picking a random angle +- 30 degrees,
        while checking if the next step is an obstacle
        
        '''
        if random.random() < self.config.p_change_direction:
            angle_change = random.uniform(-self.config.max_angle_change, self.config.max_angle_change)
            self.move = self.move.rotate(angle_change)
        
        self.move = self.move.normalize() * self.config.movement_speed
        next_step = self.pos + self.move * self.config.delta_time
        self.obstacle_avoidance(next_step)
        self.pos += self.move * self.config.delta_time

    def joining(self):
        '''
        A timer for when to switch to still state
        '''
        self.wandering()
        if self.timer > self.t_join:
            self.state = 'still'
            print("State changed to still")
        else:
            self.timer += self.config.delta_time

    def joiningProbability(self, in_proximity):
        '''
        https://hal.science/hal-02082903v1/file/Self_organised_Aggregation_in_Swarms_of_Robots_with_Informed_Robots.pdf
        Pstay = 0.03 + 0.48 ∗ (1 − e ^−an);
        
        '''
        p_stay = 0.03 + 0.48 * (1 - math.exp(-self.config.a * (in_proximity + 1)))
        return p_stay

    def still(self):

        '''
        Method for freezing the movement of the agent, if in the site

        '''
        if not self.checkInSite():
            print(f"Agent left the site, changing state to 'wandering'. Agent position: {self.pos}")
            self.state = 'wandering'
            return

        self.freeze_movement()
        #print("freezing")

        rand = random.random()
        in_proximity = self.in_proximity_performance().count()

        # Every d time steps, try to leave the site
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
        '''
        https://hal.science/hal-02082903v1/file/Self_organised_Aggregation_in_Swarms_of_Robots_with_Informed_Robots.pdf
        
        p_leave = e^−bn;
        '''
        return math.exp(-self.config.b * (in_proximity + 1))

    def checkInSite(self):
        '''
        Method for checking whether an agent is on the site
        because the provided on_site() does not work for me
        '''
        site_id = self.on_site_id() # Maybe use later for data

        sites = [
        (250, 375, self.config.site_width, self.config.site_width),
        (500, 375, 100, 100)]

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
                print(f"Agent left the site while still, changing state to 'wandering'. Agent position: {self.pos}")
                self.state = 'wandering'
            else:
                self.still()
        elif self.state == 'leaving':
            self.leaving()


                # Save additional data
        in_proximity = self.in_proximity_accuracy().count()
        self.save_data("in_proximity", in_proximity)
        self.save_data("state", self.state)


        return super().update()

class AggregationSimulation(Simulation):
    config: AggregationConfig = AggregationConfig()
    init_pos: Vector2 = Vector2(0, 0)
    global_delta_time: int = 0


    def __init__(self, config, num_of_roaches = 1):
        super().__init__(config)
        self.site_image_path = "Assignment_0/images/bubble-full.png"
        self.site_image_resized_path = "Assignment_0/images/bubble-full-resized.png"
        self.resize_image(self.site_image_path, self.site_image_resized_path, (100, 100))  # Resize to (width, height)
        self.site_width, self.site_height = self.get_image_dimensions(self.site_image_resized_path)
        self.config.site_width = self.site_width
        self.config.site_height = self.site_height
        print(f"Site dimensions: width={self.site_width}, height={self.site_height}")
        self.simulation_start_time = None
        self.num_of_roaches = num_of_roaches

    def resize_image(self, image_path, output_path, size):
        with Image.open(image_path) as img:
            resized_img = img.resize(size, Image.ANTIALIAS)
            resized_img.save(output_path)

    def get_image_dimensions(self, image_path):
        with Image.open(image_path) as img:
            return img.size  # Returns (width, height)
        

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
                print(self.global_count)

        elapsed_time = datetime.datetime.now() - self.simulation_start_time
        
        if self.global_count == self.num_of_roaches:
            with open("elapsed_time.txt", "w") as file:
                file.write(str(self.num_of_roaches) + " " + str(elapsed_time))
            self.stop()


def run_simulation(number_of_roaches):
    AggregationSimulation(
        AggregationConfig(
            fps_limit=0,
            seed=1,
            movement_speed=1,
            radius=50,
        ), number_of_roaches
    ).batch_spawn_agents(number_of_roaches, Cockroach, images=["Assignment_0/images/roach40.png"]).spawn_site("Assignment_0/images/bubble-full.png", x=250, y=375).spawn_site("Assignment_0/images/bubble-full-resized.png", x=500, y=375).run()
    
run_simulation(20)