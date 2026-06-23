# AGENTS.md — Connor Voxel Engine

Operating guide for AI coding agents (and humans) working in this repository. It is
tool-agnostic; GitHub Copilot also reads [`.github/copilot-instructions.md`](.github/copilot-instructions.md),
which carries the deeper, code-level detail. Foundational rules live in the
[Constitution](.specify/memory/constitution.md).

**Read order for any task:** this file → `.github/copilot-instructions.md` → the module you're editing.

---

## What this project is

A small, teaching-focused **Minecraft-style voxel engine** in Python (pygame + PyOpenGL +
Pillow). It builds terrain from Perlin noise, batches blocks into 16×16 chunks, meshes them,
and renders with a fly-around camera. **Optimize for learnability**, not for shipping a AAA game.

```
main.py     game loop / window / input        camera.py   player position + mouse-look
world.py    terrain + chunks                   renderer.py meshing + VBOs + draw
textures.py procedural block textures          glwrap.py   safe OpenGL wrapper (lowest layer)
```

Dependency direction (never invert): `main → camera, world → renderer, textures → glwrap`.

---

## Quick start

```powershell
pip install pygame PyOpenGL Pillow   # no requirements.txt yet — install explicitly
python main.py                       # 800x600 window; WASD move, Space/Shift up/down, Mouse look, ESC quit
python -m compileall -q .            # cheap syntax gate; run before every commit
python -m pytest                     # run tests once a tests/ dir exists
```

---

## Golden rules (condensed from the Constitution)

1. **Modular** — one responsibility per module; communicate through clean interfaces, no shortcuts.
2. **Clear over clever** — readable code + "why" comments + docstrings beat micro-optimizations.
3. **Incremental** — design → implement core → test in isolation → integrate; keep changes reviewable.
4. **Performance-aware** — keep face culling and chunk/visibility limits; target 60 FPS.
5. **Tested** — add `pytest` tests for new logic; everything must pass before merge.

When two rules collide, prioritize: **Clarity → Modularity → Quality → Performance → Incrementalism**.

---

## House conventions

- Start modules with `from __future__ import annotations`; use **type hints** everywhere.
- **All OpenGL access goes through `glwrap.py`** — never `import OpenGL.*` in engine modules.
- Create chunks/meshes **only** via `World.get_chunk` (it populates terrain, then builds the mesh once).
- In `renderer.build_mesh`, **keep face culling** (emit a face only when its neighbor is air).
- Name or comment gameplay magic numbers (noise frequency, height range, view distance, speeds).
- Cross-platform only (Windows/macOS/Linux); no OS-specific paths or APIs.

See `.github/copilot-instructions.md` → *Common Pitfalls* for codebase-specific gotchas
(coordinate spaces, `stone` texture id `0`, mouse grab, etc.).

---

## Agent workflow

1. **Understand first.** Read this file, the Copilot instructions, and the target module(s)
   before editing. State any assumptions you make.
2. **Scope tightly.** Touch only the module that owns the responsibility. Don't refactor
   unrelated code or invert the dependency direction.
3. **Implement with comments.** Add docstrings and "why" comments as you go (Rule 2).
4. **Verify before claiming done:**
   - `python -m compileall -q .` passes.
   - New/changed **logic** has a `pytest` test (prefer headless-safe tests — `glwrap`'s no-op
     fallback lets most logic run without a GL context).
   - If rendering/input changed, run `python main.py` and confirm behavior visually.
5. **Document.** Update `readme.md` if controls/architecture change; update these instruction
   files if conventions change.
6. **Commit cleanly.** Use `feat:`, `fix:`, `chore:`, or `docs:` prefixes; keep commits focused
   and messages descriptive. Open a PR that explains *what* and *why*, plus any performance impact.

### Definition of done

Compiles, runs (or tests pass for logic-only changes), respects the golden rules and dependency
direction, and is documented. Don't mark a task complete until you've verified it.

---

## Adding a new block type (canonical example)

1. `textures.py` — add `make_<block>()` and register it in `load_block_textures()`.
2. `renderer.py` — map its faces in `get_face_texture()`.
3. `world.py` — place it in `populate_chunk()` via `chunk.set_block(...)`.
4. Run `python main.py` to confirm; add a test if you changed selection logic.

---

## References

- `.github/copilot-instructions.md` — detailed, code-level agent guidance
- `.specify/memory/constitution.md` — principles, quality gates, governance
- `readme.md` — architecture overview and controls
- PyOpenGL docs: https://pyopengl.sourceforge.net/ · pygame docs: https://www.pygame.org/docs/
