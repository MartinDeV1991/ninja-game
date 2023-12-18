import pygame
import random
import math

# Screen dimensions
SCREEN_WIDTH, SCREEN_HEIGHT = 640, 480

# Colors
COLOR = (150, 75, 0)


# dust class
class Dust:
    def __init__(self, image, x, y):
        self.x = x
        self.y = y
        self.y_original = self.y
        self.amplitude = random.randint(5, 20)
        self.frequency = random.uniform(0.002, 0.01)
        self.offset = random.uniform(0, 2 * math.pi)
        self.image = image
        self.image = pygame.transform.scale(self.image, (200, 200))

    def update(self, frame, player):
        self.x += 0.35 * min(1 + frame / 2000, 2)
        self.y = self.y_original + self.amplitude * math.sin(
            self.frequency * frame + self.offset
        )

        if self.y > player.pos[1] + SCREEN_HEIGHT / 2:
            self.y = player.pos[1] - SCREEN_HEIGHT / 2
            self.y_original = player.pos[1] - SCREEN_HEIGHT / 2
        if self.y < player.pos[1] - self.image.get_height() - SCREEN_HEIGHT / 2:
            self.y = player.pos[1] + SCREEN_HEIGHT / 4
            self.y_original = player.pos[1] + SCREEN_HEIGHT / 4

    def render(self, surf, offset):
        surf.blit(
            self.image,
            (
                int(self.x - offset[0]),
                int(self.y - offset[1])
            ),
        )
       
