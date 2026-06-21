# glwrap.py
from __future__ import annotations
import importlib
from typing import Any, Callable, cast

def _noop(*args: Any, **kwargs: Any) -> None:
    return None

def _load(name: str):
    try:
        return importlib.import_module(name)
    except ImportError:
        return None

_GL = _load("OpenGL.GL")
_GLU = _load("OpenGL.GLU")

# -----------------------------
# Core GL constants
# -----------------------------
GL_COLOR_BUFFER_BIT = int(getattr(_GL, "GL_COLOR_BUFFER_BIT", 0x00004000))
GL_DEPTH_BUFFER_BIT = int(getattr(_GL, "GL_DEPTH_BUFFER_BIT", 0x00000100))
GL_DEPTH_TEST = int(getattr(_GL, "GL_DEPTH_TEST", 0x0B71))
GL_MODELVIEW = int(getattr(_GL, "GL_MODELVIEW", 0x1700))
GL_PROJECTION = int(getattr(_GL, "GL_PROJECTION", 0x1701))
GL_QUADS = int(getattr(_GL, "GL_QUADS", 0x0007))
GL_TRIANGLES = int(getattr(_GL, "GL_TRIANGLES", 0x0004))
GL_TEXTURE_2D = int(getattr(_GL, "GL_TEXTURE_2D", 0x0DE1))
GL_TEXTURE_MIN_FILTER = int(getattr(_GL, "GL_TEXTURE_MIN_FILTER", 0x2801))
GL_TEXTURE_MAG_FILTER = int(getattr(_GL, "GL_TEXTURE_MAG_FILTER", 0x2800))
GL_LINEAR = int(getattr(_GL, "GL_LINEAR", 0x2601))

# -----------------------------
# VBO / client state constants
# -----------------------------
GL_ARRAY_BUFFER = int(getattr(_GL, "GL_ARRAY_BUFFER", 0x8892))
GL_STATIC_DRAW = int(getattr(_GL, "GL_STATIC_DRAW", 0x88E4))
GL_VERTEX_ARRAY = int(getattr(_GL, "GL_VERTEX_ARRAY", 0x8074))
GL_TEXTURE_COORD_ARRAY = int(getattr(_GL, "GL_TEXTURE_COORD_ARRAY", 0x8078))
GL_FLOAT = int(getattr(_GL, "GL_FLOAT", 0x1406))

# -----------------------------
# Basic GL wrappers
# -----------------------------
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

# -----------------------------
# Texture helpers
# -----------------------------
def glGenTextures(n: int) -> int:
    fn = getattr(_GL, "glGenTextures", _noop)
    result = fn(n)
    if isinstance(result, (list, tuple)):
        return int(result[0])
    return int(result)

def glBindTexture(target: int, texture: int) -> None:
    cast(Callable[[int, int], Any], getattr(_GL, "glBindTexture", _noop))(target, texture)

def glTexParameteri(target: int, pname: int, param: int) -> None:
    cast(Callable[[int, int, int], Any], getattr(_GL, "glTexParameteri", _noop))(target, pname, param)

def glTexImage2D(target: int, level: int, internalformat: int,
                 width: int, height: int, border: int,
                 format: int, type: int, pixels: Any) -> None:
    cast(Callable[..., Any], getattr(_GL, "glTexImage2D", _noop))(
        target, level, internalformat, width, height, border, format, type, pixels
    )

# -----------------------------
# VBO / client state wrappers
# -----------------------------
def glGenBuffers(n: int) -> int:
    fn = getattr(_GL, "glGenBuffers", _noop)
    result = fn(n)
    if isinstance(result, (list, tuple)):
        return int(result[0])
    return int(result)

def glBindBuffer(target: int, buffer: int) -> None:
    cast(Callable[[int, int], Any], getattr(_GL, "glBindBuffer", _noop))(target, buffer)

def glBufferData(target: int, data, usage: int) -> None:
    cast(Callable[[int, Any, int], Any], getattr(_GL, "glBufferData", _noop))(target, data, usage)

def glEnableClientState(array: int) -> None:
    cast(Callable[[int], Any], getattr(_GL, "glEnableClientState", _noop))(array)

def glDisableClientState(array: int) -> None:
    cast(Callable[[int], Any], getattr(_GL, "glDisableClientState", _noop))(array)

def glVertexPointer(size: int, type_: int, stride: int, pointer) -> None:
    cast(Callable[[int, int, int, Any], Any], getattr(_GL, "glVertexPointer", _noop))(size, type_, stride, pointer)

def glTexCoordPointer(size: int, type_: int, stride: int, pointer) -> None:
    cast(Callable[[int, int, int, Any], Any], getattr(_GL, "glTexCoordPointer", _noop))(size, type_, stride, pointer)

def glDrawArrays(mode: int, first: int, count: int) -> None:
    cast(Callable[[int, int, int], Any], getattr(_GL, "glDrawArrays", _noop))(mode, first, count)
