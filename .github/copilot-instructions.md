# Duck Hunt Project Guidelines

## Scope

- Keep the current web version stable while planning the Python migration.
- Prioritize migration planning and architecture over large rewrites in one step.
- Do not implement computer vision yet. Keep it as a later phase after gameplay parity.

## Code Style

- JavaScript side uses singleton-style modules: `Config`, `Storage`, `Menu`, `Game`.
- Preserve existing DOM IDs and class names when editing UI flows.
- Keep changes small and focused; avoid broad refactors unless requested.

## Architecture

- Critical script load order in `index.html`: `config.js` -> `storage.js` -> `menu.js` -> `game.js` -> `main.js`.
- Screen visibility is controlled with the `.hidden` class.
- Main responsibilities:
  - `src/js/config.js`: gameplay constants, maps, random creature/map helpers.
  - `src/js/storage.js`: rankings persistence in localStorage (`duckHuntRankings`).
  - `src/js/menu.js`: menu/rankings/game-over/player-name flows.
  - `src/js/game.js`: game loop, entities, score, HUD updates.
  - `src/js/main.js`: intro flow and global audio bootstrap.

## Build and Test

- No build system or package manager scripts; this is vanilla HTML/CSS/JS.
- Run by opening `index.html` in a browser.
- Validate changes with manual gameplay checks (menu flow, score updates, round progression, rankings save/load, audio behavior after user interaction).

## Migration Strategy (Python)

- Use gradual migration with parity checkpoints.
- Target order:
  1. Define and validate an independent RNG module contract.
  2. Port config/storage foundations.
  3. Port menu/UI flow.
  4. Port game loop and entities.
  5. Add optional computer vision later.

## RNG Module Requirements

- Keep RNG logic independent from rendering/UI.
- Start with two explicit seeds (`seed_a`, `seed_b`) and deterministic output.
- Add a third derived seed (`seed_c`) generated from deterministic mixing of the first two seeds plus controlled run metadata.
- Expose a compact API that both JS and Python can mirror:
  - `set_seeds(seed_a, seed_b)`
  - `derive_seed_c(context)`
  - `next_u32()`
  - `next_float()`
  - `randint(min, max)`
- Before porting gameplay, create sequence parity tests between JS and Python RNG implementations.

## Pitfalls

- Browser autoplay restrictions can block audio until user interaction.
- Timing logic and requestAnimationFrame loops in `game.js` are sensitive to ordering/state.
- Asset paths are hardcoded in multiple places; update carefully.

## References

- Mechanics and project overview: `README.md`
- User-facing gameplay details: `GUIA_RAPIDA.md`
- Flow/state overview: `ESTRUCTURA_PROYECTO.txt`
