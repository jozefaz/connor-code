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
    for y in range(32):                              # Loop over every row
        for x in range(32):                          # Loop over every column
            if (x + y) % 2 == 0:                      # On a checkerboard pattern (every other pixel)...
                px[x, y] = (0x38, 0x8E, 0x3C, 255)    # ...paint a darker green for a subtle dithered look
    return img                                       # Hand back the finished grass-top image

def make_grass_side() -> Image.Image:                # Draw the side face: dirt below, a thin grass strip on top
    img = Image.new("RGBA", (32, 32), "#795548")     # Start with a 32x32 image filled with base dirt brown
    px = img.load()                                  # Get pixel access for per-pixel editing

    # Dirt dither
    for y in range(8, 32):                           # For the lower rows (the dirt portion)...
        for x in range(32):                          # ...across every column...
            if (x + y) % 2 == 0:                      # ...on the checkerboard pattern...
                px[x, y] = (0x6D, 0x4C, 0x41, 255)    # ...paint a darker brown to texture the dirt

    # Grass strip
    for y in range(8):                               # For the top 8 rows (the grassy lip)...
        for x in range(32):                          # ...across every column...
            px[x, y] = (0x4C, 0xAF, 0x50, 255)        # ...paint the base grass green
            if (x + y) % 2 == 0:                      # ...and on the checkerboard pattern...
                px[x, y] = (0x38, 0x8E, 0x3C, 255)    # ...paint the darker green dither

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
