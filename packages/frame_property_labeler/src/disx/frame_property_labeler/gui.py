#!/usr/bin/env python3
"""Simple GUI tool for labeling frame properties using OpenCV.

The tool iterates through image frames inside a directory, displays them, and
lets the user assign numeric properties (1-9) to each frame. Each property can
have only one value at a time (mutually exclusive). Supports multiple named 
properties per frame and variable playback speeds.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List, Set

import cv2
import numpy as np

SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif"}


class FrameLabelerApp:
    def __init__(self, image_dir: Path, labels_path: Path, property_name: str, fps: float = 5.0):
        self.image_dir = image_dir
        self.labels_path = labels_path
        self.property_name = property_name
        self.base_fps = fps
        self.fps = fps
        self.speed_multiplier = 1.0
        self.available_speeds = [1.0, 1.5, 2.0]
        self.speed_index = 0
        self.replace_property = None  # Will be set during label loading
        
        self.frames: List[Path] = self._load_frames()
        if not self.frames:
            raise SystemExit(f"No image frames found in {image_dir}")
        
        self.labels: Dict[str, Dict[str, Set[int]]] = self._load_existing_labels()
        
        # Always set up value mappings if not already defined for this property
        if (self.property_name not in self.value_mappings or 
            not self.value_mappings.get(self.property_name, {})):
            self._setup_value_mappings()
        
        self.current_index = 0
        self.current_property = 1
        self.playing = False
        self.display_size = (960, 540)
        self.window_name = f"Frame Property Labeler - {property_name}"
        
        # Apply default properties from existing labels
        for i, frame_path in enumerate(self.frames):
            key = self._frame_key(frame_path)
            if key in self.labels and self.property_name in self.labels[key]:
                if i == 0 and self.labels[key][self.property_name]:
                    # Use the first value as default
                    self.current_property = min(self.labels[key][self.property_name])
    
    def _load_frames(self) -> List[Path]:
        files = [
            path for path in sorted(self.image_dir.iterdir())
            if path.suffix.lower() in SUPPORTED_EXTENSIONS and path.is_file()
        ]
        return files
    
    def _load_existing_labels(self) -> Dict[str, Dict[str, Set[int]]]:
        """Load existing labels. Structure: {frame_key: {property_name: set(values)}}"""
        if not self.labels_path.exists():
            self.value_mappings = {}
            return {}
        
        try:
            with self.labels_path.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
        except json.JSONDecodeError as exc:
            print(f"Failed to read {self.labels_path}: {exc}")
            print("Starting with empty labels.")
            self.value_mappings = {}
            return {}
        
        # Handle both new format (with frames/mappings) and legacy format
        if "frames" in data:
            # New format
            frame_data = data["frames"]
            self.value_mappings = data.get("mappings", {})
            if self.property_name in self.value_mappings:
                print(f"\nLoaded value mappings for '{self.property_name}':")
                for value, meaning in self.value_mappings[self.property_name].items():
                    print(f"  {value}: {meaning}")
        else:
            # Legacy format - frame data is at root level
            frame_data = data
            self.value_mappings = {}
        
        # Convert loaded data to the expected structure
        result = {}
        property_exists = False
        existing_frames_count = 0
        
        for frame_key, properties in frame_data.items():
            if isinstance(properties, dict):
                # New format: multiple properties
                result[frame_key] = {}
                for prop_name, values in properties.items():
                    if isinstance(values, list):
                        result[frame_key][prop_name] = set(values)
                    else:
                        # Single value, convert to set
                        result[frame_key][prop_name] = {values}
                    
                    # Check if current property already exists
                    if prop_name == self.property_name:
                        property_exists = True
                        existing_frames_count += 1
            else:
                # Old format: single unnamed property
                result[frame_key] = {"default": {properties}}
                if self.property_name == "default":
                    property_exists = True
                    existing_frames_count += 1
        
        # Ask about property replacement if this property already exists
        if property_exists:
            print(f"\nFound existing property '{self.property_name}' in {existing_frames_count} frames.")
            print("Options:")
            print("  1. Keep existing - Augment/modify existing values (recommended)")
            print("  2. Replace all - Clear all existing values for this property")
            print("  3. Cancel - Exit without changes")
            
            while True:
                choice = input("Choose option (1/2/3) [default: 1]: ").strip() or "1"
                if choice in ["1", "2", "3"]:
                    break
                print("Invalid choice. Please enter 1, 2, or 3.")
            
            if choice == "3":
                raise SystemExit("Cancelled by user")
            elif choice == "2":
                # Clear existing property values
                for frame_key in result:
                    if self.property_name in result[frame_key]:
                        result[frame_key][self.property_name].clear()
                print(f"Cleared all existing values for property '{self.property_name}'")
                self.replace_property = True
            else:
                self.replace_property = False
                print(f"Will keep and show existing values for property '{self.property_name}'")
        
        return result
    
    def _setup_value_mappings(self) -> None:
        """Set up value mappings for the current property."""
        print(f"\n{'='*60}")
        print(f"Setting up value meanings for property: '{self.property_name}'")
        print("="*60)
        print("Define what each number (1-9) means for this property.")
        print("This helps make your labels more readable and meaningful.")
        print("  - Press Enter to skip a value")
        print("  - Type 'done' to finish early") 
        print("  - Type 'skip' to skip all mappings")
        print("\nExamples: 1='slow', 2='medium', 3='fast'")
        
        if self.property_name not in self.value_mappings:
            self.value_mappings[self.property_name] = {}
        
        for i in range(1, 10):
            current_meaning = self.value_mappings[self.property_name].get(str(i), "")
            if current_meaning:
                prompt = f"  Value {i} (currently '{current_meaning}'): "
            else:
                prompt = f"  Value {i}: "
            
            meaning = input(prompt).strip()
            if meaning.lower() == 'skip':
                print("Skipping all value mappings.")
                self.value_mappings[self.property_name] = {}
                return
            elif meaning.lower() == 'done':
                break
            elif meaning:
                self.value_mappings[self.property_name][str(i)] = meaning
            elif str(i) in self.value_mappings[self.property_name]:
                # Keep existing mapping if user pressed enter
                pass
        
        if self.value_mappings[self.property_name]:
            print(f"\nValue mappings for '{self.property_name}':")
            for value, meaning in sorted(self.value_mappings[self.property_name].items()):
                print(f"  {value}: {meaning}")
        else:
            print(f"\nNo value mappings defined for '{self.property_name}'.")
    
    def _frame_key(self, frame_path: Path) -> str:
        return frame_path.relative_to(self.image_dir).as_posix()
    
    def _get_frame_properties(self, index: int) -> Set[int]:
        """Get all property values for a frame in the current property category."""
        frame_path = self.frames[index]
        key = self._frame_key(frame_path)
        
        if key in self.labels and self.property_name in self.labels[key]:
            return self.labels[key][self.property_name]
        elif index > 0:
            # Inherit from previous frame
            prev_key = self._frame_key(self.frames[index - 1])
            if prev_key in self.labels and self.property_name in self.labels[prev_key]:
                return self.labels[prev_key][self.property_name].copy()
        return {self.current_property}
    
    def _display_frame(self) -> np.ndarray:
        """Load and prepare the current frame for display."""
        frame_path = self.frames[self.current_index]
        img = cv2.imread(str(frame_path))
        
        if img is None:
            # Create placeholder for broken images
            img = np.zeros((100, 200, 3), dtype=np.uint8)
            cv2.putText(img, "Error loading image", (10, 50), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        else:
            # Resize to display size while maintaining aspect ratio
            h, w = img.shape[:2]
            aspect = w / h
            if aspect > self.display_size[0] / self.display_size[1]:
                new_w = self.display_size[0]
                new_h = int(new_w / aspect)
            else:
                new_h = self.display_size[1]
                new_w = int(new_h * aspect)
            img = cv2.resize(img, (new_w, new_h))
        
        # Add status information
        status = self._create_status_bar(img.shape[1])
        
        # Combine image with status bar
        combined = np.vstack([img, status])
        
        return combined
    
    def _create_status_bar(self, width: int) -> np.ndarray:
        """Create a status bar showing current frame info and controls."""
        height = 160  # Increased height for better property visualization
        status_bar = np.ones((height, width, 3), dtype=np.uint8) * 30
        
        # Frame info
        frame_path = self.frames[self.current_index]
        key = self._frame_key(frame_path)
        info_text = f"Frame {self.current_index + 1}/{len(self.frames)} | {key}"
        cv2.putText(status_bar, info_text, (10, 25), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        
        # Property name and current values
        current_props = self._get_frame_properties(self.current_index)
        
        # Create value display with meanings
        prop_values_display = []
        for value in sorted(current_props):
            meaning = self.value_mappings.get(self.property_name, {}).get(str(value), "")
            if meaning:
                prop_values_display.append(f"{value}:{meaning}")
            else:
                prop_values_display.append(str(value))
        
        # Enhanced property display when keeping existing values
        if self.replace_property is False and current_props:
            # Show existing values more prominently
            prop_text = f"Property [{self.property_name}] (EXISTING): {prop_values_display}"
            # Use cyan color for existing values
            cv2.putText(status_bar, prop_text, (10, 50), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
            
            # Add visual indicator for existing data
            cv2.putText(status_bar, "* Existing data - Press numbers to set (exclusive)", (10, 75), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)
        else:
            prop_text = f"Property [{self.property_name}]: {prop_values_display}"
            cv2.putText(status_bar, prop_text, (10, 50), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        # Speed indicator
        speed_text = f"Speed: {self.speed_multiplier:.1f}x"
        y_offset = 95 if self.replace_property is False and current_props else 75
        cv2.putText(status_bar, speed_text, (10, y_offset), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 0), 1)
        
        # Controls help (line 1)
        y_offset += 25
        help_text1 = "Keys: 1-9:Set property (exclusive) | Left/Right:Navigate | Space:Play/Pause"
        cv2.putText(status_bar, help_text1, (10, y_offset), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (150, 150, 150), 1)
        
        # Controls help (line 2)
        y_offset += 20
        help_text2 = "D:Speed up | A:Speed down | C:Clear all | S:Save | Q:Quit"
        cv2.putText(status_bar, help_text2, (10, y_offset), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (150, 150, 150), 1)
        
        # Playing status
        if self.playing:
            play_text = f"PLAYING {self.speed_multiplier:.1f}x"
            cv2.putText(status_bar, play_text, (width - 150, 50), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        return status_bar
    
    def _update_delay(self) -> None:
        """Update the delay based on current FPS and speed multiplier."""
        effective_fps = self.fps * self.speed_multiplier
        self.delay_ms = int(1000 / effective_fps) if effective_fps > 0 else 200
    
    def _save_labels(self) -> None:
        """Save current labels to JSON file."""
        # Convert sets to lists for JSON serialization
        frame_data = {}
        for frame_key, properties in self.labels.items():
            frame_data[frame_key] = {}
            for prop_name, values in properties.items():
                frame_data[frame_key][prop_name] = sorted(list(values))
        
        # Create complete save data structure with mappings
        save_data = {
            "frames": frame_data,
            "mappings": getattr(self, 'value_mappings', {}),
            "metadata": {
                "created_with": "frame_property_labeler",
                "version": "2.0",
                "total_frames": len(self.frames),
                "properties": list(self.labels.keys()) if hasattr(self, 'labels') else []
            }
        }
        
        try:
            with self.labels_path.open("w", encoding="utf-8") as fh:
                json.dump(save_data, fh, indent=2)
            print(f"Labels saved to {self.labels_path}")
        except OSError as exc:
            print(f"Error saving labels: {exc}")
    
    def toggle_property(self, value: int) -> None:
        """Toggle a property value for the current frame. Values are mutually exclusive."""
        frame_path = self.frames[self.current_index]
        key = self._frame_key(frame_path)
        
        # Initialize if needed
        if key not in self.labels:
            self.labels[key] = {}
        if self.property_name not in self.labels[key]:
            self.labels[key][self.property_name] = set()
        
        # For exclusive values: clear existing value and set new one
        current_values = self.labels[key][self.property_name]
        
        if value in current_values:
            # If clicking the same value, remove it (toggle off)
            self.labels[key][self.property_name].clear()
            print(f"Removed property {value} from frame {self.current_index + 1}")
        else:
            # Clear any existing value and set the new one
            self.labels[key][self.property_name] = {value}
            print(f"Set property {value} for frame {self.current_index + 1}")
        
        self.current_property = value
        self._save_labels()
    
    def clear_properties(self) -> None:
        """Clear all properties for the current frame in the current category."""
        frame_path = self.frames[self.current_index]
        key = self._frame_key(frame_path)
        
        if key in self.labels and self.property_name in self.labels[key]:
            self.labels[key][self.property_name].clear()
            print(f"Cleared all properties for frame {self.current_index + 1}")
            self._save_labels()
    
    def change_speed(self, direction: int) -> None:
        """Change playback speed. direction: 1 for increase, -1 for decrease."""
        if direction > 0:
            self.speed_index = min(self.speed_index + 1, len(self.available_speeds) - 1)
        else:
            self.speed_index = max(self.speed_index - 1, 0)
        
        self.speed_multiplier = self.available_speeds[self.speed_index]
        self._update_delay()
        print(f"Playback speed: {self.speed_multiplier:.1f}x")
    
    def show_next(self) -> bool:
        """Move to next frame. Returns False if at the end."""
        if self.current_index < len(self.frames) - 1:
            self.current_index += 1
            return True
        return False
    
    def show_previous(self) -> bool:
        """Move to previous frame. Returns False if at the beginning."""
        if self.current_index > 0:
            self.current_index -= 1
            return True
        return False
    
    def run(self) -> None:
        """Main application loop."""
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(self.window_name, self.display_size[0], self.display_size[1] + 160)
        
        self._update_delay()
        
        print(f"\nFrame Property Labeler - Property: [{self.property_name}]")
        print("=" * 60)
        print("Controls:")
        print("  1-9: Set property value for current frame (exclusive)")
        print("  Left/Right Arrow: Navigate frames")
        print("  Space: Play/Pause automatic playback")
        print("  D: Increase playback speed (1x -> 1.5x -> 2x)")
        print("  A: Decrease playback speed (2x -> 1.5x -> 1x)")
        print("  C: Clear all properties for current frame")
        print("  S: Save labels")
        print("  Q/ESC: Quit")
        print("=" * 60)
        print(f"Note: Multiple properties can be assigned to each frame")
        print(f"Press a number to set it for the current frame (only one value per property)\n")
        
        while True:
            # Display current frame
            display_img = self._display_frame()
            cv2.imshow(self.window_name, display_img)
            
            # Handle keyboard input
            if self.playing:
                key = cv2.waitKey(self.delay_ms) & 0xFF
            else:
                key = cv2.waitKey(0) & 0xFF
            
            # Process key
            if key == ord('q') or key == 27:  # Q or ESC
                break
            elif key == ord('s'):  # Save
                self._save_labels()
            elif key == ord('c'):  # Clear
                self.clear_properties()
            elif key == ord('d'):  # Speed up
                self.change_speed(1)
            elif key == ord('a'):  # Speed down
                self.change_speed(-1)
            elif key == ord(' '):  # Space - toggle play
                self.playing = not self.playing
                if self.playing:
                    print(f"Playback started at {self.speed_multiplier:.1f}x speed")
                else:
                    print("Playback paused")
            elif key == 81 or key == 2:  # Left arrow
                if self.show_previous():
                    self.playing = False
            elif key == 83 or key == 3:  # Right arrow  
                if not self.show_next():
                    self.playing = False
            elif ord('1') <= key <= ord('9'):  # Number keys
                value = key - ord('0')
                self.toggle_property(value)
            
            # Auto-advance if playing
            if self.playing:
                if not self.show_next():
                    self.playing = False
                    print("Reached end of frames")
        
        # Cleanup
        cv2.destroyAllWindows()
        self._save_labels()
        print("\nLabels saved. Goodbye!")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Frame property labeling tool using OpenCV")
    parser.add_argument(
        "directory",
        help="Directory containing frame images."
    )
    parser.add_argument(
        "--property",
        type=str,
        default=None,
        help="Name of the property to label (e.g., 'motion', 'quality', 'object'). Will be prompted if not provided."
    )
    parser.add_argument(
        "--labels",
        type=Path,
        default=None,
        help="Optional path to the labels JSON file (defaults to <directory>/labels.json)."
    )
    parser.add_argument(
        "--fps",
        type=float,
        default=5.0,
        help="Base playback frames per second (default: 5). Can be adjusted during playback."
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    
    directory = Path(args.directory)
    if not directory.exists() or not directory.is_dir():
        raise SystemExit(f"Directory not found: {directory}")
    
    # Get property name
    property_name = args.property
    if not property_name:
        print("\nEnter a name for the property you want to label")
        print("Examples: 'motion', 'quality', 'person', 'action', etc.")
        property_name = input("Property name: ").strip()
        if not property_name:
            property_name = "default"
            print(f"Using default property name: {property_name}")
    
    labels_path = args.labels or directory / "labels.json"
    
    print(f"\nStarting labeling session for property: [{property_name}]")
    
    app = FrameLabelerApp(directory, labels_path, property_name, fps=args.fps)
    app.run()


if __name__ == "__main__":
    main()