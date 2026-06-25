# textures.py
# -------------------------------------------------------------------
# Builds the block textures in code (no image files needed) and uploads
# them to the GPU. Each texture is a tiny 32x32 image drawn pixel-by-pixel
# with a checkerboard "dither" for a retro look, then handed to OpenGL.
# -------------------------------------------------------------------
from __future__ import annotations                  # Enable modern type-hint syntax on older Python versions
from typing import Any                               # Generic "any type" hint used by helpers
from PIL import Image                                # Pillow: lets us create and edit images in memory
import pygame                                        # Used here to convert images into a GL-friendly byte layout

from glwrap import (                                 # Pull GL helpers/constants from our safe wrapper layer
    glGenTextures, glBindTexture, glTexParameteri, glTexImage2D,  # Functions to create/configure/upload textures
    GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_TEXTURE_MAG_FILTER,  # Texture target + min/mag filter parameter names
    GL_LINEAR                                        # Linear (smooth) filtering value
)

# ---------------------------------------------------------
# Procedural block textures (replacing SVGs)
# ---------------------------------------------------------

def make_grass_top() -> Image.Image:                 # Draw the green top face of a grass block
    img = Image.new("RGBA", (32, 32), "#4CAF50")     # Start with a 32x32 image filled with base green
    px = img.load()                                  # Get a pixel-access object so we can edit individual pixels

    green_shades = [
        (0x4C, 0xAF, 0x50, 255),  # base green
        (0x56, 0xBB, 0x4F, 255),  # lighter green
        (0x38, 0x8E, 0x3C, 255),  # darker green
        (0x6B, 0x9B, 0x3A, 255),  # olive green
    ]
    brown_spots = [
        (0x6D, 0x4C, 0x41, 255),
        (0x5D, 0x43, 0x32, 255),
    ]

    for y in range(32):                              # Loop over every row
        for x in range(32):                          # Loop over every column
            shade = green_shades[(x * 3 + y * 2) % len(green_shades)]
            px[x, y] = shade                          # Paint a varied grass color
            if (x * y) % 11 == 0:                     # Add scattered brown spots for natural variation
                px[x, y] = brown_spots[(x + y) % len(brown_spots)]
    return img                                       # Hand back the finished grass-top image


def make_grass_side() -> Image.Image:                # Draw the side face: dirt below, a thin grass strip on top
    img = Image.new("RGBA", (32, 32), "#795548")     # Start with a 32x32 image filled with base dirt brown
    px = img.load()                                  # Get pixel access for per-pixel editing

    grass_shades = [
        (0x4C, 0xAF, 0x50, 255),
        (0x56, 0xBB, 0x4F, 255),
        (0x38, 0x8E, 0x3C, 255),
    ]
    dirt_shades = [
        (0x6D, 0x4C, 0x41, 255),
        (0x5D, 0x43, 0x32, 255),
        (0x43, 0x2E, 0x25, 255),
    ]
    brown_spots = [
        (0x6D, 0x4C, 0x41, 255),
        (0x5D, 0x43, 0x32, 255),
    ]

    # Dirt portion with extra brown scatter
    for y in range(8, 32):                           # For the lower rows (the dirt portion)...
        for x in range(32):                          # ...across every column...
            if (x + y) % 2 == 0:                      # ...on the checkerboard pattern...
                px[x, y] = dirt_shades[(x + y) % len(dirt_shades)]
            elif (x * y) % 13 == 0:                   # occasional darker brown spots
                px[x, y] = dirt_shades[(x + y + 1) % len(dirt_shades)]

    # Grass strip with color variation and brown scatter near the bottom edge
    for y in range(8):                               # For the top 8 rows (the grassy lip)...
        for x in range(32):                          # ...across every column...
            px[x, y] = grass_shades[(x + y) % len(grass_shades)]
            if (x + y) % 5 == 0:                      # occasional darker mottling
                px[x, y] = (0x38, 0x8E, 0x3C, 255)
            if y > 4 and (x * y) % 7 == 0:             # small brown patches near the bottom of the grass strip
                px[x, y] = brown_spots[(x + y) % len(brown_spots)]

    return img                                       # Hand back the finished grass-side image

def make_dirt() -> Image.Image:                      # Draw a plain dirt texture (used for dirt and grass bottoms)
    img = Image.new("RGBA", (32, 32), "#795548")     # Start with a 32x32 image filled with base dirt brown
    px = img.load()                                  # Get pixel access for per-pixel editing
    for y in range(32):                              # Loop over every row
        for x in range(32):                          # Loop over every column
            if (x + y) % 2 == 0:                      # On the checkerboard pattern...
                px[x, y] = (0x6D, 0x4C, 0x41, 255)    # ...paint a darker brown dither
    return img                                       # Hand back the finished dirt image

# ---------------------------------------------------------
# Upload PIL image → OpenGL texture
# ---------------------------------------------------------

def texture_from_image(img: Image.Image) -> int:     # Turn a Pillow image into a GPU texture and return its ID
    """Convert a PIL image into an OpenGL texture ID."""  # Docstring: states the function's job
    image = img.convert("RGBA")                      # Ensure the image has red/green/blue/alpha channels
    surface = pygame.image.fromstring(image.tobytes(), image.size, "RGBA")  # Wrap raw bytes in a pygame surface
    image_data = pygame.image.tostring(surface, "RGBA", True)  # Re-serialize bytes; True flips vertically for GL's origin
    width, height = image.size                       # Unpack the image dimensions for the upload call

    tex_id = glGenTextures(1)                         # Ask OpenGL for a fresh texture ID
    glBindTexture(GL_TEXTURE_2D, tex_id)              # Make that texture the active 2D texture to configure

    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)  # Smooth sampling when the texture is shrunk
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)  # Smooth sampling when the texture is enlarged

    glTexImage2D(                                    # Upload the pixel data into the bound texture
        GL_TEXTURE_2D, 0, 4,                         # Target, mipmap level 0, 4 channels (RGBA) internal format
        width, height, 0,                            # Texture width, height, and border (must be 0)
        0x1908,  # GL_RGBA                           # Pixel format of our data: RGBA
        0x1401,  # GL_UNSIGNED_BYTE                  # Pixel data type: one unsigned byte per channel
        image_data                                   # The actual bytes to upload
    )

    return tex_id                                    # Return the texture ID so the renderer can bind it later

# ---------------------------------------------------------
# Public texture loader for the engine
# ---------------------------------------------------------

def load_block_textures() -> dict[str, int]:         # Build every block texture once and return a name→ID map
    """Return a dict of all block textures."""       # Docstring: states the function's job
    return {                                         # Map each texture name the renderer asks for to its GL ID
        "grass_top": texture_from_image(make_grass_top()),    # Top face of grass blocks
        "grass_side": texture_from_image(make_grass_side()),  # Side faces of grass blocks
        "dirt": texture_from_image(make_dirt()),              # Dirt blocks (and grass bottoms)
        "stone": 0,  # no texture, use solid color           # Stone uses ID 0 = no texture, just a flat color
    }
