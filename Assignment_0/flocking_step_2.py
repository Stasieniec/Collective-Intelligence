from enum import Enum, auto
import pygame as pg
from pygame.math import Vector2
from vi import Agent, Simulation
from vi.config import Config, dataclass, deserialize
import datetime
from datetime import timedelta
import arcade

@deserialize
@dataclass
class FlockingConfig(Config):
    # You can change these for different starting weights
    alignment_weight: float = 1.0
    cohesion_weight: float = 0.5
    separation_weight: float = 1.0

    #sum_vel: pg.math.Vector2 = 0,0
    #sum_pos: pg.math.Vector2 = 0,0

    # These should be left as is.
    delta_time: float = 0.5                                   # To learn more https://gafferongames.com/post/integration_basics/ 
    mass: int = 20                                            

    def weights(self) -> tuple[float, float, float]:
        return (self.alignment_weight, self.cohesion_weight, self.separation_weight)


class Bird(Agent):
    config: FlockingConfig
    cursor_pos: Vector2 = Vector2(0, 0)

    def get_alignment_weigth(self)-> float:
        return self.config.alignment_weight

    def change_position(self):
        # Pac-man-style teleport to the other end of the screen when trying to escape
        self.there_is_no_escape()

        timedelta = self.config.delta_time

        #YOUR CODE HERE -----------

        # Calculate total change
        a = self.alignment() * self.config.alignment_weight
        s = self.separation() * self.config.separation_weight
        c = self.cohesion() * self.config.cohesion_weight
        cursor_force = self.cursor_attraction()

        f_total = (a + s + c + cursor_force) / self.config.mass

        self.move += f_total

        # Normalize the change
        max_velocity = self.config.movement_speed
        if self.move.length() > max_velocity:
            self.move = self.move.normalize() * max_velocity

        self.pos += self.move * timedelta

        #END CODE -----------------

    def alignment(self):
        in_proximity = list(self.in_proximity_accuracy())
            
        sum_vel = Vector2(0,0)
        for agent, dist in in_proximity:
            vel = agent.move
            sum_vel += vel
        
        if len(in_proximity) > 0:
            avg_vel = sum_vel / len(in_proximity)
        else:
            avg_vel = sum_vel

        Vboid = self.move
        alignment = avg_vel - Vboid

        return alignment

    def separation(self):
        in_proximity = list(self.in_proximity_accuracy())

        sum_pos = Vector2(0,0)
        for agent, dist in in_proximity:
            sum_pos += self.pos - agent.pos

        if len(in_proximity) > 0:
            avg_pos = sum_pos / len(in_proximity)
        else:
            avg_pos = sum_pos

        return avg_pos

    def cohesion(self):
        
        in_proximity = list(self.in_proximity_accuracy())

        sum_pos = Vector2(0,0)
        for agent, dist in in_proximity:
            sum_pos += agent.pos

        if len(in_proximity) > 0:
            avg_pos = sum_pos / len(in_proximity)
        else:
            avg_pos = sum_pos

        fc = avg_pos - self.pos

        Vboid = self.move
        cohesion = fc - Vboid

        return cohesion
    
    def cursor_attraction(self):
        force = self.cursor_pos - self.pos
        return force


#the closer boid is, the more it steers left or right

#or for each boid, calculate the path ahead, and if it is blocked, change direction
""" def obstacle_avoidance(self, obstacle):
        # Avoid collision with obstacles at all cost
    if self.distance(obstacle) < 45:
		self.velocityX = -1 * (obstacle.real_x - self.rect.x)
		self.velocityY = -1 * (obstacle.real_y - self.rect.y)

    else:
		self.velocityX += -1 * (obstacle.real_x - self.rect.x) / self.obstacle_avoidance_weight
		self.velocityY += -1 * (obstacle.real_y - self.rect.y) / self.obstacle_avoidance_weight
     """

class Selection(Enum):
    ALIGNMENT = auto()
    COHESION = auto()
    SEPARATION = auto()


class FlockingLive(Simulation):
    selection: Selection = Selection.ALIGNMENT
    config: FlockingConfig

    def handle_event(self, by: float):
        if self.selection == Selection.ALIGNMENT:
            self.config.alignment_weight += by
        elif self.selection == Selection.COHESION:
            self.config.cohesion_weight += by
        elif self.selection == Selection.SEPARATION:
            self.config.separation_weight += by

    def before_update(self):
        super().before_update()

        for event in pg.event.get():
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_UP:
                    self.handle_event(by=0.1)
                elif event.key == pg.K_DOWN:
                    self.handle_event(by=-0.1)
                elif event.key == pg.K_1:
                    self.selection = Selection.ALIGNMENT
                elif event.key == pg.K_2:
                    self.selection = Selection.COHESION
                elif event.key == pg.K_3:
                    self.selection = Selection.SEPARATION
            elif event.type == pg.MOUSEMOTION:
                cursor_pos = Vector2(event.pos)
                # TODO Update cursor position for all agents

        a, c, s = self.config.weights()
        print(f"A: {a:.1f} - C: {c:.1f} - S: {s:.1f}")


(
    FlockingLive(
        FlockingConfig(
            image_rotation=True,
            movement_speed=2,
            radius=20,
            #seed=1,
        )
    )
    .batch_spawn_agents(50, Bird, images=["images/bird.png"])
    .run()
)