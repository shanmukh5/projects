#!/usr/bin/env python3
import math
import os
import random
import select
import signal
import sys
import termios
import time
import tty
from dataclasses import dataclass
from shutil import get_terminal_size


ESC = "\x1b"


@dataclass(frozen=True)
class Cell:
    ch: str
    fg: tuple | None = None
    bg: tuple | None = None


def fg_color(rgb: tuple[int, int, int]) -> str:
    r, g, b = rgb
    return f"{ESC}[38;2;{r};{g};{b}m"


def bg_color(rgb: tuple[int, int, int]) -> str:
    r, g, b = rgb
    return f"{ESC}[48;2;{r};{g};{b}m"


def reset_colors() -> str:
    return f"{ESC}[0m"


def enter_alt_screen() -> None:
    sys.stdout.write(f"{ESC}[?1049h{ESC}[?25l")
    sys.stdout.flush()


def exit_alt_screen() -> None:
    sys.stdout.write(f"{ESC}[?1049l{ESC}[?25h{reset_colors()}")
    sys.stdout.flush()


def clear_screen() -> None:
    sys.stdout.write(f"{ESC}[2J{ESC}[H")
    sys.stdout.flush()


def nonblocking_read() -> str | None:
    if select.select([sys.stdin], [], [], 0)[0]:
        return sys.stdin.read(1)
    return None


def lerp(a: int, b: int, t: float) -> int:
    return int(a + (b - a) * t)


def gradient_color(y: int, height: int) -> tuple[int, int, int]:
    top = (15, 20, 35)
    bottom = (5, 10, 18)
    t = y / max(1, height - 1)
    return (
        lerp(top[0], bottom[0], t),
        lerp(top[1], bottom[1], t),
        lerp(top[2], bottom[2], t),
    )


def place_sprite(
    buffer: list[list[Cell]],
    sprite: list[str],
    x: int,
    y: int,
    color: tuple[int, int, int],
) -> None:
    height = len(buffer)
    width = len(buffer[0]) if height else 0
    for row_idx, row in enumerate(sprite):
        for col_idx, ch in enumerate(row):
            if ch == " ":
                continue
            px = x + col_idx
            py = y + row_idx
            if 0 <= px < width and 0 <= py < height:
                buffer[py][px] = Cell(ch, fg=color, bg=buffer[py][px].bg)


def build_frame(width: int, height: int, frame: int) -> list[list[Cell]]:
    buffer: list[list[Cell]] = []
    rain_speed = 2
    for y in range(height):
        row: list[Cell] = []
        bg = gradient_color(y, height)
        for x in range(width):
            ch = " "
            fg = None
            bg_cell = bg
            if (x * 7 + y * 3 + frame * rain_speed) % 17 == 0:
                ch = "╲"
                fg = (120, 160, 200)
            row.append(Cell(ch, fg=fg, bg=bg_cell))
        buffer.append(row)

    shimmer = int(30 + 20 * math.sin(frame / 6))
    ground_color = (10, 12, 18)
    for y in range(int(height * 0.7), height):
        for x in range(width):
            buffer[y][x] = Cell(" ", fg=None, bg=ground_color)
            if (x + frame) % 23 == 0 and y == height - 2:
                buffer[y][x] = Cell("·", fg=(80, 90, 120), bg=ground_color)

    left_sprite = [
        "   /|\\     ",
        "  /_|_\\    ",
        "   / \\     ",
        "  /___\\    ",
        "   | |     ",
        "  /  |\\    ",
        " /   | \\   ",
        "/    |  \\  ",
    ]
    right_sprite = [
        "     /|\\   ",
        "    /_|_\\  ",
        "     / \\   ",
        "    /___\\  ",
        "     | |   ",
        "    /|  \\  ",
        "   / |   \\ ",
        "  /  |    \\",
    ]

    mid_y = int(height * 0.45)
    left_x = max(2, int(width * 0.2) - 5)
    right_x = min(width - 12, int(width * 0.7))
    place_sprite(buffer, left_sprite, left_x, mid_y, (200, 200, 210))
    place_sprite(buffer, right_sprite, right_x, mid_y, (210, 180, shimmer))

    slash_y = mid_y + 2
    slash_x = int(width * 0.45)
    if 0 <= slash_y < height:
        for i in range(6):
            px = slash_x + i
            if 0 <= px < width:
                buffer[slash_y][px] = Cell("─", fg=(240, 220, 120), bg=buffer[slash_y][px].bg)

    return buffer


def render_frame(buffer: list[list[Cell]]) -> str:
    lines: list[str] = []
    last_fg = None
    last_bg = None
    for row in buffer:
        line_parts: list[str] = []
        for cell in row:
            if cell.bg != last_bg:
                if cell.bg is None:
                    line_parts.append(reset_colors())
                else:
                    line_parts.append(bg_color(cell.bg))
                last_bg = cell.bg
            if cell.fg != last_fg:
                if cell.fg is None:
                    line_parts.append(f"{ESC}[39m")
                else:
                    line_parts.append(fg_color(cell.fg))
                last_fg = cell.fg
            line_parts.append(cell.ch)
        line_parts.append(reset_colors())
        lines.append("".join(line_parts))
        last_fg = None
        last_bg = None
    return "\n".join(lines)


def main() -> int:
    fps = 30
    duration = 10
    total_frames = fps * duration
    frame = 0
    paused = False

    def handle_resize(_signum, _frame) -> None:
        pass

    signal.signal(signal.SIGWINCH, handle_resize)

    old_settings = termios.tcgetattr(sys.stdin)
    try:
        tty.setcbreak(sys.stdin.fileno())
        enter_alt_screen()
        clear_screen()
        last_time = time.monotonic()
        while True:
            now = time.monotonic()
            elapsed = now - last_time
            if not paused and elapsed < 1 / fps:
                time.sleep(max(0, (1 / fps) - elapsed))
                continue
            last_time = time.monotonic()

            key = nonblocking_read()
            if key:
                if key == "q":
                    break
                if key == " ":
                    paused = not paused
                if key.lower() == "r":
                    frame = 0

            if not paused:
                frame = (frame + 1) % total_frames

            size = get_terminal_size(fallback=(120, 40))
            width = max(40, size.columns)
            height = max(20, size.lines)
            buffer = build_frame(width, height - 1, frame)
            frame_text = render_frame(buffer)
            status = (
                f" Frame {frame + 1:03d}/{total_frames} "
                f"{'(paused)' if paused else ''} "
                " | Space: pause/resume  R: restart  Q: quit "
            )
            status = status[: width - 1].ljust(width - 1)
            sys.stdout.write(f"{ESC}[H{frame_text}\n{reset_colors()}{status}")
            sys.stdout.flush()
    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
        exit_alt_screen()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
