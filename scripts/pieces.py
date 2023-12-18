import pygame


class Piece:
    def __init__(self, img, pos, speed):
        self.img = img
        self.pos = pos
        self.speed = speed

    def update(self):
        self.pos[0] += self.speed[0]
        self.speed[1] += 0.10
        self.pos[1] += self.speed[1]

    def render(self, surf, offset=(0, 0)):
        render_pos = (
            self.pos[0] - offset[0],
            self.pos[1] - offset[1],
        )
        surf.blit(
            pygame.transform.smoothscale(self.img, [5, 5]),
            (render_pos[0], render_pos[1]),
        )
