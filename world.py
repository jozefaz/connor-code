# world.py
# -------------------------------------------------------------------
# World, chunks, and terrain generation.
# -------------------------------------------------------------------

from __future__ import annotations
from typing import Optional, Dict, Tuple
import math
import random

from renderer import Renderer, build_mesh
from textures import load_block_textures


def fade(t: float) -> float:
    return t * t * t * (t * (t * 6 - 15) + 10)


def lerp(a: float, b: float, t: float) -> float:
    return a + t * (b - a)


def grad(hash: int, x: float, z: float) -> float:
    h = hash & 3
    u = x if h < 2 else z
    v = z if h < 2 else x
    return (u if (h & 1) == 0 else -u) + (v if (h & 2) == 0 else -v)


class Perlin:
    def __init__(self, seed: int = 0):
        random.seed(seed)
        self.p = list(range(256))
        random.shuffle(self.p)
        self.p = self.p * 2

    def noise(self, x: float, z: float) -> float:
        X = int(math.floor(x)) & 255
        Z = int(math.floor(z)) & 255

        xf = x - math.floor(x)
        zf = z - math.floor(z)

        u = fade(xf)
        v = fade(zf)

        aa = self.p[self.p[X] + Z]
        ab = self.p[self.p[X] + Z + 1]
        ba = self.p[self.p[X + 1] + Z]
        bb = self.p[self.p[X + 1] + Z + 1]

        x1 = lerp(grad(aa, xf, zf), grad(ba, xf - 1, zf), u)
        x2 = lerp(grad(ab, xf, zf - 1), grad(bb, xf - 1, zf - 1), u)

        return (lerp(x1, x2, v) + 1) / 2


class Chunk:
    SIZE = 16

    def __init__(self, cx: int, cz: int):
        self.cx = cx
        self.cz = cz
        self.blocks: Dict[Tuple[int, int, int], str] = {}
        self.mesh = None
        self.generated = False

    def set_block(self, x: int, y: int, z: int, block: str):
        self.blocks[(x, y, z)] = block

    def get_block(self, x: int, y: int, z: int) -> Optional[str]:
        return self.blocks.get((x, y, z))


class World:
    def __init__(self):
        self.textures = load_block_textures()
        self.renderer = Renderer(self.textures)

        self.perlin = Perlin(seed=1337)
        self.chunks: Dict[Tuple[int, int], Chunk] = {}

        self.view_distance_chunks = 4

    def get_chunk(self, cx: int, cz: int) -> Chunk:
        key = (cx, cz)
        if key not in self.chunks:
            chunk = Chunk(cx, cz)
            self.populate_chunk(chunk)
            chunk.mesh = build_mesh(chunk)
            self.chunks[key] = chunk
        return self.chunks[key]

    def populate_chunk(self, chunk: Chunk):
        if chunk.generated:
            return

        base_x = chunk.cx * Chunk.SIZE
        base_z = chunk.cz * Chunk.SIZE

        for x in range(Chunk.SIZE):
            for z in range(Chunk.SIZE):
                wx = base_x + x
                wz = base_z + z

                h = int(self.perlin.noise(wx * 0.08, wz * 0.08) * 12 + 4)

                for y in range(h):
                    if y == h - 1:
                        block = "grass"
                    elif y > h - 4:
                        block = "dirt"
                    else:
                        block = "stone"
                    chunk.set_block(x, y, z, block)

        chunk.generated = True

    def update_visible_chunks(self, camera):
        cam_cx = int(math.floor(camera.x / Chunk.SIZE))
        cam_cz = int(math.floor(camera.z / Chunk.SIZE))

        for dx in range(-self.view_distance_chunks, self.view_distance_chunks + 1):
            for dz in range(-self.view_distance_chunks, self.view_distance_chunks + 1):
                self.get_chunk(cam_cx + dx, cam_cz + dz)

    def draw(self, camera):
        cam_cx = int(math.floor(camera.x / Chunk.SIZE))
        cam_cz = int(math.floor(camera.z / Chunk.SIZE))

        max_dist = self.view_distance_chunks

        rad = math.radians(camera.yaw)
        fx = math.sin(rad)
        fz = -math.cos(rad)

        for (cx, cz), chunk in self.chunks.items():
            if abs(cx - cam_cx) > max_dist or abs(cz - cam_cz) > max_dist:
                continue

            wx = cx * Chunk.SIZE + Chunk.SIZE / 2
            wz = cz * Chunk.SIZE + Chunk.SIZE / 2

            dx = wx - camera.x
            dz = wz - camera.z

            dot = dx * fx + dz * fz
            if dot < -Chunk.SIZE:
                continue

            if chunk.mesh:
                self.renderer.draw_mesh(chunk.mesh)

    def get_height_at(self, wx: int, wz: int) -> int:
        cx = math.floor(wx / Chunk.SIZE)
        cz = math.floor(wz / Chunk.SIZE)
        chunk = self.get_chunk(cx, cz)

        lx = int(wx - cx * Chunk.SIZE)
        lz = int(wz - cz * Chunk.SIZE)

        max_y = 0
        for y in range(0, 128):
            if chunk.get_block(lx, y, lz):
                max_y = y
        return max_y
