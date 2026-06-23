# main.py
from __future__ import annotations
import sys
import pygame
from pygame.locals import DOUBLEBUF, OPENGL, QUIT, KEYDOWN, K_ESCAPE

from glwrap import (
    glEnable, glClear, glClearColor, glMatrixMode, glLoadIdentity,
    gluPerspective, GL_DEPTH_TEST, GL_COLOR_BUFFER_BIT, GL_DEPTH_BUFFER_BIT,
    GL_MODELVIEW, GL_PROJECTION, glRotatef, glTranslatef
)

from camera import Camera
from world import World


def main():
    pygame.init()

    WIDTH, HEIGHT = 800, 600
    pygame.display.set_mode((WIDTH, HEIGHT), DOUBLEBUF | OPENGL)
    pygame.display.set_caption("Minecraft Prototype")

    pygame.event.set_grab(True)
    pygame.mouse.set_visible(False)

    glEnable(GL_DEPTH_TEST)

    glMatrixMode(GL_PROJECTION)
    gluPerspective(75, WIDTH / HEIGHT, 0.1, 100.0)
    glMatrixMode(GL_MODELVIEW)

    clock = pygame.time.Clock()

# Create world AFTER OpenGL context exists
    world = World()

    camera = Camera()


    ground_y = world.get_height_at(0, 0)
    camera.x = 0.5
    camera.z = 0.5
    camera.y = ground_y + 3.0

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    running = False

        keys = pygame.key.get_pressed()
        camera.apply_keyboard(keys)

        dx, dy = pygame.mouse.get_rel()
        camera.apply_mouse(dx, dy)

        world.update_visible_chunks(camera)

        glLoadIdentity()
        camera.apply_gl_transform(glRotatef, glTranslatef)

        glClearColor(0.6, 0.8, 1.0, 1)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        world.draw(camera)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
