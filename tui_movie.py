#!/usr/bin/env python3
import math
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


def draw_rect(
    fg_mask: list[list[bool]],
    fg_color: list[list[tuple[int, int, int] | None]],
    x0: int,
    y0: int,
    x1: int,
    y1: int,
    color: tuple[int, int, int],
) -> None:
    height = len(fg_mask)
    width = len(fg_mask[0]) if height else 0
    for y in range(max(0, y0), min(height, y1)):
        for x in range(max(0, x0), min(width, x1)):
            fg_mask[y][x] = True
            fg_color[y][x] = color


def draw_ellipse(
    fg_mask: list[list[bool]],
    fg_color: list[list[tuple[int, int, int] | None]],
    cx: int,
    cy: int,
    rx: int,
    ry: int,
    color: tuple[int, int, int],
) -> None:
    height = len(fg_mask)
    width = len(fg_mask[0]) if height else 0
    for y in range(cy - ry, cy + ry + 1):
        if not (0 <= y < height):
            continue
        dy = (y - cy) / max(1, ry)
        for x in range(cx - rx, cx + rx + 1):
            if not (0 <= x < width):
                continue
            dx = (x - cx) / max(1, rx)
            if dx * dx + dy * dy <= 1.0:
                fg_mask[y][x] = True
                fg_color[y][x] = color


def draw_line(
    fg_mask: list[list[bool]],
    fg_color: list[list[tuple[int, int, int] | None]],
    x0: int,
    y0: int,
    x1: int,
    y1: int,
    color: tuple[int, int, int],
) -> None:
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    x, y = x0, y0
    height = len(fg_mask)
    width = len(fg_mask[0]) if height else 0
    while True:
        if 0 <= x < width and 0 <= y < height:
            fg_mask[y][x] = True
            fg_color[y][x] = color
        if x == x1 and y == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x += sx
        if e2 <= dx:
            err += dx
            y += sy


def draw_samurai(
    fg_mask: list[list[bool]],
    fg_color: list[list[tuple[int, int, int] | None]],
    center_x: int,
    base_y: int,
    scale: int,
    color: tuple[int, int, int],
    highlight: tuple[int, int, int],
    facing: int,
) -> None:
    helmet_rx = 3 * scale
    helmet_ry = 2 * scale
    draw_ellipse(fg_mask, fg_color, center_x, base_y - 12 * scale, helmet_rx, helmet_ry, color)
    draw_rect(
        fg_mask,
        fg_color,
        center_x - 2 * scale,
        base_y - 11 * scale,
        center_x + 2 * scale,
        base_y - 8 * scale,
        highlight,
    )
    draw_rect(
        fg_mask,
        fg_color,
        center_x - 4 * scale,
        base_y - 8 * scale,
        center_x + 4 * scale,
        base_y - 2 * scale,
        color,
    )
    draw_rect(
        fg_mask,
        fg_color,
        center_x - 6 * scale,
        base_y - 2 * scale,
        center_x + 6 * scale,
        base_y + 2 * scale,
        color,
    )
    draw_rect(
        fg_mask,
        fg_color,
        center_x - 5 * scale,
        base_y + 2 * scale,
        center_x - 1 * scale,
        base_y + 8 * scale,
        color,
    )
    draw_rect(
        fg_mask,
        fg_color,
        center_x + 1 * scale,
        base_y + 2 * scale,
        center_x + 5 * scale,
        base_y + 8 * scale,
        color,
    )
    draw_rect(
        fg_mask,
        fg_color,
        center_x - 2 * scale,
        base_y + 8 * scale,
        center_x - 1 * scale,
        base_y + 12 * scale,
        color,
    )
    draw_rect(
        fg_mask,
        fg_color,
        center_x + 1 * scale,
        base_y + 8 * scale,
        center_x + 2 * scale,
        base_y + 12 * scale,
        color,
    )
    sword_x0 = center_x + facing * 7 * scale
    sword_y0 = base_y - 4 * scale
    sword_x1 = sword_x0 + facing * 8 * scale
    sword_y1 = sword_y0 - 6 * scale
    draw_line(fg_mask, fg_color, sword_x0, sword_y0, sword_x1, sword_y1, (240, 220, 140))
    draw_line(fg_mask, fg_color, sword_x0, sword_y0 + 1, sword_x1, sword_y1 + 1, (200, 180, 120))


def build_frame(width: int, height: int, frame: int) -> list[list[Cell]]:
    hi_width = width * 2
    hi_height = height * 4
    bg_color_map: list[list[tuple[int, int, int]]] = []
    fg_mask: list[list[bool]] = []
    fg_color: list[list[tuple[int, int, int] | None]] = []

    rain_speed = 6
    for y in range(hi_height):
        row_bg: list[tuple[int, int, int]] = []
        row_mask: list[bool] = []
        row_fg: list[tuple[int, int, int] | None] = []
        bg = gradient_color(y, hi_height)
        for x in range(hi_width):
            row_bg.append(bg)
            row_mask.append(False)
            row_fg.append(None)
        bg_color_map.append(row_bg)
        fg_mask.append(row_mask)
        fg_color.append(row_fg)

    ground_line = int(hi_height * 0.72)
    for y in range(ground_line, hi_height):
        for x in range(hi_width):
            bg_color_map[y][x] = (8, 10, 14)

    for x in range(hi_width):
        for y in range(0, hi_height, 2):
            if (x * 11 + y * 7 + frame * rain_speed) % 29 == 0:
                for streak in range(3):
                    yy = y + streak
                    if 0 <= yy < hi_height:
                        fg_mask[yy][x] = True
                        fg_color[yy][x] = (120, 170, 220)

    shimmer = int(40 + 30 * math.sin(frame / 8))
    left_center = int(hi_width * 0.3)
    right_center = int(hi_width * 0.7)
    base_y = int(hi_height * 0.62)
    scale = max(1, hi_width // 220)
    draw_samurai(
        fg_mask,
        fg_color,
        left_center,
        base_y,
        scale,
        (200, 205, 215),
        (240, 230, 200),
        1,
    )
    draw_samurai(
        fg_mask,
        fg_color,
        right_center,
        base_y,
        scale,
        (210, 190, shimmer),
        (240, 220, 200),
        -1,
    )

    slash_color = (255, 235, 160)
    draw_line(
        fg_mask,
        fg_color,
        int(hi_width * 0.46),
        int(hi_height * 0.52),
        int(hi_width * 0.54),
        int(hi_height * 0.46),
        slash_color,
    )

    return braille_from_pixels(bg_color_map, fg_mask, fg_color, width, height)


def braille_from_pixels(
    bg_color_map: list[list[tuple[int, int, int]]],
    fg_mask: list[list[bool]],
    fg_color: list[list[tuple[int, int, int] | None]],
    width: int,
    height: int,
) -> list[list[Cell]]:
    buffer: list[list[Cell]] = []
    dot_map = [
        (0, 0, 0),
        (0, 1, 1),
        (0, 2, 2),
        (1, 0, 3),
        (1, 1, 4),
        (1, 2, 5),
        (0, 3, 6),
        (1, 3, 7),
    ]

    for y in range(height):
        row: list[Cell] = []
        for x in range(width):
            bits = 0
            fg_acc = [0, 0, 0]
            fg_count = 0
            bg_acc = [0, 0, 0]
            bg_count = 0
            for dx, dy, bit in dot_map:
                px = x * 2 + dx
                py = y * 4 + dy
                if py >= len(bg_color_map) or px >= len(bg_color_map[0]):
                    continue
                bg = bg_color_map[py][px]
                bg_acc[0] += bg[0]
                bg_acc[1] += bg[1]
                bg_acc[2] += bg[2]
                bg_count += 1
                if fg_mask[py][px]:
                    bits |= 1 << bit
                    color = fg_color[py][px] or bg
                    fg_acc[0] += color[0]
                    fg_acc[1] += color[1]
                    fg_acc[2] += color[2]
                    fg_count += 1

            if bg_count:
                bg_color_val = (bg_acc[0] // bg_count, bg_acc[1] // bg_count, bg_acc[2] // bg_count)
            else:
                bg_color_val = (0, 0, 0)
            if fg_count:
                fg_color_val = (fg_acc[0] // fg_count, fg_acc[1] // fg_count, fg_acc[2] // fg_count)
                ch = chr(0x2800 + bits)
                row.append(Cell(ch, fg=fg_color_val, bg=bg_color_val))
            else:
                row.append(Cell(" ", fg=None, bg=bg_color_val))
        buffer.append(row)
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
