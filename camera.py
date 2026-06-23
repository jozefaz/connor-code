# camera.py
# -------------------------------------------------------------------
# A simple "fly" camera. It stores where the player is (x, y, z) and
# which way they are looking (yaw = left/right, pitch = up/down), and
# turns keyboard + mouse input into movement. Think of it as the
# player's eyes inside the world.
# -------------------------------------------------------------------
from __future__ import annotations                       # Enable modern type-hint syntax on older Python versions
import math                                              # Trig (sin/cos/radians) for direction math
from pygame.locals import K_w, K_s, K_a, K_d, K_SPACE, K_LSHIFT  # Key codes for movement (WASD + space + shift)

class Camera:                                            # Holds the player's position, orientation, and movement speeds
    def __init__(self):                                  # Set up a brand-new camera with sensible defaults
        self.x = 0.0                                     # World X position (east/west)
        self.y = 2.0                                     # World Y position (height); 2.0 starts slightly above ground
        self.z = 6.0                                     # World Z position (north/south)

        self.yaw = 0.0                                   # Left/right look angle in degrees (rotation around Y axis)
        self.pitch = 0.0                                 # Up/down look angle in degrees (rotation around X axis)

        self.move_speed = 0.15                           # Units moved per frame when walking with WASD
        self.mouse_sensitivity = 0.15                    # How fast the view turns per pixel of mouse movement
        self.fly_speed = 0.15                            # Units moved per frame when flying up/down

    def apply_mouse(self, dx: float, dy: float) -> None:  # Turn the view based on mouse movement since last frame
        self.yaw += dx * self.mouse_sensitivity          # Horizontal mouse motion changes yaw (turn left/right)
        self.pitch -= dy * self.mouse_sensitivity        # Vertical mouse motion changes pitch (minus = natural look)
        self.pitch = max(-89, min(89, self.pitch))       # Clamp pitch to ±89° so the view never flips upside down

    def apply_keyboard(self, keys) -> None:              # Move the player based on which keys are currently held
        rad = math.radians(self.yaw)                     # Convert yaw to radians for trig functions

        fx = math.sin(rad)                               # Forward vector X component (where "forward" points)
        fz = -math.cos(rad)                              # Forward vector Z component (negative: -Z is "into" the scene)

        rx = math.cos(rad)                               # Right vector X component (90° clockwise from forward)
        rz = math.sin(rad)                               # Right vector Z component

        if keys[K_w]:                                    # W: walk forward
            self.x += fx * self.move_speed               # Step along forward X
            self.z += fz * self.move_speed               # Step along forward Z
        if keys[K_s]:                                    # S: walk backward
            self.x -= fx * self.move_speed               # Step opposite forward X
            self.z -= fz * self.move_speed               # Step opposite forward Z
        if keys[K_a]:                                    # A: strafe left
            self.x -= rx * self.move_speed               # Step opposite right X (i.e. to the left)
            self.z -= rz * self.move_speed               # Step opposite right Z
        if keys[K_d]:                                    # D: strafe right
            self.x += rx * self.move_speed               # Step along right X
            self.z += rz * self.move_speed               # Step along right Z

        if keys[K_SPACE]:                                # Space: fly straight up
            self.y += self.fly_speed                     # Increase height
        if keys[K_LSHIFT]:                               # Left Shift: fly straight down
            self.y -= self.fly_speed                     # Decrease height

    def apply_gl_transform(self, glRotatef, glTranslatef) -> None:  # Apply the camera as an OpenGL view transform
        glRotatef(self.pitch, 1, 0, 0)                   # Tilt the world opposite our pitch (rotate around X axis)
        glRotatef(self.yaw, 0, 1, 0)                     # Turn the world opposite our yaw (rotate around Y axis)
        glTranslatef(-self.x, -self.y, -self.z)          # Shift the world opposite our position (camera stays at origin)
