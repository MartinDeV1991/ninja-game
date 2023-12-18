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
from scripts.projectile import Projectile
from scripts.dust import Dust
from scripts.pieces import Piece
from scripts.jump_pad import JumpPad
from scripts.lever import Lever

LEVELS = [
    "Easy-1",
    "Easy-2",
    "Easy-3",
    "Easy-4",
    "Easy-5",
    "Easy-6",
    "Medium-1",
    "Medium-2",
    "Medium-3",
    "Medium-4",
    "Medium-5",
    "Medium-6",
    "Hard-1",
    "Hard-2",
    "Insane-1",
    "Insane-2",
]


class Game:
    def __init__(self):
        pygame.init()

        pygame.display.set_caption("ninja game")
        self.screen = pygame.display.set_mode((640, 480))
        self.display = pygame.Surface((320, 240), pygame.SRCALPHA)
        self.display_2 = pygame.Surface((320, 240))

        self.clock = pygame.time.Clock()
        self.frame = 0
        self.movement = [False, False]
        self.gravity = 0.1

        self.assets = {
            "decor": load_images("tiles/decor"),
            "grass": load_images("tiles/grass"),
            "wall": load_images("tiles/wall"),
            "block": load_images("tiles/block"),
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
            "dragon/idle": Animation(
                load_images("entities/dragon/idle", 1), img_dur=10
            ),
            "dragon/run": Animation(load_images("entities/dragon/run", 1), img_dur=10),
            "dragon/attack": Animation(
                load_images("entities/dragon/attack", 1), img_dur=10, loop=False
            ),
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
            "projectile2": load_image("projectile5.png", 1),
            "dust": load_image("dust1.png", 1),
            "pieces": load_images("broken_wall"),
            "jump_pad_anim": Animation(load_images("jump_pad"), img_dur=6, loop=False),
            "lever": Animation(load_images("lever", 1), img_dur=10, loop=False),
        }

        self.sfx = {
            "jump": pygame.mixer.Sound("data/sfx/jump.wav"),
            "dash": pygame.mixer.Sound("data/sfx/dash.wav"),
            "hit": pygame.mixer.Sound("data/sfx/hit.wav"),
            "shoot": pygame.mixer.Sound("data/sfx/shoot.wav"),
            "ambience": pygame.mixer.Sound("data/sfx/ambience.wav"),
            "wall": pygame.mixer.Sound("data/sfx/break5.wav"),
            "jump_pad": pygame.mixer.Sound("data/sfx/jump_pad.mp3"),
        }

        for i in range(len(self.assets["jump_pad_anim"].images)):
            self.assets["jump_pad_anim"].images[i] = pygame.transform.scale(
                self.assets["jump_pad_anim"].images[i], [16, 16]
            )

        for i in range(len(self.assets["lever"].images)):
            self.assets["lever"].images[i] = pygame.transform.scale(
                self.assets["lever"].images[i], [16, 16]
            )

        self.sound_factor = 0.5
        self.sfx["jump"].set_volume(0.7 * self.sound_factor)
        self.sfx["dash"].set_volume(0.3 * self.sound_factor)
        self.sfx["hit"].set_volume(0.8 * self.sound_factor)
        self.sfx["shoot"].set_volume(0.4 * self.sound_factor)
        self.sfx["ambience"].set_volume(0.2 * self.sound_factor)
        self.sfx["wall"].set_volume(0.4 * self.sound_factor)
        self.sfx["jump_pad"].set_volume(0.7 * self.sound_factor)

        self.player = Player(self, (50, 50), (8, 15))
        self.tilemap = Tilemap(self, tile_size=16)

        self.level = 0
        self.load_level(LEVELS[self.level])
        self.screenshake = 0

        self.lowest_block_position = self.tilemap.find_lowest_block_position()
        self.gun = False
        self.all_projectiles = []
        self.pieces = []

    def load_level(self, map_id):
        self.frame = 0
        self.gravity = 0.1
        self.tilemap.load("data/maps/" + str(map_id) + ".json")
        ground_tile_positions = []
        for loc in self.tilemap.tilemap:
            tile = self.tilemap.tilemap[loc]
            if tile["type"] in {"grass", "stone", "wall", "block"}:
                ground_tile_positions.append(
                    (
                        tile["pos"][0] * self.tilemap.tile_size,
                        tile["pos"][1] * self.tilemap.tile_size,
                    )
                )

        self.night = random.randint(0, 1)
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
            [("spawners", 0), ("spawners", 1), ("spawners", 2), ("spawners", 3)]
        ):
            if spawner["variant"] == 0:
                self.player.pos = spawner["pos"]
                self.player.air_time = 0
            elif spawner["variant"] == 1:
                self.enemies.append(Enemy(self, spawner["pos"], (8, 15), 0, 1, "enemy"))
            elif spawner["variant"] == 2:
                self.enemies.append(
                    Enemy(self, spawner["pos"], (24, 45), 1, 5, "enemy")
                )
            elif spawner["variant"] == 3:
                self.enemies.append(
                    Enemy(self, spawner["pos"], (100, 100), 0, 5, "dragon")
                )
        self.jump_pads = []
        for jump_pad in self.tilemap.extract([("jump_pad", 0), ("jump_pad", 1)]):
            self.jump_pads.append(
                JumpPad(self, jump_pad["pos"], self.assets["jump_pad_anim"])
            )
        self.levers = []
        for lever in self.tilemap.extract([("lever", 0)]):
            self.levers.append(Lever(self, lever["pos"], self.assets["lever"]))

        self.gun_pos = self.player.pos
        for _ in range(1000):
            x, y = random.choice(ground_tile_positions)
            y -= self.tilemap.tile_size
            if (
                not self.tilemap.solid_check((x, y))
                and abs(self.player.pos[0] - x) < 200
                and abs(self.player.pos[1] - y) < 50
            ):
                self.gun_pos = (x, y)
                break

        self.gun_size = (5, 5)
        self.gun_image = self.assets["gun"]
        self.gun_rect = self.gun_image.get_rect(center=self.gun_pos)

        self.projectiles = []
        self.particles = []
        self.sparks = []

        self.scroll = [0, 0]
        self.dead = 0
        self.transition = -30

        self.dusts = []
        if map_id in ["Insane-1", "Insane-2"]:
            for i in range(8):
                self.dusts.append(
                    Dust(self.assets["dust"], random.randint(-500, -470), i * 100 - 200)
                )
                self.dusts.append(
                    Dust(self.assets["dust"], random.randint(-400, -370), i * 100 - 200)
                )

    def handle_projectiles(self, render_scroll):
        for projectile in self.projectiles.copy():
            projectile.collided = False
            projectile.update(self.player, self.gravity)
            projectile.render(self.display, render_scroll)

            if self.tilemap.wall_check(projectile.pos, projectile.speed):
                self.sfx["wall"].play()
                projectile.collided = True
                for _ in range(len(self.assets["pieces"])):
                    pos = [
                        projectile.pos[0] + random.random() * 20 - 10,
                        projectile.pos[1] + random.random() * 20 - 10,
                    ]
                    speed = [random.random() * 2 - 1, random.random()]
                    self.pieces.append(Piece(self.assets["pieces"][0], pos, speed))

            if self.tilemap.solid_check(projectile.pos):
                if projectile.weaponType == 1 or projectile.weaponType == 4:
                    projectile.collided = True

                elif projectile.weaponType == 2:
                    projectile.speed[1] = -projectile.speed[1] * 0.8
                    projectile.bounces += 1
                    if projectile.bounces == 5:
                        projectile.collided = True

                elif projectile.weaponType == 3:
                    projectile.collided = True
                    speed = [1, self.gravity * 10]
                    spawn_velocities = [
                        [-speed[0], 0],
                        [speed[0], 0],
                        [0.5 * speed[0], 0],
                        [-0.5 * speed[0], 0],
                    ]
                    for velocity in spawn_velocities:
                        new_projectile = Projectile(
                            pos=[
                                projectile.pos[0] - projectile.speed[0],
                                projectile.pos[1] - projectile.speed[1],
                            ],
                            img=projectile.img,
                            speed=velocity,
                            entity=projectile.entity,
                            weaponType=2,
                            gravity=self.gravity,
                        )
                        self.projectiles.append(new_projectile)

                if projectile.collided:
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

            elif projectile.entity == 0:
                if (
                    self.player.rect().collidepoint(projectile.pos)
                    and abs(self.player.dashing) < 50
                ):
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
                        if (
                            enemy.spawn != 1 and enemy.type != "dragon"
                        ) or enemy.headRect().collidepoint(projectile.pos):
                            enemy.health -= 1
                            self.create_particles(enemy)
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

    def drawGun(self, render_scroll):
        if self.gun:
            gun_image = self.assets["gun"]
            gun_image = pygame.transform.scale(
                gun_image, (gun_image.get_width() * 2, gun_image.get_height() * 2)
            )
            gun_rect = gun_image.get_rect()
            square_size = max(gun_rect.width, gun_rect.height)
            square_surface = pygame.Surface(
                (square_size + 5, square_size + 5), pygame.SRCALPHA
            )
            square_surface1 = square_surface.copy()
            square_surface2 = square_surface.copy()
            square_surface3 = square_surface.copy()
            if self.player.weaponType == 1:
                square_surface1.fill((0, 0, 0, 100))
                square_surface2.fill((0, 0, 0, 255))
                square_surface3.fill((0, 0, 0, 255))
            elif self.player.weaponType == 2:
                square_surface1.fill((0, 0, 0, 255))
                square_surface2.fill((0, 0, 0, 100))
                square_surface3.fill((0, 0, 0, 255))
            elif self.player.weaponType == 3:
                square_surface1.fill((0, 0, 0, 255))
                square_surface2.fill((0, 0, 0, 255))
                square_surface3.fill((0, 0, 0, 100))

            square_rect1 = square_surface1.get_rect(topleft=(10, 10))
            square_rect2 = square_surface2.get_rect(topleft=(30, 10))
            square_rect3 = square_surface3.get_rect(topleft=(50, 10))

            gun_rect.topleft = [12, 15]
            gun_img = gun_image.copy()
            self.display.blit(square_surface1, square_rect1)
            self.display.blit(gun_img, gun_rect)

            gun_img = gun_image.copy()
            gun_img.fill(
                (
                    0,
                    255,
                    0,
                ),
                special_flags=pygame.BLEND_RGB_MULT,
            )
            gun_rect.topleft = [32, 15]
            self.display.blit(square_surface2, square_rect2)
            self.display.blit(gun_img, gun_rect)

            gun_img = gun_image.copy()
            gun_img.fill(
                (
                    255,
                    0,
                    0,
                ),
                special_flags=pygame.BLEND_RGB_MULT,
            )
            gun_rect.topleft = [52, 15]
            self.display.blit(square_surface3, square_rect3)
            self.display.blit(gun_img, gun_rect)

        else:
            self.display.blit(
                self.assets["gun"],
                (
                    self.gun_pos[0] + self.tilemap.tile_size / 2 - render_scroll[0],
                    self.gun_pos[1] - render_scroll[1],
                ),
            )

    def run(self):
        pygame.mixer.music.load("data/music.wav")
        pygame.mixer.music.set_volume(0.5 * self.sound_factor)
        pygame.mixer.music.play(-1)

        self.sfx["ambience"].play(-1)

        while True:
            self.frame += 1
            self.display.fill((0, 0, 0, 0))
            self.display_2.fill((19, 24, 98, 1))
            self.screenshake = max(0, self.screenshake - 1)

            for enemy in self.enemies:
                if enemy.spawn == 1 and random.random() < 0.001:
                    self.enemies.append(Enemy(self, enemy.pos, (8, 15), 0, 1, "enemy"))

            if not len(self.enemies):
                self.transition += 1
                if self.transition > 30:
                    self.level = min(self.level + 1, len(os.listdir("data/maps")) - 1)
                    self.load_level(LEVELS[self.level])
            if self.transition < 0:
                self.transition += 1

            if self.dead:
                self.dead += 1
                if self.dead == 10:
                    self.transition = min(30, self.transition + 1)
                if self.dead > 40:
                    self.load_level(LEVELS[self.level])
                    self.gun = False

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

            if self.night:
                for i in range(0, len(self.stars_pos)):
                    img = pygame.image.load("data/images/star.png")
                    img.set_colorkey((0, 0, 0, 0))
                    self.display_2.blit(
                        pygame.transform.smoothscale(
                            img, (self.starsize[i], self.starsize[i])
                        ),
                        self.stars_pos[i],
                    )
            else:
                self.display_2.blit(self.assets["background"], (0, 0))
                self.clouds.update()
                self.clouds.render(self.display_2, offset=render_scroll)

            self.tilemap.render(self.display, offset=render_scroll)

            for enemy in self.enemies.copy():
                kill = enemy.update(self.tilemap, (0, 0), self.gravity)
                enemy.render(self.display, offset=render_scroll)
                if kill:
                    self.enemies.remove(enemy)

            for jump_pad in self.jump_pads:
                if jump_pad.update(self.player.rect()):
                    self.player.jump(-5)
                    self.sfx["jump_pad"].play()
                jump_pad.render(self.display, render_scroll)

            for lever in self.levers:
                if lever.update(self.player.rect()):
                    self.gravity = -self.gravity
                lever.render(self.display, render_scroll)

            self.tilemap.block_check(self.player)

            if not self.dead:
                self.player.update(
                    self.tilemap, (self.movement[1] - self.movement[0], 0), self.gravity
                )
                self.player.render(self.display, offset=render_scroll)

            self.handle_projectiles(render_scroll)
            self.handle_particles(render_scroll)
            self.drawGun(render_scroll)

            for piece in self.pieces:
                piece.update()
                piece.render(self.display, offset=render_scroll)
                if piece.pos[1] > self.player.pos[1] + 1000:
                    self.pieces.remove(piece)

            for dust in self.dusts:
                dust.update(self.frame, self.player)
            for dust in self.dusts:
                dust.render(self.display, offset=render_scroll)

            for dust in self.dusts:
                if self.player.rect().colliderect(
                    dust.x,
                    dust.y,
                    dust.image.get_width(),
                    dust.image.get_height(),
                ):
                    self.dead += 1

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
                        if self.player.jump():
                            self.sfx["jump"].play()
                    if event.key == pygame.K_x:
                        self.player.dash()
                    if event.key == pygame.K_z and self.gun:
                        self.player.shoot = True
                    if event.key == pygame.K_c and self.gun:
                        self.player.weaponType += 1
                        if self.player.weaponType > 3:
                            self.player.weaponType = 1

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
