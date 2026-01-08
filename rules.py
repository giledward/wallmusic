"""Load and apply wallpaper rules based on track metadata."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional

from media_session import TrackInfo


@dataclass(frozen=True)
class Rule:
    wallpaper: Path
    artist_contains: Optional[str] = None
    title_contains: Optional[str] = None
    album_contains: Optional[str] = None
    title_regex: Optional[str] = None
    artist_regex: Optional[str] = None
    album_regex: Optional[str] = None
    app_id_contains: Optional[str] = None
    priority: int = 0

    def matches(self, track: TrackInfo) -> bool:
        if self.artist_contains and self.artist_contains.lower() not in track.artist.lower():
            return False
        if self.title_contains and self.title_contains.lower() not in track.title.lower():
            return False
        if self.album_contains and self.album_contains.lower() not in track.album.lower():
            return False
        if self.app_id_contains and self.app_id_contains.lower() not in track.app_id.lower():
            return False
        if self.title_regex and not re.search(self.title_regex, track.title, re.IGNORECASE):
            return False
        if self.artist_regex and not re.search(self.artist_regex, track.artist, re.IGNORECASE):
            return False
        if self.album_regex and not re.search(self.album_regex, track.album, re.IGNORECASE):
            return False
        return True


@dataclass(frozen=True)
class RuleSet:
    default_wallpaper: Optional[Path]
    rules: List[Rule]

    @classmethod
    def load(cls, path: Path) -> "RuleSet":
        payload = json.loads(path.read_text())
        default_wallpaper = payload.get("default_wallpaper")
        rules_payload = payload.get("rules", [])

        rules = []
        for item in rules_payload:
            match = item.get("match", {})
            rules.append(
                Rule(
                    wallpaper=Path(item["wallpaper"]).expanduser(),
                    artist_contains=match.get("artist_contains"),
                    title_contains=match.get("title_contains"),
                    album_contains=match.get("album_contains"),
                    title_regex=match.get("title_regex"),
                    artist_regex=match.get("artist_regex"),
                    album_regex=match.get("album_regex"),
                    app_id_contains=match.get("app_id_contains"),
                    priority=int(match.get("priority", item.get("priority", 0))),
                )
            )

        rules.sort(key=lambda rule: rule.priority, reverse=True)
        default_path = Path(default_wallpaper).expanduser() if default_wallpaper else None
        return cls(default_wallpaper=default_path, rules=rules)

    def match(self, track: TrackInfo) -> Optional[Path]:
        for rule in self.rules:
            if rule.matches(track):
                return rule.wallpaper
        return self.default_wallpaper

    def iter_paths(self) -> Iterable[Path]:
        if self.default_wallpaper:
            yield self.default_wallpaper
        for rule in self.rules:
            yield rule.wallpaper
