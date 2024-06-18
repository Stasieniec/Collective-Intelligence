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
from PIL import Image

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

class Agent(BaseAgent):
    def __init__(self, images, simulation, pos=None, move=None):
        super().__init__(images, simulation, pos, move)
        self._simulation = simulation

class CompetitionConfig(Config):
    delta_time: float = 1.0                         # Increased delta time for larger time steps
    mass: int = 20

    movement_speed_f: float = 2.1                # Increased movement speed for foxes
    movement_speed_r: float = 1.2                   # Increased movement speed for rabbits
    max_angle_change: float = 30.0 

    p_change_direction: float = 0.05

    time_step_d: int = 50                           # Reduced time step for more frequent updates

class Foxes(Agent):
    config: CompetitionConfig

    def __init__(self, images, simulation, pos=None, move=None):
        super().__init__(images, simulation, pos, move)
        if move is None:                            
            angle = random.uniform(0, 360)
            self.move = Vector2(self.config.movement_speed, 0).rotate(angle)

        self.state = 'wandering'
        self.health = 10

        self.reproduction_flag = False
        self.eat_flag = False

    def change_position(self):
        self.there_is_no_escape()
        
    def update(self):
        self.lose_health()
        self.steer_towards_rabbit()
        self.wandering()
        self.death()
        self.eat()
        self.reproduction()

    def steer_towards_rabbit(self):
        closest_rabbit = self.find_closest_rabbit()
        
        if closest_rabbit:
            direction = closest_rabbit.pos - self.pos
            direction.normalize_ip()
            direction *= self.config.movement_speed_f

            # Introduce randomness to the movement direction
            angle_change = random.uniform(-self.config.max_angle_change, self.config.max_angle_change)
            direction = direction.rotate(angle_change)

            next_step = self.pos + direction * self.config.delta_time
            self.obstacle_avoidance(next_step)
            self.pos = next_step  # Update position directly based on next_step

    def hunt_rabbit(self):
        closest_rabbit = self.find_closest_rabbit()
        if closest_rabbit:
            direction = (closest_rabbit.pos - self.pos).normalize()
            self.move = direction * self.config.movement_speed_f
            next_step = self.pos + self.move * self.config.delta_time
            self.obstacle_avoidance(next_step)
            self.pos += self.move * self.config.delta_time

    def find_closest_rabbit(self):
        closest_distance = float('inf')
        closest_rabbit = None

        for agent in self._simulation._agents:
            if isinstance(agent, Rabbits) and agent.alive:
                distance = self.pos.distance_to(agent.pos)
                if distance < closest_distance:
                    closest_distance = distance
                    closest_rabbit = agent
        
        return closest_rabbit
    
    def predator(self):
        pass

    def eat(self):
        in_proximity = self.in_proximity_accuracy()
        for agent, dist in in_proximity:
            if isinstance(agent, Rabbits):
                if dist < 30:
                    self.health += 5
                    print(f"Fox ID {self.id} ate: +5HP, health: {self.health}")
                    agent.eaten()
                    agent.death()
                    self.eat_flag = True
            

    def in_proximity_accuracy(self):
        agent_distances = []
        for agent in self._simulation._agents:
            if isinstance(agent, Rabbits) and agent.alive:
                distance = self.pos.distance_to(agent.pos)
                agent_distances.append((agent, distance))
        agent_distances.sort(key=lambda x: x[1])  # Sort by distance
        return agent_distances[:5]  # Return closest 5 agents
                
    def reproduction(self):
        if self.eat_flag:  # Adjust the probability as needed
            self.reproduce()
            self.eat_flag = False


    def lose_health(self):
        if CompetitionSimulation.global_delta_time % self.config.time_step_d == 0:
            self.health -= 1
            return

    def death(self):
        if self.health == 0:
            print(f"Fox ID {self.id} died of starvation, silly fox")
            self.kill()
            return

    def wandering(self):
        if random.random() < self.config.p_change_direction:
            angle_change = random.uniform(-self.config.max_angle_change, self.config.max_angle_change)
            self.move = self.move.rotate(angle_change)

        self.move = self.move.normalize() * self.config.movement_speed_f
        next_step = self.pos + self.move * self.config.delta_time
        self.obstacle_avoidance(next_step)
        self.pos = next_step  # Update position directly based on next_step
    
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
    p_reproduction: float = 0.1

    time_step_d: int = 100
    fleeing_distance: int = 100  # Distance threshold to start fleeing

    def __init__(self, images, simulation, pos=None, move=None):
        super().__init__(images, simulation, pos, move)
        if move is None:
            angle = random.uniform(0, 360)
            self.move = Vector2(self.config.movement_speed, 0).rotate(angle)

        self.state = 'wandering'
        self.health = 1
        self.frame = 0
        self.energy = 5

    def update(self):
        if self.should_flee():
            self.flee_from_fox()
        else:
            self.wandering()

        self.check_for_grass()
        self.reproduction()
        
    def lose_health(self):
        if CompetitionSimulation.global_delta_time % self.config.time_step_d == 0:
            self.health -= 1
            return
        
    def add_health(self, amount):
        self.health += amount
        print(f"Rabbit ID {self.id} gained {amount} health, current health: {self.health}")

    def should_flee(self):
        closest_fox = self.find_closest_fox()
        if closest_fox:
            return self.pos.distance_to(closest_fox.pos) < self.fleeing_distance
        return False

    def flee_from_fox(self):
        closest_fox = self.find_closest_fox()
        if closest_fox:
            direction = (self.pos - closest_fox.pos).normalize()
            self.move = direction * self.config.movement_speed_r
            next_step = self.pos + self.move * self.config.delta_time
            self.obstacle_avoidance(next_step)
            self.boundary_avoidance(next_step)
            self.animation(self.pos, next_step)
            self.pos += self.move * self.config.delta_time
        else:
            self.wandering()

    def find_closest_fox(self):
        closest_fox = None
        min_dist = float('inf')
        for agent in self._simulation._agents:
            if isinstance(agent, Foxes) and agent.alive:
                dist = self.pos.distance_to(agent.pos)
                if dist < min_dist:
                    min_dist = dist
                    closest_fox = agent
        return closest_fox

    def reproduction(self):
        if CompetitionSimulation.global_delta_time % self.time_step_d == 0:
            if random.random() < self.p_reproduction:
                self.reproduce()

    def wandering(self):
        if random.random() < self.config.p_change_direction:
            angle_change = random.uniform(-self.config.max_angle_change, self.config.max_angle_change)
            self.move = self.move.rotate(angle_change)

        self.move = self.move.normalize() * self.config.movement_speed_r
        next_step = self.pos + self.move * self.config.delta_time
        self.obstacle_avoidance(next_step)
        self.boundary_avoidance(next_step)
        self.animation(self.pos, next_step)
        self.pos = next_step

    def obstacle_avoidance(self, next_step):
        while self.is_obstacle(next_step):
            angle_change = random.uniform(-self.config.max_angle_change, self.config.max_angle_change)
            self.move = self.move.rotate(angle_change)
            next_step = self.pos + self.move * self.config.delta_time

    def boundary_avoidance(self, next_step):
        margin = 50  # Distance from the edge to start avoiding
        environment_width, environment_height = 750, 750  # Size of your simulated environment

        if next_step.x < margin:
            self.move.x = abs(self.move.x)  # Move away from left edge
        elif next_step.x > environment_width - margin:
            self.move.x = -abs(self.move.x)  # Move away from right edge

        if next_step.y < margin:
            self.move.y = abs(self.move.y)  # Move away from top edge
        elif next_step.y > environment_height - margin:
            self.move.y = -abs(self.move.y)  # Move away from bottom edge

        # Ensure rabbits do not go out of bounds
        self.pos.x = max(margin, min(self.pos.x, environment_width - margin))
        self.pos.y = max(margin, min(self.pos.y, environment_height - margin))

    def is_obstacle(self, position):
        if position.x < 0 or position.x >= 750 or position.y < 0 or position.y >= 750:
            return True
        return False

    def animation(self, current_pos, next_pos):
        dx = current_pos.x - next_pos.x
        dy = current_pos.y - next_pos.y

        # Determine the direction of movement
        if dx < 0:
            start_frame = 0  # Moving left
        elif dx > 0:
            start_frame = 8  # Moving right

        if dy < 0:
            start_frame = 8  # Moving down
        elif dy > 0:
            start_frame = 24  # Moving up

        if CompetitionSimulation.global_delta_time % 8 == 0:
            self.change_image(start_frame + self.frame)
            self.frame += 1

        if self.frame == 8:
            self.frame = 0

    def check_for_grass(self):
        for agent in self._simulation._agents:
            if isinstance(agent, Grass) and self.pos.distance_to(agent.pos) < 10:  # Adjust distance as needed
                self.add_health(2)  # Adjust the health gained as needed
                agent.eaten()  # Remove the grass

    def eaten(self):
        self.health = 0  # Define what happens when a rabbit is eaten
        self.death()  # Call the death method when a rabbit is eaten

    def death(self):
        if self.health == 0:
            print("Rabbit died by fox, health 0")
            self.kill()  # Implement any other actions related to rabbit death


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
        print(f"Grass at {self.pos} was eaten")

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
    '''
    def spawn_grass(self):
        pos = Vector2(random.randint(0, 750), random.randint(0, 750))  # Random position within bounds
        grass = Grass(images=["Assignment_2/images/grass.png"], simulation=self, pos=pos)
        self.spawn_agent(grass, ["Assignment_2/images/grass.png"])
        self.grass_population.append(grass)
    '''
    def spawn_grass(self):
          # Random position within bounds
          
        self.spawn_agent(Grass, images=["Assignment_2/images/grass (1) (1).png"])
    def save_population_data(self):
        rabbit_count = sum(1 for agent in self._agents if isinstance(agent, Rabbits) and agent.alive)
        fox_count = sum(1 for agent in self._agents if isinstance(agent, Foxes) and agent.alive)
        self.rabbit_population.append(rabbit_count)
        self.fox_population.append(fox_count)


n_rabbits = 16
n_foxes = 4

#resize_image("Assignment_2/images/grass.png", "Assignment_2/images", (100, 100))


df = (CompetitionSimulation(
    CompetitionConfig(
        #duration=10_000,
        fps_limit=60,  
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
    ]).batch_spawn_agents(n_foxes, Foxes, images=["Assignment_0/images/triangle@50px.png"]).run()

.snapshots.group_by("frame", "image_index")
.agg(pl.count("id").alias("agents"))

)

print(df)

plot = sns.relplot(x=df["frame"], y =df["agents"], hue=df["image_index"])
plot.savefig("population.png", dpi = 300)