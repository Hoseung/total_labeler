#!/usr/bin/env python3
"""Simple GUI tool for labeling frame properties.

The tool iterates through image frames inside a directory, displays them, and
lets the user assign a numeric property (1-9) to each frame. The default
property for a frame inherits from the previous frame to make labeling
contiguous regions faster.
"""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import tkinter as tk
from tkinter import filedialog, messagebox

try:
    from PIL import Image, ImageTk
except ImportError as exc:  # pragma: no cover - makes missing dependency obvious
    raise SystemExit(
        "Pillow is required. Install it with 'pip install Pillow'."
    ) from exc

SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif"}


@dataclass
class FrameInfo:
    path: Path
    property_value: Optional[int] = None


class FrameLabelerApp:
    def __init__(self, root: tk.Tk, image_dir: Path, labels_path: Path, fps: float = 5.0):
        self.root = root
        self.image_dir = image_dir
        self.labels_path = labels_path
        self.interval_ms = int(max(1, 1000 / max(fps, 0.1)))

        self.frames: List[FrameInfo] = self._load_frames()
        if not self.frames:
            raise SystemExit(f"No image frames found in {image_dir}")

        self.labels: Dict[str, int] = self._load_existing_labels()
        self.current_index = 0
        self.playing = False
        self.photo_cache: Dict[int, ImageTk.PhotoImage] = {}
        self.display_size = (960, 540)

        self.property_var = tk.IntVar()
        self.status_text = tk.StringVar()

        self._build_ui()
        self._apply_default_property(0)
        self._show_frame()
        self._update_status()

    def _load_frames(self) -> List[FrameInfo]:
        files = [
            FrameInfo(path=path)
            for path in sorted(self.image_dir.iterdir())
            if path.suffix.lower() in SUPPORTED_EXTENSIONS and path.is_file()
        ]
        return files

    def _load_existing_labels(self) -> Dict[str, int]:
        if not self.labels_path.exists():
            return {}
        try:
            with self.labels_path.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
        except json.JSONDecodeError as exc:
            messagebox.showwarning(
                "Labels file error",
                f"Failed to read {self.labels_path}: {exc}\nStarting with empty labels.",
            )
            return {}
        return {str(k): int(v) for k, v in data.items()}

    def _build_ui(self) -> None:
        self.root.title("Frame Property Labeler")
        self.root.bind("<Left>", lambda _event: self.show_previous())
        self.root.bind("<Right>", lambda _event: self.show_next())
        self.root.bind("<space>", lambda _event: self.toggle_play())
        for digit in range(1, 10):
            self.root.bind(str(digit), lambda event, value=digit: self.set_property(value))

        # Image display area.
        self.image_label = tk.Label(self.root)
        self.image_label.pack(side=tk.TOP, padx=10, pady=10, expand=True)

        # Property selection controls.
        property_frame = tk.Frame(self.root)
        property_frame.pack(side=tk.TOP, pady=5)
        tk.Label(property_frame, text="Property:").pack(side=tk.LEFT, padx=4)
        for value in range(1, 10):
            btn = tk.Radiobutton(
                property_frame,
                text=str(value),
                variable=self.property_var,
                value=value,
                command=lambda v=value: self.set_property(v),
            )
            btn.pack(side=tk.LEFT)

        # Playback controls.
        controls = tk.Frame(self.root)
        controls.pack(side=tk.TOP, pady=10)
        tk.Button(controls, text="Prev", command=self.show_previous).pack(side=tk.LEFT, padx=5)
        self.play_button = tk.Button(controls, text="Play", command=self.toggle_play)
        self.play_button.pack(side=tk.LEFT, padx=5)
        tk.Button(controls, text="Next", command=self.show_next).pack(side=tk.LEFT, padx=5)

        # Status bar.
        status_bar = tk.Frame(self.root)
        status_bar.pack(side=tk.TOP, fill=tk.X, pady=(5, 10))
        tk.Label(status_bar, textvariable=self.status_text).pack(side=tk.LEFT, padx=10)
        tk.Button(status_bar, text="Save", command=self._save_labels).pack(side=tk.RIGHT, padx=10)

    def _apply_default_property(self, index: int) -> None:
        frame = self.frames[index]
        key = self._frame_key(frame)
        if key in self.labels:
            frame.property_value = self.labels[key]
        elif index > 0:
            prev_property = self.frames[index - 1].property_value
            frame.property_value = prev_property
        else:
            frame.property_value = frame.property_value or 1
        self.property_var.set(frame.property_value or 1)

    def _frame_key(self, frame: FrameInfo) -> str:
        return frame.path.relative_to(self.image_dir).as_posix()

    def _show_frame(self) -> None:
        frame = self.frames[self.current_index]
        photo = self._get_photo(self.current_index)
        self.image_label.configure(image=photo)
        self.image_label.image = photo
        if frame.property_value is None:
            self._apply_default_property(self.current_index)
        else:
            self.property_var.set(frame.property_value)

    def _update_status(self) -> None:
        frame = self.frames[self.current_index]
        key = self._frame_key(frame)
        property_value = frame.property_value or self.property_var.get()
        self.status_text.set(
            f"Frame {self.current_index + 1}/{len(self.frames)} | {key} | Property: {property_value}"
        )

    def _get_photo(self, index: int) -> ImageTk.PhotoImage:
        if index in self.photo_cache:
            return self.photo_cache[index]
        frame = self.frames[index]
        with Image.open(frame.path) as img:
            image = img.copy()
        image.thumbnail(self.display_size, Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(image)
        self.photo_cache[index] = photo
        return photo

    def set_property(self, value: int) -> None:
        frame = self.frames[self.current_index]
        frame.property_value = value
        self.property_var.set(value)
        self.labels[self._frame_key(frame)] = value
        self._save_labels()
        self._update_status()

    def show_next(self) -> None:
        if self.current_index < len(self.frames) - 1:
            self.current_index += 1
            self._apply_default_property(self.current_index)
            self._show_frame()
            self._update_status()
        elif self.playing:
            self.toggle_play()

    def show_previous(self) -> None:
        if self.current_index > 0:
            self.current_index -= 1
            self._apply_default_property(self.current_index)
            self._show_frame()
            self._update_status()

    def toggle_play(self) -> None:
        self.playing = not self.playing
        self.play_button.configure(text="Pause" if self.playing else "Play")
        if self.playing:
            self._schedule_next_frame()

    def _schedule_next_frame(self) -> None:
        if not self.playing:
            return
        self.root.after(self.interval_ms, self._advance_if_playing)

    def _advance_if_playing(self) -> None:
        if not self.playing:
            return
        if self.current_index < len(self.frames) - 1:
            self.show_next()
            self._schedule_next_frame()
        else:
            self.toggle_play()

    def _save_labels(self) -> None:
        payload = {self._frame_key(frame): frame.property_value for frame in self.frames if frame.property_value}
        try:
            with self.labels_path.open("w", encoding="utf-8") as fh:
                json.dump(payload, fh, indent=2)
        except OSError as exc:
            messagebox.showerror("Save failed", f"Could not save labels to {self.labels_path}: {exc}")

    def on_close(self) -> None:
        self._save_labels()
        self.root.destroy()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Frame property labeling tool")
    parser.add_argument(
        "directory",
        nargs="?",
        default=None,
        help="Directory containing frame images. If omitted, a dialog will open.",
    )
    parser.add_argument(
        "--labels",
        type=Path,
        default=None,
        help="Optional path to the labels JSON file (defaults to <directory>/labels.json).",
    )
    parser.add_argument(
        "--fps",
        type=float,
        default=5.0,
        help="Playback frames per second while playing (default: 5).",
    )
    return parser.parse_args()


def choose_directory(start_dir: Optional[str]) -> Optional[Path]:
    directory = filedialog.askdirectory(initialdir=start_dir or os.getcwd(), title="Select frame directory")
    if not directory:
        return None
    return Path(directory)


def main() -> None:
    args = parse_args()

    if args.directory is None:
        root = tk.Tk()
        root.withdraw()
        directory = choose_directory(None)
        if directory is None:
            return
        root.destroy()
    else:
        directory = Path(args.directory)

    if not directory.exists() or not directory.is_dir():
        raise SystemExit(f"Directory not found: {directory}")

    labels_path = args.labels or directory / "labels.json"

    root = tk.Tk()
    app = FrameLabelerApp(root, directory, labels_path, fps=args.fps)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()


if __name__ == "__main__":
    main()
