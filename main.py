# main.py
# -------------------------------------------------------------------
# Entry point for the voxel engine. Creates the window, sets up OpenGL,
# initializes the camera + world, and runs the main game loop.
# -------------------------------------------------------------------

import pygame
from pygame.locals import DOUBLEBUF, OPENGL, QUIT

from OpenGL.GL import (
    GL_QUADS,
    glBegin,
    glColor3f,
    glEnable,
    glClearColor,
    glClear,
    glEnd,
    glMatrixMode,
    glLoadIdentity,
    GL_COLOR_BUFFER_BIT,
    GL_DEPTH_BUFFER_BIT,
    GL_DEPTH_TEST,
    GL_LEQUAL,
    GL_PROJECTION,
    GL_MODELVIEW,
    glDepthFunc,
    glVertex3f,
)
from OpenGL.GLU import gluPerspective

from camera import Camera
from world import World


def init_opengl(width: int, height: int) -> None:
    glEnable(GL_DEPTH_TEST)
    glDepthFunc(GL_LEQUAL)

    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(70.0, width / float(height), 0.1, 500.0)

    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    glClearColor(0.5, 0.7, 1.0, 1.0)  # sky blue


def main() -> None:
    pygame.init()
    pygame.display.set_caption("Minecraft Clone")

    width, height = 1960, 1060
    screen = pygame.display.set_mode((width, height), DOUBLEBUF | OPENGL)

    init_opengl(width, height)

    clock = pygame.time.Clock()

    pygame.font.init()
    font = pygame.font.SysFont("Consolas", 20)

    camera = Camera()
    world = World()

    running = True
    while running:
        dt = clock.tick(60) / 1000.0  # seconds

        for event in pygame.event.get():
            if event.type == QUIT:
                running = False

        keys = pygame.key.get_pressed()
        camera.update(keys, dt)

        world.update_visible_chunks(camera)

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        glLoadIdentity()
        camera.apply()
        world.draw(camera)

        from glwrap import glBegin, glEnd, glVertex3f, glColor3f, GL_QUADS

        glColor3f(1.0, 0.0, 0.0)  # bright red
        glBegin(GL_QUADS)
        glVertex3f(-5, 0, -5)
        glVertex3f( 5, 0, -5)
        glVertex3f( 5, 0,  5)
        glVertex3f(-5, 0,  5)
        glEnd()


        fps = clock.get_fps()
        fps_surface = font.render(f"FPS: {int(fps)}", True, (255, 255, 255))  # white text
        screen.blit(fps_surface, (100, 100))

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
print("Game session has exited.")