import pygame
import math
from pygame.math import Vector2

BACKGROUND_COLOR = pygame.color.Color("darkslategray")
QUAD_CAPACITY = 1
G = Vector2(0, 9.81)
AIR_VISCOSITY = .148e-4
AIR_K = 6 * math.pi * AIR_VISCOSITY
MAX_TRAJECTORY_POINTS = 199
R = 8.314  # gas constant