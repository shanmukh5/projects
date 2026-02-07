# Terminal Samurai Duel (TUI demo)

This is a terminal animation demo that uses **braille-based subcell rendering** to show higher-detail samurai silhouettes fighting in the rain. It aims for clarity and motion readability rather than photoreal detail, and includes **pause**, **restart**, and **quit** controls.

## Requirements
- Python 3.10+
- A truecolor-capable terminal (iTerm2, Ghostty, etc.) with good Unicode braille support

## Run
```bash
python3 tui_movie.py
```

## Controls
- **Space**: pause/resume
- **R**: restart from frame 1
- **Q**: quit

## Notes
- The animation is designed for full-screen terminals. Larger window sizes increase clarity and effective detail.
- It renders at ~30 FPS by default and loops at 10 seconds.
