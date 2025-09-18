# Frame Property Labeler

A lightweight Tkinter GUI for quickly reviewing a directory of frame images and assigning each frame a numeric property (1-9). The label for each frame defaults to the previous frame’s value, making it easy to tag contiguous sequences with minimal effort.

## Features
- Display frames from a directory and step through them one by one.
- Start, pause, and resume playback at a configurable frame rate.
- Assign properties with on-screen radio buttons or number key shortcuts (1-9).
- Automatically inherit the previous frame’s property when moving forward.
- Persist labels to JSON on every change and via a manual **Save** button.
- Resume work later by reloading the labels file.

## Requirements
- Python 3.8+
- [Pillow](https://python-pillow.org/) for image loading

Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage
The tool accepts the directory containing your frame images and will save labels to `labels.json` inside that directory by default.

```bash
python3 labeler_gui.py /path/to/frame_directory
```

Optional arguments:

- `--labels /path/to/file.json` – custom output file for saved labels.
- `--fps 8` – playback rate in frames per second while in Play mode (default: 5).

If you omit the directory argument, a folder picker dialog will open.

## Supported Images
Files with extensions `.png`, `.jpg`, `.jpeg`, `.bmp`, `.tiff`, or `.tif` are loaded in alphanumeric order.

## Controls
- **Play/Pause** button or spacebar – start or stop playback.
- **Prev/Next** buttons or left/right arrow keys – step one frame at a time.
- **Number keys 1-9** or radio buttons – set the current frame’s property.
- **Save** button – persist labels immediately (auto-save also occurs on each change and when exiting).

## Output Format
Labels are written as JSON with frame paths relative to the selected directory:

```json
{
  "frame_0001.png": 3,
  "frame_0002.png": 3,
  "frame_0003.png": 5
}
```

Reopening the same directory reuses existing labels so you can continue where you left off.

## UV Environment
Use [uv](https://docs.astral.sh/uv/) to manage the virtual environment and dependencies. The project already includes a `pyproject.toml` and `uv.lock` created with `uv` so you can get started with a single command.

```bash
uv sync
```

This creates `.venv` inside the repository and installs the pinned dependencies. Once synced, run the app via uv-managed Python:

```bash
uv run frame-labeler /path/to/frame_directory
```

You can also drop into the environment:

```bash
uv shell
```

When you are done, exit the shell with `exit`.

