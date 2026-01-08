"""Set Windows desktop wallpaper."""

from __future__ import annotations

import ctypes
import logging
from pathlib import Path
from typing import Optional

from PIL import Image, ImageDraw, ImageFont

SPI_SETDESKWALLPAPER = 20
SPIF_UPDATEINIFILE = 0x01
SPIF_SENDCHANGE = 0x02

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".bmp", ".png"}


class WallpaperSetter:
    def __init__(self) -> None:
        self._current_wallpaper: Optional[Path] = None

    def set_wallpaper(self, path: str | Path) -> bool:
        image_path = Path(path).expanduser().resolve()
        if not image_path.exists():
            logging.warning("Wallpaper file does not exist: %s", image_path)
            return False

        if image_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            logging.warning("Unsupported wallpaper format: %s", image_path.suffix)
            return False

        if self._current_wallpaper == image_path:
            return False

        if image_path.suffix.lower() == ".png":
            image_path = self._ensure_png_compatible(image_path)

        result = ctypes.windll.user32.SystemParametersInfoW(
            SPI_SETDESKWALLPAPER,
            0,
            str(image_path),
            SPIF_UPDATEINIFILE | SPIF_SENDCHANGE,
        )
        if not result:
            raise ctypes.WinError()

        self._current_wallpaper = image_path
        return True

    def _ensure_png_compatible(self, image_path: Path) -> Path:
        bmp_path = image_path.with_suffix(".bmp")
        if bmp_path.exists():
            return bmp_path

        try:
            with Image.open(image_path) as img:
                img.save(bmp_path, format="BMP")
            logging.info("Converted %s to %s for wallpaper compatibility.", image_path, bmp_path)
            return bmp_path
        except Exception:
            logging.exception("Failed to convert PNG to BMP; using original PNG.")
            return image_path


class TextWallpaperBuilder:
    def __init__(self, settings: dict) -> None:
        background_image = settings.get("background_image", "wallpapers/background.jpg")
        self._background = Path(background_image) if background_image else None
        self._output = Path(settings.get("output_image", ".generated/current_wallpaper.bmp"))
        self._font_path = settings.get("font_path")
        self._font_size = int(settings.get("font_size", 48))
        self._text_color = tuple(settings.get("text_color", [255, 255, 255]))
        self._shadow_color = tuple(settings.get("shadow_color", [0, 0, 0]))
        self._padding = int(settings.get("padding", 40))
        self._background_color = tuple(settings.get("background_color", [0, 0, 0]))

    def build(self, track) -> Path:
        background = self._load_background()
        text = self._format_text(track)
        image = background.copy()
        draw = ImageDraw.Draw(image)
        font = self._load_font()

        width, height = image.size
        text_bbox = draw.multiline_textbbox((0, 0), text, font=font, spacing=8)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        x = self._padding
        y = height - text_height - self._padding

        shadow_offset = 2
        draw.multiline_text(
            (x + shadow_offset, y + shadow_offset),
            text,
            font=font,
            fill=self._shadow_color,
            spacing=8,
        )
        draw.multiline_text((x, y), text, font=font, fill=self._text_color, spacing=8)

        self._output.parent.mkdir(parents=True, exist_ok=True)
        image.save(self._output)
        return self._output

    def _load_background(self) -> Image.Image:
        if self._background and self._background.exists():
            return Image.open(self._background).convert("RGB")
        if self._background:
            logging.warning("Background image not found: %s. Using solid color.", self._background)
        return Image.new("RGB", (1920, 1080), self._background_color)

    def _load_font(self) -> ImageFont.FreeTypeFont:
        if self._font_path:
            font_path = Path(self._font_path).expanduser()
            if font_path.exists():
                try:
                    return ImageFont.truetype(str(font_path), self._font_size)
                except OSError:
                    logging.warning("Failed to load font at %s. Falling back to default.", font_path)
        try:
            return ImageFont.truetype("arial.ttf", self._font_size)
        except OSError:
            logging.warning("Arial font not found. Falling back to default font.")
            return ImageFont.load_default()

    @staticmethod
    def _format_text(track) -> str:
        parts = [track.title]
        if track.artist:
            parts.append(track.artist)
        if track.album:
            parts.append(track.album)
        return "\n".join(parts)
