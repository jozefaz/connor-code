# textures.py
from __future__ import annotations
from typing import Any
from PIL import Image
import pygame

from glwrap import (
    glGenTextures, glBindTexture, glTexParameteri, glTexImage2D,
    GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_TEXTURE_MAG_FILTER,
    GL_LINEAR
)

# ---------------------------------------------------------
# Procedural block textures (replacing SVGs)
# ---------------------------------------------------------

def make_grass_top() -> Image.Image:
    img = Image.new("RGBA", (32, 32), "#4CAF50")
    px = img.load()
    for y in range(32):
        for x in range(32):
            if (x + y) % 2 == 0:
                px[x, y] = (0x38, 0x8E, 0x3C, 255)
    return img

def make_grass_side() -> Image.Image:
    img = Image.new("RGBA", (32, 32), "#795548")
    px = img.load()

    # Dirt dither
    for y in range(8, 32):
        for x in range(32):
            if (x + y) % 2 == 0:
                px[x, y] = (0x6D, 0x4C, 0x41, 255)

    # Grass strip
    for y in range(8):
        for x in range(32):
            px[x, y] = (0x4C, 0xAF, 0x50, 255)
            if (x + y) % 2 == 0:
                px[x, y] = (0x38, 0x8E, 0x3C, 255)

    return img

def make_dirt() -> Image.Image:
    img = Image.new("RGBA", (32, 32), "#795548")
    px = img.load()
    for y in range(32):
        for x in range(32):
            if (x + y) % 2 == 0:
                px[x, y] = (0x6D, 0x4C, 0x41, 255)
    return img

# ---------------------------------------------------------
# Upload PIL image → OpenGL texture
# ---------------------------------------------------------

def texture_from_image(img: Image.Image) -> int:
    """Convert a PIL image into an OpenGL texture ID."""
    image = img.convert("RGBA")
    surface = pygame.image.fromstring(image.tobytes(), image.size, "RGBA")
    image_data = pygame.image.tostring(surface, "RGBA", True)
    width, height = image.size

    tex_id = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, tex_id)

    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

    glTexImage2D(
        GL_TEXTURE_2D, 0, 4,
        width, height, 0,
        0x1908,  # GL_RGBA
        0x1401,  # GL_UNSIGNED_BYTE
        image_data
    )

    return tex_id

# ---------------------------------------------------------
# Public texture loader for the engine
# ---------------------------------------------------------

def load_block_textures() -> dict[str, int]:
    """Return a dict of all block textures."""
    return {
        "grass_top": texture_from_image(make_grass_top()),
        "grass_side": texture_from_image(make_grass_side()),
        "dirt": texture_from_image(make_dirt()),
        "stone": 0,  # no texture, use solid color
    }
