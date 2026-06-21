🌍 Voxel Engine (Minecraft‑Style)
This project is a small 3D voxel engine written in Python, using Pygame and OpenGL.
It shows how games like Minecraft build worlds out of cubes, generate terrain, and draw everything on the screen.

It’s designed to be easy to read and learn from, especially for beginners.

📁 Project Files Explained
main.py
This is the main game file.
It:

Creates the game window

Sets up OpenGL

Creates the camera

Creates the world

Runs the game loop (updates 60 times per second)

Handles keyboard + mouse input

Draws the world

Think of it as the “director” of the whole program.

camera.py
Controls how the player moves and looks around.

It handles:

Player position (x, y, z)

Looking around with the mouse

Moving with WASD

Moving up/down with Space and Shift

This file is basically your eyes inside the world.

world.py
This file builds the actual world.

It handles:

Chunks (16×16 block sections of the world)

Terrain generation using Perlin noise

Block types (grass, dirt, stone)

Loading only nearby chunks to keep things fast

Building meshes for the renderer

This is the “world builder.”

renderer.py
Turns blocks into triangles that OpenGL can draw.

It:

Builds the mesh (the geometry) for each chunk

Uploads the mesh to the GPU using VBOs

Chooses the correct texture for each block face

Draws everything on the screen

This is the “artist” that draws the world.

glwrap.py
A helper file that wraps OpenGL functions so they are safe to call.

It:

Loads OpenGL functions

Provides constants like GL_TRIANGLES

Prevents crashes if a function is missing

This file is the “translator” between Python and OpenGL.

textures.py
Loads the block textures:

grass_top

grass_side

dirt

stone

These textures are sent to the GPU so the renderer can use them.

🎮 Controls
Key	Action
W	Move forward
S	Move backward
A	Move left
D	Move right
Space	Move up
Left Shift	Move down
Mouse	Look around
ESC	Quit


🧠 How It Works (Simple Explanation)
The world is made of blocks.

Blocks are grouped into chunks (16×16).

Terrain is generated using Perlin noise.

The renderer turns blocks into triangles.

OpenGL draws the triangles on the screen.

The camera moves around so you can explore.

🚀 What You Can Learn
How 3D graphics work

How voxel engines work

How to generate terrain

How to structure a game project

How OpenGL and Python work together

This project is a great starting point for building:

A Minecraft‑style game

A terrain generator

A 3D engine

A sandbox or simulation game