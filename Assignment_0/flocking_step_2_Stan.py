from enum import Enum, auto
import pygame as pg
from pygame.math import Vector2
from vi import Agent, Simulation
from vi.config import Config, dataclass, deserialize
import datetime
from datetime import timedelta
import arcade
import math

@deserialize
@dataclass
class FlockingConfig(Config):
    # You can change these for different starting weights
    alignment_weight: float = 0.5
    cohesion_weight: float = 0.5
    separation_weight: float = 0.5

    #sum_vel: pg.math.Vector2 = 0,0
    #sum_pos: pg.math.Vector2 = 0,0

    # These should be left as is.
    delta_time: float = 0.5       #or 3                         # To learn more https://gafferongames.com/post/integration_basics/ 
    mass: int = 20                                            

    def weights(self) -> tuple[float, float, float]:
        return (self.alignment_weight, self.cohesion_weight, self.separation_weight)


class Bird(Agent):
    config: FlockingConfig

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cursor_pos: Vector2 = Vector2(0, 0)
        self.flock_to_cursor = False

    def get_alignment_weigth(self)-> float:
        return self.config.alignment_weight
    
    
    #cursor_pos: Vector2 = Vector2(0, 0)

    def change_position(self):
        # Pac-man-style teleport to the other end of the screen when trying to escape
        self.there_is_no_escape()

        # timedelta = self.config.delta_time

        in_proximity = list(self.in_proximity_accuracy())

        #YOUR CODE HERE -----------
        #self.pos += self.move

        if self.in_proximity_accuracy().count() == 0:
            self.pos += self.move * self.config.delta_time
        else:


            al, sum_vel = self.alignment(in_proximity)
            a =  al * self.config.alignment_weight
            s = self.separation(in_proximity) * self.config.separation_weight
            c = self.cohesion(in_proximity) * self.config.cohesion_weight


            cursor_force = Vector2(0, 0)

            # When the boid is in the follow the cursor mode
            if self.flock_to_cursor:
                cursor_force = self.cursor_attraction()
                print("Cursor Force:", cursor_force)
                distance_to_cursor = self.cursor_pos.distance_to(self.pos)

                # Don't start too fast
                cursor_force = cursor_force.normalize()

                # Go faster when far away
                if distance_to_cursor > 200:
                    cursor_force *= 3       
                
                # The boids should not get stuck in the cursor position
                if distance_to_cursor < 40:
                    cursor_force *= -1
                    s = s.normalize()
                elif distance_to_cursor <= 50:
                    s *= 1.1
                elif distance_to_cursor <= 100:
                    s *= 1.2


            avoidance_force = self.obstacle_avoidance(in_proximity)

            # Total force
            f_total = (a+s+c+cursor_force + avoidance_force)/self.config.mass

            if self.move.length() > sum_vel.length():
                self.move.normalize() * sum_vel
            
            # Move the boid
            self.move += f_total
            self.pos += self.move * self.config.delta_time

        #END CODE -----------------
        
    def cursor_attraction(self):
            force = self.cursor_pos - self.pos
            print("Cursor Position:", self.cursor_pos)
            return force

    def obstacle_avoidance(self,in_proximity):
        avoidance_radius = 100
        avoidance_force = Vector2(0,0)
        for agent, dist in in_proximity:
            if isinstance(agent, RedCube):
                distance_to_cube = self.pos.distance_to(agent.pos)
                if distance_to_cube < avoidance_radius:
                    avoidance_force += self.pos - agent.pos
        return avoidance_force

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


class RedCube(Agent):
    def __init__(self, pos: Vector2, images: pg.Surface, simulation: Simulation, *args, **kwargs):
        super().__init__([images], simulation, *args, **kwargs)
        self.pos = pos
    def change_position(self):
        pass


class Selection(Enum):
    ALIGNMENT = auto()
    COHESION = auto()
    SEPARATION = auto()


class FlockingLive(Simulation):
    selection: Selection = Selection.ALIGNMENT
    config: FlockingConfig
    cursor_pos: Vector2 = Vector2(0, 0)

    def handle_event(self, by: float):
        if self.selection == Selection.ALIGNMENT:
            self.config.alignment_weight += by
        elif self.selection == Selection.COHESION:
            self.config.cohesion_weight += by
        elif self.selection == Selection.SEPARATION:
            self.config.separation_weight += by

    def before_update(self):
        super().before_update()
        for bird in self._agents:
            if isinstance(bird, Bird):
                bird.cursor_pos = self.cursor_pos

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
                elif event.key == pg.K_m:
                    for agent in self._agents:
                        if isinstance(agent, Bird):
                            agent.flock_to_cursor = not agent.flock_to_cursor
            elif event.type == pg.MOUSEMOTION:
                self.cursor_pos = Vector2(event.pos)
            elif event.type == pg.MOUSEBUTTONDOWN:
                if event.button == 1:
                    cube_pos = Vector2(event.pos)
                    self.spawn_red_cube(cube_pos)

        a, c, s = self.config.weights()
        # print(f"A: {a:.1f} - C: {c:.1f} - S: {s:.1f}")

    def spawn_red_cube(self, position: Vector2):
        cube_image = "Assignment_0/images/red.png"
        cube_image = pg.image.load(cube_image).convert_alpha()
        cube = RedCube(pos=position, images=cube_image, simulation=self)
        self._agents.add(cube)


(
    FlockingLive(
        FlockingConfig(
            image_rotation=True,
            movement_speed=1,
            radius=50,
            #seed=1,
            fps_limit=0
            #duration=10_000
        )
    )
    #.batch_spawn_agents(50, Bird, images=["Assignment_0/images/bird.png"])
    .batch_spawn_agents(50, Bird, images=["Assignment_0/images/bird.png"])
    .run()
)