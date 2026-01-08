# wallmusic

Change the Windows desktop wallpaper by rendering the currently playing track name over a
background image. It uses Windows Global System Media Transport Controls (GSMTC), so it
works with Spotify or any app that reports to Windows media controls.

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

## Configuration

Edit `config/settings.json` to pick a background image and customize the text overlay:

```json
{
  "background_image": "",
  "background_color": [0, 0, 0],
  "output_image": ".generated/current_wallpaper.bmp",
  "font_path": "",
  "font_size": 48,
  "text_color": [255, 255, 255],
  "shadow_color": [0, 0, 0],
  "padding": 40
}
```

- `background_image`: Base image to draw text on.
- `background_color`: RGB background color when no image is provided.
- `output_image`: Generated wallpaper file.
- `font_path`: Optional path to a `.ttf` font file (leave empty to use Arial).
- `font_size`: Font size in points.
- `text_color`: RGB text color.
- `shadow_color`: RGB shadow color for legibility.
- `padding`: Margin from the bottom-left corner.

## Troubleshooting

- **No metadata appears:** Some apps do not publish track metadata. Try another media
  player or make sure the app is actually playing (not paused).
- **Wallpaper does not change:** Verify Windows allows wallpaper changes (Group Policy
  may block it) and that slideshow settings are disabled.
- **Font not found:** Provide a `font_path` to a valid `.ttf` file if Arial is unavailable.
