import sys
import math
import random
import os

import pygame

from scripts.utils import load_image, load_images, Animation
from scripts.entities import PhysicsEntity, Player, Enemy
from scripts.tilemap import Tilemap
from scripts.clouds import Clouds
from scripts.particles import Particle
from scripts.spark import Spark


class Game:
    def __init__(self):
        pygame.init()

        pygame.display.set_caption("ninja game")
        self.screen = pygame.display.set_mode((640, 480))
        self.display = pygame.Surface((320, 240), pygame.SRCALPHA)
        self.display_2 = pygame.Surface((320, 240))

        self.clock = pygame.time.Clock()

        self.movement = [False, False]

        self.assets = {
            "decor": load_images("tiles/decor"),
            "grass": load_images("tiles/grass"),
            "large_decor": load_images("tiles/large_decor"),
            "stone": load_images("tiles/stone"),
            "player": load_image("entities/player.png"),
            "background": load_image("background.png"),
            "stars": load_image("star.png"),
            "clouds": load_images("clouds"),
            "enemy/idle": Animation(load_images("entities/enemy/idle"), img_dur=6),
            "enemy/run": Animation(load_images("entities/enemy/run"), img_dur=4),
            "enemy1/idle": Animation(load_images("entities/enemy1/idle"), img_dur=6),
            "enemy1/run": Animation(load_images("entities/enemy1/run"), img_dur=4),
            "player/idle": Animation(load_images("entities/player/idle"), img_dur=6),
            "player/run": Animation(load_images("entities/player/run"), img_dur=4),
            "player/jump": Animation(load_images("entities/player/jump")),
            "player/slide": Animation(load_images("entities/player/slide")),
            "player/wall_slide": Animation(load_images("entities/player/wall_slide")),
            "particle/leaf": Animation(
                load_images("particles/leaf"), img_dur=20, loop=False
            ),
            "particle/particle": Animation(
                load_images("particles/particle"), img_dur=6, loop=False
            ),
            "gun": load_image("gun.png"),
            "projectile": load_image("projectile.png"),
        }

        self.sfx = {
            "jump": pygame.mixer.Sound("data/sfx/jump.wav"),
            "dash": pygame.mixer.Sound("data/sfx/dash.wav"),
            "hit": pygame.mixer.Sound("data/sfx/hit.wav"),
            "shoot": pygame.mixer.Sound("data/sfx/shoot.wav"),
            "ambience": pygame.mixer.Sound("data/sfx/ambience.wav"),
        }

        self.sound_factor = 0.5
        self.sfx["jump"].set_volume(0.7 * self.sound_factor)
        self.sfx["dash"].set_volume(0.3 * self.sound_factor)
        self.sfx["hit"].set_volume(0.8 * self.sound_factor)
        self.sfx["shoot"].set_volume(0.4 * self.sound_factor)
        self.sfx["ambience"].set_volume(0.2 * self.sound_factor)
        
        self.player = Player(self, (50, 50), (8, 15))
        self.tilemap = Tilemap(self, tile_size=16)

        self.level = 0
        self.load_level(self.level)
        self.screenshake = 0

        self.lowest_block_position = self.tilemap.find_lowest_block_position()

    def load_level(self, map_id):
        self.tilemap.load("data/maps/" + str(map_id) + ".json")
        self.night = random.randint(0,1)
        if self.night:
            self.stars_pos = []
            self.starsize = []
            for i in range(0, 100):
                self.starsize.append(random.randint(0, 10))
                self.stars_pos.append([random.randint(0, 320), random.randint(0, 240)])
        else:
            self.clouds = Clouds(self.assets["clouds"], count=16)
        self.leaf_spawners = []
        for tree in self.tilemap.extract([("large_decor", 2)], keep=True):
            self.leaf_spawners.append(
                pygame.Rect(4 + tree["pos"][0], 4 + tree["pos"][1], 23, 13)
            )

        self.enemies = []
        for spawner in self.tilemap.extract(
            [("spawners", 0), ("spawners", 1), ("spawners", 2)]
        ):
            if spawner["variant"] == 0:
                self.player.pos = spawner["pos"]
                self.player.air_time = 0
            elif spawner["variant"] == 1:
                self.enemies.append(Enemy(self, spawner["pos"], (8, 15), 0, 1))
            else:
                self.enemies.append(Enemy(self, spawner["pos"], (24, 45), 1, 5))

        self.projectiles = []
        self.particles = []
        self.sparks = []

        self.scroll = [0, 0]
        self.dead = 0
        self.transition = -30

    def handle_projectiles(self, render_scroll):
        for projectile in self.projectiles.copy():
            projectile.collided = False
            projectile.update(self.player.pos)
            projectile.render(self.display, render_scroll)
            if self.tilemap.solid_check(projectile.pos):
                projectile.collided = True
                for i in range(4):
                    self.sparks.append(
                        Spark(
                            projectile.pos,
                            random.random()
                            - 0.5
                            + (math.pi if projectile.speed[0] > 0 else 0),
                            2 + random.random(),
                        )
                    )
            elif projectile.time > projectile.maxTime:
                projectile.collided = True
            elif abs(self.player.dashing) < 50 and projectile.entity == 0:
                if self.player.rect().collidepoint(projectile.pos):
                    projectile.collided = True
                    self.dead += 1
                    self.sfx["hit"].play()
                    self.screenshake = max(16, self.screenshake)
                    self.create_particles(self.player)
            elif projectile.entity == 1:
                for enemy in self.enemies.copy():
                    if enemy.rect().collidepoint(projectile.pos):
                        projectile.collided = True
                        self.sfx["hit"].play()
                        self.create_particles(enemy)
                        enemy.health -= 1
                        if enemy.health <= 0:
                            self.enemies.remove(enemy)

            if projectile.collided:
                self.projectiles.remove(projectile)


    def create_particles(self, entity):
        self.sfx["hit"].play()
        for i in range(30):
            angle = random.random() * math.pi * 2
            speed = random.random() * 5
            self.sparks.append(
                Spark(
                    entity.rect().center,
                    angle,
                    2 + random.random(),
                )
            )
            self.particles.append(
                Particle(
                    self,
                    "particle",
                    entity.rect().center,
                    velocity=[
                        math.cos(angle + math.pi) * speed * 0.5,
                        math.sin(angle + math.pi) * speed * 0.5,
                    ],
                    frame=random.randint(0, 7),
                )
            )

    def handle_particles(self, render_scroll):
        for rect in self.leaf_spawners:
            if random.random() * 49999 < rect.width * rect.height:
                pos = (
                    rect.x + random.random() * rect.width,
                    rect.y + random.random() * rect.height,
                )
                self.particles.append(
                    Particle(
                        self,
                        "leaf",
                        pos,
                        velocity=[-0.1, 0.3],
                        frame=random.randint(0, 20),
                    )
                )

        for particle in self.particles.copy():
            kill = particle.update()
            particle.render(self.display, offset=render_scroll)
            if particle.type == "leaf":
                particle.pos[0] += math.sin(particle.animation.frame * 0.035) * 0.3
            if kill:
                self.particles.remove(particle)

        for spark in self.sparks.copy():
            kill = spark.update()
            spark.render(self.display, offset=render_scroll)
            if kill:
                self.sparks.remove(spark)

    def run(self):
        pygame.mixer.music.load("data/music.wav")
        pygame.mixer.music.set_volume(0.5 * self.sound_factor)
        pygame.mixer.music.play(-1)

        self.sfx["ambience"].play(-1)

        while True:
            self.display.fill((0, 0, 0, 0))
            self.display_2.fill((19, 24, 98, 1))                
            self.screenshake = max(0, self.screenshake - 1)

            if not len(self.enemies):
                self.transition += 1
                if self.transition > 30:
                    self.level = min(self.level + 1, len(os.listdir("data/maps")) - 1)
                    self.load_level(self.level)
            if self.transition < 0:
                self.transition += 1

            if self.dead:
                self.dead += 1
                if self.dead == 10:
                    self.transition = min(30, self.transition + 1)
                if self.dead > 40:
                    self.load_level(self.level)

            self.scroll[0] += (
                self.player.rect().centerx
                - self.display.get_width() / 2
                - self.scroll[0]
            ) / 30
            self.scroll[1] += (
                self.player.rect().centery
                - self.display.get_height() / 2
                - self.scroll[1]
            ) / 30
            render_scroll = (int(self.scroll[0]), int(self.scroll[1]))

            # lowest_block = pygame.Rect(
            #     self.lowest_block_position[0] * 16 - self.scroll[0],
            #     (self.lowest_block_position[1] + 2) * 16 - self.scroll[1],
            #     1000,
            #     5,
            # )
            # pygame.draw.rect(self.display, (255, 255, 0), lowest_block)

            if self.night:
                for i in range(0, len(self.stars_pos)):
                    img = pygame.image.load("data/images/star.png")
                    img.set_colorkey((0, 0, 0, 0))
                    self.display_2.blit(pygame.transform.smoothscale(img, (self.starsize[i], self.starsize[i])), self.stars_pos[i])
            else:
                self.display_2.blit(self.assets["background"], (0, 0))
                self.clouds.update()
                self.clouds.render(self.display_2, offset=render_scroll)
                
            self.tilemap.render(self.display, offset=render_scroll)

            for enemy in self.enemies.copy():
                kill = enemy.update(self.tilemap, (0, 0))
                enemy.render(self.display, offset=render_scroll)
                if kill:
                    self.enemies.remove(enemy)

            if not self.dead:
                self.player.update(
                    self.tilemap, (self.movement[1] - self.movement[0], 0)
                )
                self.player.render(self.display, offset=render_scroll)

            self.handle_projectiles(render_scroll)
            self.handle_particles(render_scroll)

            display_mask = pygame.mask.from_surface(self.display)
            display_silhouette = display_mask.to_surface(
                setcolor=(0, 0, 0, 180), unsetcolor=(0, 0, 0, 0)
            )
            for offset in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                self.display_2.blit(display_silhouette, offset)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LEFT:
                        self.movement[0] = True
                    if event.key == pygame.K_RIGHT:
                        self.movement[1] = True
                    if event.key == pygame.K_UP:
                        self.player.jump()
                        if self.player.jump():
                            self.sfx["jump"].play()
                    if event.key == pygame.K_x:
                        self.player.dash()
                    if event.key == pygame.K_z:
                        self.player.shoot = True
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_LEFT:
                        self.movement[0] = False
                    if event.key == pygame.K_RIGHT:
                        self.movement[1] = False

            if self.transition:
                transition_surf = pygame.Surface(self.display.get_size())
                pygame.draw.circle(
                    transition_surf,
                    (255, 255, 255),
                    (self.display.get_width() // 2, self.display.get_height() // 2),
                    (30 - abs(self.transition)) * 8,
                )
                transition_surf.set_colorkey((255, 255, 255))
                self.display.blit(transition_surf, (0, 0))

            self.display_2.blit(self.display, (0, 0))

            screenshake_offset = (
                random.random() * self.screenshake - self.screenshake / 2,
                random.random() * self.screenshake - self.screenshake / 2,
            )
            self.screen.blit(
                pygame.transform.smoothscale(self.display_2, self.screen.get_size()),
                screenshake_offset,
            )
            pygame.display.update()
            self.clock.tick(60)


Game().run()
