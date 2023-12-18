import json
import random
import pygame

AUTOTILE_MAP = {
    tuple(sorted([(1, 0), (0, 1)])): 0,
    tuple(sorted([(1, 0), (0, 1), (-1, 0)])): 1,
    tuple(sorted([(-1, 0), (0, 1)])): 2,
    tuple(sorted([(-1, 0), (0, -1), (0, 1)])): 3,
    tuple(sorted([(-1, 0), (0, -1)])): 4,
    tuple(sorted([(-1, 0), (0, -1), (1, 0)])): 5,
    tuple(sorted([(1, 0), (0, -1)])): 6,
    tuple(sorted([(1, 0), (0, -1), (0, 1)])): 7,
    tuple(sorted([(1, 0), (-1, 0), (0, 1), (0, -1)])): 8,
}

NEIGHBOR_OFFSETS = [
    (-3, 3),
    (-2, 3),
    (-1, 3),
    (0, 3),
    (1, 3),
    (2, 3),
    (3, 3),
    (-3, 2),
    (-2, 2),
    (-1, 2),
    (0, 2),
    (1, 2),
    (2, 2),
    (3, 2),
    (-3, 1),
    (-2, 1),
    (-1, 1),
    (0, 1),
    (1, 1),
    (2, 1),
    (3, 1),
    (-3, 0),
    (-2, 0),
    (-1, 0),
    (0, 0),
    (1, 0),
    (2, 0),
    (3, 0),
    (-3, -1),
    (-2, -1),
    (-1, -1),
    (0, -1),
    (1, -1),
    (2, -1),
    (3, -1),
    (-3, -2),
    (-2, -2),
    (-1, -2),
    (0, -2),
    (1, -2),
    (2, -2),
    (3, -2),
    (-3, -3),
    (-2, -3),
    (-1, -3),
    (0, -3),
    (1, -3),
    (2, -3),
    (3, -3),
]
PHYSICS_TILES = {"grass", "stone", "wall", "jump_pad", "block"}
AUTOTILE_TYPES = {"grass", "stone"}


class Tilemap:
    def __init__(self, game, tile_size=16):
        self.game = game
        self.tile_size = tile_size
        self.tilemap = {}
        self.offgrid_tiles = []

    def extract(self, id_pairs, keep=False):
        matches = []
        for tile in self.offgrid_tiles.copy():
            if (tile["type"], tile["variant"]) in id_pairs:
                matches.append(tile.copy())
                if not keep:
                    self.offgrid_tiles.remove(tile)

        for loc in self.tilemap.copy():
            tile = self.tilemap[loc]
            if (tile["type"], tile["variant"]) in id_pairs:
                matches.append(tile.copy())
                matches[-1]["pos"] = matches[-1]["pos"].copy()
                matches[-1]["pos"][0] *= self.tile_size
                matches[-1]["pos"][1] *= self.tile_size
                if not keep:
                    del self.tilemap[loc]

        return matches

    def tiles_around(self, pos):
        tiles = []
        tile_loc = (int(pos[0] // self.tile_size), int(pos[1] // self.tile_size))
        for (
            offset
        ) in (
            NEIGHBOR_OFFSETS
        ):  # warning: breaks on entity enlargement. NEIGHBOR_OFFSETS must be adjusted
            check_loc = (
                str(tile_loc[0] + offset[0]) + ";" + str(tile_loc[1] + offset[1])
            )
            if check_loc in self.tilemap:
                tiles.append(self.tilemap[check_loc])
        return tiles

    def save(self, path):
        f = open(path, "w")
        json.dump(
            {
                "tilemap": self.tilemap,
                "tile_size": self.tile_size,
                "offgrid": self.offgrid_tiles,
            },
            f,
        )
        f.close()

    def load(self, path):
        f = open(path, "r")
        map_data = json.load(f)
        f.close()

        self.tilemap = map_data["tilemap"]
        self.tile_size = map_data["tile_size"]
        self.offgrid_tiles = map_data["offgrid"]

        for tile_loc in self.tilemap:
            self.tilemap[tile_loc]["blockShake"] = 0
            self.tilemap[tile_loc]["falling"] = 0
            if self.tilemap[tile_loc]["type"] == "wall":
                if self.tilemap[tile_loc]["variant"] == 0:
                    self.tilemap[tile_loc]["health"] = 5
                else:
                    self.tilemap[tile_loc]["health"] = 1

    def solid_check(self, pos):
        tile_loc = (
            str(int(pos[0] // self.tile_size))
            + ";"
            + str(int(pos[1] // self.tile_size))
        )
        if tile_loc in self.tilemap:
            if self.tilemap[tile_loc]["type"] in PHYSICS_TILES:
                return self.tilemap[tile_loc]

    def block_check(self, player):
        keys_to_delete = []
        for tile_loc in self.tilemap:
            if (
                self.tilemap[tile_loc]["type"] == "block"
                and self.tilemap[tile_loc]["falling"] > 0
            ):
                self.tilemap[tile_loc]["falling"] += 1
                if self.tilemap[tile_loc]["falling"] > 10:
                    self.tilemap[tile_loc]["pos"][1] += (
                        self.tilemap[tile_loc]["falling"] / 500
                    )
            if self.tilemap[tile_loc]["falling"] > 300:
                keys_to_delete.append(tile_loc)

        for key in keys_to_delete:
            del self.tilemap[key]
                
        tile_loc = (
            str(int(player.pos[0] // self.tile_size))
            + ";"
            + str(int(player.pos[1] // self.tile_size + 1))
        )
        player_rect = player.rect()
        if tile_loc in self.tilemap:
            if self.tilemap[tile_loc]["type"] == "block":
                if (
                    player_rect.bottom >= self.tilemap[tile_loc]["pos"][1]
                    and self.tilemap[tile_loc]["falling"] == 0
                ):
                    self.tilemap[tile_loc]["falling"] = 1

    def wall_check(self, pos, speed):
        tile_loc = (
            str(int(pos[0] // self.tile_size))
            + ";"
            + str(int(pos[1] // self.tile_size))
        )
        if tile_loc in self.tilemap:
            if self.tilemap[tile_loc]["type"] == "wall":
                self.tilemap[tile_loc]["health"] -= 1
                self.tilemap[tile_loc]["pos"][0] += 0.01
                if speed[0] > 1:
                    self.tilemap[tile_loc]["blockShake"] = 60
                else:
                    self.tilemap[tile_loc]["blockShake"] = -60
                if self.tilemap[tile_loc]["health"] == 0:
                    del self.tilemap[tile_loc]
                return tile_loc

    def physics_rects_around(self, pos):
        rects = []
        for tile in self.tiles_around(pos):
            if tile["type"] in PHYSICS_TILES:
                rects.append(
                    pygame.Rect(
                        tile["pos"][0] * self.tile_size,
                        tile["pos"][1] * self.tile_size,
                        self.tile_size,
                        self.tile_size,
                    )
                )
        return rects

    def autotile(self):
        for loc in self.tilemap:
            tile = self.tilemap[loc]
            neighbors = set()
            for shift in [(1, 0), (-1, 0), (0, -1), (0, 1)]:
                check_loc = (
                    str(tile["pos"][0] + shift[0])
                    + ";"
                    + str(tile["pos"][1] + shift[1])
                )
                if check_loc in self.tilemap:
                    if self.tilemap[check_loc]["type"] == tile["type"]:
                        neighbors.add(shift)
            neighbors = tuple(sorted(neighbors))
            if (tile["type"] in AUTOTILE_TYPES) and (neighbors in AUTOTILE_MAP):
                tile["variant"] = AUTOTILE_MAP[neighbors]

    def render(self, surf, offset=(0, 0)):
        for tile in self.offgrid_tiles:
            surf.blit(
                self.game.assets[tile["type"]][tile["variant"]],
                (tile["pos"][0] - offset[0], tile["pos"][1] - offset[1]),
            )

        for x in range(
            offset[0] // self.tile_size,
            (offset[0] + surf.get_width()) // self.tile_size + 1,
        ):
            for y in range(
                offset[1] // self.tile_size,
                (offset[1] + surf.get_height()) // self.tile_size + 1,
            ):
                loc = str(x) + ";" + str(y)
                if loc in self.tilemap:
                    if self.tilemap[loc]["blockShake"] > 0:
                        self.tilemap[loc]["blockShake"] -= 1
                    elif self.tilemap[loc]["blockShake"] < 0:
                        self.tilemap[loc]["blockShake"] += 1

                    blockShake = self.tilemap[loc]["blockShake"]
                    tile = self.tilemap[loc]
                    surf.blit(
                        self.game.assets[tile["type"]][tile["variant"]],
                        (
                            tile["pos"][0] * self.tile_size
                            - offset[0]
                            + blockShake / 30,
                            tile["pos"][1] * self.tile_size - offset[1],
                        ),
                    )

    def find_lowest_block_position(self):
        lowest_y = float("-inf")
        lowest_block_position = None

        for tile in self.tilemap:
            tile_y = self.tilemap[tile]["pos"][1]
            if tile_y > lowest_y:
                lowest_y = tile_y
                lowest_block_position = self.tilemap[tile]["pos"]
        return lowest_block_position
