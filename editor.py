import sys
import os
import pygame

from scripts.utils import load_images
from scripts.tilemap import Tilemap

RENDER_SCALE = 2.0


class Editor:
    def __init__(self):
        pygame.init()

        pygame.display.set_caption("editor")
        self.screen = pygame.display.set_mode((640, 480))
        self.display = pygame.Surface((320, 240))

        self.clock = pygame.time.Clock()

        self.assets = {
            "decor": load_images("tiles/decor"),
            "grass": load_images("tiles/grass"),
            "wall": load_images("tiles/wall"),
            "large_decor": load_images("tiles/large_decor"),
            "stone": load_images("tiles/stone"),
            "spawners": load_images("tiles/spawners"),
            "jump_pad": load_images("tiles/jump_pad"),
            "lever": load_images("tiles/lever", 1),
            "block": load_images("tiles/block"),
        }

        for i in range(len(self.assets["jump_pad"])):
            self.assets["jump_pad"][i] = pygame.transform.scale(
                self.assets["jump_pad"][i], [16, 16]
            )
        for i in range(len(self.assets["lever"])):
            self.assets["lever"][i] = pygame.transform.scale(
                self.assets["lever"][i], [16, 16]
            )

        self.movement = [False, False, False, False]

        self.tilemap = Tilemap(self, tile_size=16)

        try:
            self.tilemap.load("map.json")
        except FileNotFoundError:
            pass

        self.scroll = [0, 0]

        self.tile_list = list(self.assets)
        self.tile_group = 0
        self.tile_variant = 0

        self.clicking = False
        self.right_clicking = False
        self.shift = False
        self.ongrid = True

    def get_map_list(self):
        map_list = []
        for filename in os.listdir():
            if filename.endswith(".json") and not filename.endswith("_temp.json"):
                map_list.append(filename)
        return map_list

    def save_current_map(self, map_name):
        temp_filename = map_name.replace(".json", "_temp.json")
        self.tilemap.save(temp_filename)
        print(f"Saved {temp_filename}")

    def load_map(self, map_name):
        map_file = map_name
        temp_filename = map_name.replace(".json", "_temp.json")

        if os.path.exists(temp_filename):
            self.tilemap.load(temp_filename)
            print(f"Loaded {temp_filename}")
        else:
            self.tilemap.load(map_file)
            print(f"Loaded {map_file}")

    def cleanup_temp_files(self):
        map_files = os.listdir()
        for map_file in map_files:
            if map_file.endswith("_temp.json"):
                os.remove(map_file)

    def run(self):
        map_list = self.get_map_list()
        selected_map_index = 0
        current_map = None

        while True:
            self.display.fill((0, 0, 0))

            if current_map is None:
                current_map = map_list[selected_map_index]
                self.load_map(current_map)
                self.scroll[0] = 0
                self.scroll[1] = 0

            self.scroll[0] += (self.movement[1] - self.movement[0]) * 2
            self.scroll[1] += (self.movement[3] - self.movement[2]) * 2
            render_scroll = (int(self.scroll[0]), int(self.scroll[1]))

            self.tilemap.render(self.display, offset=render_scroll)

            current_tile_img = self.assets[self.tile_list[self.tile_group]][
                self.tile_variant
            ].copy()
            current_tile_img.set_alpha(100)

            mpos = pygame.mouse.get_pos()
            mpos = (mpos[0] / RENDER_SCALE, mpos[1] / RENDER_SCALE)
            tile_pos = (
                int((mpos[0] + self.scroll[0]) // self.tilemap.tile_size),
                int((mpos[1] + self.scroll[1]) // self.tilemap.tile_size),
            )

            if self.ongrid:
                self.display.blit(
                    current_tile_img,
                    (
                        tile_pos[0] * self.tilemap.tile_size - self.scroll[0],
                        tile_pos[1] * self.tilemap.tile_size - self.scroll[1],
                    ),
                )
            else:
                self.display.blit(current_tile_img, mpos)

            if self.clicking and self.ongrid:
                self.tilemap.tilemap[str(tile_pos[0]) + ";" + str(tile_pos[1])] = {
                    "type": self.tile_list[self.tile_group],
                    "variant": self.tile_variant,
                    "pos": tile_pos,
                    "blockShake": 0,
                }
            if self.right_clicking:
                tile_loc = str(tile_pos[0]) + ";" + str(tile_pos[1])
                if tile_loc in self.tilemap.tilemap:
                    del self.tilemap.tilemap[tile_loc]
                for tile in self.tilemap.offgrid_tiles.copy():
                    tile_img = self.assets[tile["type"]][tile["variant"]]
                    tile_r = pygame.Rect(
                        tile["pos"][0] - self.scroll[0],
                        tile["pos"][1] - self.scroll[1],
                        tile_img.get_width(),
                        tile_img.get_height(),
                    )
                    if tile_r.collidepoint(mpos):
                        self.tilemap.offgrid_tiles.remove(tile)

            self.display.blit(current_tile_img, (5, 5))

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.cleanup_temp_files()
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        self.clicking = True
                        if not self.ongrid:
                            self.tilemap.offgrid_tiles.append(
                                {
                                    "type": self.tile_list[self.tile_group],
                                    "variant": self.tile_variant,
                                    "pos": (
                                        mpos[0] + self.scroll[0],
                                        mpos[1] + self.scroll[1],
                                    ),
                                }
                            )
                    if event.button == 3:
                        self.right_clicking = True
                    if self.shift:
                        if event.button == 4:
                            self.tile_variant = (self.tile_variant - 1) % len(
                                self.assets[self.tile_list[self.tile_group]]
                            )
                        if event.button == 5:
                            self.tile_variant = (self.tile_variant + 1) % len(
                                self.assets[self.tile_list[self.tile_group]]
                            )
                    else:
                        if event.button == 4:
                            self.tile_group = (self.tile_group - 1) % len(
                                self.tile_list
                            )
                            self.tile_variant = 0
                        if event.button == 5:
                            self.tile_group = (self.tile_group + 1) % len(
                                self.tile_list
                            )
                            self.tile_variant = 0
                if event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        self.clicking = False
                    if event.button == 3:
                        self.right_clicking = False

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_a:
                        self.movement[0] = True
                    if event.key == pygame.K_d:
                        self.movement[1] = True
                    if event.key == pygame.K_w:
                        self.movement[2] = True
                    if event.key == pygame.K_s:
                        self.movement[3] = True
                    if event.key == pygame.K_g:
                        self.ongrid = not self.ongrid
                    if event.key == pygame.K_t:
                        self.tilemap.autotile()
                    if event.key == pygame.K_o:
                        self.tilemap.save(current_map)
                    if event.key == pygame.K_LSHIFT:
                        self.shift = True
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_a:
                        self.movement[0] = False
                    if event.key == pygame.K_d:
                        self.movement[1] = False
                    if event.key == pygame.K_w:
                        self.movement[2] = False
                    if event.key == pygame.K_s:
                        self.movement[3] = False
                    if event.key == pygame.K_LSHIFT:
                        self.shift = False

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        self.save_current_map(current_map)
                        selected_map_index = (selected_map_index - 1) % len(map_list)
                        current_map = None
                    elif event.key == pygame.K_DOWN:
                        self.save_current_map(current_map)
                        selected_map_index = (selected_map_index + 1) % len(map_list)
                        current_map = None

            for idx, map_filename in enumerate(map_list):
                color = (255, 255, 255)
                if idx == selected_map_index:
                    color = (0, 255, 0)
                map_label = pygame.font.Font(None, 10).render(map_filename, True, color)
                label_x = self.display.get_width() - map_label.get_width() - 10
                label_y = 30 + idx * 10
                self.display.blit(map_label, (label_x, label_y))

            self.screen.blit(
                pygame.transform.scale(self.display, self.screen.get_size()), (0, 0)
            )
            pygame.display.update()
            self.clock.tick(60)


Editor().run()
