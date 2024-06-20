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
'''
---+++ TO DO +++---

-- Empty environment based on Lotka-Volterra model:
    Population of Foxes
        Foxes reproduce if it eats a rabbit.
        Certain probability of dying if they don't eat
    Population of Rabbits
        Certain probability of spontaneous asexual reproduction
        Dies if eaten

'''

'''

Animation brainstorm:
    try to get the direction of the agent so either up down left or right
    then change image depending on direction

'''


'''
---+++---+++ Cool things to add +++---+++---
- - - Animation for the rabbits and foxes
-+
- - - Fox stears towards closest rabbit
-+
- - - Rabbit runs away from Fox
-+ 
- - - Agents don't collide with eachother
-+
- - -
-+
- - -
-+
---+++---+++---+++---+++---+++---+++---+++---
'''


class CompetitionConfig(Config):
    delta_time: float = 0.5                         # Value for time steps
    mass: int = 20

    movement_speed_f: float = 3                      # Velocity of the Agents
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
        #self.reproduction()

        #self.save_data("population", Foxes)

    # def animation(self, current_pos, next_pos):

    #     dx = current_pos.x - next_pos.x
    #     dy = current_pos.y - next_pos.y

    #     # Determine the direction of movement

    #     # Moving left
    #     if dx < 0:
            
    #         start_frame = 0
        
    #     # Moving right
    #     elif dx > 0:
            
    #         start_frame = 2

    #     # # Moving down
    #     # if dy < 0:
            
    #     #     start_frame = 8

    #     # # Moving up
    #     # elif dy > 0:
            
    #     #     start_frame = 24

    #     # Every 8 time steps, update the frame 
    #     if CompetitionSimulation.global_delta_time % 8 == 0:
    #         self.change_image(start_frame + self.frame)
    #         self.frame += 1

    #     # Reset frame animation loop 
    #     if self.frame == 5:
    #         self.frame = 0


    def eat(self):

        #self.reproduction_flag = True
    
        in_proximity = self.in_proximity_accuracy()
        for agent, dist in in_proximity:
            if isinstance(agent, Rabbits):
                if dist < 20:
                    self.health += 5
                    print(f"Fox ID {self.id} ate: +5HP, health:{self.health}")
                    agent.eaten()
                    agent.death()
                    self.reproduce()
                    self.eat_flag = True

            

        
                
    def reproduction(self):
        if self.eat_flag == True:
            self.reproduce()
            self.eat_flag = False
        return


    def lose_health(self):
        if CompetitionSimulation.global_delta_time % self.config.time_step_d == 0:
            if random.random() < self.death_probability:
                print(f"Fox probabilistically died")
                self.health = 0
            return

    def death(self):
        if self.health == 0:
            print(f"Fox ID {self.id} died of starvation, silly fox")
            self.kill()
            return

    def wandering(self):
        '''
        Elicits a random walking behaviour of the Agent
        by picking a random angle +- 30 degrees,
        while checking if the next step is an obstacle
        
        '''
        fox_neighbours = [(agent, dist) for agent, dist in self.in_proximity_accuracy() if isinstance(agent, Foxes)]
        
        in_proximity = list(self.in_proximity_accuracy())

        #fox_neighbours


        #if self.in_proximity_accuracy().count() == 0:
        if not fox_neighbours:
            if random.random() < self.config.p_change_direction:
                angle_change = random.uniform(-self.config.max_angle_change, self.config.max_angle_change)
                self.move = self.move.rotate(angle_change)
            
            self.move = self.move.normalize() * self.config.movement_speed_f
            next_step = self.pos + self.move * self.config.delta_time
            self.obstacle_avoidance(next_step)
            #self.animation(self.pos,next_step)
            self.pos += self.move * self.config.delta_time
            return

        else:
            al, sum_vel = self.alignment(fox_neighbours)
            a =  al * 0.5
            s = self.separation(fox_neighbours) * 0.5
            c = self.cohesion(fox_neighbours) * 0.5


        if self.eat_flag == True:
            s *= 1.1
        f_total = (a+s+c)/self.config.mass

        if self.move.length() > sum_vel.length():
            self.move.normalize() * sum_vel
            
        # Move the boid
        self.move += f_total
        self.pos += self.move * self.config.delta_time *1.5

    def alignment(self,in_proximity):
        
        sum_vel = Vector2(0,0)
        for agent, dist in in_proximity:
            vel = agent.move.normalize()
            sum_vel += vel
        
        avg_vel = sum_vel / len(in_proximity)

        Vboid = self.move
        alignment = avg_vel - Vboid

        return alignment, sum_vel

    def separation(self,in_proximity):

        sum_pos = Vector2(0,0)
        for agent, dist in in_proximity:
            sum_pos += self.pos - agent.pos

        avg_pos = sum_pos / len(in_proximity)

        return avg_pos

    def cohesion(self,in_proximity):

        sum_pos = Vector2(0,0)
        for agent, dist in in_proximity:
            sum_pos += agent.pos

        avg_pos = sum_pos / len(in_proximity)

        fc = avg_pos - self.pos

        Vboid = self.move
        cohesion = fc - Vboid

        return cohesion

    
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

        

    def animation(self, current_pos, next_pos):

        dx = current_pos.x - next_pos.x
        dy = current_pos.y - next_pos.y

        # Determine the direction of movement

        # Moving left
        if dx < 0:
            
            start_frame = 0
        
        # Moving right
        elif dx > 0:
            
            start_frame = 8

        # Moving down
        if dy < 0:
            
            start_frame = 8

        # Moving up
        elif dy > 0:
            
            start_frame = 24

        # Every 8 time steps, update the frame 
        if CompetitionSimulation.global_delta_time % 8 == 0:
            self.change_image(start_frame + self.frame)
            self.frame += 1

        # Reset frame animation loop 
        if self.frame == 8:
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
            print("Rabbit died by fox, health 0")
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


class CompetitionSimulation(Simulation):
    
    config: CompetitionConfig
    global_delta_time: int = 0
    

    def __init__(self, config):
        super().__init__(config)
        self.rabbit_population = []
        self.fox_population = []
        self.background_image = pg.image.load("Assignment_2/images/yYC6_f.png")


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

    def after_update(self):
        self._screen.blit(self.background_image, (0, 0))
        return super().after_update()


n_rabbits = 5
n_foxes = 15

df = (CompetitionSimulation(
    CompetitionConfig(
        #duration=10_000,
        fps_limit=120,
        seed=1,
        movement_speed=1,
        radius=50,
        image_rotation=True,
    )

        
).batch_spawn_agents(n_rabbits, Rabbits, 
                        images=[
"Assignment_2/sprite_frames/sprite_l.png",
"Assignment_2/sprite_frames/sprite_l (1).png",
"Assignment_2/sprite_frames/sprite_l (2).png",
"Assignment_2/sprite_frames/sprite_l (3).png",
"Assignment_2/sprite_frames/sprite_l (4).png",
"Assignment_2/sprite_frames/sprite_l (5).png",
"Assignment_2/sprite_frames/sprite_l (6).png",
"Assignment_2/sprite_frames/sprite_l (7).png",
"Assignment_2/sprite_frames/sprite_r.png",
"Assignment_2/sprite_frames/sprite_r (1).png",
"Assignment_2/sprite_frames/sprite_r (2).png",
"Assignment_2/sprite_frames/sprite_r (3).png",
"Assignment_2/sprite_frames/sprite_r (4).png",
"Assignment_2/sprite_frames/sprite_r (5).png",
"Assignment_2/sprite_frames/sprite_r (6).png",
"Assignment_2/sprite_frames/sprite_r (7).png",
"Assignment_2/sprite_frames/sprite_f.png",
"Assignment_2/sprite_frames/sprite_f (1).png",
"Assignment_2/sprite_frames/sprite_f (2).png",
"Assignment_2/sprite_frames/sprite_f (3).png",
"Assignment_2/sprite_frames/sprite_f (4).png",
"Assignment_2/sprite_frames/sprite_f (5).png",
"Assignment_2/sprite_frames/sprite_f (6).png",
"Assignment_2/sprite_frames/sprite_f (7).png",
"Assignment_2/sprite_frames/sprite_b.png",
"Assignment_2/sprite_frames/sprite_b (1).png",
"Assignment_2/sprite_frames/sprite_b (2).png",
"Assignment_2/sprite_frames/sprite_b (3).png",
"Assignment_2/sprite_frames/sprite_b (4).png",
"Assignment_2/sprite_frames/sprite_b (5).png",
"Assignment_2/sprite_frames/sprite_b (6).png",
"Assignment_2/sprite_frames/sprite_b (7).png",
    ]).batch_spawn_agents(n_foxes, Foxes, 
                          images=
                          ["Assignment_2/sprite_frames_fox/fox_sprite.png",
                           "Assignment_2/sprite_frames_fox/fox_sprite (1).png",
                           "Assignment_2/sprite_frames_fox/fox_sprite (2).png",
                           "Assignment_2/sprite_frames_fox/fox_sprite (3).png",
                           "Assignment_2/sprite_frames_fox/fox_sprite (4).png",
                           "Assignment_2/sprite_frames_fox/fox_sprite (5).png"
                           
                           ]).run()


)
