from vi import Agent as BaseAgent, Simulation, Config
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

list_for_plotting = []
class Agent(BaseAgent):
    def __init__(self, images, simulation, pos=None, move=None):
        super().__init__(images, simulation, pos, move)
        self._simulation = simulation

class CompetitionConfig(Config):
    delta_time: float = 0.5                         # Value for time steps
    mass: int = 20

    movement_speed_f: float = 2                      # Velocity of the Agents
    movement_speed_r: float = 2 
    max_angle_change: float = 30.0 

    p_change_direction: float = 0.05

    time_step_d: int = 100

class Foxes(Agent):
    config: CompetitionConfig
    animation_frames: int = 6

    def __init__(self, images, simulation, pos=None, move=None):
        super().__init__(images, simulation, pos, move)
        self.age = 1
        if move is None:                            
            angle = random.uniform(0, 360)
            self.move = Vector2(self.config.movement_speed, 0).rotate(angle)

        self.state = 'wandering'
        self.health = 20

        self.frame = 0

        self.reproduction_flag = False
        self.eat_flag = False
        self.gender = random.choice(['male', 'female'])  # Added gender


    def change_position(self):
        self.there_is_no_escape()

    def update(self):
        
        self.lose_health()
        self.wandering()
        self.death()
        self.eat()
        self.reproduction()
        self.age += 0.001

        #self.save_data("population", Foxes)


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
                    self.eat_flag = True
            

        
                
    def reproduction(self):
        reproduction_chance = 0.9  # 50% chance to reproduce upon meeting an opposite-sex partner
        if self.eat_flag:
            compatible_partner = next((agent for agent in self.in_proximity_accuracy() if isinstance(agent[0], Foxes) and agent[0].gender != self.gender), None)
            if compatible_partner and random.random() < reproduction_chance:
                print('Reproduction!')
                self.reproduce()
                self.eat_flag = False
        return


    def lose_health(self):
        if CompetitionSimulation.global_delta_time % self.config.time_step_d == 0:
            self.health -= (1 + self.age)
            return

    def death(self):
        if self.health <= 0: 
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

        f_total = (a+s+c)/self.config.mass

        if self.move.length() > sum_vel.length():
            self.move.normalize() * sum_vel
        
        
        # Move the boid
        self.move += f_total
        self.pos += self.move * self.config.delta_time * 2


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

    site_x = 500
    site_y = 375
    site_width = 100
    site_height = 100
    attraction_probability: float = 0.01
    stay_duration: int = 200


    def __init__(self, images, simulation, pos=None, move=None):
        super().__init__(images, simulation, pos, move)
        self.age = 1
        if move is None:                            
            angle = random.uniform(0, 360)
            self.move = Vector2(self.config.movement_speed, 0).rotate(angle)


        self.state = 'wandering'

        self.health = 1

        self.frame = 0
        self.energy = 5
        self.gender = random.choice(['male', 'female'])  # Added gender
        

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

    def move_towards_site(self):
        site_center = Vector2(self.site_x, self.site_y)
        direction = (site_center - self.pos).normalize()
        angle = math.degrees(math.atan2(direction.y, direction.x))
        self.move = Vector2(self.config.movement_speed_r, 0).rotate(angle)

    def checkInSite(self):
        '''
        Method for checking whether an agent is on the site
        because the provided on_site() does not work for me
        '''
        
        #site_id = self.on_site_id() # Maybe use later for data

        site = [500, 375, 100, 100]

        site_x, site_y, site_width, site_height = site
        half_width, half_height = site_width / 2, site_height / 2
        if (site_x - half_width <= self.pos.x <= site_x + half_width and
            site_y - half_height <= self.pos.y <= site_y + half_height):
            #print(f"rabbit {self.id} in rabbit heaven ")
            return True
        
        return False
    
    def leave_site(self):
        if random.random() < self.config.p_change_direction:
            angle_change = random.uniform(-self.config.max_angle_change, self.config.max_angle_change)
            self.move = self.move.rotate(angle_change)

        self.move = self.move.normalize() * self.config.movement_speed_r
        next_step = self.pos + self.move * self.config.delta_time
        self.obstacle_avoidance(next_step)
        #self.animation(self.pos, next_step)
        self.pos += self.move * self.config.delta_time
    
    def siteBehaviour(self):
        self.freeze_movement()   

    def change_position(self):
        self.there_is_no_escape()

    def update(self):
        if self.state == 'wandering':
            self.wandering()

            if self.checkInSite():
                self.state = 'in_site'
                self.timer = CompetitionSimulation.global_delta_time
        elif self.state == 'in_site':
            #print(f"Rabbit ID {self.id} arrived")
            self.siteBehaviour()
            if CompetitionSimulation.global_delta_time - self.timer > self.stay_duration:
                self.state = 'leaving'
        elif self.state == 'leaving':
            #print(f"ID {self.id} leaving site")
            self.leave_site()
            if not self.checkInSite():
                self.state = 'wandering'
        self.reproduction()
        self.age += 0.001
        self.check_for_grass()

    def eaten(self):
        self.health = 0
        return
    
    def check_for_grass(self):
        for agent in self._simulation._agents:
            if isinstance(agent, Grass) and self.pos.distance_to(agent.pos) < 10:  # Adjust distance as needed
                self.add_health(2)  # Adjust the health gained as needed
                agent.eaten()  # Remove the
    def death(self):
        if self.health <= 0:
            #print("Rabbit died by fox, health 0")
            self.kill()
            return

    def reproduction(self):
        reproduction_chance = 0.2  # 50% chance to reproduce upon meeting an opposite-sex partner
        if CompetitionSimulation.global_delta_time % self.time_step_d == 0 and self.gender == 'female':
            compatible_partner = next((agent for agent in self.in_proximity_accuracy() if isinstance(agent[0], Rabbits) and agent[0].gender == 'male'), None)
            if compatible_partner and random.random() < reproduction_chance:
                self.reproduce()
        return

    def lose_health(self):
        if CompetitionSimulation.global_delta_time % self.config.time_step_d == 0:
            self.health -= 1
            return
        
    def add_health(self, amount):
        self.health += amount
        #print(f"Rabbit ID {self.id} gained {amount} health, current health: {self.health}")

    def wandering(self):
        '''
        Elicits a random walking behaviour of the Agent
        by picking a random angle +- 30 degrees,
        while checking if the next step is an obstacle
        
        '''


        if random.random() < self.attraction_probability:
            if CompetitionSimulation.global_delta_time % self.time_step_d == 0:
                print(f"ID {self.id} going to rabbit heaven")
                self.move_towards_site()
        else:
            if random.random() < self.config.p_change_direction:
                angle_change = random.uniform(-self.config.max_angle_change, self.config.max_angle_change)
                #print(angle_change)
                self.move = self.move.rotate(angle_change)

        self.move = self.move.normalize() * self.config.movement_speed_r
        next_step = self.pos + self.move * self.config.delta_time
        self.obstacle_avoidance(next_step)
        #self.animation(self.pos, next_step)
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

class Grass(Agent):
    def __init__(self, images, simulation, pos=None, move=None):
        super().__init__(images, simulation, pos, move)
        self.state = 'static'
        self.pos = Vector2(random.randint(0, 750), random.randint(0, 750))
        self.move = Vector2(0, 0)

    def update(self):
        pass

    def eaten(self):
        self.kill()  # Remove grass when eaten
        #print(f"Grass at {self.pos} was eaten")

class CompetitionSimulation(Simulation):
    
    config: CompetitionConfig
    global_delta_time: int = 0

    def __init__(self, config):
        super().__init__(config)
        self.rabbit_population = []
        self.fox_population = []
        self.grass_population = []


    def before_update(self):
        CompetitionSimulation.global_delta_time += 1

        self.save_population_data()
        if random.random() < 0.01:  # Adjust the probability as needed
            self.spawn_grass()

        super().before_update()

    def rabbit_pop(self):
        return self.rabbit_population

    def fox_pop(self):
        return self.fox_population
    
    def spawn_grass(self):
          # Random position within bounds   
        self.spawn_agent(Grass, images=["Assignment_2/images/grass (1) (1).png"])

    def save_population_data(self):
        rabbit_count = sum(1 for agent in self._agents if isinstance(agent, Rabbits) and agent.alive)
        fox_count = sum(1 for agent in self._agents if isinstance(agent, Foxes) and agent.alive)
        self.rabbit_population.append(rabbit_count)
        self.fox_population.append(fox_count)
        list_for_plotting.append((rabbit_count, fox_count))


def run_simulation(n_rabbits, n_foxes, duration):
    global list_for_plotting
    list_for_plotting = []
    
    n_rabbits = n_rabbits
    n_foxes = n_foxes
    CompetitionSimulation(
    CompetitionConfig(
        duration=duration,
        fps_limit=120,
        seed=1,
        movement_speed=1,
        radius=50,
        image_rotation=True,
    )).batch_spawn_agents(n_rabbits, Rabbits, images=[
    "Assignment_2/sprite_frames/sprite_l.png"]).batch_spawn_agents(n_foxes, Foxes, 
                          images=
                          ["Assignment_2/sprite_frames_fox/fox_sprite.png"]).run()
    return list_for_plotting


run_simulation(30, 20, 5000)