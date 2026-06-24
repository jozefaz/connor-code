# renderer.py  # This file tells the computer how to turn blocks into triangles the GPU can draw

from __future__ import annotations  # This lets us use some newer typing features in older Python
from typing import Dict, List, Tuple  # We use these to describe what types our variables are
import array  # This helps us store lots of numbers in a compact way for the GPU

from glwrap import (  # We import OpenGL helper functions and constants from our wrapper
    glEnable, glDisable, glBindTexture,  # Turn things on/off and choose which texture to use
    glEnableClientState, glDisableClientState,  # Tell OpenGL we will send it vertex/UV data
    glBindBuffer, glBufferData, glGenBuffers,  # Create and fill GPU buffers
    glVertexPointer, glTexCoordPointer, glDrawArrays,  # Tell OpenGL how to read our buffers and draw
    GL_TEXTURE_2D, GL_VERTEX_ARRAY, GL_TEXTURE_COORD_ARRAY,  # Names for texture and array types
    GL_ARRAY_BUFFER, GL_STATIC_DRAW, GL_TRIANGLES, GL_FLOAT,  # More OpenGL constants we need
    glColor3f  # Lets us set a flat color when we don't use a texture
)

BLOCK_SIZE = 1.0  # Each block is 1 unit wide, tall, and deep in the world


class Mesh:  # This class holds all the data needed to draw one chunk
    def __init__(self):  # This runs when we make a new Mesh
        self.vertex_buffer = 0  # This will store the ID of the GPU buffer for positions (0 means none yet)
        self.uv_buffer = 0  # This will store the ID of the GPU buffer for texture coordinates
        self.count = 0  # This is how many vertices we will draw
        self.faces: List[Tuple[str, int, int]] = []  # This is a list of (texture_name, start_index, vertex_count)


def get_face_texture(block: str, face: str) -> str:  # This decides which picture (texture) to use for a block face
    if block == "grass":  # If the block is grass
        if face == "top":  # If we are drawing the top face
            return "grass_top"  # Use the grass_top texture
        elif face == "bottom":  # If we are drawing the bottom face
            return "dirt"  # Use the dirt texture
        else:  # For all the side faces
            return "grass_side"  # Use the grass_side texture
    return block  # For other blocks like "dirt" or "stone", use the texture with the same name


def build_mesh(chunk) -> Mesh:  # This function builds a mesh for one chunk using greedy meshing
    mesh = Mesh()  # Make an empty mesh to fill
    blocks = chunk.blocks  # This is a dictionary of all blocks in the chunk: (x,y,z) -> block_name

    CHUNK_SIZE = chunk.SIZE  # How wide and deep the chunk is (16)
    MAX_HEIGHT = 128  # How tall the world can be (we scan up to this height)

    verts: List[float] = []  # This list will hold all vertex positions (x, y, z, x, y, z, ...)
    uvs: List[float] = []  # This list will hold all texture coordinates (u, v, u, v, ...)

    def get_block(x: int, y: int, z: int):  # Helper to get which block is at a position
        return blocks.get((x, y, z))  # Return the block name or None if there is no block (air)

    # We will do greedy meshing in 3D by looking at 6 directions (faces)
    # Each direction is: (axis_index, direction_sign, face_name)
    directions = [  # These tell us which faces we are building
        (0, 1, "east"),   # Faces pointing +X (east)
        (0, -1, "west"),  # Faces pointing -X (west)
        (1, 1, "top"),    # Faces pointing +Y (top)
        (1, -1, "bottom"),  # Faces pointing -Y (bottom)
        (2, 1, "south"),  # Faces pointing +Z (south)
        (2, -1, "north"),  # Faces pointing -Z (north)
    ]

    # The world size in each axis: x, y, z
    dims = [CHUNK_SIZE, MAX_HEIGHT, CHUNK_SIZE]  # X and Z are chunk size, Y is max height

    for axis, direction, face_name in directions:  # Loop over each face direction we want to build
        u_axis = (axis + 1) % 3  # This is the first axis on the face plane
        v_axis = (axis + 2) % 3  # This is the second axis on the face plane

        # We make a 2D "mask" that represents which squares on this slice need faces
        mask: List[str | None] = [None] * (dims[u_axis] * dims[v_axis])  # Start with all empty

        # We slide through the chunk along the main axis (like slicing bread)
        for d in range(dims[axis]):  # For each slice along this axis
            # Build the mask for this slice
            n = 0  # This is the index into the mask list
            for v in range(dims[v_axis]):  # Loop over the v direction on the slice
                for u in range(dims[u_axis]):  # Loop over the u direction on the slice
                    pos = [0, 0, 0]  # This will hold x, y, z for the current block
                    pos[axis] = d  # Set the slice position on the main axis
                    pos[u_axis] = u  # Set the position on the u axis
                    pos[v_axis] = v  # Set the position on the v axis

                    block_here = get_block(pos[0], pos[1], pos[2])  # Get the block at this position

                    neighbor_pos = pos.copy()  # Copy the position to check the neighbor
                    neighbor_pos[axis] = d + direction  # Move one step in the face direction
                    block_neighbor = get_block(neighbor_pos[0], neighbor_pos[1], neighbor_pos[2])  # Get neighbor block

                    if block_here and not block_neighbor:  # If there is a block here and air next to it
                        mask[n] = block_here  # We need a face here, remember which block type
                    else:
                        mask[n] = None  # No face needed here
                    n += 1  # Move to the next mask cell

            # Now we run the greedy algorithm on this 2D mask
            n = 0  # Reset mask index
            v = 0  # Start at the first row
            while v < dims[v_axis]:  # Loop over rows
                u = 0  # Start at the first column
                while u < dims[u_axis]:  # Loop over columns
                    block_type = mask[n]  # Check what block type is at this mask cell
                    if block_type:  # If we need a face here
                        # Find how wide we can go to the right with the same block type
                        width = 1  # Start with width 1
                        while (u + width < dims[u_axis] and  # Stay inside the row
                               mask[n + width] == block_type):  # Same block type continues
                            width += 1  # Make the rectangle wider

                        # Now find how tall we can go down with the same block type for this width
                        height = 1  # Start with height 1
                        done = False  # This tells us when to stop growing
                        while (v + height < dims[v_axis] and not done):  # Stay inside the mask vertically
                            for k in range(width):  # Check each cell in the next row for this width
                                if mask[n + k + height * dims[u_axis]] != block_type:  # If any cell is different
                                    done = True  # We can't grow taller
                                    break  # Stop checking this row
                            if not done:  # If all cells matched
                                height += 1  # Grow the rectangle taller

                        # Now we have a big rectangle of faces we can draw as one quad
                        # We need to turn this rectangle into 4 corner points in 3D
                        x0 = [0, 0, 0]  # First corner
                        x1 = [0, 0, 0]  # Second corner
                        x2 = [0, 0, 0]  # Third corner
                        x3 = [0, 0, 0]  # Fourth corner

                        # All corners share the same slice position on the main axis
                        x0[axis] = d
                        x1[axis] = d
                        x2[axis] = d
                        x3[axis] = d

                        # Set the u and v coordinates for each corner
                        x0[u_axis] = u
                        x0[v_axis] = v

                        x1[u_axis] = u + width
                        x1[v_axis] = v

                        x2[u_axis] = u + width
                        x2[v_axis] = v + height

                        x3[u_axis] = u
                        x3[v_axis] = v + height

                        # Now we have a quad (square) with 4 corners: x0, x1, x2, x3
                        # We will turn it into 2 triangles (6 vertices)
                        start_index = len(verts) // 3  # Remember where these vertices start in the list

                        # The order [0,1,2, 0,2,3] makes two triangles that form the quad
                        corners = [x0, x1, x2, x3]  # Put corners in a list so we can index them
                        uv_corners = [(0, 0), (1, 0), (1, 1), (0, 1)]  # Simple full-texture UVs

                        for idx in [0, 1, 2, 0, 2, 3]:  # For each vertex of the two triangles
                            px, py, pz = corners[idx]  # Get the corner position
                            # Multiply by BLOCK_SIZE so blocks are the right size in the world
                            verts.extend([px * BLOCK_SIZE, py * BLOCK_SIZE, pz * BLOCK_SIZE])  # Add position
                            u_tex, v_tex = uv_corners[idx]  # Get the UV for this corner
                            uvs.extend([u_tex, v_tex])  # Add texture coordinates

                        end_index = len(verts) // 3  # Where this quad's vertices end
                        tex_name = get_face_texture(block_type, face_name)  # Decide which texture to use
                        mesh.faces.append((tex_name, start_index, end_index - start_index))  # Remember this draw call

                        # Clear the mask cells we just used so we don't use them again
                        for dv in range(height):  # For each row in the rectangle
                            for du in range(width):  # For each column in the rectangle
                                mask[n + du + dv * dims[u_axis]] = None  # Mark this cell as used

                        u += width  # Skip past this rectangle horizontally
                        n += width  # Move mask index too
                    else:
                        u += 1  # Move to the next column
                        n += 1  # Move mask index too
                v += 1  # Move to the next row

    # If we didn't add any vertices, just return the empty mesh
    if not verts:  # If the list is empty
        return mesh  # Nothing to draw

    # Turn the Python lists into compact arrays for the GPU
    v_arr = array.array("f", verts)  # Make a float array for positions
    uv_arr = array.array("f", uvs)  # Make a float array for texture coordinates

    # Make a GPU buffer for positions
    vb = glGenBuffers(1)  # Ask OpenGL to create 1 buffer and give us its ID
    glBindBuffer(GL_ARRAY_BUFFER, vb)  # Tell OpenGL we are working with this buffer now
    glBufferData(GL_ARRAY_BUFFER, v_arr.tobytes(), GL_STATIC_DRAW)  # Upload the position data to the GPU

    # Make a GPU buffer for texture coordinates
    ub = glGenBuffers(1)  # Create another buffer for UVs
    glBindBuffer(GL_ARRAY_BUFFER, ub)  # Select the UV buffer
    glBufferData(GL_ARRAY_BUFFER, uv_arr.tobytes(), GL_STATIC_DRAW)  # Upload the UV data

    mesh.vertex_buffer = vb  # Remember the position buffer ID in the mesh
    mesh.uv_buffer = ub  # Remember the UV buffer ID in the mesh
    mesh.count = len(verts) // 3  # Total number of vertices we have

    # Sort faces by texture name so we change textures less often
    mesh.faces.sort(key=lambda f: f[0])  # This makes drawing faster by grouping same textures

    return mesh  # Give back the finished mesh


class Renderer:  # This class knows how to draw a mesh using OpenGL
    def __init__(self, textures: Dict[str, int]):  # It needs a dictionary of texture names to texture IDs
        self.textures = textures  # Save the textures so we can use them later

    def draw_mesh(self, mesh: Mesh):  # This draws one chunk's mesh on the screen
        if mesh.count == 0:  # If there are no vertices, nothing to draw
            return  # Just stop

        glEnable(GL_TEXTURE_2D)  # Turn on 2D texturing
        glEnableClientState(GL_VERTEX_ARRAY)  # Tell OpenGL we will send vertex positions
        glEnableClientState(GL_TEXTURE_COORD_ARRAY)  # Tell OpenGL we will send texture coordinates

        glBindBuffer(GL_ARRAY_BUFFER, mesh.vertex_buffer)  # Select the vertex buffer
        glVertexPointer(3, GL_FLOAT, 0, None)  # Tell OpenGL that each vertex has 3 floats (x, y, z)

        glBindBuffer(GL_ARRAY_BUFFER, mesh.uv_buffer)  # Select the UV buffer
        glTexCoordPointer(2, GL_FLOAT, 0, None)  # Tell OpenGL that each UV has 2 floats (u, v)

        for tex_name, start, count in mesh.faces:  # Loop over each group of faces that share a texture
            if tex_name == "stone":  # If the texture is stone
                glDisable(GL_TEXTURE_2D)  # Turn off texturing
                glColor3f(0.6, 0.6, 0.6)  # Draw stone as a flat gray color
            else:
                glEnable(GL_TEXTURE_2D)  # Make sure texturing is on
                glBindTexture(GL_TEXTURE_2D, self.textures[tex_name])  # Bind the correct texture by its ID

            glDrawArrays(GL_TRIANGLES, start, count)  # Draw these vertices as triangles

        glDisableClientState(GL_TEXTURE_COORD_ARRAY)  # Stop sending UVs
        glDisableClientState(GL_VERTEX_ARRAY)  # Stop sending positions
        glDisable(GL_TEXTURE_2D)  # Turn off texturing when we're done
