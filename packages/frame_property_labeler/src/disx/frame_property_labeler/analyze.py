#!/usr/bin/env python3
"""Visualization tool for analyzing frame property labels.

This tool reads labels.json files and creates line plots showing property
values across frame sequences, revealing completeness and patterns.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.colors import ListedColormap
import numpy as np


class LabelAnalyzer:
    def __init__(self, labels_path: Path, image_dir: Optional[Path] = None):
        self.labels_path = labels_path
        self.image_dir = image_dir
        self.labels = self._load_labels()
        self.frame_sequence = self._build_frame_sequence()
        self.properties = self._extract_properties()
    
    def _load_labels(self) -> Dict[str, Dict[str, List[int]]]:
        """Load labels from JSON file."""
        if not self.labels_path.exists():
            raise FileNotFoundError(f"Labels file not found: {self.labels_path}")
        
        with self.labels_path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        
        # Handle both new format (with frames/mappings) and legacy format
        if "frames" in data:
            # New format
            frame_data = data["frames"]
            self.value_mappings = data.get("mappings", {})
            self.metadata = data.get("metadata", {})
        else:
            # Legacy format - frame data is at root level
            frame_data = data
            self.value_mappings = {}
            self.metadata = {}
        
        # Normalize data structure
        result = {}
        for frame_key, properties in frame_data.items():
            if isinstance(properties, dict):
                # New format: multiple properties
                result[frame_key] = {}
                for prop_name, values in properties.items():
                    if isinstance(values, list):
                        result[frame_key][prop_name] = sorted(values)
                    else:
                        result[frame_key][prop_name] = [values]
            else:
                # Old format: single property
                result[frame_key] = {"default": [properties]}
        
        return result
    
    def _extract_frame_number(self, frame_key: str) -> int:
        """Extract frame number from filename for sorting."""
        # Try common patterns: frame001.jpg, img_123.png, 00042.jpg, etc.
        patterns = [
            r'(\d+)\.(?:jpg|jpeg|png|bmp|tiff|tif)$',  # number.ext
            r'frame[_-]?(\d+)',  # frame123, frame_123, frame-123
            r'img[_-]?(\d+)',    # img123, img_123, img-123
            r'(\d+)'             # any number in filename
        ]
        
        for pattern in patterns:
            match = re.search(pattern, frame_key, re.IGNORECASE)
            if match:
                return int(match.group(1))
        
        # Fallback: use hash of filename for consistent ordering
        return hash(frame_key) % 100000
    
    def _build_frame_sequence(self) -> List[str]:
        """Build ordered list of frame keys."""
        # Get all frames from labels
        labeled_frames = set(self.labels.keys())
        
        # If image_dir provided, include all frames (labeled and unlabeled)
        all_frames = set()
        if self.image_dir and self.image_dir.exists():
            extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif'}
            for path in self.image_dir.iterdir():
                if path.suffix.lower() in extensions:
                    frame_key = path.name
                    all_frames.add(frame_key)
        
        # Use union of labeled frames and all frames
        frames_to_plot = all_frames if all_frames else labeled_frames
        
        # Sort by extracted frame number
        return sorted(frames_to_plot, key=self._extract_frame_number)
    
    def _extract_properties(self) -> Set[str]:
        """Extract all unique property names."""
        properties = set()
        for frame_data in self.labels.values():
            properties.update(frame_data.keys())
        return properties
    
    def _get_frame_properties(self, frame_key: str, property_name: str) -> List[int]:
        """Get property values for a specific frame and property."""
        if frame_key in self.labels and property_name in self.labels[frame_key]:
            return self.labels[frame_key][property_name]
        return []
    
    def _analyze_completeness(self) -> Dict[str, Dict[str, float]]:
        """Analyze completeness statistics for each property."""
        stats = {}
        total_frames = len(self.frame_sequence)
        
        for prop_name in self.properties:
            labeled_frames = 0
            total_values = 0
            
            for frame_key in self.frame_sequence:
                values = self._get_frame_properties(frame_key, prop_name)
                if values:
                    labeled_frames += 1
                    total_values += len(values)
            
            stats[prop_name] = {
                'labeled_frames': labeled_frames,
                'total_frames': total_frames,
                'completeness': labeled_frames / total_frames if total_frames > 0 else 0,
                'avg_values_per_frame': total_values / labeled_frames if labeled_frames > 0 else 0,
                'total_values': total_values
            }
        
        return stats
    
    def create_line_plots(self, save_path: Optional[Path] = None, show_plot: bool = True) -> None:
        """Create line plots for all properties."""
        if not self.properties:
            print("No properties found in labels file.")
            return
        
        # Handle display environment
        if not show_plot or save_path:
            # Use non-interactive backend for headless environments or when only saving
            matplotlib.use('Agg')
        else:
            # Try to use an interactive backend, fall back to Agg if not available
            try:
                import tkinter
                matplotlib.use('TkAgg')
            except ImportError:
                try:
                    matplotlib.use('Qt5Agg')
                except ImportError:
                    matplotlib.use('Agg')
                    show_plot = False  # Can't show without interactive backend
                    print("No interactive display available. Use --save to generate plot file.")
        
        n_properties = len(self.properties)
        fig, axes = plt.subplots(n_properties, 1, figsize=(12, 4 * n_properties))
        
        # Handle single property case
        if n_properties == 1:
            axes = [axes]
        
        # Get completeness stats
        stats = self._analyze_completeness()
        
        # Color map for different property values
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', 
                 '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22']  # For values 1-9
        
        for i, prop_name in enumerate(sorted(self.properties)):
            ax = axes[i]
            
            # Build state timeline - property values mark state transitions
            state_timeline = self._build_state_timeline(prop_name)
            
            # Plot state blocks
            for start_frame, end_frame, values in state_timeline:
                # Handle multiple values per state (show as stacked or overlapping blocks)
                if values:
                    block_height = 0.8 / len(values)  # Distribute height among values
                    for j, value in enumerate(sorted(values)):
                        y_bottom = value - 0.4 + j * block_height
                        y_height = block_height * 0.9  # Small gap between stacked values
                        
                        # Create rectangle for this state block
                        rect = patches.Rectangle(
                            (start_frame, y_bottom), 
                            end_frame - start_frame, 
                            y_height,
                            linewidth=1, 
                            edgecolor='black', 
                            facecolor=colors[value-1], 
                            alpha=0.7,
                            label=f'Value {value}' if j == 0 else ""
                        )
                        ax.add_patch(rect)
            
            # Add gaps visualization (where no labels exist and no state inheritance)
            gaps = self._find_state_gaps(prop_name)
            for start_gap, end_gap in gaps:
                ax.axvspan(start_gap, end_gap + 1, alpha=0.3, color='red', zorder=0)
            
            # Formatting
            state_timeline = self._build_state_timeline(prop_name)
            total_state_frames = sum(end - start for start, end, values in state_timeline)
            
            ax.set_title(f'Property: {prop_name} (State-based)\n'
                        f'Transitions: {len(state_timeline)}, '
                        f'Covered Frames: {total_state_frames}/{len(self.frame_sequence)} '
                        f'({total_state_frames/len(self.frame_sequence):.1%})')
            ax.set_xlabel('Frame Index')
            ax.set_ylabel('Property Value')
            ax.set_ylim(0.5, 9.5)
            ax.set_yticks(range(1, 10))
            ax.grid(True, alpha=0.3)
            
            # Create custom legend for used values
            used_values = set()
            for _, _, values in state_timeline:
                used_values.update(values)
            
            legend_elements = []
            for value in sorted(used_values):
                # Include meaning in legend if available
                meaning = self.value_mappings.get(prop_name, {}).get(str(value), "")
                if meaning:
                    label = f'{value}: {meaning}'
                else:
                    label = f'Value {value}'
                legend_elements.append(
                    patches.Patch(color=colors[value-1], label=label)
                )
            
            if legend_elements:
                ax.legend(handles=legend_elements, bbox_to_anchor=(1.05, 1), loc='upper left')
            
            # Add frame numbers on x-axis (sample every nth frame to avoid crowding)
            step = max(1, len(self.frame_sequence) // 20)
            frame_labels = []
            frame_positions = []
            for idx in range(0, len(self.frame_sequence), step):
                frame_key = self.frame_sequence[idx]
                frame_num = self._extract_frame_number(frame_key)
                frame_labels.append(str(frame_num))
                frame_positions.append(idx)
            
            ax.set_xticks(frame_positions)
            ax.set_xticklabels(frame_labels, rotation=45, ha='right')
        
        plt.tight_layout()
        
        # Add summary text
        fig.suptitle(f'Property Analysis: {self.labels_path.name}\n'
                    f'Total Frames: {len(self.frame_sequence)}, '
                    f'Properties: {len(self.properties)}', 
                    fontsize=14, y=0.98)
        
        plt.tight_layout(rect=[0, 0, 1, 0.96])
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Plot saved to: {save_path}")
        
        if show_plot and matplotlib.get_backend() != 'Agg':
            try:
                plt.show()
            except Exception as e:
                print(f"Could not display plot: {e}")
                print("Use --save to generate plot file instead.")
        
        # Print detailed statistics
        self._print_statistics(stats)
    
    def _print_statistics(self, stats: Dict[str, Dict[str, float]]) -> None:
        """Print detailed statistics about the labels."""
        print("\n" + "="*60)
        print("LABEL ANALYSIS SUMMARY")
        print("="*60)
        
        print(f"Labels file: {self.labels_path}")
        print(f"Total frames in sequence: {len(self.frame_sequence)}")
        print(f"Properties found: {len(self.properties)}")
        
        # Show value mappings if available
        if hasattr(self, 'value_mappings') and self.value_mappings:
            print(f"\nValue Mappings:")
            for prop_name, mappings in self.value_mappings.items():
                print(f"  {prop_name}:")
                for value, meaning in mappings.items():
                    print(f"    {value}: {meaning}")
        
        # Show metadata if available
        if hasattr(self, 'metadata') and self.metadata:
            version = self.metadata.get('version', 'unknown')
            created_with = self.metadata.get('created_with', 'unknown')
            print(f"\nFile Info: {created_with} v{version}")
        
        for prop_name in sorted(self.properties):
            stat = stats[prop_name]
            state_timeline = self._build_state_timeline(prop_name)
            total_state_frames = sum(end - start for start, end, values in state_timeline)
            
            print(f"\nProperty: {prop_name} (State-based)")
            print(f"  State transitions: {len(state_timeline)}")
            print(f"  State coverage: {total_state_frames}/{len(self.frame_sequence)} frames "
                  f"({total_state_frames/len(self.frame_sequence):.1%})")
            print(f"  Transition points: {stat['labeled_frames']} frames")
            print(f"  Avg values per transition: {stat['avg_values_per_frame']:.1f}")
            
            # Show state transitions
            if state_timeline:
                print(f"  State timeline:")
                for start, end, values in state_timeline[:10]:  # Show first 10 states
                    duration = end - start
                    
                    # Format values with meanings
                    value_displays = []
                    for value in sorted(values):
                        meaning = self.value_mappings.get(prop_name, {}).get(str(value), "")
                        if meaning:
                            value_displays.append(f"{value}:{meaning}")
                        else:
                            value_displays.append(str(value))
                    
                    print(f"    Frames {start}-{end-1} ({duration} frames): {value_displays}")
                if len(state_timeline) > 10:
                    print(f"    ... and {len(state_timeline) - 10} more states")
            
            # Show gaps (before first state)
            state_gaps = self._find_state_gaps(prop_name)
            if state_gaps:
                print(f"  Undefined states (before first transition): {len(state_gaps)} gaps")
                for start, end in state_gaps[:5]:
                    gap_size = end - start + 1
                    print(f"    Frames {start}-{end} ({gap_size} frames)")
    
    def _build_state_timeline(self, property_name: str) -> List[Tuple[int, int, Set[int]]]:
        """Build state timeline where property values mark transitions and persist until next transition."""
        timeline = []
        current_state = set()
        state_start = 0
        
        for i, frame_key in enumerate(self.frame_sequence):
            frame_values = self._get_frame_properties(frame_key, property_name)
            
            if frame_values:
                # Transition detected - save previous state if it exists
                if current_state and i > state_start:
                    timeline.append((state_start, i, current_state.copy()))
                
                # Start new state
                current_state = set(frame_values)
                state_start = i
        
        # Add final state if it exists
        if current_state:
            timeline.append((state_start, len(self.frame_sequence), current_state))
        
        return timeline
    
    def _find_state_gaps(self, property_name: str) -> List[Tuple[int, int]]:
        """Find gaps where no initial state is defined (before first transition)."""
        gaps = []
        
        # Find first transition
        first_transition = None
        for i, frame_key in enumerate(self.frame_sequence):
            if self._get_frame_properties(frame_key, property_name):
                first_transition = i
                break
        
        # If there's a gap before first transition
        if first_transition is not None and first_transition > 0:
            gaps.append((0, first_transition - 1))
        elif first_transition is None:
            # No transitions at all - entire sequence is a gap
            gaps.append((0, len(self.frame_sequence) - 1))
        
        return gaps
    
    def _find_gaps(self, property_name: str) -> List[Tuple[int, int]]:
        """Find consecutive ranges of unlabeled frames (legacy method for statistics)."""
        gaps = []
        gap_start = None
        
        for i, frame_key in enumerate(self.frame_sequence):
            has_label = bool(self._get_frame_properties(frame_key, property_name))
            
            if not has_label:
                if gap_start is None:
                    gap_start = i
            else:
                if gap_start is not None:
                    gaps.append((gap_start, i - 1))
                    gap_start = None
        
        # Handle gap at the end
        if gap_start is not None:
            gaps.append((gap_start, len(self.frame_sequence) - 1))
        
        return gaps


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze and visualize frame property labels")
    parser.add_argument(
        "labels_path",
        type=Path,
        help="Path to the labels.json file"
    )
    parser.add_argument(
        "--image-dir",
        type=Path,
        default=None,
        help="Directory containing frame images (to include unlabeled frames in analysis)"
    )
    parser.add_argument(
        "--save",
        type=Path,
        default=None,
        help="Save plot to file (e.g., analysis.png)"
    )
    parser.add_argument(
        "--no-show",
        action="store_true",
        help="Don't display the plot (useful when saving only)"
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    
    # Auto-detect image directory if not provided
    image_dir = args.image_dir
    if not image_dir:
        # Try parent directory of labels file
        potential_dir = args.labels_path.parent
        if potential_dir.exists() and any(
            f.suffix.lower() in {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif'}
            for f in potential_dir.iterdir()
        ):
            image_dir = potential_dir
            print(f"Auto-detected image directory: {image_dir}")
    
    analyzer = LabelAnalyzer(args.labels_path, image_dir)
    analyzer.create_line_plots(
        save_path=args.save,
        show_plot=not args.no_show
    )


if __name__ == "__main__":
    main()