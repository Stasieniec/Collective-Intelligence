from vi import Agent, Simulation, Config
from pygame.math import Vector2
import random
import math
import pygame as pg


class AggregationConfig(Config):
    delta_time: float = 0.5
    mass: int = 20  
    movement_speed: float = 1.0

    max_angle_change: float = 30.0              # The maximum angle to change direction into, small for smoothness
    p_change_direction: float = 0.1             # The probability of an agent changing direction, is small for smoothness

    t_join_base: float = 100.0                  # The base time steps needed to stop
    t_join_noise: float = 2000.0               # The noise to add to the base time steps

    p_base_leaving: float = 0.05                 # The base probability for leaving 
    p_base_joining: float = 0.5                 # The base probability for joining 

    time_step_d: int = 200                      # The number of time steps before checking to leave


class Particle(Agent):
    config: AggregationConfig

    def __init__(self, images, simulation, pos=None, move=None):
        super().__init__(images, simulation, pos, move)

        # Initialise move to a random angle, (0 to 360)
        if move is None:
            angle = random.uniform(0, 360)
            self.move = Vector2(self.config.movement_speed, 0).rotate(angle)
        # Initialise the state of the agent
        self.state = 'wandering'
        # Initialise the joining timer
        self.timer = 0

    def change_position(self):
        self.there_is_no_escape()  # The Agents teleport to the opposite side of the screen

    def wandering(self):  
        '''
        Agent elicits random walking behaviour
        '''  
        # Probability to change direction
        if random.random() < self.config.p_change_direction:
            # Choose a random angle to rotate the current direction by
            angle_change = random.uniform(-self.config.max_angle_change, self.config.max_angle_change)
            # Rotate the move by the chosen angle
            self.move = self.move.rotate(angle_change)
        
        # Normalise move to keep the speed constant
        self.move = self.move.normalize() * self.config.movement_speed
        # Update the agent's position
        self.pos += self.move * self.config.delta_time

        if self.checkInSite() and self.joiningProbability(self.in_proximity_accuracy().count()):
            #print("joining")
            self.state = 'joining'

    def joining(self):
        '''
        timer for transitions from wandering to still based on t_join duration
        '''
    
        self.t_join = self.config.t_join_base + abs(random.gauss(0, self.config.t_join_noise))
        #print(self.t_join)

        if self.timer > self.t_join:
            #print("Still")
            self.state = 'still'
        else:
            self.timer += self.config.delta_time

    def joiningProbability(self, in_proximity):
        ''' 
        the more neighbours, the more chance of joining

        p_join = p_base * N

        '''
        neighbour_count = in_proximity
        # Directly multiplying neighbour count with base probability
        p_joining = self.config.p_base_joining * (neighbour_count+1)
        return p_joining

    def still(self):
        # Freeze the current movement to stay still
        self.freeze_movement()
        # Pick a random float for the probability below
        rand = random.random()
        # Count the number of neighbours in the radius
        in_proximity = self.in_proximity_accuracy().count()
        print(AggregationSimulation.global_delta_time) #debugging
        # Calculate when to consider leaving every 'd' time steps
        if AggregationSimulation.global_delta_time % self.config.time_step_d == 0:
            print(self.leavingProbability(in_proximity)) #debugging

            if rand < self.leavingProbability(in_proximity):
                print(f"random int",{rand}) 
                print("leaving")
                # Change the state to leaving
                self.state = 'leaving'
                # Continue the movement to start wandering again
                self.continue_movement()


    def leaving(self):
        if random.random() < self.config.p_change_direction:
            # Choose a random angle to rotate the current direction by
            angle_change = random.uniform(-self.config.max_angle_change, self.config.max_angle_change)
            # Rotate the move by the chosen angle
            self.move = self.move.rotate(angle_change)
        
        # Normalise move to keep the speed constant
        self.move = self.move.normalize() * self.config.movement_speed
        # Update the agent's position
        self.pos += self.move * self.config.delta_time
        
        

    def leavingProbability(self, in_proximity):
        '''
        the more neighbours there are, the less chance of leaving

        p_leave = p_base / N

        '''
        neighbour_count = in_proximity
        # Dividing the base probability by the neighbour count to get the inverse
        p_leaving = self.config.p_base_leaving / (1 + neighbour_count)

        return p_leaving

    def checkInSite(self):
        intersections = list(self.obstacle_intersections())
        return bool(intersections)

    def update(self):

        if self.state == 'wandering':           # Agent performs the walking/wandering behavior
            self.wandering()
        elif self.state == 'joining':           # Agent performs the joining behavior
            self.joining()
            self.wandering()
        elif self.state == 'still':             # Agent performs the still behavior
            self.still()
        elif self.state == 'leaving':           # Agent performs the leaving behaviour
            self.leaving()
            # Checks if the agent has crossed the site boundary
            if self.checkInSite():              
                self.state = 'wandering'   

        return super().update()
    




class AggregationSimulation(Simulation):
    config: AggregationConfig
    init_pos: Vector2 = Vector2(0, 0)

    global_delta_time: int = 0

    def before_update(self):
        super().before_update()

        AggregationSimulation.global_delta_time += 1
        
        #temporarily testing the joining -> still functionality by pressing 'M'   
        for event in pg.event.get():
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_m:
                    for agent in self._agents:
                        agent.state = "joining"



(
    AggregationSimulation(
        AggregationConfig(
            duration=10_000, 
            fps_limit=0,
            seed=1,
            movement_speed= 1,
            radius=75
        )
    )
    .batch_spawn_agents(50, Particle, images=["Assignment_0/images/green.png"])
    .spawn_obstacle("Assignment_0/images/bubble-full.png",x=375, y=375)
    .run()
)
