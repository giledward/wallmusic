# wallmusic

Change the Windows desktop wallpaper based on the currently playing media track (Spotify
or any other app reporting through Windows Global System Media Transport Controls).

## Requirements

- Windows 10/11
- Python 3.11+

## Installation

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

## Usage

```powershell
python main.py
python main.py --spotify-only --verbose
```

The app runs in the background and updates the wallpaper when the active media track
changes. Stop it with Ctrl+C.

## Rule configuration

Rules live in `config/rules.json` and map track metadata to local image files:

```json
{
  "default_wallpaper": "wallpapers/default.jpg",
  "rules": [
    {"match": {"artist_contains": "Kanye"}, "wallpaper": "wallpapers/kanye.jpg"},
    {"match": {"title_regex": ".*(night|midnight).*"}, "wallpaper": "wallpapers/night.jpg"},
    {"match": {"album_contains": "Graduation"}, "wallpaper": "wallpapers/graduation.jpg"},
    {"match": {"app_id_contains": "Spotify"}, "wallpaper": "wallpapers/spotify.jpg"}
  ]
}
```

Supported match keys:

- `artist_contains`
- `title_contains`
- `album_contains`
- `title_regex`
- `artist_regex`
- `album_regex`
- `app_id_contains`
- Optional `priority` (higher wins, defaults to 0)

The first rule after sorting by priority wins. If no rules match, the default wallpaper
is used.

## Troubleshooting

- **No metadata appears:** Some apps do not publish track metadata. Try another media
  player or make sure the app is actually playing (not paused).
- **Wallpaper does not change:** Verify Windows allows wallpaper changes (Group Policy
  may block it) and that slideshow settings are disabled.
- **PNG wallpaper fails:** The app will convert PNGs to BMP using Pillow when needed. If
  conversion fails, use JPG/BMP files or ensure Pillow is installed.
