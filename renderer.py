# renderer.py
# -------------------------------------------------------------------
# Turns block data into triangles the GPU can draw. It builds a "mesh"
# (a list of vertices + texture coordinates) for each chunk, uploads it
# to GPU buffers (VBOs), and later draws it. This is the "artist" that
# actually paints the world on screen.
# -------------------------------------------------------------------
from __future__ import annotations                 # Enable modern type-hint syntax on older Python versions
from typing import Dict, List, Tuple                # Type hints for the data structures we build
import array                                        # Compact C-style float arrays, ideal for GPU uploads

from glwrap import (                                # Pull GL helpers/constants from our safe wrapper layer
    glEnable, glDisable, glBindTexture,             # Enable capabilities and bind textures
    glEnableClientState, glDisableClientState,      # Turn vertex/texcoord client arrays on and off
    glBindBuffer, glBufferData, glGenBuffers,       # Create and fill GPU buffers (VBOs)
    glVertexPointer, glTexCoordPointer, glDrawArrays,  # Describe array layouts and issue the draw call
    GL_TEXTURE_2D, GL_VERTEX_ARRAY, GL_TEXTURE_COORD_ARRAY,  # Texture target and client-array names
    GL_ARRAY_BUFFER, GL_STATIC_DRAW, GL_TRIANGLES, GL_FLOAT,  # Buffer target, usage hint, primitive + data type
    glColor3f                                       # Set a flat color (used for the untextured stone)
)

BLOCK_SIZE = 1.0                                    # Edge length of one cube in world units


class Mesh:                                         # Holds the GPU buffer IDs and draw info for one chunk
    def __init__(self):                              # Create an empty mesh (nothing uploaded yet)
        self.vertex_buffer = 0                       # GL buffer ID holding vertex positions (0 = none)
        self.uv_buffer = 0                           # GL buffer ID holding texture coordinates (0 = none)
        self.count = 0                               # Total number of vertices to draw
        # (texture_name, start, count)
        self.faces: List[Tuple[str, int, int]] = []  # Draw list: which texture to use for each vertex range


def get_face_texture(block: str, face: str) -> str:  # Decide which texture a given block face should use
    if block == "grass":                             # Grass blocks have three different looks...
        if face == "top":                            # The upward face...
            return "grass_top"                       # ...is fully green
        elif face == "bottom":                       # The downward face...
            return "dirt"                            # ...is plain dirt
        else:                                        # All four side faces...
            return "grass_side"                      # ...show the grass-over-dirt strip
    return block                                     # Other blocks (dirt, stone) use a texture named after themselves


def build_mesh(chunk) -> Mesh:                       # Build a drawable mesh from a chunk's block dictionary
    mesh = Mesh()                                    # Start with an empty mesh to fill in
    blocks = chunk.blocks                            # Local alias for this chunk's {(x,y,z): name} blocks

    verts: List[float] = []                          # Flat list of vertex coordinates: x, y, z, x, y, z, ...
    uvs: List[float] = []                            # Flat list of texture coords: u, v, u, v, ...

    def get(x, y, z):                                # Tiny helper: what block sits at this local position?
        return blocks.get((x, y, z))                 # Returns the block name, or None if that spot is empty (air)

    faces = [                                        # The six neighbor directions paired with a face name
        ((1, 0, 0), "east"),                         # +X neighbor → east face
        ((-1, 0, 0), "west"),                        # -X neighbor → west face
        ((0, 1, 0), "top"),                          # +Y neighbor → top face
        ((0, -1, 0), "bottom"),                      # -Y neighbor → bottom face
        ((0, 0, 1), "south"),                        # +Z neighbor → south face
        ((0, 0, -1), "north"),                       # -Z neighbor → north face
    ]

    for (x, y, z), block in blocks.items():          # Visit every solid block in the chunk
        for (dx, dy, dz), face in faces:             # Check each of its six faces
            nx, ny, nz = x + dx, y + dy, z + dz      # Coordinates of the neighbor on this side
            if get(nx, ny, nz) is None:              # Only draw the face if the neighbor is air (face culling)
                start = len(verts) // 3              # Vertex index where this face's geometry begins
                add_face_triangles(verts, uvs, x, y, z, face)  # Append the two triangles that make this face
                end = len(verts) // 3                # Vertex index just after this face's geometry
                tex = get_face_texture(block, face)  # Pick the texture this face should use
                mesh.faces.append((tex, start, end - start))  # Record texture + vertex range for drawing

    if not verts:                                    # If the chunk produced no visible faces...
        return mesh                                  # ...return the empty mesh (nothing to upload)

    v_arr = array.array("f", verts)                  # Pack vertex floats into a compact byte-ready array
    uv_arr = array.array("f", uvs)                   # Pack texture-coord floats into a compact array

    vb = glGenBuffers(1)                             # Allocate a GPU buffer for vertex positions
    glBindBuffer(GL_ARRAY_BUFFER, vb)                # Make it the active buffer
    glBufferData(GL_ARRAY_BUFFER, v_arr.tobytes(), GL_STATIC_DRAW)  # Upload vertex bytes (won't change often)

    ub = glGenBuffers(1)                             # Allocate a GPU buffer for texture coordinates
    glBindBuffer(GL_ARRAY_BUFFER, ub)                # Make it the active buffer
    glBufferData(GL_ARRAY_BUFFER, uv_arr.tobytes(), GL_STATIC_DRAW)  # Upload UV bytes (won't change often)

    mesh.vertex_buffer = vb                          # Remember the vertex buffer ID on the mesh
    mesh.uv_buffer = ub                              # Remember the UV buffer ID on the mesh
    mesh.count = len(verts) // 3                     # Total vertices = float count / 3 (x, y, z each)

    return mesh                                      # Hand back the fully built, GPU-uploaded mesh


def add_face_triangles(verts: List[float], uvs: List[float], x: int, y: int, z: int, face: str):  # Add one face's 2 triangles
    s = BLOCK_SIZE                                   # Cube size (1.0) — short name for readability below
    x0 = x * s                                       # World X of the block's near-origin corner
    y0 = y * s                                       # World Y of the block's near-origin corner
    z0 = z * s                                       # World Z of the block's near-origin corner

    faces = {                                        # The four corners of each face, as a quad (square)
        "top": [                                     # Upward-facing square (constant y0+s)
            (x0,     y0+s, z0),                       # Corner 1
            (x0+s,   y0+s, z0),                       # Corner 2
            (x0+s,   y0+s, z0+s),                     # Corner 3
            (x0,     y0+s, z0+s),                     # Corner 4
        ],
        "bottom": [                                  # Downward-facing square (constant y0)
            (x0,     y0, z0),                         # Corner 1
            (x0+s,   y0, z0),                         # Corner 2
            (x0+s,   y0, z0+s),                       # Corner 3
            (x0,     y0, z0+s),                       # Corner 4
        ],
        "north": [                                   # -Z facing square (constant z0)
            (x0,     y0,   z0),                       # Corner 1
            (x0,     y0+s, z0),                       # Corner 2
            (x0+s,   y0+s, z0),                       # Corner 3
            (x0+s,   y0,   z0),                       # Corner 4
        ],
        "south": [                                   # +Z facing square (constant z0+s)
            (x0,     y0,   z0+s),                     # Corner 1
            (x0+s,   y0,   z0+s),                     # Corner 2
            (x0+s,   y0+s, z0+s),                     # Corner 3
            (x0,     y0+s, z0+s),                     # Corner 4
        ],
        "west": [                                    # -X facing square (constant x0)
            (x0,     y0,   z0),                       # Corner 1
            (x0,     y0,   z0+s),                     # Corner 2
            (x0,     y0+s, z0+s),                     # Corner 3
            (x0,     y0+s, z0),                       # Corner 4
        ],
        "east": [                                    # +X facing square (constant x0+s)
            (x0+s,   y0,   z0),                       # Corner 1
            (x0+s,   y0+s, z0),                       # Corner 2
            (x0+s,   y0+s, z0+s),                     # Corner 3
            (x0+s,   y0,   z0+s),                     # Corner 4
        ],
    }

    quad = faces[face]                               # Pick the four corners for the requested face
    uv_quad = [(0, 0), (1, 0), (1, 1), (0, 1)]       # Texture coordinates for those four corners (full image)

    indices = [0, 1, 2, 0, 2, 3]                     # Two triangles (0-1-2 and 0-2-3) cover the quad
    for idx in indices:                              # Walk the six corner references in triangle order
        vx, vy, vz = quad[idx]                        # Look up that corner's 3D position
        u, v = uv_quad[idx]                           # Look up that corner's 2D texture coordinate
        verts.extend([vx, vy, vz])                    # Append the position to the vertex list
        uvs.extend([u, v])                            # Append the texture coordinate to the UV list


class Renderer:                                      # Knows the texture IDs and how to draw a finished mesh
    def __init__(self, textures: Dict[str, int]):    # Receive the name→texture-ID map built by textures.py
        self.textures = textures                     # Store it for use when binding textures during draw

    def draw_mesh(self, mesh: Mesh):                 # Draw one chunk's mesh this frame
        if mesh.count == 0:                          # Nothing to draw for an empty mesh...
            return                                   # ...so bail out early

        glEnable(GL_TEXTURE_2D)                       # Turn on 2D texturing

        glEnableClientState(GL_VERTEX_ARRAY)          # Tell GL we will supply vertex positions
        glEnableClientState(GL_TEXTURE_COORD_ARRAY)   # Tell GL we will supply texture coordinates

        glBindBuffer(GL_ARRAY_BUFFER, mesh.vertex_buffer)  # Activate this mesh's vertex buffer
        glVertexPointer(3, GL_FLOAT, 0, None)         # Positions are 3 floats each, tightly packed from the buffer

        glBindBuffer(GL_ARRAY_BUFFER, mesh.uv_buffer)  # Activate this mesh's texture-coordinate buffer
        glTexCoordPointer(2, GL_FLOAT, 0, None)       # Tex coords are 2 floats each, tightly packed from the buffer

        for tex, start, count in mesh.faces:          # For each recorded (texture, vertex-range) group...
            glBindTexture(GL_TEXTURE_2D, self.textures[tex])  # Bind that group's texture
            glDrawArrays(GL_TRIANGLES, start, count)  # Draw just that group's vertices as triangles

        glDisableClientState(GL_TEXTURE_COORD_ARRAY)  # Done: turn the texture-coord array back off
        glDisableClientState(GL_VERTEX_ARRAY)         # Done: turn the vertex array back off
