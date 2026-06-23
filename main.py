# main.py
# -------------------------------------------------------------------
# The "director" of the whole program. It creates the window, sets up
# OpenGL, builds the camera and world, then runs the game loop: read
# input, update the world, draw everything, repeat ~60 times a second.
# -------------------------------------------------------------------
from __future__ import annotations              # Enable modern type-hint syntax on older Python versions
import sys                                       # Used to exit the program cleanly at the end
import pygame                                    # Window creation, input handling, and the main clock
from pygame.locals import DOUBLEBUF, OPENGL, QUIT, KEYDOWN, K_ESCAPE  # Display flags + event/key constants

from glwrap import (                             # Pull GL helpers/constants from our safe wrapper layer
    glEnable, glClear, glClearColor, glMatrixMode, glLoadIdentity,  # Setup, clearing, and matrix functions
    gluPerspective, GL_DEPTH_TEST, GL_COLOR_BUFFER_BIT, GL_DEPTH_BUFFER_BIT,  # Projection + capability/clear flags
    GL_MODELVIEW, GL_PROJECTION, glRotatef, glTranslatef  # Matrix modes + transforms used by the camera
)

from camera import Camera                        # The fly camera that turns input into a view
from world import World                          # The world that generates terrain and draws chunks


def main():                                      # Program entry point: set everything up and run the loop
    pygame.init()                                # Start up all the pygame subsystems

    WIDTH, HEIGHT = 800, 600                     # Window size in pixels
    pygame.display.set_mode((WIDTH, HEIGHT), DOUBLEBUF | OPENGL)  # Open an OpenGL window with double buffering
    pygame.display.set_caption("Minecraft Prototype")  # Set the window title bar text

    pygame.event.set_grab(True)                  # Lock the mouse to the window (for continuous looking)
    pygame.mouse.set_visible(False)              # Hide the cursor while playing

    glEnable(GL_DEPTH_TEST)                       # Enable depth testing so nearer blocks hide farther ones

    glMatrixMode(GL_PROJECTION)                  # Switch to the projection matrix to set up the lens
    gluPerspective(75, WIDTH / HEIGHT, 0.1, 100.0)  # 75° field of view, screen aspect, near 0.1, far 100
    glMatrixMode(GL_MODELVIEW)                   # Switch back to the model-view matrix for camera/world transforms

    clock = pygame.time.Clock()                  # Clock used to cap the frame rate

    # Create the world AFTER the OpenGL context exists (World() uploads textures/VBOs to the GPU)
    world = World()                              # Create the world (also builds textures + renderer)

    camera = Camera()                            # Create the player's camera

    ground_y = world.get_height_at(0, 0)         # Find the terrain surface height at the origin
    camera.x = 0.5                               # Place the camera near the center of the origin block (X)
    camera.z = 0.5                               # Place the camera near the center of the origin block (Z)
    camera.y = ground_y + 3.0                    # Start 3 units above the ground so we don't spawn inside terrain

    running = True                               # Loop control flag; set False to quit
    while running:                               # The main game loop, one pass per frame
        for event in pygame.event.get():         # Process every queued input/window event
            if event.type == QUIT:               # Window close button pressed...
                running = False                  # ...request loop exit
            elif event.type == KEYDOWN:          # A key was pressed down...
                if event.key == K_ESCAPE:        # ...and it was Escape...
                    running = False              # ...so request loop exit

        keys = pygame.key.get_pressed()          # Snapshot of which keys are currently held
        camera.apply_keyboard(keys)              # Move the camera based on held movement keys

        dx, dy = pygame.mouse.get_rel()          # Mouse movement since the last frame (delta x, delta y)
        camera.apply_mouse(dx, dy)               # Turn the camera based on that mouse movement

        world.update_visible_chunks(camera)      # Make sure chunks around the camera are generated/loaded

        glLoadIdentity()                         # Reset the model-view matrix for this frame
        camera.apply_gl_transform(glRotatef, glTranslatef)  # Apply the camera's rotation + position

        glClearColor(0.6, 0.8, 1.0, 1)           # Set the sky-blue background color
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)  # Clear both the color and depth buffers

        world.draw(camera)                       # Draw all visible chunks

        pygame.display.flip()                    # Swap the back buffer to the screen (show this frame)
        clock.tick(60)                           # Wait as needed to cap the loop at 60 frames per second

    pygame.quit()                                # Shut down pygame subsystems
    sys.exit()                                   # Exit the process


if __name__ == "__main__":                       # Only run main() when this file is executed directly...
    main()                                       # ...not when it is imported as a module
