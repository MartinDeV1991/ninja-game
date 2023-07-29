import math

class Projectile:
    def __init__(self, pos, img, speed, entity, chase):
        self.pos = list(pos)
        self.img = img
        self.speed = speed
        self.collided = False
        self.maxTime = 360
        self.time = 0
        self.entity = entity
        self.chase = chase
        
    def update(self, player_pos):
        if self.chase:
            dx = player_pos[0] - self.pos[0]
            dy = player_pos[1] - self.pos[1]
            distance = math.sqrt(dx ** 2 + dy ** 2)

            if distance != 0:
                direction_x = dx / distance
                direction_y = dy / distance
                self.direction = math.atan2(direction_y, direction_x)
                self.pos[0] += abs(self.speed[0]) * math.cos(self.direction)
                self.pos[1] += abs(self.speed[0]) * math.sin(self.direction)
        else:
            self.pos[0] += self.speed[0]
            self.time += 1

    def render(self, surf, offset=(0, 0)):
        surf.blit(
            self.img,
            (
                self.pos[0] - self.img.get_width() / 2 - offset[0],
                self.pos[1] - self.img.get_height() / 2 - offset[1],
            ),
        )
