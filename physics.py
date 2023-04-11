import math
import pygame
from pygame.math import Vector2

G = Vector2(0, 9.81)
AIR_VISCOSITY = .148e-4
AIR_K = 6 * math.pi * AIR_VISCOSITY

MAX_TRAJECTORY_POINTS = 199


class Body:
    def __init__(self, app, position: Vector2, mass: float, radius: float, elasticity: float, static: bool = False, show_trajectory=False):
        self.app = app
        self.position = position
        self.velocity = Vector2(0, 0)
        self.mass = mass
        self.inv_mass = 1 / mass
        self.radius = radius
        self.elasticity = elasticity
        self.static = static
        self.trajectory = []
        self.show_trajectory = show_trajectory

    def create_trajectory_points(self):
        if self.static or not self.show_trajectory:
            return
        self.trajectory = []
        t = 0
        while True:
            t += 0.01
            self.trajectory.append(
                self.position + self.velocity * t + G * t * t / 2)
            if self.trajectory[-1].y > self.app.screen.get_size()[1]:
                break
            if len(self.trajectory) > MAX_TRAJECTORY_POINTS:
                break

    def update(self, deltatime: float):
        self.controls()
        self.check_collision()
        if self.static:
            return
        self.velocity += G * deltatime
        wsx, wsy = self.app.screen.get_size()

        if self.position.x + self.radius > wsx:
            self.position.x = wsx - self.radius
            self.velocity.x *= -self.elasticity
        if self.position.x - self.radius < 0:
            self.position.x = self.radius
            self.velocity.x *= -self.elasticity
        if self.position.y + self.radius > wsy:
            self.position.y = wsy - self.radius
            self.velocity.y *= -self.elasticity
        if self.position.y - self.radius < 0:
            self.position.y = self.radius
            self.velocity.y *= -self.elasticity

        # if self.velocity.length() > 1000:
        #     self.velocity.scale_to_length(1000)

        self.velocity -= AIR_K * self.radius * self.velocity * deltatime

        self.position += self.velocity * deltatime
        self.create_trajectory_points()

    def draw(self):
        if self.show_trajectory:
            last_point = None
            for point in self.trajectory:
                if last_point:
                    pygame.draw.aaline(self.app.screen, pygame.color.Color(
                        "white"), last_point, point)
                last_point = point
        color = pygame.color.Color("white")
        if self.static:
            color = pygame.color.Color("red")
        pygame.draw.circle(self.app.screen, color, self.position, self.radius)
        #pygame.draw.rect(self.app.screen, pygame.color.Color("red"), self.rect, 1)
        if self.velocity.length() > 0 and self.radius > 7:
            direction = self.velocity.normalize()
            pygame.draw.line(self.app.screen, pygame.color.Color(
                "red"), self.position, self.position + direction * self.radius)

    def check_collision(self):
        bodys = self.app.quad_tree.query_range(self.rect)
        for body in bodys:
            if body is not self:
                self.collide(body)

    def collide(self, other: 'Body'):
        distance = self.position.distance_to(other.position)
        if distance < self.radius + other.radius:
            try:
                c_direction = (self.position - other.position).normalize()

                self.position += c_direction * \
                    (self.radius + other.radius - distance)
                other.position -= c_direction * \
                    (self.radius + other.radius - distance)

                relative_velocity = self.velocity - other.velocity
                if relative_velocity.dot(c_direction) > 0:
                    return

                e = min(self.elasticity, other.elasticity)
                j = -(1 + e) * relative_velocity.dot(c_direction)
                j /= self.inv_mass + other.inv_mass
                impulse = c_direction * j

                self.apply_force(impulse)
                other.apply_force(-impulse)
            except Exception:
                pass

    def controls(self):
        mouse_pressed = pygame.mouse.get_pressed()
        key_pressed = pygame.key.get_pressed()
        if mouse_pressed[2]:
            mouse_position = Vector2(pygame.mouse.get_pos())
            if self.rect.collidepoint(mouse_position):
                # self.position = mouse_position
                self.app.bodys.remove(self)
                return
        if key_pressed[pygame.K_k]:
            mouse_position = Vector2(pygame.mouse.get_pos())
            if self.rect.collidepoint(mouse_position):
                self.static = not self.static

    def apply_force(self, force: Vector2):
        self.velocity += force * self.inv_mass

    @property
    def rect(self):
        return pygame.Rect(self.position.x - self.radius, self.position.y - self.radius, self.radius * 2, self.radius * 2)


class WireSegment:
    def __init__(self, app, body1: Body, body2: Body):
        self.app = app
        self.body1 = body1
        self.body2 = body2
        self.length = body1.position.distance_to(body2.position) - \
            body1.radius - body2.radius

    def update(self, deltatime: float):
        if self.body1 not in self.app.bodys or self.body2 not in self.app.bodys:
            # provvisorio
            self.app.wires[0].wire_segments.remove(self)
            return
        if (self.body2.position - self.body1.position).length() == 0:
            return
        distance = self.body1.position.distance_to(self.body2.position) - \
            self.body1.radius - self.body2.radius
        dx = self.body2.position.x - self.body1.position.x
        dy = self.body2.position.y - self.body1.position.y
        angle = math.atan2(dy, dx)
        dl = distance - self.length
        body1_force = Vector2(
            math.cos(angle), math.sin(angle)) * dl
        body2_force = Vector2(
            math.cos(angle), math.sin(angle)) * -dl
        # body1_force = body1_force * self.body1.velocity.length() * deltatime
        # body2_force = body2_force * self.body2.velocity.length() * deltatime
        if not self.body1.static:
            self.body1.apply_force(body1_force)
        if not self.body2.static:
            self.body2.apply_force(body2_force)

    def draw(self):
        pygame.draw.aaline(self.app.screen, pygame.color.Color(
            "white"), self.body1.position, self.body2.position, 2)


class Wire:
    def __init__(self, app, start: Vector2, end: Vector2, segments: int):
        self.app = app
        self.start = start
        self.end = end
        self.segments = segments
        self.bodys = []
        self.wire_segments = []
        self.create_bodys()
        self.create_wire_segments()

    def create_bodys(self):
        for i in range(self.segments):
            static = False
            radius = 2
            if i == 0 or i == self.segments - 1:
                static = True
                radius = 5
            position = Vector2(self.start.x + (self.end.x - self.start.x) / self.segments * i,
                               self.start.y + (self.end.y - self.start.y) / self.segments * i)
            self.bodys.append(
                Body(self.app, position, radius, radius, 0.3, static))
            self.app.bodys.append(self.bodys[i])

    def create_wire_segments(self):
        for i in range(self.segments - 1):
            self.wire_segments.append(
                WireSegment(self.app, self.bodys[i], self.bodys[i + 1]))

    def update(self, deltatime: float):
        for wire_segment in self.wire_segments:
            wire_segment.update(deltatime)

    def draw(self):
        for wire_segment in self.wire_segments:
            wire_segment.draw()


class Cloth:
    def __init__(self, app, position: Vector2, width: int, height: int, segments: int):
        self.app = app
        self.position = position
        self.width = width
        self.height = height
        self.segments = segments
        self.wire_segments = []
        self.bodys = []

        self.create_bodys()
        self.create_wires()

    def create_bodys(self):
        for i in range(self.segments):
            for j in range(self.segments):
                static = False
                radius = 2
                if (j == 0 and (i == 0 or i == self.segments - 1)):
                    radius = 5
                    static = True
                position = Vector2(self.position.x + self.width / self.segments * i,
                                   self.position.y + self.height / self.segments * j)
                self.bodys.append(
                    Body(self.app, position, radius, radius, 0.3, static))
                self.app.bodys.append(self.bodys[-1])

    def create_wires(self):
        for i in range(self.segments):
            for j in range(self.segments):
                if i < self.segments - 1:
                    self.wire_segments.append(
                        WireSegment(self.app, self.bodys[i + j * self.segments], self.bodys[i + 1 + j * self.segments]))
                if j < self.segments - 1:
                    self.wire_segments.append(
                        WireSegment(self.app, self.bodys[i + j * self.segments], self.bodys[i + (j + 1) * self.segments]))
                if i < self.segments - 1 and j < self.segments - 1:
                    self.wire_segments.append(
                        WireSegment(self.app, self.bodys[i + j * self.segments], self.bodys[i + 1 + (j + 1) * self.segments]))
                    self.wire_segments.append(
                        WireSegment(self.app, self.bodys[i + 1 + j * self.segments], self.bodys[i + (j + 1) * self.segments]))

    def update(self, deltatime: float):
        for wire in self.wire_segments:
            wire.update(deltatime)

    def draw(self):
        for wire in self.wire_segments:
            wire.draw()
