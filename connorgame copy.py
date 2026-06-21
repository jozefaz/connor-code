from __future__ import annotations

import importlib
import math
import sys
from typing import Any, Callable, Optional, cast

import pygame
from pygame.locals import (
    DOUBLEBUF, OPENGL, QUIT, KEYDOWN,
    K_ESCAPE, K_w, K_a, K_s, K_d, K_1, K_9
)

from PIL import Image

def _noop(*args: Any, **kwargs: Any) -> None:
    return None

def _load_module(name: str) -> Any:
    try:
        return importlib.import_module(name)
    except ImportError:
        return None

_GL = _load_module("OpenGL.GL")
_GLU = _load_module("OpenGL.GLU")

# ---- GL CONSTANTS ----
GL_COLOR_BUFFER_BIT = int(getattr(_GL, "GL_COLOR_BUFFER_BIT", 0x00004000))
GL_DEPTH_BUFFER_BIT = int(getattr(_GL, "GL_DEPTH_BUFFER_BIT", 0x00000100))
GL_DEPTH_TEST = int(getattr(_GL, "GL_DEPTH_TEST", 0x0B71))
GL_MODELVIEW = int(getattr(_GL, "GL_MODELVIEW", 0x1700))
GL_PROJECTION = int(getattr(_GL, "GL_PROJECTION", 0x1701))
GL_QUADS = int(getattr(_GL, "GL_QUADS", 0x0007))
GL_TEXTURE_2D = int(getattr(_GL, "GL_TEXTURE_2D", 0x0DE1))
GL_TEXTURE_MIN_FILTER = int(getattr(_GL, "GL_TEXTURE_MIN_FILTER", 0x2801))
GL_TEXTURE_MAG_FILTER = int(getattr(_GL, "GL_TEXTURE_MAG_FILTER", 0x2800))
GL_LINEAR = int(getattr(_GL, "GL_LINEAR", 0x2601))

# ---- GL WRAPPERS ----
def glBegin(mode: int) -> None:
    cast(Callable[[int], Any], getattr(_GL, "glBegin", _noop))(mode)

def glEnd() -> None:
    cast(Callable[[], Any], getattr(_GL, "glEnd", _noop))()

def glClear(mask: int) -> None:
    cast(Callable[[int], Any], getattr(_GL, "glClear", _noop))(mask)

def glClearColor(r: float, g: float, b: float, a: float) -> None:
    cast(Callable[[float, float, float, float], Any], getattr(_GL, "glClearColor", _noop))(r, g, b, a)

def glColor3f(r: float, g: float, b: float) -> None:
    cast(Callable[[float, float, float], Any], getattr(_GL, "glColor3f", _noop))(r, g, b)

def glEnable(cap: int) -> None:
    cast(Callable[[int], Any], getattr(_GL, "glEnable", _noop))(cap)

def glDisable(cap: int) -> None:
    cast(Callable[[int], Any], getattr(_GL, "glDisable", _noop))(cap)

def glLoadIdentity() -> None:
    cast(Callable[[], Any], getattr(_GL, "glLoadIdentity", _noop))()

def glMatrixMode(mode: int) -> None:
    cast(Callable[[int], Any], getattr(_GL, "glMatrixMode", _noop))(mode)

def glPushMatrix() -> None:
    cast(Callable[[], Any], getattr(_GL, "glPushMatrix", _noop))()

def glPopMatrix() -> None:
    cast(Callable[[], Any], getattr(_GL, "glPopMatrix", _noop))()

def glTranslatef(x: float, y: float, z: float) -> None:
    cast(Callable[[float, float, float], Any], getattr(_GL, "glTranslatef", _noop))(x, y, z)

def glRotatef(a: float, x: float, y: float, z: float) -> None:
    cast(Callable[[float, float, float, float], Any], getattr(_GL, "glRotatef", _noop))(a, x, y, z)

def glVertex3f(x: float, y: float, z: float) -> None:
    cast(Callable[[float, float, float], Any], getattr(_GL, "glVertex3f", _noop))(x, y, z)

def glTexCoord2f(u: float, v: float) -> None:
    cast(Callable[[float, float], Any], getattr(_GL, "glTexCoord2f", _noop))(u, v)

def gluPerspective(fov: float, aspect: float, near: float, far: float) -> None:
    cast(Callable[[float, float, float, float], Any], getattr(_GLU, "gluPerspective", _noop))(fov, aspect, near, far)

def glGenTextures(n: int) -> list[int]:
    return cast(Callable[[int], list[int]], getattr(_GL, "glGenTextures", _noop))(n)

def glBindTexture(target: int, texture: int) -> None:
    cast(Callable[[int, int], Any], getattr(_GL, "glBindTexture", _noop))(target, texture)

def glTexParameteri(target: int, pname: int, param: int) -> None:
    cast(Callable[[int, int, int], Any], getattr(_GL, "glTexParameteri", _noop))(target, pname, param)

def glTexImage2D(
    target: int,
    level: int,
    internalformat: int,
    width: int,
    height: int,
    border: int,
    format: int,
    type: int,
    pixels: Any,
) -> None:
    cast(
        Callable[[int, int, int, int, int, int, int, int, Any], Any],
        getattr(_GL, "glTexImage2D", _noop),
    )(target, level, internalformat, width, height, border, format, type, pixels)

# ---- WINDOW ----
WIDTH, HEIGHT = 800, 600
BLOCK_SIZE = 1.0

cam_x, cam_y, cam_z = 0.0, 2.0, 6.0
yaw, pitch = 0.0, 0.0

move_speed = 0.15
mouse_sensitivity = 0.15

pygame.init()
flags = DOUBLEBUF | OPENGL if _GL and _GLU else 0
screen = pygame.display.set_mode((WIDTH, HEIGHT), flags)
pygame.display.set_caption("Minecraft Prototype")

pygame.event.set_grab(True)
pygame.mouse.set_visible(False)

glEnable(GL_DEPTH_TEST)
glEnable(GL_TEXTURE_2D)

glMatrixMode(GL_PROJECTION)
gluPerspective(75, WIDTH / HEIGHT, 0.1, 100.0)
glMatrixMode(GL_MODELVIEW)

clock = pygame.time.Clock()

# ---- PROCEDURAL TEXTURES ----

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

    for y in range(8, 32):
        for x in range(32):
            if (x + y) % 2 == 0:
                px[x, y] = (0x6D, 0x4C, 0x41, 255)

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

def texture_from_image(img: Image.Image) -> int:
    image = img.convert("RGBA")
    surface = pygame.image.fromstring(image.tobytes(), image.size, "RGBA")
    image_data = pygame.image.tostring(surface, "RGBA", True)
    width, height = image.size

    tex_id = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, tex_id)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexImage2D(
        GL_TEXTURE_2D, 0, 4, width, height, 0,
        getattr(_GL, "GL_RGBA", 0x1908),
        getattr(_GL, "GL_UNSIGNED_BYTE", 0x1401),
        image_data
    )
    return tex_id

# ---- BLOCK WORLD ----
class BlockSelector:
    def __init__(self) -> None:
        self.blocks: dict[tuple[int, int, int], str] = {
            (x, 0, z): "grass"
            for x in range(-20, 21)
            for z in range(-20, 21)
        }
        self.selected_slot: int = 0
        self.hotbar: list[Optional[str]] = ["stone", "dirt", "grass", None, None, None, None, None, None]

        self.textures: dict[str, int] = {
            "grass_top": texture_from_image(make_grass_top()),
            "grass_side": texture_from_image(make_grass_side()),
            "dirt": texture_from_image(make_dirt()),
            "stone": 0,
        }

    def draw_cube(self, x: float, y: float, z: float, tex: Optional[str]) -> None:
        s = BLOCK_SIZE / 2

        glPushMatrix()
        glTranslatef(x, y, z)

        if tex == "grass":
            glEnable(GL_TEXTURE_2D)

            glBindTexture(GL_TEXTURE_2D, self.textures["grass_side"])
            glBegin(GL_QUADS)
            glTexCoord2f(0, 0); glVertex3f(-s, -s,  s)
            glTexCoord2f(1, 0); glVertex3f( s, -s,  s)
            glTexCoord2f(1, 1); glVertex3f( s,  s,  s)
            glTexCoord2f(0, 1); glVertex3f(-s,  s,  s)
            glEnd()

            glBindTexture(GL_TEXTURE_2D, self.textures["grass_side"])
            glBegin(GL_QUADS)
            glTexCoord2f(0, 0); glVertex3f(-s, -s, -s)
            glTexCoord2f(1, 0); glVertex3f(-s,  s, -s)
            glTexCoord2f(1, 1); glVertex3f( s,  s, -s)
            glTexCoord2f(0, 1); glVertex3f( s, -s, -s)
            glEnd()

            glBindTexture(GL_TEXTURE_2D, self.textures["grass_side"])
            glBegin(GL_QUADS)
            glTexCoord2f(0, 0); glVertex3f(-s, -s, -s)
            glTexCoord2f(1, 0); glVertex3f(-s, -s,  s)
            glTexCoord2f(1, 1); glVertex3f(-s,  s,  s)
            glTexCoord2f(0, 1); glVertex3f(-s,  s, -s)
            glEnd()

            glBindTexture(GL_TEXTURE_2D, self.textures["grass_side"])
            glBegin(GL_QUADS)
            glTexCoord2f(0, 0); glVertex3f( s, -s, -s)
            glTexCoord2f(1, 0); glVertex3f( s,  s, -s)
            glTexCoord2f(1, 1); glVertex3f( s,  s,  s)
            glTexCoord2f(0, 1); glVertex3f( s, -s,  s)
            glEnd()

            glBindTexture(GL_TEXTURE_2D, self.textures["grass_top"])
            glBegin(GL_QUADS)
            glTexCoord2f(0, 0); glVertex3f(-s,  s,  s)
            glTexCoord2f(1, 0); glVertex3f( s,  s,  s)
            glTexCoord2f(1, 1); glVertex3f( s,  s, -s)
            glTexCoord2f(0, 1); glVertex3f(-s,  s, -s)
            glEnd()

            glBindTexture(GL_TEXTURE_2D, self.textures["dirt"])
            glBegin(GL_QUADS)
            glTexCoord2f(0, 0); glVertex3f(-s, -s, -s)
            glTexCoord2f(1, 0); glVertex3f( s, -s, -s)
            glTexCoord2f(1, 1); glVertex3f( s, -s,  s)
            glTexCoord2f(0, 1); glVertex3f(-s, -s,  s)
            glEnd()

        elif tex == "dirt":
            glEnable(GL_TEXTURE_2D)
            glBindTexture(GL_TEXTURE_2D, self.textures["dirt"])
            glBegin(GL_QUADS)

            glTexCoord2f(0, 0); glVertex3f(-s, -s,  s)
            glTexCoord2f(1, 0); glVertex3f( s, -s,  s)
            glTexCoord2f(1, 1); glVertex3f( s,  s,  s)
            glTexCoord2f(0, 1); glVertex3f(-s,  s,  s)

            glTexCoord2f(0, 0); glVertex3f(-s, -s, -s)
            glTexCoord2f(1, 0); glVertex3f(-s,  s, -s)
            glTexCoord2f(1, 1); glVertex3f( s,  s, -s)
            glTexCoord2f(0, 1); glVertex3f( s, -s, -s)

            glTexCoord2f(0, 0); glVertex3f(-s, -s, -s)
            glTexCoord2f(1, 0); glVertex3f(-s, -s,  s)
            glTexCoord2f(1, 1); glVertex3f(-s,  s,  s)
            glTexCoord2f(0, 1); glVertex3f(-s,  s, -s)

            glTexCoord2f(0, 0); glVertex3f( s, -s, -s)
            glTexCoord2f(1, 0); glVertex3f( s,  s, -s)
            glTexCoord2f(1, 1); glVertex3f( s,  s,  s)
            glTexCoord2f(0, 1); glVertex3f( s, -s,  s)

            glTexCoord2f(0, 0); glVertex3f(-s,  s,  s)
            glTexCoord2f(1, 0); glVertex3f( s,  s,  s)
            glTexCoord2f(1, 1); glVertex3f( s,  s, -s)
            glTexCoord2f(0, 1); glVertex3f(-s,  s, -s)

            glTexCoord2f(0, 0); glVertex3f(-s, -s, -s)
            glTexCoord2f(1, 0); glVertex3f( s, -s, -s)
            glTexCoord2f(1, 1); glVertex3f( s, -s,  s)
            glTexCoord2f(0, 1); glVertex3f(-s, -s,  s)
            glEnd()

        elif tex == "stone":
            glDisable(GL_TEXTURE_2D)
            glColor3f(0.6, 0.6, 0.65)
            glBegin(GL_QUADS)

            glVertex3f(-s, -s,  s)
            glVertex3f( s, -s,  s)
            glVertex3f( s,  s,  s)
            glVertex3f(-s,  s,  s)

            glVertex3f(-s, -s, -s)
            glVertex3f(-s,  s, -s)
            glVertex3f( s,  s, -s)
            glVertex3f( s, -s, -s)

            glVertex3f(-s, -s, -s)
            glVertex3f(-s, -s,  s)
            glVertex3f(-s,  s,  s)
            glVertex3f(-s,  s, -s)

            glVertex3f( s, -s, -s)
            glVertex3f( s,  s, -s)
            glVertex3f( s,  s,  s)
            glVertex3f( s, -s,  s)

            glVertex3f(-s,  s,  s)
            glVertex3f( s,  s,  s)
            glVertex3f( s,  s, -s)
            glVertex3f(-s,  s, -s)

            glVertex3f(-s, -s, -s)
            glVertex3f( s, -s, -s)
            glVertex3f( s, -s,  s)
            glVertex3f(-s, -s,  s)
            glEnd()
            glEnable(GL_TEXTURE_2D)

        else:
            glDisable(GL_TEXTURE_2D)
            glColor3f(1.0, 1.0, 1.0)
            glBegin(GL_QUADS)

            glVertex3f(-s, -s,  s)
            glVertex3f( s, -s,  s)
            glVertex3f( s,  s,  s)
            glVertex3f(-s,  s,  s)

            glVertex3f(-s, -s, -s)
            glVertex3f(-s,  s, -s)
            glVertex3f( s,  s, -s)
            glVertex3f( s, -s, -s)

            glVertex3f(-s, -s, -s)
            glVertex3f(-s, -s,  s)
            glVertex3f(-s,  s,  s)
            glVertex3f(-s,  s, -s)

            glVertex3f( s, -s, -s)
            glVertex3f( s,  s, -s)
            glVertex3f( s,  s,  s)
            glVertex3f( s, -s,  s)

            glVertex3f(-s,  s,  s)
            glVertex3f( s,  s,  s)
            glVertex3f( s,  s, -s)
            glVertex3f(-s,  s, -s)

            glVertex3f(-s, -s, -s)
            glVertex3f( s, -s, -s)
            glVertex3f( s, -s,  s)
            glVertex3f(-s, -s,  s)
            glEnd()
            glEnable(GL_TEXTURE_2D)

        glPopMatrix()

    def move_camera(self, keys: pygame.key.ScancodeWrapper) -> None:
        global cam_x, cam_z, yaw
        rad = math.radians(yaw)
        fx, fz = math.sin(rad), -math.cos(rad)
        rx, rz = math.cos(rad), math.sin(rad)

        if keys[K_w]:
            cam_x += fx * move_speed
            cam_z += fz * move_speed
        if keys[K_s]:
            cam_x -= fx * move_speed
            cam_z -= fz * move_speed
        if keys[K_a]:
            cam_x -= rx * move_speed
            cam_z -= rz * move_speed
        if keys[K_d]:
            cam_x += rx * move_speed
            cam_z += rz * move_speed

    def main_loop(self) -> None:
        global yaw, pitch, cam_x, cam_y, cam_z

        running = True
        while running:
            for event in pygame.event.get():
                if event.type == QUIT:
                    running = False
                elif event.type == KEYDOWN:
                    if event.key == K_ESCAPE:
                        running = False
                    elif K_1 <= event.key <= K_9:
                        self.selected_slot = event.key - K_1

            keys = pygame.key.get_pressed()
            self.move_camera(keys)

            dx, dy = pygame.mouse.get_rel()
            yaw += dx * mouse_sensitivity
            pitch -= dy * mouse_sensitivity
            pitch = max(-89, min(89, pitch))

            glLoadIdentity()
            glRotatef(pitch, 1, 0, 0)
            glRotatef(yaw, 0, 1, 0)
            glTranslatef(-cam_x, -cam_y, -cam_z)

            glClearColor(0.6, 0.8, 1.0, 1)
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

            for (x, y, z), tex in self.blocks.items():
                self.draw_cube(float(x), float(y), float(z), tex)

            pygame.display.flip()
            clock.tick(60)

        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    BlockSelector().main_loop()
