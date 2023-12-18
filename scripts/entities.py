import math
import random

import pygame

from scripts.particles import Particle
from scripts.spark import Spark
from scripts.projectile import Projectile


class PhysicsEntity:
    def __init__(self, game, e_type, pos, size):
        self.game = game
        self.type = e_type
        self.pos = list(pos)
        self.size = size
        self.velocity = [0, 0]
        self.collisions = {"up": False, "down": False, "right": False, "left": False}
        self.action = ""
        self.anim_offset = (-3, -3)
        self.flip = False if self.type != "dragon" else True
        self.set_action("idle")

        self.last_movement = [0, 0]
        if self.type == "dragon":
            self.pos[1] -= 25
        self.gravity = self.game.gravity

    def rect(self):
        return pygame.Rect(self.pos[0], self.pos[1], self.size[0], self.size[1])

    def headRect(self):
        return pygame.Rect(self.pos[0], self.pos[1], self.size[0], self.size[1] / 3)

    def set_action(self, action):
        if action != self.action:
            self.action = action
            self.animation = self.game.assets[self.type + "/" + self.action].copy()
            self.animation.frame = 0

    def update(self, tilemap, movement=(0, 0)):
        self.collisions = {"up": False, "down": False, "right": False, "left": False}
        if self.type != "dragon":
            frame_movement = (
                movement[0] + self.velocity[0],
                movement[1] + self.velocity[1],
            )

            self.pos[0] += frame_movement[0]
            entity_rect = self.rect()
            for rect in tilemap.physics_rects_around(self.pos):
                if entity_rect.colliderect(rect):
                    if frame_movement[0] > 0:
                        entity_rect.right = rect.left
                        self.collisions["right"] = True
                    if frame_movement[0] < 0:
                        entity_rect.left = rect.right
                        self.collisions["left"] = True
                    self.pos[0] = entity_rect.x

            self.pos[1] += frame_movement[1]
            entity_rect = self.rect()
            for rect in tilemap.physics_rects_around(self.pos):
                if entity_rect.colliderect(rect):
                    if frame_movement[1] > 0:
                        entity_rect.bottom = rect.top
                        self.collisions["down"] = True
                    if frame_movement[1] < 0:
                        entity_rect.top = rect.bottom
                        self.collisions["up"] = True
                    self.pos[1] = entity_rect.top

            if movement[0] > 0:
                self.flip = False
            if movement[0] < 0:
                self.flip = True

        self.last_movement = movement
        self.velocity[1] = min(5, self.velocity[1] + self.gravity)

        if self.collisions["down"] or self.collisions["up"]:
            self.velocity[1] = 0

        self.animation.update()

    def render(self, surf, offset=(0, 0), spawn=0):
        img = pygame.transform.flip(self.animation.img(), self.flip, False)
        img = pygame.transform.flip(img, False, self.gravity < 0)
        if self.type == "dragon":
            if self.action == "attack":
                self.size = (60, 80)
            else:
                self.size = (100, 100)
        if spawn == 1 or self.type == "dragon":
            img = pygame.transform.scale(img, self.size)

        surf.blit(
            img,
            (
                self.pos[0] - offset[0] + self.anim_offset[0],
                self.pos[1] - offset[1] + self.anim_offset[1],
            ),
        )


class Enemy(PhysicsEntity):
    def __init__(self, game, pos, size, spawn, health, e_type):
        super().__init__(game, e_type, pos, size)
        self.spawn = spawn
        self.health = health
        self.maxHealth = health
        self.walking = 0
        self.idle = 1
        if self.type == "dragon":
            self.weaponType = 4
        else:
            self.weaponType = 1

    def update(self, tilemap, movement=(0, 0), gravity=0.1):
        self.gravity = gravity
        if self.walking:
            if tilemap.solid_check(
                (
                    self.rect().centerx + (-7 if self.flip else 7),
                    self.pos[1] + self.size[1] + 1,
                )
            ):
                if self.collisions["right"] or self.collisions["left"]:
                    self.flip = not self.flip
                else:
                    movement = (movement[0] - 0.5 if self.flip else 0.5, movement[1])
            else:
                self.flip = not self.flip

            self.walking = max(0, self.walking - 1)
            if not self.walking:
                dis = (
                    self.game.player.pos[0] - self.pos[0],
                    self.game.player.pos[1] - self.pos[1],
                )
                if abs(dis[1]) < 16:
                    if (self.flip and dis[0] < 0) or (not self.flip and dis[0] > 0):
                        self.game.sfx["shoot"].play()
                        xSpeed = -1.5 if self.flip else 1.5
                        self.game.projectiles.append(
                            Projectile(
                                [self.rect().centerx - 7, self.rect().centery],
                                self.game.assets["projectile"],
                                [xSpeed, 0],
                                0,
                                self.weaponType,
                                self.gravity,
                            )
                        )
                        for _ in range(4):
                            self.game.sparks.append(
                                Spark(
                                    self.game.projectiles[-1].pos,
                                    random.random() - 0.5 + math.pi * self.flip,
                                    2 + random.random(),
                                )
                            )

        elif random.random() < 0.01 and self.type != "dragon":
            self.walking = random.randint(30, 120)

        super().update(tilemap, movement=movement)

        if self.type != "dragon":
            if movement[0] != 0:
                self.set_action("run")
            else:
                self.set_action("idle")

        if self.type == "dragon":
            if self.idle:
                self.idle = max(0, self.idle - 1)
                if not self.idle:
                    self.set_action("attack")

            if (
                self.action == "attack"
                and self.animation.frame
                == (len(self.animation.images) - 1) * self.animation.img_duration
            ):
                xSpeed = [-2] if self.flip else [2]

                for i in xSpeed:
                    self.game.projectiles.append(
                        Projectile(
                            [self.rect().centerx - 20, self.rect().centery - 5],
                            self.game.assets["projectile2"],
                            [i, 0],
                            0,
                            self.weaponType,
                            self.gravity,
                        )
                    )
                for _ in range(4):
                    self.game.sparks.append(
                        Spark(
                            self.game.projectiles[-1].pos,
                            random.random() - 0.5 + math.pi * self.flip,
                            2 + random.random(),
                        )
                    )
            if self.animation.done:
                self.idle = random.randint(30, 120)
                self.set_action("idle")

        if abs(self.game.player.dashing) >= 50:
            if self.rect().colliderect(self.game.player.rect()):
                self.game.screenshake = max(16, self.game.screenshake)
                self.game.sfx["hit"].play()
                for i in range(30):
                    angle = random.random() * math.pi * 2
                    speed = random.random() * 5
                    self.game.sparks.append(
                        Spark(self.rect().center, angle, 2 + random.random())
                    )
                    self.game.particles.append(
                        Particle(
                            self.game,
                            "particle",
                            self.rect().center,
                            velocity=[
                                math.cos(angle + math.pi) * speed * 0.5,
                                math.sin(angle + math.pi) * speed * 0.5,
                            ],
                            frame=random.randint(0, 7),
                        )
                    )
                self.game.sparks.append(
                    Spark(self.rect().center, 0, 5 + random.random())
                )
                self.game.sparks.append(
                    Spark(self.rect().center, math.pi, 5 + random.random())
                )
                self.health -= 1
        return self.health <= 0

    def render(self, surf, offset=(0, 0)):
        super().render(surf, offset=offset, spawn=self.spawn)

        if self.flip:
            surf.blit(
                pygame.transform.flip(self.game.assets["gun"], True, False),
                (
                    self.rect().centerx
                    - 4
                    - self.spawn * 5
                    - self.game.assets["gun"].get_width()
                    - offset[0],
                    self.rect().centery - offset[1],
                ),
            )
        else:
            surf.blit(
                self.game.assets["gun"],
                (self.rect().centerx + 4 - offset[0], self.rect().centery - offset[1]),
            )

        if self.spawn == 1:
            self.draw_health_bar(surf, offset)

    def draw_health_bar(self, surf, offset=(0, 0)):
        bar_width = self.size[0]
        bar_height = 5
        bar_x = self.pos[0] - offset[0]
        bar_y = self.pos[1] - offset[1] - bar_height - 5

        health_percentage = max(self.health / self.maxHealth, 0.0)
        pygame.draw.rect(surf, (255, 0, 0), (bar_x, bar_y, bar_width, bar_height))
        pygame.draw.rect(
            surf,
            (0, 255, 0),
            (bar_x, bar_y, int(bar_width * health_percentage), bar_height),
        )


class Player(PhysicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, "player", pos, size)
        self.air_time = 0
        self.jumps = 1
        self.wall_slide = False
        self.dashing = 0
        self.shoot = False
        self.bounce = False
        self.cannon = True
        self.weaponType = 1

    def update(self, tilemap, movement=(0, 0), gravity=0.1):
        self.gravity = gravity
        super().update(tilemap, movement=movement)

        if not self.game.gun and self.rect().colliderect(self.game.gun_rect):
            self.game.gun = True

        if self.game.gun:
            if self.weaponType == 1:
                pass
            elif self.weaponType == 2:
                self.bounce = True
            elif self.weaponType == 3:
                self.cannon = True

        self.air_time += 1

        if self.pos[1] > (self.game.lowest_block_position[1] + 5) * 16:
            if not self.game.dead:
                self.game.screenshake = max(16, self.game.screenshake)
            self.game.dead += 1

        if self.collisions["down"] and self.gravity > 0:
            self.air_time = 0
            self.jumps = 1
        elif self.collisions["up"] and self.gravity < 0:
            self.air_time = 0
            self.jumps = 1

        self.wall_slide = False
        if (self.collisions["right"] or self.collisions["left"]) and self.air_time > 4:
            self.wall_slide = True
            if self.gravity > 0:
                self.velocity[1] = min(self.velocity[1], 0.5)
            elif self.gravity < 0:
                self.velocity[1] = max(self.velocity[1], -0.5)
                
            if self.collisions["right"]:
                self.flip = False
            else:
                self.flip = True
            self.set_action("wall_slide")

        if not self.wall_slide:
            if self.air_time > 4:
                self.set_action("jump")
            elif movement[0] != 0:
                self.set_action("run")
            else:
                self.set_action("idle")

        if abs(self.dashing) in {60, 50}:
            for i in range(20):
                angle = random.random() * math.pi * 2
                speed = random.random() * 0.5 + 0.5
                pvelocity = [math.cos(angle) * speed, math.sin(angle) * speed]
                self.game.particles.append(
                    Particle(
                        self.game,
                        "particle",
                        self.rect().center,
                        velocity=pvelocity,
                        frame=random.randint(0, 7),
                    )
                )
        if self.dashing > 0:
            self.dashing = max(0, self.dashing - 1)
        if self.dashing < 0:
            self.dashing = min(0, self.dashing + 1)
        if abs(self.dashing) > 50:
            self.velocity[0] = abs(self.dashing) / self.dashing * 8
            if abs(self.dashing) == 51:
                self.velocity[0] *= 0.1
            pvelocity = [abs(self.dashing) / self.dashing * random.random() * 3, 0]
            self.game.particles.append(
                Particle(
                    self.game,
                    "particle",
                    self.rect().center,
                    velocity=pvelocity,
                    frame=random.randint(0, 7),
                )
            )

        if self.velocity[0] > 0:
            self.velocity[0] = max(self.velocity[0] - 0.1, 0)
        else:
            self.velocity[0] = min(self.velocity[0] + 0.1, 0)

        if self.shoot:
            self.game.sfx["shoot"].play()
            if self.flip:
                self.game.projectiles.append(
                    Projectile(
                        [self.rect().centerx - 7, self.rect().centery],
                        self.game.assets["projectile"],
                        [-1.5, 0],
                        1,
                        self.weaponType,
                        self.gravity,
                    )
                )
                for i in range(4):
                    self.game.sparks.append(
                        Spark(
                            self.game.projectiles[-1].pos,
                            random.random() - 0.5 + math.pi,
                            2 + random.random(),
                        )
                    )
            if not self.flip:
                self.game.projectiles.append(
                    Projectile(
                        [self.rect().centerx + 7, self.rect().centery],
                        self.game.assets["projectile"],
                        [1.5, 0],
                        1,
                        self.weaponType,
                        self.gravity,
                    )
                )
                for i in range(4):
                    self.game.sparks.append(
                        Spark(
                            self.game.projectiles[-1].pos,
                            random.random() - 0.5,
                            2 + random.random(),
                        )
                    )
            self.shoot = False

    def render(self, surf, offset=(0, 0)):
        if abs(self.dashing) <= 50:
            super().render(surf, offset=offset)
            if self.game.gun:
                gun_img = self.game.assets["gun"].copy()
                if self.weaponType == 2:
                    gun_img.fill((0, 255, 0), special_flags=pygame.BLEND_RGB_MULT)
                elif self.weaponType == 3:
                    gun_img.fill((255, 0, 0), special_flags=pygame.BLEND_RGB_MULT)

                if self.flip:
                    surf.blit(
                        pygame.transform.flip(gun_img, True, False),
                        (
                            self.rect().centerx
                            - 4
                            - self.game.assets["gun"].get_width()
                            - offset[0],
                            self.rect().centery - offset[1],
                        ),
                    )
                else:
                    surf.blit(
                        gun_img,
                        (
                            self.rect().centerx + 4 - offset[0],
                            self.rect().centery - offset[1],
                        ),
                    )

    def jump(self, jump_power=-3):
        if self.wall_slide:
            if self.flip and self.last_movement[0] < 0:
                self.velocity[0] = 3.5
                if self.gravity > 0:
                    self.velocity[1] = -2.5
                elif self.gravity < 0:
                    self.velocity[1] = 2.5
                self.air_time = 5
                self.jumps = max(0, self.jumps - 1)
                return True
            elif not self.flip and self.last_movement[0] > 0:
                self.velocity[0] = -3.5
                if self.gravity > 0:
                    self.velocity[1] = -2.5
                elif self.gravity < 0:
                    self.velocity[1] = 2.5
                self.air_time = 5
                self.jumps = max(0, self.jumps - 1)
                return True

        elif self.jumps:
            if self.gravity > 0:
                self.velocity[1] = jump_power
            elif self.gravity < 0:
                self.velocity[1] = -jump_power
            self.jumps -= 1
            self.air_time = 5
            return True

    def dash(self):
        if not self.dashing:
            self.game.sfx["dash"].play()
            if self.flip:
                self.dashing = -60
            else:
                self.dashing = 60
