from vi import Agent, Simulation, Config
from pygame.math import Vector2
import random
import pygame as pg
import math
from PIL import Image
import polars as pl
import seaborn as sns
import matplotlib.pyplot as plt
import sys
from datetime import timedelta
import datetime
import polars as pl


class CompetitionConfig(Config):
    delta_time: float = 0.5                         # Value for time steps
    mass: int = 20

    movement_speed_f: float = 2                      # Velocity of the Agents
    movement_speed_r: float = 0.5  
    max_angle_change: float = 30.0 

    p_change_direction: float = 0.05

    time_step_d: int = 100

class Foxes(Agent):
    config: CompetitionConfig
    animation_frames: int = 6

    death_probability: float = 0.05


    def __init__(self, images, simulation, pos=None, move=None):
        super().__init__(images, simulation, pos, move)
        if move is None:                            
            angle = random.uniform(0, 360)
            self.move = Vector2(self.config.movement_speed, 0).rotate(angle)

        self.state = 'wandering'
        self.health = 10

        self.frame = 0

        self.reproduction_flag = False
        self.eat_flag = False

    def change_position(self):
        self.there_is_no_escape()

    def update(self):
        
        self.lose_health()
        self.wandering()
        self.death()
        self.eat()
        self.reproduction()

    def eat(self):

        #self.reproduction_flag = True
    
        in_proximity = self.in_proximity_accuracy()
        for agent, dist in in_proximity:
            if isinstance(agent, Rabbits):
                if dist < 10:
                    self.health += 5
                    agent.eaten()
                    agent.death()
                    self.eat_flag = True
            

        
                
    def reproduction(self):
        if self.eat_flag == True:
            self.reproduce()
            self.eat_flag = False
        return


    def lose_health(self):
        if CompetitionSimulation.global_delta_time % self.config.time_step_d == 0:
            if random.random() < self.death_probability:
                self.health = 0
            return

    def death(self):
        if self.health == 0:
            self.kill()
            return

    def wandering(self):
        '''
        Elicits a random walking behaviour of the Agent
        by picking a random angle +- 30 degrees,
        while checking if the next step is an obstacle
        
        '''

        if random.random() < self.config.p_change_direction:
            angle_change = random.uniform(-self.config.max_angle_change, self.config.max_angle_change)
            self.move = self.move.rotate(angle_change)
        
        self.move = self.move.normalize() * self.config.movement_speed_f
        next_step = self.pos + self.move * self.config.delta_time
        self.obstacle_avoidance(next_step)
        #self.animation(self.pos,next_step)
        self.pos += self.move * self.config.delta_time
    
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
    

class Rabbits(Agent):
    config: CompetitionConfig
    animation_frames: int = 8
    p_reproduction: float = 0.09

    time_step_d: int = 100


    def __init__(self, images, simulation, pos=None, move=None):
        super().__init__(images, simulation, pos, move)
        if move is None:                            
            angle = random.uniform(0, 360)
            self.move = Vector2(self.config.movement_speed, 0).rotate(angle)


        self.state = 'wandering'

        self.health = 1

        self.frame = 0


    def change_position(self):
        self.there_is_no_escape()

    def update(self):
        self.wandering()
        self.reproduction()

    def eaten(self):
        self.health = 0
        return

    def death(self):
        if self.health == 0:
            self.kill()
            return

    def reproduction(self):

        if CompetitionSimulation.global_delta_time % self.time_step_d == 0:
            if random.random() < self.p_reproduction:
                self.reproduce()
            return

    def wandering(self):
        '''
        Elicits a random walking behaviour of the Agent
        by picking a random angle +- 30 degrees,
        while checking if the next step is an obstacle
        
        '''

        if random.random() < self.config.p_change_direction:
            angle_change = random.uniform(-self.config.max_angle_change, self.config.max_angle_change)
            self.move = self.move.rotate(angle_change)
        
        self.move = self.move.normalize() * self.config.movement_speed_r
        next_step = self.pos + self.move * self.config.delta_time
        self.obstacle_avoidance(next_step)
        self.pos += self.move * self.config.delta_time

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


class CompetitionSimulation(Simulation):
    
    config: CompetitionConfig
    global_delta_time: int = 0

    def __init__(self, config):
        super().__init__(config)
        self.rabbit_population = []
        self.fox_population = []


    def before_update(self):
        CompetitionSimulation.global_delta_time += 1

        self.save_population_data()
        

        super().before_update()

    def rabbit_pop(self):
        return self.rabbit_population

    def fox_pop(self):
        return self.fox_population

    def save_population_data(self):
        rabbit_count = sum(1 for agent in self._agents if isinstance(agent, Rabbits) and agent.alive)
        fox_count = sum(1 for agent in self._agents if isinstance(agent, Foxes) and agent.alive)
        self.rabbit_population.append(rabbit_count)
        self.fox_population.append(fox_count)

        if fox_count == 0 and rabbit_count == 0:
            self.stop()


n_rabbits = 20
n_foxes = 3

def run_simulation(n_rabbits, n_foxes, duration):
    global list_for_plotting
    list_for_plotting = []
    
    n_rabbits = n_rabbits
    n_foxes = n_foxes
    CompetitionSimulation(
    CompetitionConfig(
        duration=duration,
        fps_limit=0,
        seed=0,
        movement_speed=1,
        radius=10,
        image_rotation=True,

    )).batch_spawn_agents(n_rabbits, Rabbits, images=[
    "Assignment_2/sprite_frames/sprite_l.png"]).batch_spawn_agents(n_foxes, Foxes, 
                          images=
                          ["Assignment_2/sprite_frames_fox/fox_sprite.png"]).run()
    
    return list_for_plotting

