import pygame
from physics import Body


class QuadTree:
    def __init__(self, capacity: int, boundary: pygame.Rect, _bodys: list):
        self.capacity = capacity
        self.boundary = boundary
        self.bodys = []
        self.color = (0, 0, 0)

        self.northWest = None
        self.northEast = None
        self.southWest = None
        self.southEast = None

        for body in _bodys:
            self.insert(body)

    def subdivide(self):
        x = self.boundary.x
        y = self.boundary.y
        w = self.boundary.w / 2
        h = self.boundary.h / 2

        self.northWest = QuadTree(self.capacity, pygame.Rect(
            x, y, w, h), self.bodys)
        self.northEast = QuadTree(self.capacity, pygame.Rect(
            x + w, y, w, h), self.bodys)
        self.southWest = QuadTree(self.capacity, pygame.Rect(
            x, y + h, w, h), self.bodys)
        self.southEast = QuadTree(self.capacity, pygame.Rect(
            x + w, y + h, w, h), self.bodys)

    def insert(self, body: Body):
        if not self.boundary.colliderect(body.rect):
            return False

        if len(self.bodys) < self.capacity and self.northWest == None:
            self.bodys.append(body)
            return True
        else:
            if self.northWest == None:
                self.subdivide()
            if self.northWest.insert(body):
                return True
            if self.northEast.insert(body):
                return True
            if self.southWest.insert(body):
                return True
            if self.southEast.insert(body):
                return True

    def query_range(self, range: pygame.Rect):
        found = []
        if not self.boundary.colliderect(range):
            return found
        for body in self.bodys:
            if range.colliderect(body.rect):
                found.append(body)
        if self.northWest != None:
            found += self.northWest.query_range(range)
            found += self.northEast.query_range(range)
            found += self.southWest.query_range(range)
            found += self.southEast.query_range(range)
        return found

    def draw(self, screen: pygame.Surface):
        pygame.draw.rect(screen, self.color, self.boundary, 1)
        if self.northWest is not None:
            self.northWest.draw(screen)
            self.northEast.draw(screen)
            self.southWest.draw(screen)
            self.southEast.draw(screen)