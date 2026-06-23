# glwrap.py
# -------------------------------------------------------------------
# Safe OpenGL abstraction layer.
#
# Every other engine module talks to OpenGL THROUGH this file. Why:
# PyOpenGL might be missing (e.g. on a headless CI machine) or a given
# GL function may be unavailable on a particular driver. Instead of
# crashing, we fall back to a harmless no-op function and to hard-coded
# enum values, so logic-only code can still import and run without a GPU.
# -------------------------------------------------------------------
from __future__ import annotations          # Enable modern type-hint syntax on older Python versions
import importlib                             # Lets us import OpenGL modules dynamically (they may be absent)
from typing import Any, Callable, cast       # Any = anything, Callable = a function type, cast = hint-only conversion


def _noop(*args: Any, **kwargs: Any) -> None:  # Stand-in used whenever a real GL function is unavailable
    return None                                # Accept any arguments, ignore them all, and return nothing


def _load(name: str):                          # Attempt to import an optional module by dotted name
    try:                                       # The import can fail when PyOpenGL is not installed
        return importlib.import_module(name)   # Success: hand back the real module object
    except ImportError:                        # Module not present on this machine...
        return None                            # ...so return None and let callers use no-op fallbacks


_GL = _load("OpenGL.GL")                       # Core OpenGL module, or None if PyOpenGL is unavailable
_GLU = _load("OpenGL.GLU")                     # OpenGL Utility (GLU) module, or None if unavailable

# -----------------------------
# Core GL constants
# -----------------------------
# Read each constant from the real GL module when present; otherwise use the
# fixed hex value from the OpenGL spec so the rest of the engine still works.
GL_COLOR_BUFFER_BIT = int(getattr(_GL, "GL_COLOR_BUFFER_BIT", 0x00004000))  # Selects the color buffer in glClear
GL_DEPTH_BUFFER_BIT = int(getattr(_GL, "GL_DEPTH_BUFFER_BIT", 0x00000100))  # Selects the depth buffer in glClear
GL_DEPTH_TEST = int(getattr(_GL, "GL_DEPTH_TEST", 0x0B71))                  # Capability flag: per-pixel depth testing
GL_MODELVIEW = int(getattr(_GL, "GL_MODELVIEW", 0x1700))                    # Matrix mode for camera/world transforms
GL_PROJECTION = int(getattr(_GL, "GL_PROJECTION", 0x1701))                  # Matrix mode for the perspective projection
GL_QUADS = int(getattr(_GL, "GL_QUADS", 0x0007))                           # Primitive type: quadrilaterals (legacy)
GL_TRIANGLES = int(getattr(_GL, "GL_TRIANGLES", 0x0004))                    # Primitive type: triangles (what we use)
GL_TEXTURE_2D = int(getattr(_GL, "GL_TEXTURE_2D", 0x0DE1))                  # Target/capability for 2D textures
GL_TEXTURE_MIN_FILTER = int(getattr(_GL, "GL_TEXTURE_MIN_FILTER", 0x2801))  # Sampling rule when a texture is minified
GL_TEXTURE_MAG_FILTER = int(getattr(_GL, "GL_TEXTURE_MAG_FILTER", 0x2800))  # Sampling rule when a texture is magnified
GL_LINEAR = int(getattr(_GL, "GL_LINEAR", 0x2601))                         # Smooth (linear) texture filtering mode

# -----------------------------
# VBO / client state constants
# -----------------------------
GL_ARRAY_BUFFER = int(getattr(_GL, "GL_ARRAY_BUFFER", 0x8892))                       # Buffer target holding vertex data
GL_STATIC_DRAW = int(getattr(_GL, "GL_STATIC_DRAW", 0x88E4))                         # Hint: data set once, drawn many times
GL_VERTEX_ARRAY = int(getattr(_GL, "GL_VERTEX_ARRAY", 0x8074))                       # Client array of vertex positions
GL_TEXTURE_COORD_ARRAY = int(getattr(_GL, "GL_TEXTURE_COORD_ARRAY", 0x8078))         # Client array of texture coordinates
GL_FLOAT = int(getattr(_GL, "GL_FLOAT", 0x1406))                                     # Data type tag: 32-bit float values

# -----------------------------
# Basic GL wrappers
# -----------------------------
def glBegin(mode: int) -> None:                                                      # Begin a legacy immediate-mode primitive
    cast(Callable[[int], Any], getattr(_GL, "glBegin", _noop))(mode)                 # Call real glBegin, or no-op if missing

def glEnd() -> None:                                                                 # End a legacy immediate-mode primitive
    cast(Callable[[], Any], getattr(_GL, "glEnd", _noop))()                          # Call real glEnd, or no-op if missing

def glClear(mask: int) -> None:                                                      # Clear buffers selected by the bit mask
    cast(Callable[[int], Any], getattr(_GL, "glClear", _noop))(mask)                 # Forward to real glClear, or no-op

def glClearColor(r: float, g: float, b: float, a: float) -> None:                    # Set the color used to clear the screen
    cast(Callable[[float, float, float, float], Any], getattr(_GL, "glClearColor", _noop))(r, g, b, a)  # Forward RGBA values

def glColor3f(r: float, g: float, b: float) -> None:                                 # Set the current draw color (RGB)
    cast(Callable[[float, float, float], Any], getattr(_GL, "glColor3f", _noop))(r, g, b)  # Forward RGB, or no-op

def glEnable(cap: int) -> None:                                                      # Turn a GL capability on (e.g. depth test)
    cast(Callable[[int], Any], getattr(_GL, "glEnable", _noop))(cap)                 # Forward to real glEnable, or no-op

def glDisable(cap: int) -> None:                                                     # Turn a GL capability off
    cast(Callable[[int], Any], getattr(_GL, "glDisable", _noop))(cap)                # Forward to real glDisable, or no-op

def glLoadIdentity() -> None:                                                        # Reset the active matrix to identity
    cast(Callable[[], Any], getattr(_GL, "glLoadIdentity", _noop))()                 # Forward to real glLoadIdentity, or no-op

def glMatrixMode(mode: int) -> None:                                                 # Choose which matrix stack to edit
    cast(Callable[[int], Any], getattr(_GL, "glMatrixMode", _noop))(mode)            # Forward to real glMatrixMode, or no-op

def glPushMatrix() -> None:                                                          # Save the current matrix on the stack
    cast(Callable[[], Any], getattr(_GL, "glPushMatrix", _noop))()                   # Forward to real glPushMatrix, or no-op

def glPopMatrix() -> None:                                                           # Restore the last saved matrix
    cast(Callable[[], Any], getattr(_GL, "glPopMatrix", _noop))()                    # Forward to real glPopMatrix, or no-op

def glTranslatef(x: float, y: float, z: float) -> None:                              # Move the world/camera by (x, y, z)
    cast(Callable[[float, float, float], Any], getattr(_GL, "glTranslatef", _noop))(x, y, z)  # Forward translation, or no-op

def glRotatef(a: float, x: float, y: float, z: float) -> None:                       # Rotate by angle a around axis (x, y, z)
    cast(Callable[[float, float, float, float], Any], getattr(_GL, "glRotatef", _noop))(a, x, y, z)  # Forward rotation, or no-op

def glVertex3f(x: float, y: float, z: float) -> None:                                # Emit one vertex (legacy immediate mode)
    cast(Callable[[float, float, float], Any], getattr(_GL, "glVertex3f", _noop))(x, y, z)  # Forward vertex, or no-op

def glTexCoord2f(u: float, v: float) -> None:                                        # Set texture coordinate for next vertex
    cast(Callable[[float, float], Any], getattr(_GL, "glTexCoord2f", _noop))(u, v)   # Forward UV, or no-op

def gluPerspective(fov: float, aspect: float, near: float, far: float) -> None:      # Build a perspective projection matrix
    cast(Callable[[float, float, float, float], Any], getattr(_GLU, "gluPerspective", _noop))(fov, aspect, near, far)  # Forward to GLU, or no-op

# -----------------------------
# Texture helpers
# -----------------------------
def glGenTextures(n: int) -> int:                                                    # Allocate n texture IDs, return the first
    fn = getattr(_GL, "glGenTextures", _noop)                                        # Look up the real function (or no-op)
    result = fn(n)                                                                   # Ask GL for n new texture names
    if isinstance(result, (list, tuple)):                                            # PyOpenGL may return a list/tuple...
        return int(result[0])                                                        # ...so return the first ID as an int
    return int(result)                                                               # Otherwise it's a single value; return it

def glBindTexture(target: int, texture: int) -> None:                                # Make a texture ID the active one
    cast(Callable[[int, int], Any], getattr(_GL, "glBindTexture", _noop))(target, texture)  # Forward bind, or no-op

def glTexParameteri(target: int, pname: int, param: int) -> None:                    # Set an integer texture parameter
    cast(Callable[[int, int, int], Any], getattr(_GL, "glTexParameteri", _noop))(target, pname, param)  # Forward param, or no-op

def glTexImage2D(target: int, level: int, internalformat: int,                       # Upload pixel data as a 2D texture...
                 width: int, height: int, border: int,                              # ...with the given size and border
                 format: int, type: int, pixels: Any) -> None:                      # ...and the given pixel format/type
    cast(Callable[..., Any], getattr(_GL, "glTexImage2D", _noop))(                   # Forward all arguments to real glTexImage2D
        target, level, internalformat, width, height, border, format, type, pixels  # The full GL argument list, in order
    )                                                                               # (no-op if GL is unavailable)

# -----------------------------
# VBO / client state wrappers
# -----------------------------
def glGenBuffers(n: int) -> int:                                                     # Allocate n buffer (VBO) IDs, return first
    fn = getattr(_GL, "glGenBuffers", _noop)                                         # Look up the real function (or no-op)
    result = fn(n)                                                                   # Ask GL for n new buffer names
    if isinstance(result, (list, tuple)):                                            # Normalize a list/tuple return...
        return int(result[0])                                                        # ...to the first ID as an int
    return int(result)                                                               # Otherwise return the single value

def glBindBuffer(target: int, buffer: int) -> None:                                  # Make a buffer the active one for a target
    cast(Callable[[int, int], Any], getattr(_GL, "glBindBuffer", _noop))(target, buffer)  # Forward bind, or no-op

def glBufferData(target: int, data, usage: int) -> None:                             # Upload raw bytes into the bound buffer
    cast(Callable[[int, Any, int], Any], getattr(_GL, "glBufferData", _noop))(target, data, usage)  # Forward data, or no-op

def glEnableClientState(array: int) -> None:                                         # Enable a client vertex array (e.g. coords)
    cast(Callable[[int], Any], getattr(_GL, "glEnableClientState", _noop))(array)    # Forward enable, or no-op

def glDisableClientState(array: int) -> None:                                        # Disable a client vertex array
    cast(Callable[[int], Any], getattr(_GL, "glDisableClientState", _noop))(array)   # Forward disable, or no-op

def glVertexPointer(size: int, type_: int, stride: int, pointer) -> None:            # Describe how vertex positions are laid out
    cast(Callable[[int, int, int, Any], Any], getattr(_GL, "glVertexPointer", _noop))(size, type_, stride, pointer)  # Forward, or no-op

def glTexCoordPointer(size: int, type_: int, stride: int, pointer) -> None:          # Describe how texture coords are laid out
    cast(Callable[[int, int, int, Any], Any], getattr(_GL, "glTexCoordPointer", _noop))(size, type_, stride, pointer)  # Forward, or no-op

def glDrawArrays(mode: int, first: int, count: int) -> None:                         # Draw `count` vertices from the bound arrays
    cast(Callable[[int, int, int], Any], getattr(_GL, "glDrawArrays", _noop))(mode, first, count)  # Forward draw call, or no-op
