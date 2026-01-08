"""Set Windows desktop wallpaper."""

from __future__ import annotations

import ctypes
import logging
from pathlib import Path
from typing import Optional

try:
    from PIL import Image
except ImportError:  # pragma: no cover - optional dependency
    Image = None

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
        if Image is None:
            logging.warning(
                "Pillow not installed; PNG support may be limited. "
                "Install pillow or use JPG/BMP wallpapers.",
            )
            return image_path

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
