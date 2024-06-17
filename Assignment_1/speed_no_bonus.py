from vi import Agent, Simulation, Config
from pygame.math import Vector2
import random
import pygame as pg
import math
from PIL import Image
import datetime

class AggregationConfig(Config):
    delta_time: float = 0.5
    mass: int = 20
    movement_speed: float = 10  # Increased movement speed
    max_angle_change: float = 120.0  # Increased max angle change
    p_change_direction: float = 0.95  # Increased probability of changing direction
    t_join_base: float = 1.0  # Further reduced base time before joining
    t_join_noise: float = 0.1  # Reduced noise for faster joining
    p_base_leaving: float = 0.05
    p_base_joining: float = 0.9  # Increased base joining probability
    a: float = 3.0  # Further increased joining probability factor
    b: float = 2.5
    time_step_d: int = 5  # Further reduced time steps for sampling join/leave probability
    site_width: int = 0
    site_height: int = 0


class Cockroach(Agent):
    config: AggregationConfig

    def __init__(self, images, simulation, pos=None, move=None):
        super().__init__(images, simulation, pos, move)
        self.state = 'wandering'
        self.timer = 0
        self.t_join = self.config.t_join_base + abs(random.gauss(0, self.config.t_join_noise))  # Initialize t_join here

        if move is None:
            angle = random.uniform(0, 360)
            self.move = Vector2(self.config.movement_speed, 0).rotate(angle)


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
        
        # Calculate direction towards the larger aggregation zone
        larger_zone_center = Vector2(100, 300)  # Coordinates of the larger aggregation zone center
        direction_to_larger_zone = (larger_zone_center - self.pos).normalize()
        
        # Adjust movement direction towards the larger zone
        self.move = direction_to_larger_zone * self.config.movement_speed
        
        # Avoid obstacles
        next_step = self.pos + self.move * self.config.delta_time
        self.pos = self.obstacle_avoidance(next_step)

    def joining(self):
        self.wandering()
        if self.timer > self.t_join:
            self.state = 'still'
            print("State changed to still")
        else:
            self.timer += self.config.delta_time

    def joiningProbability(self, in_proximity):
        p_stay = 0.03 + 0.48 * (1 - math.exp(-self.config.a * (in_proximity + 1)))
        return p_stay

    def still(self):
        if not self.checkInSite():
            print(f"Agent left the site, changing state to 'wandering'. Agent position: {self.pos}")
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
                print(f"Agent left the site while still, changing state to 'wandering'. Agent position: {self.pos}")
                self.state = 'wandering'
                print('huj')
            else:
                self.still()
        elif self.state == 'leaving':
            self.leaving()

        return super().update()

class AggregationSimulation(Simulation):
    config: AggregationConfig
    init_pos: Vector2 = Vector2(0, 0)
    global_delta_time: int = 0

    def _init_(self, config):
        super()._init_(config)
        self.site_image_path = "Assignment_0/images/bubble-full.png"
        self.site_image_resized_path = "Assignment_0/images/bubble-full-resized.png"
        self.site_dimensions = self.resize_image(self.site_image_path, self.site_image_resized_path, (100, 100))
        self.config.site_width, self.config.site_height = self.site_dimensions
        print(f"Site dimensions: width={self.config.site_width}, height={self.config.site_height}")

    def resize_image(self, image_path, output_path, size):
        with Image.open(image_path) as img:
            resized_img = img.resize(size)
            resized_img.save(output_path)
            return resized_img.size

    def before_update(self):
        super().before_update()
        AggregationSimulation.global_delta_time += 1
        for event in pg.event.get():
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_m:
                    for agent in self._agents:
                        agent.state = "joining"

        AggregationSimulation.global_delta_time += 1
        self.global_count = 0

        for cockroach in self._agents:
            if cockroach.state == 'still':
                self.global_count += 1

        if self.global_count == 50:
            elapsed_time = datetime.datetime.now() - self.simulation_start_time
            print(elapsed_time)
            print('huj')
            self.stop()

# Define and run the simulation
simulation = AggregationSimulation(
    AggregationConfig(
        fps_limit=0,
        seed=1.5,
        movement_speed=25,  # Further increased movement speed
        radius=50,
        #duration=20_000  # Increased duration for more time
    )
)
simulation.batch_spawn_agents(50, Cockroach, images=["Assignment_0/images/roach40.png"])
simulation.spawn_site("Assignment_0/images/bubble-full.png", x=100, y=300)  # Adjusted larger zone coordinates
simulation.spawn_site("Assignment_0/images/bubble-full-resized.png", x=500, y=375)
simulation.run()