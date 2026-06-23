# Connor Voxel Engine — AI Agent Instructions

Portable, tool-agnostic agent guidance lives in [`AGENTS.md`](../AGENTS.md). Foundational
principles live in [`.specify/memory/constitution.md`](../.specify/memory/constitution.md).
This file adds Copilot-specific, code-level guidance for **this** repository only. Read it
before editing any `.py` file.

> **Audience & tone:** This is a teaching codebase. Write code a motivated beginner can read.
> Favor clear names and explanatory comments over clever tricks. Clarity beats micro-optimization
> (see Constitution Principle II — Educational Clarity).

<!-- SPECKIT START -->
For additional context about technologies to be used, project structure,
shell commands, and other important information, read the current plan
<!-- SPECKIT END -->

---

## Project Overview

Connor is a small **Minecraft-style voxel engine** written in Python using **pygame**
(windowing/input) and **PyOpenGL** (rendering), with **Pillow** for procedural textures. It
generates infinite-ish terrain from Perlin noise, groups blocks into 16×16 chunks, builds
per-chunk meshes, uploads them to the GPU via VBOs, and lets you fly around with a
mouse-look camera. The goal is **learning**, not shipping a game — every module is intentionally
small and self-contained.

- **Language:** Python 3.8+
- **Runtime deps:** `pygame`, `PyOpenGL`, `Pillow` (no `requirements.txt` yet — install explicitly)
- **Entry point:** `python main.py`
- **Repo:** `jozefaz/connor-code`

---

## Core Architecture

Each module has one job. Respect these boundaries — do **not** merge responsibilities or add
cross-module shortcuts (Constitution Principle I — Modular Architecture).

| Module | Responsibility | Key symbols |
|--------|----------------|-------------|
| `main.py` | Game loop "director": window, GL setup, input dispatch, per-frame draw | `main()` |
| `camera.py` | Player position + mouse-look + WASD/space/shift movement | `Camera` |
| `world.py` | Terrain gen (Perlin), chunk lifecycle, visible-chunk management | `World`, `Chunk`, `Perlin` |
| `renderer.py` | Mesh building (face culling), VBO upload, textured draw | `Renderer`, `Mesh`, `build_mesh` |
| `textures.py` | Procedural PIL block textures → GPU texture IDs | `load_block_textures` |
| `glwrap.py` | Safe OpenGL abstraction layer (constants + thin wrappers) | `gl*` functions, `GL_*` constants |

### Data Flow (one frame)

```
main loop
  → camera.apply_keyboard / apply_mouse        # update player from input
  → world.update_visible_chunks(camera)        # ensure chunks around camera exist
      → World.get_chunk → populate_chunk        # Perlin terrain into chunk.blocks
      → renderer.build_mesh(chunk)              # cull hidden faces, upload VBOs
  → camera.apply_gl_transform(...)             # set the view matrix
  → world.draw(camera)                         # cull distant chunks, draw meshes
      → renderer.draw_mesh(mesh)               # bind textures, glDrawArrays
```

### Dependency direction (never invert)

`main` → `camera`, `world`  ·  `world` → `renderer`, `textures`  ·  `renderer`, `textures` → `glwrap`

`glwrap.py` is the lowest layer and imports nothing from the engine. **All OpenGL access goes
through `glwrap`** — never `import OpenGL.GL` directly in `world/renderer/textures/main`.

---

## Critical Patterns

### 1. OpenGL goes through `glwrap` (and degrades gracefully)

`glwrap.py` loads `OpenGL.GL`/`OpenGL.GLU` with `importlib` and falls back to a `_noop` if a
function is missing, and to hard-coded enum values via `getattr(_GL, "NAME", 0x....)` for
constants. This lets logic-only code run/import in headless environments without a GL context.

- When you need a new GL call or constant, **add a wrapper/constant to `glwrap.py`** with the
  correct fallback value — don't bypass the layer.
- Texture/buffer generators (`glGenTextures`, `glGenBuffers`) normalize list/scalar returns to a
  single `int`. Preserve that behavior if you touch them.

### 2. Chunk + mesh lifecycle

- A `Chunk` stores blocks as a dict `{(x, y, z): "grass"|"dirt"|"stone"}` in **chunk-local**
  coordinates; `Chunk.SIZE == 16`.
- `World.get_chunk` is the single creation path: it populates terrain **then** builds the mesh
  **once**, then caches in `World.chunks[(cx, cz)]`. Don't generate terrain or meshes elsewhere.
- `build_mesh` does **face culling** — a face is emitted only if the neighboring block is absent
  (`get(nx,ny,nz) is None`). Keep this; emitting hidden faces tanks performance.
- Meshes group geometry by texture into `mesh.faces = [(texture_name, start, count), ...]` so the
  renderer can minimize texture binds. Preserve this batching.

### 3. Block → face → texture mapping

`renderer.get_face_texture` maps a block+face to a texture name (`grass` → `grass_top` /
`grass_side` / `dirt` for top/side/bottom). `textures.load_block_textures` returns the
name→GL-id map. To add a block type you must touch **both**: generate/return its texture(s) in
`textures.py` and map its faces in `get_face_texture`.

### 4. Inline comments explain *why* (Constitution II)

Comment non-obvious intent, not syntax. Good:

```python
h = int(self.perlin.noise(wx * 0.08, wz * 0.08) * 12 + 4)  # 0.08 = terrain frequency; *12+4 = height range 4..16
if get(nx, ny, nz) is None:                                 # only draw faces exposed to air (face culling)
```

Every public function keeps a docstring describing purpose, params, and return.

---

## Essential Workflows

### Run the engine

```powershell
pip install pygame PyOpenGL Pillow      # one-time; no requirements.txt yet
python main.py                          # opens an 800x600 window; ESC to quit
```

Controls: **WASD** move, **Space/Shift** up/down, **Mouse** look, **ESC** quit.

### Add a new block type (worked example)

1. `textures.py`: add a `make_<block>()` PIL generator and register it in `load_block_textures()`.
2. `renderer.py`: extend `get_face_texture()` to map the block's faces to texture name(s).
3. `world.py`: place the block in `populate_chunk()` (set it via `chunk.set_block(...)`).
4. Run `python main.py` and visually confirm; add/adjust a test if logic changed.

### Add a feature (general)

Follow the phased approach in the Constitution: design → implement core in the owning module →
test the module in isolation → integrate into the loop. Keep each change reviewable.

---

## Testing

There is **no test suite yet**. When you add logic, add `pytest` tests under a `tests/` directory.

- Prefer testing **pure logic** that doesn't need a GL context: `Perlin.noise` determinism for a
  fixed seed, `World.get_height_at`, face-culling decisions in `build_mesh` (assert face count /
  `mesh.faces` entries), `get_face_texture` mappings, camera math (`apply_keyboard`/`apply_mouse`).
- `glwrap`'s no-op fallback means much of this runs headless — exploit that for fast unit tests.
- Run with `python -m pytest`. Validate `python -m compileall -q .` before committing.

---

## Common Pitfalls (this codebase)

- **Bypassing `glwrap`** by importing `OpenGL.GL` directly — breaks headless testing and the
  safety layer. Always route through `glwrap`.
- **Emitting culled faces** — if you "simplify" `build_mesh` and drop the `is None` neighbor
  check, frame rate collapses. Keep face culling.
- **Regenerating chunks/meshes** outside `World.get_chunk` — causes duplicate GPU uploads and
  inconsistent caches.
- **`stone` has texture id `0`** (solid color, no image) on purpose — don't assume every block
  name maps to a real texture.
- **Coordinate spaces:** terrain height uses **world** coords (`wx, wz`) while a chunk's blocks
  are stored in **local** 0..15 coords. Keep these straight when editing `world.py`.
- **Mouse grab is on** (`set_grab(True)`, cursor hidden); the window captures the mouse while running.

---

## Project-Specific Conventions

- Every module starts with `from __future__ import annotations` and uses **type hints**. Keep both.
- Keep modules small and single-purpose; if a function grows complex, split it rather than nesting.
- Magic numbers that affect gameplay/terrain (frequencies, height ranges, view distance, speeds)
  should be named or commented so learners can tweak them.
- Cross-platform: code MUST run on Windows/macOS/Linux. Avoid OS-specific paths/APIs.

---

## NEVER Do These

- Import `OpenGL.*` directly in engine modules — use `glwrap`.
- Replace clear code with obscure one-liners "for speed" without a measured reason (Constitution II).
- Bake terrain generation or mesh building into the render path or `main` loop.
- Commit code that fails `python -m compileall -q .` or that you haven't run at least once.
- Add heavy dependencies/frameworks without justification (Constitution — keep deps minimal).

---

## Key Files & References

- Source: `main.py`, `camera.py`, `world.py`, `renderer.py`, `textures.py`, `glwrap.py`
- Docs: `readme.md` (architecture + controls), `AGENTS.md` (agent protocol),
  `.specify/memory/constitution.md` (principles & governance)
- PyOpenGL: https://pyopengl.sourceforge.net/ · pygame: https://www.pygame.org/docs/
