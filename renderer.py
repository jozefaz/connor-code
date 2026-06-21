# renderer.py
from __future__ import annotations
from typing import Dict, List, Tuple
import array

from glwrap import (
    glEnable, glDisable, glBindTexture,
    glEnableClientState, glDisableClientState,
    glBindBuffer, glBufferData, glGenBuffers,
    glVertexPointer, glTexCoordPointer, glDrawArrays,
    GL_TEXTURE_2D, GL_VERTEX_ARRAY, GL_TEXTURE_COORD_ARRAY,
    GL_ARRAY_BUFFER, GL_STATIC_DRAW, GL_TRIANGLES, GL_FLOAT,
    glColor3f
)

BLOCK_SIZE = 1.0


class Mesh:
    def __init__(self):
        self.vertex_buffer = 0
        self.uv_buffer = 0
        self.count = 0
        # (texture_name, start, count)
        self.faces: List[Tuple[str, int, int]] = []


def get_face_texture(block: str, face: str) -> str:
    if block == "grass":
        if face == "top":
            return "grass_top"
        elif face == "bottom":
            return "dirt"
        else:
            return "grass_side"
    return block


def build_mesh(chunk) -> Mesh:
    mesh = Mesh()
    blocks = chunk.blocks

    verts: List[float] = []
    uvs: List[float] = []

    def get(x, y, z):
        return blocks.get((x, y, z))

    faces = [
        ((1, 0, 0), "east"),
        ((-1, 0, 0), "west"),
        ((0, 1, 0), "top"),
        ((0, -1, 0), "bottom"),
        ((0, 0, 1), "south"),
        ((0, 0, -1), "north"),
    ]

    for (x, y, z), block in blocks.items():
        for (dx, dy, dz), face in faces:
            nx, ny, nz = x + dx, y + dy, z + dz
            if get(nx, ny, nz) is None:
                start = len(verts) // 3
                add_face_triangles(verts, uvs, x, y, z, face)
                end = len(verts) // 3
                tex = get_face_texture(block, face)
                mesh.faces.append((tex, start, end - start))

    if not verts:
        return mesh

    v_arr = array.array("f", verts)
    uv_arr = array.array("f", uvs)

    vb = glGenBuffers(1)
    glBindBuffer(GL_ARRAY_BUFFER, vb)
    glBufferData(GL_ARRAY_BUFFER, v_arr.tobytes(), GL_STATIC_DRAW)

    ub = glGenBuffers(1)
    glBindBuffer(GL_ARRAY_BUFFER, ub)
    glBufferData(GL_ARRAY_BUFFER, uv_arr.tobytes(), GL_STATIC_DRAW)

    mesh.vertex_buffer = vb
    mesh.uv_buffer = ub
    mesh.count = len(verts) // 3

    return mesh


def add_face_triangles(verts: List[float], uvs: List[float], x: int, y: int, z: int, face: str):
    s = BLOCK_SIZE
    x0 = x * s
    y0 = y * s
    z0 = z * s

    faces = {
        "top": [
            (x0,     y0+s, z0),
            (x0+s,   y0+s, z0),
            (x0+s,   y0+s, z0+s),
            (x0,     y0+s, z0+s),
        ],
        "bottom": [
            (x0,     y0, z0),
            (x0+s,   y0, z0),
            (x0+s,   y0, z0+s),
            (x0,     y0, z0+s),
        ],
        "north": [
            (x0,     y0,   z0),
            (x0,     y0+s, z0),
            (x0+s,   y0+s, z0),
            (x0+s,   y0,   z0),
        ],
        "south": [
            (x0,     y0,   z0+s),
            (x0+s,   y0,   z0+s),
            (x0+s,   y0+s, z0+s),
            (x0,     y0+s, z0+s),
        ],
        "west": [
            (x0,     y0,   z0),
            (x0,     y0,   z0+s),
            (x0,     y0+s, z0+s),
            (x0,     y0+s, z0),
        ],
        "east": [
            (x0+s,   y0,   z0),
            (x0+s,   y0+s, z0),
            (x0+s,   y0+s, z0+s),
            (x0+s,   y0,   z0+s),
        ],
    }

    quad = faces[face]
    uv_quad = [(0, 0), (1, 0), (1, 1), (0, 1)]

    indices = [0, 1, 2, 0, 2, 3]
    for idx in indices:
        vx, vy, vz = quad[idx]
        u, v = uv_quad[idx]
        verts.extend([vx, vy, vz])
        uvs.extend([u, v])


class Renderer:
    def __init__(self, textures: Dict[str, int]):
        self.textures = textures

    def draw_mesh(self, mesh: Mesh):
        if mesh.count == 0:
            return

        glEnable(GL_TEXTURE_2D)

        glEnableClientState(GL_VERTEX_ARRAY)
        glEnableClientState(GL_TEXTURE_COORD_ARRAY)

        glBindBuffer(GL_ARRAY_BUFFER, mesh.vertex_buffer)
        glVertexPointer(3, GL_FLOAT, 0, None)

        glBindBuffer(GL_ARRAY_BUFFER, mesh.uv_buffer)
        glTexCoordPointer(2, GL_FLOAT, 0, None)

        for tex, start, count in mesh.faces:
            glBindTexture(GL_TEXTURE_2D, self.textures[tex])
            glDrawArrays(GL_TRIANGLES, start, count)

        glDisableClientState(GL_TEXTURE_COORD_ARRAY)
        glDisableClientState(GL_VERTEX_ARRAY)
