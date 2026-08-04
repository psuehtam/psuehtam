#!/usr/bin/env python3
"""Generate the animated code editor used by the GitHub profile README."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Iterable

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "assets" / "coding-terminal.gif"

WIDTH = 1000
HEIGHT = 520
TITLE_HEIGHT = 46
SIDEBAR_WIDTH = 230
STATUS_HEIGHT = 28
EDITOR_X = SIDEBAR_WIDTH + 58
EDITOR_Y = TITLE_HEIGHT + 64
LINE_HEIGHT = 31
TYPE_STEP = 5

COLORS = {
    "window": "#0D1117",
    "sidebar": "#161B22",
    "titlebar": "#010409",
    "border": "#30363D",
    "text": "#C9D1D9",
    "muted": "#7D8590",
    "blue": "#58A6FF",
    "green": "#3FB950",
    "yellow": "#D29922",
    "orange": "#FFA657",
    "red": "#FF7B72",
    "purple": "#D2A8FF",
    "cyan": "#79C0FF",
    "selection": "#1F6FEB33",
    "status": "#1F6FEB",
    "white": "#F0F6FC",
}


@dataclass(frozen=True)
class Scene:
    filename: str
    language: str
    code: str
    syntax: str


SCENES = [
    Scene(
        filename="Developer.java",
        language="Java 21 • Spring Boot",
        syntax="java",
        code="""package dev.matheus.profile;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.*;

@SpringBootApplication
public class Developer {
    public static void main(String[] args) {
        SpringApplication.run(Developer.class, args);
    }
}
""",
    ),
    Scene(
        filename="Profile.tsx",
        language="TypeScript • React",
        syntax="typescript",
        code="""type Developer = {
  name: string;
  stack: string[];
  building: string;
};

const matheus: Developer = {
  name: "Matheus",
  stack: ["Java", "Spring Boot", "React", "TypeScript"],
  building: "BarberBook",
};
""",
    ),
    Scene(
        filename="compose.yaml",
        language="Docker • PostgreSQL",
        syntax="yaml",
        code="""services:
  api:
    build: ./backend
    ports:
      - "8080:8080"
    depends_on:
      database:
        condition: service_healthy

  database:
    image: postgres:17-alpine
    restart: unless-stopped
""",
    ),
]

FILES = [scene.filename for scene in SCENES] + ["README.md"]


def find_font(size: int, *, bold: bool = False) -> ImageFont.FreeTypeFont:
    filename = "DejaVuSansMono-Bold.ttf" if bold else "DejaVuSansMono.ttf"
    candidates = [
        Path("/usr/share/fonts/truetype/dejavu") / filename,
        Path("/usr/share/fonts/dejavu") / filename,
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size)
    raise FileNotFoundError(f"Fonte monoespaçada não encontrada: {filename}")


FONT = find_font(18)
FONT_SMALL = find_font(14)
FONT_SMALL_BOLD = find_font(14, bold=True)
FONT_TITLE = find_font(15, bold=True)


def colorized_characters(scene: Scene) -> list[tuple[str, str]]:
    characters: list[tuple[str, str]] = []

    for line in scene.code.splitlines(keepends=True):
        colors = [COLORS["text"]] * len(line)

        def paint(pattern: str, color: str, group: int = 0) -> None:
            for match in re.finditer(pattern, line):
                start, end = match.span(group)
                for index in range(start, end):
                    colors[index] = color

        if scene.syntax == "java":
            paint(
                r"\b(package|import|public|private|protected|class|static|void|new|return|final|extends|implements)\b",
                COLORS["red"],
            )
            paint(r"\b[A-Z][A-Za-z0-9_]*\b", COLORS["orange"])
            paint(r"@[A-Za-z_][A-Za-z0-9_.]*", COLORS["yellow"])
            paint(r"\b\d+\b", COLORS["cyan"])
        elif scene.syntax == "typescript":
            paint(
                r"\b(type|const|let|interface|string|number|boolean|export|import|from|return)\b",
                COLORS["red"],
            )
            paint(r"\b[A-Z][A-Za-z0-9_]*\b", COLORS["orange"])
            paint(r"\b(true|false|null|undefined)\b", COLORS["purple"])
            paint(r"\b\d+\b", COLORS["cyan"])
        elif scene.syntax == "yaml":
            paint(r"^(\s*)([A-Za-z_][A-Za-z0-9_-]*)(:)", COLORS["blue"], group=2)
            paint(r"\b(true|false|null)\b", COLORS["purple"])
            paint(r"\b\d+\b", COLORS["cyan"])

        # Strings and comments take precedence over language keywords.
        paint(r"\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*'", COLORS["green"])
        if scene.syntax in {"java", "typescript"}:
            paint(r"//.*", COLORS["muted"])
        else:
            paint(r"#.*", COLORS["muted"])

        characters.extend(zip(line, colors))
    return characters


def draw_window_chrome(draw: ImageDraw.ImageDraw) -> None:
    draw.rounded_rectangle(
        (1, 1, WIDTH - 2, HEIGHT - 2),
        radius=16,
        fill=COLORS["window"],
        outline=COLORS["border"],
        width=2,
    )
    draw.rounded_rectangle(
        (2, 2, WIDTH - 3, TITLE_HEIGHT + 13),
        radius=14,
        fill=COLORS["titlebar"],
    )
    draw.rectangle((2, TITLE_HEIGHT, WIDTH - 3, TITLE_HEIGHT + 14), fill=COLORS["titlebar"])

    for x, color in [(23, "#FF5F56"), (49, "#FFBD2E"), (75, "#27C93F")]:
        draw.ellipse((x - 6, 17, x + 6, 29), fill=color)

    title = "matheus.dev — Visual Studio Code"
    title_width = draw.textlength(title, font=FONT_SMALL)
    draw.text(((WIDTH - title_width) / 2, 15), title, font=FONT_SMALL, fill=COLORS["muted"])


def draw_sidebar(draw: ImageDraw.ImageDraw, active_file: str) -> None:
    draw.rectangle(
        (2, TITLE_HEIGHT, SIDEBAR_WIDTH, HEIGHT - STATUS_HEIGHT - 2),
        fill=COLORS["sidebar"],
    )
    draw.line(
        (SIDEBAR_WIDTH, TITLE_HEIGHT, SIDEBAR_WIDTH, HEIGHT - STATUS_HEIGHT),
        fill=COLORS["border"],
        width=1,
    )
    draw.text((19, TITLE_HEIGHT + 18), "EXPLORER", font=FONT_SMALL, fill=COLORS["muted"])
    draw.text((19, TITLE_HEIGHT + 51), "⌄  MATHEUS.DEV", font=FONT_SMALL_BOLD, fill=COLORS["text"])

    file_colors = {
        ".java": COLORS["orange"],
        ".tsx": COLORS["blue"],
        ".yaml": COLORS["cyan"],
        ".md": COLORS["purple"],
    }
    y = TITLE_HEIGHT + 86
    for filename in FILES:
        active = filename == active_file
        if active:
            draw.rectangle((2, y - 5, SIDEBAR_WIDTH, y + 23), fill="#21262D")
            draw.rectangle((2, y - 5, 5, y + 23), fill=COLORS["blue"])
        suffix = Path(filename).suffix
        draw.text((29, y), "◆", font=FONT_SMALL, fill=file_colors.get(suffix, COLORS["muted"]))
        draw.text(
            (51, y),
            filename,
            font=FONT_SMALL,
            fill=COLORS["white"] if active else COLORS["text"],
        )
        y += 35


def draw_editor_header(draw: ImageDraw.ImageDraw, scene: Scene) -> None:
    draw.rectangle(
        (SIDEBAR_WIDTH + 1, TITLE_HEIGHT, WIDTH - 2, TITLE_HEIGHT + 38),
        fill="#0D1117",
    )
    draw.rectangle(
        (SIDEBAR_WIDTH + 1, TITLE_HEIGHT, SIDEBAR_WIDTH + 188, TITLE_HEIGHT + 38),
        fill="#161B22",
    )
    draw.line(
        (SIDEBAR_WIDTH + 1, TITLE_HEIGHT + 38, WIDTH - 2, TITLE_HEIGHT + 38),
        fill=COLORS["border"],
    )
    draw.text(
        (SIDEBAR_WIDTH + 18, TITLE_HEIGHT + 11),
        scene.filename,
        font=FONT_SMALL,
        fill=COLORS["text"],
    )
    draw.text(
        (EDITOR_X - 2, TITLE_HEIGHT + 47),
        f"matheus.dev  ›  {scene.filename}",
        font=FONT_SMALL,
        fill=COLORS["muted"],
    )


def draw_statusbar(draw: ImageDraw.ImageDraw, scene: Scene, line: int, column: int) -> None:
    y = HEIGHT - STATUS_HEIGHT - 1
    draw.rectangle((2, y, WIDTH - 3, HEIGHT - 3), fill=COLORS["status"])
    draw.text((17, y + 6), "git: main*", font=FONT_SMALL, fill=COLORS["white"])
    draw.text((121, y + 6), "OK 0   ERR 0", font=FONT_SMALL, fill=COLORS["white"])
    right = f"Ln {line}, Col {column}    UTF-8    {scene.language}"
    width = draw.textlength(right, font=FONT_SMALL)
    draw.text((WIDTH - width - 18, y + 6), right, font=FONT_SMALL, fill=COLORS["white"])


def draw_code(
    draw: ImageDraw.ImageDraw,
    characters: list[tuple[str, str]],
    visible_count: int,
    cursor_visible: bool,
) -> tuple[int, int]:
    x = EDITOR_X
    y = EDITOR_Y
    line = 1
    column = 1
    number_x = SIDEBAR_WIDTH + 19

    draw.text((number_x, y), str(line).rjust(2), font=FONT_SMALL, fill=COLORS["muted"])
    for character, color in characters[:visible_count]:
        if character == "\n":
            line += 1
            column = 1
            x = EDITOR_X
            y += LINE_HEIGHT
            draw.text((number_x, y), str(line).rjust(2), font=FONT_SMALL, fill=COLORS["muted"])
            continue
        draw.text((x, y - 2), character, font=FONT, fill=color)
        x += draw.textlength(character, font=FONT)
        column += 1

    if cursor_visible:
        draw.rectangle((x + 1, y + 1, x + 3, y + 22), fill=COLORS["blue"])
    return line, column


def render_frame(scene: Scene, visible_count: int, cursor_visible: bool = True) -> Image.Image:
    image = Image.new("RGB", (WIDTH, HEIGHT), COLORS["window"])
    draw = ImageDraw.Draw(image)
    draw_window_chrome(draw)
    draw_sidebar(draw, scene.filename)
    draw_editor_header(draw, scene)
    characters = colorized_characters(scene)
    line, column = draw_code(draw, characters, visible_count, cursor_visible)
    draw_statusbar(draw, scene, line, column)
    return image


def build_frames() -> tuple[list[Image.Image], list[int]]:
    frames: list[Image.Image] = []
    durations: list[int] = []

    for scene_index, scene in enumerate(SCENES):
        characters = colorized_characters(scene)
        counts = list(range(0, len(characters) + TYPE_STEP, TYPE_STEP))
        counts[-1] = len(characters)

        for index, visible_count in enumerate(counts):
            frames.append(render_frame(scene, visible_count, cursor_visible=True))
            if index == 0:
                durations.append(550 if scene_index else 850)
            else:
                durations.append(55)

        for cursor_visible in (False, True, False, True):
            frames.append(render_frame(scene, len(characters), cursor_visible=cursor_visible))
            durations.append(310)

    return frames, durations


def make_shared_palette(frames: Iterable[Image.Image]) -> Image.Image:
    samples = list(frames)
    strip = Image.new("RGB", (WIDTH, HEIGHT * len(samples)))
    for index, frame in enumerate(samples):
        strip.paste(frame, (0, HEIGHT * index))
    return strip.quantize(colors=128, method=Image.Quantize.MEDIANCUT)


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    frames, durations = build_frames()

    sample_frames = [frames[0], frames[len(frames) // 3], frames[(2 * len(frames)) // 3], frames[-1]]
    palette = make_shared_palette(sample_frames)
    paletted_frames = [
        frame.quantize(palette=palette, dither=Image.Dither.NONE)
        for frame in frames
    ]

    paletted_frames[0].save(
        OUTPUT,
        save_all=True,
        append_images=paletted_frames[1:],
        duration=durations,
        loop=0,
        optimize=True,
        disposal=2,
    )
    print(f"GIF criado em {OUTPUT} ({len(frames)} quadros)")


if __name__ == "__main__":
    main()
