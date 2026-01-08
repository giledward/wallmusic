"""Read media playback info from Windows GSMTC."""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Awaitable, Callable, List

import winrt.windows.media.control as wmc


@dataclass(frozen=True)
class TrackInfo:
    title: str
    artist: str
    album: str
    app_id: str
    is_playing: bool
    timestamp: float

    @property
    def identity(self) -> tuple:
        return (self.title, self.artist, self.album, self.app_id, self.is_playing)


class MediaSessionReader:
    def __init__(self, polling_interval: float = 1.0) -> None:
        self._polling_interval = max(0.2, polling_interval)
        self._callbacks: List[Callable[[TrackInfo | None], Awaitable[None]]] = []
        self._manager: wmc.GlobalSystemMediaTransportControlsSessionManager | None = None
        self._session: wmc.GlobalSystemMediaTransportControlsSession | None = None
        self._running = False
        self._last_identity: tuple | None = None
        self._lock = asyncio.Lock()

    def subscribe(self, callback: Callable[[TrackInfo | None], Awaitable[None]]) -> None:
        self._callbacks.append(callback)

    async def start(self) -> None:
        self._manager = await wmc.GlobalSystemMediaTransportControlsSessionManager.request_async()
        self._manager.sessions_changed += self._on_sessions_changed
        await self._update_session()

    async def stop(self) -> None:
        self._running = False
        if self._session is not None:
            self._session.media_properties_changed -= self._on_media_properties_changed
            self._session.playback_info_changed -= self._on_playback_info_changed

    async def run_forever(self) -> None:
        self._running = True
        while self._running:
            await self._poll_once()
            await asyncio.sleep(self._polling_interval)

    async def get_current_track(self) -> TrackInfo | None:
        if self._session is None:
            return None

        media_props = await self._session.try_get_media_properties_async()
        if not media_props:
            return None

        playback_info = self._session.get_playback_info()
        is_playing = (
            playback_info is not None
            and playback_info.playback_status
            == wmc.GlobalSystemMediaTransportControlsSessionPlaybackStatus.PLAYING
        )

        title = (media_props.title or "").strip()
        artist = (media_props.artist or "").strip()
        album = (media_props.album_title or "").strip()
        app_id = (self._session.source_app_user_model_id or "").strip()

        if not any([title, artist, album]):
            return None

        return TrackInfo(
            title=title,
            artist=artist,
            album=album,
            app_id=app_id,
            is_playing=is_playing,
            timestamp=time.time(),
        )

    async def _poll_once(self) -> None:
        track = await self.get_current_track()
        identity = track.identity if track else None
        if identity != self._last_identity:
            self._last_identity = identity
            await self._emit(track)

    async def _emit(self, track: TrackInfo | None) -> None:
        for callback in self._callbacks:
            try:
                await callback(track)
            except Exception:
                logging.exception("Error in track change callback")

    async def _update_session(self) -> None:
        async with self._lock:
            if self._manager is None:
                return
            session = self._manager.get_current_session()
            if session == self._session:
                return
            if self._session is not None:
                self._session.media_properties_changed -= self._on_media_properties_changed
                self._session.playback_info_changed -= self._on_playback_info_changed
            self._session = session
            if self._session is not None:
                self._session.media_properties_changed += self._on_media_properties_changed
                self._session.playback_info_changed += self._on_playback_info_changed
            await self._poll_once()

    def _on_sessions_changed(self, _sender, _args) -> None:
        asyncio.create_task(self._update_session())

    def _on_media_properties_changed(self, _sender, _args) -> None:
        asyncio.create_task(self._poll_once())

    def _on_playback_info_changed(self, _sender, _args) -> None:
        asyncio.create_task(self._poll_once())
