import math
import pygame
from pygame.math import Vector2
from constants import G, AIR_K, MAX_TRAJECTORY_POINTS


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


class Spring:
    def __init__(self, app, body1: Body, body2: Body, strength: float = 1, damping: float = 0.01):
        self.app = app
        self.body1 = body1
        self.body2 = body2
        self.strength = strength
        self.damping = damping
        self.length = body1.position.distance_to(body2.position) - \
            body1.radius - body2.radius

    def update(self, deltatime: float):
        if self.body1 not in self.app.bodys or self.body2 not in self.app.bodys:
            self.app.springs.remove(self)
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
            math.cos(angle), math.sin(angle)) * dl * self.strength
        body2_force = Vector2(
            math.cos(angle), math.sin(angle)) * -dl * self.strength
        body1_force -= self.body1.velocity * self.damping * deltatime
        body2_force -= self.body2.velocity * self.damping * deltatime
        if not self.body1.static:
            self.body1.apply_force(body1_force * self.body1.mass)
        if not self.body2.static:
            self.body2.apply_force(body2_force * self.body2.mass)

    def draw(self):
        pygame.draw.aaline(self.app.screen, pygame.color.Color(
            "white"), self.body1.position, self.body2.position, 2)


class SoftBody:
    def __init__(self, app):
        self.app = app
        self.springs = []
        self.bodys = []

    def update(self):
        for spring in self.springs:
            if spring not in self.app.springs:
                self.springs.remove(spring)
        for body in self.bodys:
            if body not in self.app.bodys:
                self.bodys.remove(body)


class Wire(SoftBody):
    def __init__(self, app, start: Vector2, end: Vector2, segments: int):
        super().__init__(app)
        self.start = start
        self.end = end
        self.segments = segments
        self.create_bodys()
        self.create_springs()

    def create_bodys(self):
        for i in range(self.segments):
            static = False
            radius = 2
            if i == 0 or i == self.segments - 1:
                static = True
                radius = 5
            self.bodys.append(Body(self.app, self.start + (self.end - self.start)
                              * (i / self.segments), 2, radius, 0.5, static=static))
        self.app.bodys.extend(self.bodys)

    def create_springs(self):
        for i in range(len(self.bodys) - 1):
            self.springs.append(
                Spring(self.app, self.bodys[i], self.bodys[i + 1]))
        self.app.springs.extend(self.springs)


class RectangleSoftBody(SoftBody):
    def __init__(self, app, position: Vector2, width: int, height: int, segments: list):
        super().__init__(app)
        self.position = position
        self.width = width
        self.height = height
        self.segments = segments

        self.create_bodys()
        self.create_springs()

    def create_bodys(self):
        for i in range(self.segments[0]):
            for j in range(self.segments[1]):
                static = False
                if (i == 0 or i % 2 == 0) and j == 0:
                    static = True
                position = Vector2(self.position.x + self.width / self.segments[0] * i,
                                   self.position.y + self.height / self.segments[1] * j)
                self.bodys.append(
                    Body(self.app, position, 2, 2, 0.3, static))
                self.app.bodys.append(self.bodys[-1])

    def create_springs(self):
        for i in range(self.segments[0]):
            for j in range(self.segments[1]):
                if i != self.segments[0] - 1:
                    self.springs.append(
                        Spring(self.app, self.bodys[i * self.segments[1] + j], self.bodys[(i + 1) * self.segments[1] + j]))
                if j != self.segments[1] - 1:
                    self.springs.append(
                        Spring(self.app, self.bodys[i * self.segments[1] + j], self.bodys[i * self.segments[1] + j + 1]))
                if i != self.segments[0] - 1 and j != self.segments[1] - 1:
                    self.springs.append(
                        Spring(self.app, self.bodys[i * self.segments[1] + j], self.bodys[(i + 1) * self.segments[1] + j + 1]))
                if i != self.segments[0] - 1 and j != 0:
                    self.springs.append(
                        Spring(self.app, self.bodys[i * self.segments[1] + j], self.bodys[(i + 1) * self.segments[1] + j - 1]))
        self.app.springs.extend(self.springs)


class CircleSoftBody(SoftBody):
    def __init__(self, app, position: Vector2, radius: int, segments: int):
        super().__init__(app)
        self.position = position
        self.radius = radius
        self.segments = segments
        self.springs = []
        self.bodys = []
        self.center = Body(self.app, self.position, 7, 5, 0.7)
        self.app.bodys.append(self.center)

        self.create_bodys()
        self.create_springs()

    def create_bodys(self):
        for i in range(self.segments):
            position = Vector2(self.position.x + self.radius * math.cos(
                math.radians(360 / self.segments * i)), self.position.y + self.radius * math.sin(math.radians(360 / self.segments * i)))
            self.bodys.append(
                Body(self.app, position, 2, 3, 0.5))
            self.app.bodys.append(self.bodys[-1])

    def create_springs(self):
        for i in range(self.segments):
            self.springs.append(
                Spring(self.app, self.bodys[i], self.bodys[(i + 1) % self.segments]))
            self.springs.append(Spring(
                self.app, self.bodys[i], self.bodys[(i + 2) % self.segments]))
            self.springs.append(Spring(
                self.app, self.bodys[i], self.bodys[(i + 3) % self.segments]))
            self.springs.append(Spring(
                self.app, self.bodys[i], self.center))
        self.app.springs.extend(self.springs)

    def update(self):
        super().update()
        self.check_collision()

    def collide(self, other: 'CircleSoftBody'):
        try:
            distance = (self.center.position - other.center.position).length()
            c_direction = (self.center.position - other.center.position).normalize()
            self.center.position += c_direction * \
                (self.radius + other.radius - distance)
            other.center.position -= c_direction * \
                (self.radius + other.radius - distance)
            rv = self.center.velocity - other.center.velocity
            if rv.dot(c_direction) > 0:
                return
            e = min(self.center.elasticity, other.center.elasticity)
            j = -(1 + e) * rv.dot(c_direction)
            j /= self.center.inv_mass + other.center.inv_mass
            impulse = c_direction * j

            self.center.apply_force(impulse)
            other.center.apply_force(-impulse)
        except:
            pass

    def collide_body(self, other: Body):
        try:
            distance = (self.center.position - other.position).length()
            c_direction = (self.center.position - other.position).normalize()
            self.center.position += c_direction * \
                (self.radius - distance)
            other.position -= c_direction * \
                (self.radius - distance)
            rv = self.center.velocity - other.velocity
            if rv.dot(c_direction) > 0:
                return
            e = min(self.center.elasticity, other.elasticity)
            j = -(1 + e) * rv.dot(c_direction)
            j /= self.center.inv_mass + other.inv_mass
            impulse = c_direction * j

            self.center.apply_force(impulse)
            other.apply_force(-impulse)
        except:
            pass
    
    @property
    def rect(self):
        return pygame.Rect(self.center.position.x - self.radius, self.center.position.y - self.radius, self.radius * 2, self.radius * 2)

    def check_collision(self):
        for soft_body in self.app.soft_bodys:
            if isinstance(soft_body, CircleSoftBody):
                distance = (self.center.position - soft_body.center.position).length()
                if soft_body != self and distance < self.radius + soft_body.radius:
                    self.collide(soft_body)
        bodys = self.app.quad_tree.query_range(self.rect)
        for body in bodys:
            if body not in self.bodys and body.radius > 5 and self.center.position.distance_to(body.position) < self.radius:
                self.collide_body(body)
