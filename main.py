#!/usr/bin/env python3
"""Run the wallpaper changer based on the current media session."""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
from pathlib import Path

from media_session import MediaSessionReader, TrackInfo
from wallpaper import TextWallpaperBuilder, WallpaperSetter


def load_settings(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Missing settings file: {path}")
    return json.loads(path.read_text())


async def handle_track(
    track: TrackInfo | None,
    builder: TextWallpaperBuilder,
    wallpaper_setter: WallpaperSetter,
    spotify_only: bool,
    verbose: bool,
) -> None:
    if track is None:
        if verbose:
            logging.info("No active media session.")
        return

    if spotify_only and (not track.app_id or "spotify" not in track.app_id.lower()):
        if verbose:
            logging.info("Ignoring non-Spotify track from %s", track.app_id)
        return

    image_path = builder.build(track)
    changed = wallpaper_setter.set_wallpaper(image_path)
    if changed:
        logging.info(
            "Wallpaper updated to %s for %s — %s",
            image_path,
            track.title,
            track.artist,
        )
    elif verbose:
        logging.info("Wallpaper already set to %s", image_path)


async def run(args: argparse.Namespace) -> None:
    settings = load_settings(Path("config/settings.json"))
    builder = TextWallpaperBuilder(settings)
    wallpaper_setter = WallpaperSetter()

    async def on_track_change(track: TrackInfo | None) -> None:
        await handle_track(track, builder, wallpaper_setter, args.spotify_only, args.verbose)

    reader = MediaSessionReader(polling_interval=args.polling_interval)
    reader.subscribe(on_track_change)

    await reader.start()
    try:
        await reader.run_forever()
    finally:
        await reader.stop()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Change wallpaper based on media playback.")
    parser.add_argument(
        "--spotify-only",
        action="store_true",
        help="Only respond to media sessions from Spotify.",
    )
    parser.add_argument(
        "--polling-interval",
        type=float,
        default=1.0,
        help="Polling fallback interval in seconds (default: 1.0).",
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    try:
        asyncio.run(run(args))
    except KeyboardInterrupt:
        logging.info("Shutting down.")


if __name__ == "__main__":
    main()
