import pygame
from physics import *
import random
from quadtree import QuadTree
from constants import QUAD_CAPACITY, BACKGROUND_COLOR


class App:
    def __init__(self, i_wsx=1300, i_wsy=700):
        pygame.init()
        self.screen = pygame.display.set_mode(
            (i_wsx, i_wsy), pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.RESIZABLE)
        self.clock = pygame.time.Clock()
        self.bodys = []
        self.springs = []
        self.bonds = []
        self.soft_bodys = []
        self.temperature = 200

        #self.soft_bodys.append(Wire(self, Vector2(100, 200), Vector2(400, 300), 30))

        #self.soft_bodys.append(CircleSoftBody(self, Vector2(500, 100), 60, 20))
        #self.soft_bodys.append(CircleSoftBody(self, Vector2(500, 400), 60, 20))

        #self.soft_bodys.append(RectangleSoftBody(self, Vector2(800, 300), 300, 200, (12, 9)))

        self.soft_bodys.append(PressuredCircleSoftBody(self, Vector2(1000, 600), 60, 60))
        self.soft_bodys.append(PressuredCircleSoftBody(self, Vector2(600, 600), 60, 60))

        self.quad_tree = QuadTree(QUAD_CAPACITY, pygame.Rect(
            0, 0, i_wsx, i_wsy), self.bodys)

    def update(self, deltatime: float):
        wsx, wsy = self.screen.get_size()
        self.quad_tree = QuadTree(QUAD_CAPACITY, pygame.Rect(
            0, 0, wsx, wsy), self.bodys)
        for body in self.bodys:
            body.update(deltatime)
        for spring in self.springs:
            spring.update(deltatime)
        for bond in self.bonds:
            bond.update(deltatime)
        for softbody in self.soft_bodys:
            softbody.update()

    def draw(self):
        self.screen.fill(BACKGROUND_COLOR)
        # self.quad_tree.draw(self.screen)
        for body in self.bodys:
            body.draw()
        for spring in self.springs:
            spring.draw()
        for bond in self.bonds:
            bond.draw()
        for softbody in self.soft_bodys:
            try:
                softbody.draw()
            except:
                pass

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
                    if event.key == pygame.K_SPACE:
                        for body in self.bodys:
                            body.velocity = Vector2(0, 0)
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        self.bodys.append(Body(self, Vector2(
                            event.pos[0], event.pos[1]), 30, 20, 1))
                        
            pressed = pygame.key.get_pressed()
            if pressed[pygame.K_o]:
                self.temperature += 2
            if pressed[pygame.K_p]:
                self.temperature -= 2
            self.update(deltatime)
            self.draw()
            fps = self.clock.get_fps()
            pygame.display.flip()
            pygame.display.set_caption(
                f"fps: {str(round(fps, 2))} | bodys: {len(self.bodys)} | temperature: {self.temperature}")


def main():
    app = App()
    app.run()


if __name__ == "__main__":
    main()
