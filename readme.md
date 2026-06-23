# 🌍 Connor Voxel Engine (Minecraft‑Style)

A small **3D voxel engine** written in Python using **pygame** (window + input),
**PyOpenGL** (rendering), and **Pillow** (procedural textures). It shows how games like
Minecraft build worlds out of cubes, generate terrain from noise, and draw everything on
the GPU.

It is intentionally small and **designed to be read and learned from**, especially by
beginners. Every line of the source is commented to explain what it does and why.

---

## ✨ Features

- Infinite‑style terrain generated with **Perlin noise**
- World split into **16×16 chunks** that load around the player
- Per‑chunk **mesh building with face culling** (hidden faces are skipped)
- Geometry uploaded to the GPU via **VBOs** and drawn with vertex arrays
- **Procedural textures** drawn in code (no image files needed)
- A free‑fly **mouse‑look camera**
- A **safe OpenGL wrapper** that degrades to no‑ops when OpenGL is unavailable

---

## 📦 Requirements

- Python **3.8+** (developed/tested on 3.13)
- Packages: `pygame`, `PyOpenGL`, `Pillow`

Install them with:

```bash
pip install pygame PyOpenGL Pillow
```

> There is no `requirements.txt` yet — install the three packages explicitly.

---

## 🚀 Running

```bash
python main.py
```

A 800×600 window opens with a sky‑blue background and terrain you can fly around.

### 🎮 Controls

| Key | Action |
|-----|--------|
| **W** | Move forward |
| **S** | Move backward |
| **A** | Strafe left |
| **D** | Strafe right |
| **Space** | Fly up |
| **Left Shift** | Fly down |
| **Mouse** | Look around |
| **Esc** | Quit |

---

## 📁 Project Structure

| File | Role | What it does |
|------|------|--------------|
| `main.py` | **Director** | Creates the window, sets up OpenGL, builds the camera + world, runs the 60 FPS game loop, handles input, draws each frame. |
| `camera.py` | **Your eyes** | Stores player position (x, y, z) and look angles (yaw/pitch); turns WASD + mouse into movement; applies the view transform. |
| `world.py` | **World builder** | Perlin noise, `Chunk` (16×16 block data), and `World` (terrain generation, loading chunks near the player, drawing them, spawn‑height lookup). |
| `renderer.py` | **Artist** | Builds a `Mesh` from a chunk (with face culling), uploads it to GPU buffers, picks the right texture per face, and draws it. |
| `textures.py` | **Texture maker** | Draws grass/dirt textures pixel‑by‑pixel with Pillow and uploads them to the GPU; returns a name→texture‑ID map. |
| `glwrap.py` | **Translator** | A thin, safe layer over OpenGL. Provides GL constants and function wrappers, and falls back to harmless no‑ops if PyOpenGL (or a function) is missing. |

---

## 🧠 How It Works

The world is made of **blocks**, grouped into **chunks** (16×16 columns). Here is one frame
of the game loop:

```
main loop (≈60×/second)
  ├─ camera.apply_keyboard / apply_mouse   → update player from input
  ├─ world.update_visible_chunks(camera)   → make sure nearby chunks exist
  │     └─ World.get_chunk
  │           ├─ populate_chunk            → Perlin terrain → chunk.blocks
  │           └─ build_mesh(chunk)         → cull hidden faces, upload VBOs
  ├─ camera.apply_gl_transform(...)        → set the view (where we look from)
  └─ world.draw(camera)                    → skip far chunks, draw the rest
        └─ renderer.draw_mesh(mesh)        → bind textures, glDrawArrays
```

**Dependency direction** (never inverted):

```
main → camera, world      world → renderer, textures      renderer, textures → glwrap
```

`glwrap.py` is the lowest layer and imports nothing from the engine. **All OpenGL access
goes through `glwrap`.**

### Terrain generation

For every column in a chunk, a Perlin sample picks a height:

```python
h = int(self.perlin.noise(wx * 0.08, wz * 0.08) * 12 + 4)  # height in the range 4..16
```

Blocks are then stacked from the ground up: the top block is **grass**, the next few are
**dirt**, and everything deeper is **stone**.

### Face culling

`build_mesh` only emits a cube face when the neighboring block is air:

```python
if get(nx, ny, nz) is None:   # neighbor is empty → this face is visible
    ...                       # add the two triangles for this face
```

Faces buried between solid blocks are never sent to the GPU, which keeps the frame rate up.

---

## 🔧 Tuning Knobs

These values are easy to tweak while learning:

| Where | Value | Effect |
|-------|-------|--------|
| `world.py` → `populate_chunk` | `* 0.08` | Terrain frequency (smaller = smoother hills) |
| `world.py` → `populate_chunk` | `* 12 + 4` | Terrain height range (currently 4..16) |
| `world.py` → `World.__init__` | `view_distance_chunks = 4` | How many chunks load around the player (4 → 9×9) |
| `world.py` → `Perlin(seed=1337)` | `seed` | Change the seed for a different world |
| `camera.py` → `Camera.__init__` | `move_speed`, `fly_speed`, `mouse_sensitivity` | Movement and look feel |

---

## ➕ Extending: Add a New Block Type

1. **`textures.py`** — add a `make_<block>()` generator and register it in
   `load_block_textures()`.
2. **`renderer.py`** — map the block's faces in `get_face_texture()`.
3. **`world.py`** — place the block in `populate_chunk()` via `chunk.set_block(...)`.
4. Run `python main.py` and confirm it looks right.

> Note: `stone` uses texture ID `0` on purpose — that means "no texture, flat color." Not
> every block name maps to a real image.

---

## 📝 Notes

- **Headless‑friendly:** because `glwrap` falls back to no‑ops, pure‑logic code (e.g.
  `Perlin.noise`) can be imported and tested without a GPU/OpenGL context.
- **Mouse grab:** while running, the window captures and hides the mouse for continuous
  looking. Press **Esc** to quit and release it.

---

## 🎓 What You Can Learn

- How 3D graphics and a render loop work
- How voxel engines structure a world out of chunks
- How to generate terrain with Perlin noise
- How meshes, VBOs, and textures reach the GPU
- How Python and OpenGL fit together

A great starting point for building a Minecraft‑style game, a terrain generator, a 3D
engine, or a sandbox/simulation.

---

## 📚 Further Reading

- pygame docs: <https://www.pygame.org/docs/>
- PyOpenGL: <https://pyopengl.sourceforge.net/>
- For agents/contributors: see [`AGENTS.md`](AGENTS.md) and
  [`.github/copilot-instructions.md`](.github/copilot-instructions.md).
