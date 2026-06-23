# world.py
# -------------------------------------------------------------------
# Builds and manages the actual world. It generates terrain heights
# from Perlin noise, groups blocks into 16x16 chunks, keeps only the
# chunks near the player loaded, and asks the renderer to draw them.
# This is the "world builder".
# -------------------------------------------------------------------
from __future__ import annotations              # Enable modern type-hint syntax on older Python versions
from typing import Optional, Dict, Tuple         # Type hints: Optional value, dict, and tuple key types
import math                                      # floor() and general math for chunk/coordinate calculations
import random                                    # Used to shuffle the Perlin permutation table

from renderer import Renderer, build_mesh         # Renderer class + mesh builder used by the World class
from textures import load_block_textures          # Factory that builds and uploads all block textures


# ---------------------------------------------------------
# Perlin noise (simple, fast)
# ---------------------------------------------------------
def fade(t: float) -> float:                     # Smoothing curve that softens noise transitions
    return t * t * t * (t * (t * 6 - 15) + 10)   # Classic Perlin "ease" curve 6t^5 - 15t^4 + 10t^3

def lerp(a: float, b: float, t: float) -> float:  # Linear interpolation between a and b
    return a + t * (b - a)                        # t=0 gives a, t=1 gives b, values between blend

def grad(hash: int, x: float, z: float) -> float:  # Turn a hash into a pseudo-random gradient direction
    h = hash & 3                                  # Keep only the low 2 bits → one of 4 directions
    u = x if h < 2 else z                         # Choose which axis contributes the first term
    v = z if h < 2 else x                         # Choose which axis contributes the second term
    return (u if (h & 1) == 0 else -u) + (v if (h & 2) == 0 else -v)  # Flip signs by bits to vary the gradient

class Perlin:                                     # Generates smooth, repeatable 2D noise for terrain height
    def __init__(self, seed: int = 0):            # Build the noise generator from a seed (same seed = same world)
        random.seed(seed)                         # Seed Python's RNG so the shuffle is reproducible
        self.p = list(range(256))                 # Start with the numbers 0..255 (the permutation table)
        random.shuffle(self.p)                    # Shuffle them into a random but fixed order
        self.p = self.p * 2                       # Duplicate the table so index lookups never overflow

    def noise(self, x: float, z: float) -> float:  # Sample the noise field at point (x, z) → value in 0..1
        X = int(math.floor(x)) & 255              # Integer grid cell X, wrapped into 0..255
        Z = int(math.floor(z)) & 255              # Integer grid cell Z, wrapped into 0..255

        xf = x - math.floor(x)                    # Fractional X position inside the cell (0..1)
        zf = z - math.floor(z)                    # Fractional Z position inside the cell (0..1)

        u = fade(xf)                              # Smoothed X fraction for interpolation weighting
        v = fade(zf)                              # Smoothed Z fraction for interpolation weighting

        aa = self.p[self.p[X] + Z]                # Hash for the cell's bottom-left corner
        ab = self.p[self.p[X] + Z + 1]            # Hash for the cell's top-left corner
        ba = self.p[self.p[X + 1] + Z]            # Hash for the cell's bottom-right corner
        bb = self.p[self.p[X + 1] + Z + 1]        # Hash for the cell's top-right corner

        x1 = lerp(grad(aa, xf, zf), grad(ba, xf - 1, zf), u)          # Blend bottom two corners along X
        x2 = lerp(grad(ab, xf, zf - 1), grad(bb, xf - 1, zf - 1), u)  # Blend top two corners along X

        return (lerp(x1, x2, v) + 1) / 2          # Blend along Z, then remap from -1..1 to 0..1


# ---------------------------------------------------------
# Chunk
# ---------------------------------------------------------
class Chunk:                                      # A 16x16 column of the world holding block data + its mesh
    SIZE = 16                                     # Width and depth of a chunk in blocks

    def __init__(self, cx: int, cz: int):         # Create an empty chunk at chunk-grid coords (cx, cz)
        self.cx = cx                              # Chunk index along X (not world coords)
        self.cz = cz                              # Chunk index along Z (not world coords)
        self.blocks: Dict[Tuple[int, int, int], str] = {}  # Local blocks: {(x,y,z): block_name}
        self.mesh = None                          # The built GPU mesh (filled in later by build_mesh)
        self.generated = False                    # Guard flag so terrain is only generated once

    def set_block(self, x: int, y: int, z: int, block: str):  # Place a block at local (x, y, z)
        self.blocks[(x, y, z)] = block            # Store the block name keyed by its position

    def get_block(self, x: int, y: int, z: int) -> Optional[str]:  # Look up a block at local (x, y, z)
        return self.blocks.get((x, y, z))         # Return its name, or None if that spot is empty


# ---------------------------------------------------------
# World
# ---------------------------------------------------------
class World:                                      # Owns all chunks, terrain generation, and drawing
    def __init__(self):                           # Set up textures, renderer, noise, and chunk storage
        self.textures = load_block_textures()     # Build all block textures once and keep the name→ID map
        self.renderer = Renderer(self.textures)   # Create the renderer, giving it those textures

        self.perlin = Perlin(seed=1337)           # Fixed seed → the same terrain every run
        self.chunks: Dict[Tuple[int, int], Chunk] = {}  # Cache of loaded chunks keyed by (cx, cz)

        self.view_distance_chunks = 4             # 4 → 9×9 chunks visible

    # -----------------------------------------------------
    # Chunk management
    # -----------------------------------------------------
    def get_chunk(self, cx: int, cz: int) -> Chunk:  # Fetch a chunk, creating + meshing it if it doesn't exist
        key = (cx, cz)                            # Dictionary key for this chunk
        if key not in self.chunks:                # First time we need this chunk...
            chunk = Chunk(cx, cz)                 # ...make an empty chunk
            self.populate_chunk(chunk)            # ...fill it with terrain blocks
            chunk.mesh = build_mesh(chunk)        # ...build and upload its mesh once
            self.chunks[key] = chunk              # ...cache it so we never rebuild it
        return self.chunks[key]                   # Return the (now guaranteed) cached chunk

    # -----------------------------------------------------
    # Terrain generation
    # -----------------------------------------------------
    def populate_chunk(self, chunk: Chunk):       # Fill a chunk with grass/dirt/stone based on noise
        if chunk.generated:                       # If this chunk was already generated...
            return                                # ...do nothing (avoid duplicate work)

        base_x = chunk.cx * Chunk.SIZE            # World X of the chunk's corner
        base_z = chunk.cz * Chunk.SIZE            # World Z of the chunk's corner

        for x in range(Chunk.SIZE):               # Loop over each local column X (0..15)
            for z in range(Chunk.SIZE):           # Loop over each local column Z (0..15)
                wx = base_x + x                   # World X of this column
                wz = base_z + z                   # World Z of this column

                # Terrain height
                h = int(self.perlin.noise(wx * 0.08, wz * 0.08) * 12 + 4)  # 0.08 = terrain frequency; *12+4 = height 4..16

                for y in range(h):                # Stack blocks from the ground (0) up to height h
                    if y == h - 1:                # The topmost block...
                        block = "grass"           # ...is grass
                    elif y > h - 4:               # The next few blocks below the surface...
                        block = "dirt"            # ...are dirt
                    else:                         # Everything deeper...
                        block = "stone"           # ...is stone

                    chunk.set_block(x, y, z, block)  # Place the chosen block at this local position

        chunk.generated = True                    # Mark the chunk done so we skip it next time

    # -----------------------------------------------------
    # Update visible chunks around camera
    # -----------------------------------------------------
    def update_visible_chunks(self, camera):      # Ensure every chunk near the camera exists (load on demand)
        cam_cx = int(math.floor(camera.x / Chunk.SIZE))  # Which chunk the camera is in along X
        cam_cz = int(math.floor(camera.z / Chunk.SIZE))  # Which chunk the camera is in along Z

        for dx in range(-self.view_distance_chunks, self.view_distance_chunks + 1):  # Sweep nearby chunks in X
            for dz in range(-self.view_distance_chunks, self.view_distance_chunks + 1):  # Sweep nearby chunks in Z
                self.get_chunk(cam_cx + dx, cam_cz + dz)  # Touch each chunk so it gets generated + cached

    # -----------------------------------------------------
    # Draw visible chunks
    # -----------------------------------------------------
    def draw(self, camera):                       # Draw every loaded chunk that is close enough to see
        cam_cx = int(math.floor(camera.x / Chunk.SIZE))  # Camera's chunk index along X
        cam_cz = int(math.floor(camera.z / Chunk.SIZE))  # Camera's chunk index along Z

        max_dist = self.view_distance_chunks      # How many chunks away we still bother to draw

        for (cx, cz), chunk in self.chunks.items():  # Go through every cached chunk
            if abs(cx - cam_cx) > max_dist or abs(cz - cam_cz) > max_dist:  # If it's beyond view distance...
                continue                          # ...skip it (distance culling)
            if chunk.mesh:                        # If the chunk has a built mesh...
                self.renderer.draw_mesh(chunk.mesh)  # ...hand it to the renderer to draw

    # -----------------------------------------------------
    # Height lookup for spawning
    # -----------------------------------------------------
    def get_height_at(self, wx: int, wz: int) -> int:  # Find the surface height at a world (wx, wz) — used to spawn
        cx = math.floor(wx / Chunk.SIZE)          # Which chunk contains this point along X
        cz = math.floor(wz / Chunk.SIZE)          # Which chunk contains this point along Z
        chunk = self.get_chunk(cx, cz)            # Make sure that chunk is loaded, then grab it

        lx = int(wx - cx * Chunk.SIZE)            # Convert world X to the chunk's local X (0..15)
        lz = int(wz - cz * Chunk.SIZE)            # Convert world Z to the chunk's local Z (0..15)

        max_y = 0                                 # Track the highest solid block found in this column
        for y in range(0, 128):                   # Scan upward through possible block heights
            if chunk.get_block(lx, y, lz):        # If there's a block at this height...
                max_y = y                         # ...remember it as the current top
        return max_y                              # Return the top block's Y (the surface height)
