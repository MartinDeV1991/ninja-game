import math
import pygame

class Projectile:
    def __init__(self, pos, img, speed, entity, weaponType, gravity = 0.1):
        self.pos = list(pos)
        self.img = img
        self.speed = speed
        self.collided = False
        self.maxTime = 360
        self.time = 0
        self.entity = entity
        self.weaponType = weaponType
        self.bounces = 0
        self.direction = 0
        self.gravity = gravity
        if self.weaponType == 3:
            if self.gravity > 0:
                self.speed[1] = -5
            elif self.gravity < 0:
                self.speed[1] = 5
        elif self.weaponType == 2:
            if self.gravity > 0:
                self.speed[1] = -3
            elif self.gravity < 0:
                self.speed[1] = 3

        if self.weaponType == 4:
            self.img = pygame.transform.scale(self.img, [10, 10])

    def update(self, player, gravity = 0.1):
        if self.weaponType == 4:
            playerX = player.rect().centerx
            PlayerY = player.rect().centery
            dx = playerX - self.pos[0]
            dy = PlayerY - self.pos[1]
            distance = math.sqrt(dx**2 + dy**2)
            if distance != 0:
                direction_x = dx / distance
                direction_y = dy / distance

                angle_to_player = math.atan2(direction_y, direction_x)
                angle_difference = math.atan2(math.sin(angle_to_player - self.direction), math.cos(angle_to_player - self.direction))

                max_angle_change = math.radians(math.pi / 2)
                if angle_difference > max_angle_change:
                    self.direction += max_angle_change
                elif angle_difference < -max_angle_change:
                    self.direction -= max_angle_change
                else:
                    self.direction = angle_to_player

                if self.time == 0:
                    self.direction = math.atan2(direction_y, direction_x)
                    
                self.pos[0] += abs(self.speed[0]) * math.cos(self.direction)
                self.pos[1] += abs(self.speed[0]) * math.sin(self.direction)

        elif self.weaponType == 2:
            self.pos[0] += self.speed[0]
            self.pos[1] += self.speed[1]
            if self.gravity > 0:
                self.speed[1] += 0.2
            elif self.gravity < 0:
                self.speed[1] -= 0.2

        elif self.weaponType == 3:
            self.pos[0] += self.speed[0]
            self.pos[1] += self.speed[1]
            if self.gravity > 0:
                self.speed[1] += 0.2
            elif self.gravity < 0:
                self.speed[1] -= 0.2
        else:
            self.pos[0] += self.speed[0]
            self.pos[1] += self.speed[1]
        self.time += 1

    def render(self, surf, offset=(0, 0)):
        if self.weaponType == 2:
            img = self.img.copy()
            img.fill((0, 255, 0), special_flags=pygame.BLEND_RGB_MULT)
        else:
            img = self.img.copy()

        surf.blit(
            img,
            (
                self.pos[0] - self.img.get_width() / 2 - offset[0],
                self.pos[1] - self.img.get_height() / 2 - offset[1],
            ),
        )
