import pygame


class JumpPad:
    def __init__(self, game, pos, img):
        self.game = game
        self.pos = pos
        self.animation = img.copy()
        self.active = False

    def update(self, player_rect):
        if player_rect.colliderect(pygame.Rect(self.pos[0], self.pos[1], 16, 16)):
            self.active = True
            self.animation.done = False
          
        if self.animation.done:
            self.active = False
            self.animation.frame = 0
        
        if self.active:
            self.animation.update()
            return True
        

    def render(self, surf, offset=(0, 0)):
        image = self.animation.img()
        surf.blit(image, (self.pos[0] - offset[0], self.pos[1] - offset[1]))
