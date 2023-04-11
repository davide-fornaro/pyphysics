import pygame
from physics import *
import random
from quadtree import QuadTree

BACKGROUND_COLOR = pygame.color.Color("darkslategray")

QUAD_CAPACITY = 1


class App:
    def __init__(self, i_wsx=1300, i_wsy=700):
        pygame.init()
        self.screen = pygame.display.set_mode(
            (i_wsx, i_wsy), pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.RESIZABLE)
        self.clock = pygame.time.Clock()
        self.bodys = []
        self.wires = []

        #self.wires.append(Cloth(self, Vector2(200, 100), 350, 250, 20))

        # body1 = Body(self, Vector2(i_wsx / 2, 100), 10, 20, 1, True)
        # body2 = Body(self, Vector2(i_wsx / 2 + 300, 200), 10, 10, 1)
        # body3 = Body(self, Vector2(i_wsx / 2 + 400, 400), 10, 10, 1)
        # self.bodys.append(body1)
        # self.bodys.append(body2)
        # self.bodys.append(body3)
        # self.wires.append(WireSegment(self, body1, body2))
        # self.wires.append(WireSegment(self, body2, body3))

        self.wires.append(Wire(self, Vector2(200, 100), Vector2(800, 100), 50))

        # for i in range(200):
        #     self.bodys.append(Body(self, Vector2(random.randint(
        #         0, i_wsx), random.randint(i_wsy - 200, i_wsy - 100)), 3, 4, random.uniform(0.89, 0.99)))

        self.quad_tree = QuadTree(QUAD_CAPACITY, pygame.Rect(
            0, 0, i_wsx, i_wsy), self.bodys)

    def waterfall(self, pos, angle, force):
        body = Body(self, pos, 2, 2, random.uniform(0.89, 0.99))
        body.apply_force(Vector2(force, 0).rotate(angle) * body.mass)
        self.bodys.append(body)

    def update(self, deltatime: float):
        wsx, wsy = self.screen.get_size()
        self.quad_tree = QuadTree(QUAD_CAPACITY, pygame.Rect(
            0, 0, wsx, wsy), self.bodys)
        for body in self.bodys:
            body.update(deltatime)
        for wire in self.wires:
            wire.update(deltatime)

    def draw(self):
        self.screen.fill(BACKGROUND_COLOR)
        # self.quad_tree.draw(self.screen)
        for body in self.bodys:
            body.draw()
        for wire in self.wires:
            wire.draw()

    def run(self):
        while True:
            deltatime = self.clock.tick(60) / 1000
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    pygame.quit()
                    exit()
                elif event.type == pygame.VIDEORESIZE:
                    self.screen = pygame.display.set_mode(
                        event.dict['size'], pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.RESIZABLE)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:
                        mouse_pos = pygame.mouse.get_pos()
                        for i in range(50):
                            self.waterfall(Vector2(
                                100 + i * random.uniform(0, 0.7), mouse_pos[1] + i * random.uniform(0, 0.4)), 0, 400)

                        for i in range(50):
                            self.waterfall(Vector2(
                                1000 + i * random.uniform(0, 0.7), mouse_pos[1] + i * random.uniform(0, 0.4)), 180, 400)
                    elif event.key == pygame.K_SPACE:
                        for body in self.bodys:
                            body.velocity = Vector2(0, 0)
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        self.bodys.append(Body(self, Vector2(
                            event.pos[0], event.pos[1]), 20, 20, 1))
            self.update(deltatime)
            self.draw()
            fps = self.clock.get_fps()
            pygame.display.flip()
            pygame.display.set_caption(
                f"fps: {str(round(fps, 2))} | bodys: {len(self.bodys)}")


def main():
    app = App()
    app.run()


if __name__ == "__main__":
    main()
