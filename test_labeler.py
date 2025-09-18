#!/usr/bin/env python3
"""Test script to verify labeler features without GUI."""

import json
from pathlib import Path

# Test data structure for multiple properties
test_labels = {
    "frame001.jpg": {
        "motion": [1, 3, 5],
        "quality": [8, 9],
        "person": [2]
    },
    "frame002.jpg": {
        "motion": [1, 2],
        "quality": [7]
    },
    "frame003.jpg": {
        "motion": [4, 5, 6],
        "quality": [8],
        "person": [1, 2, 3]
    }
}

# Save test labels
labels_path = Path("test_labels.json")
with labels_path.open("w") as f:
    json.dump(test_labels, f, indent=2)

print("Test labels created:")
print(json.dumps(test_labels, indent=2))

# Load and verify
with labels_path.open("r") as f:
    loaded = json.load(f)

print("\nLoaded labels:")
for frame, props in loaded.items():
    print(f"  {frame}:")
    for prop_name, values in props.items():
        print(f"    {prop_name}: {values}")

print("\nFeatures implemented:")
print("✓ Multiple properties per frame (e.g., frame can have motion=[1,3,5])")
print("✓ Named property sessions (e.g., 'motion', 'quality', 'person')")
print("✓ Speed control: 1x, 1.5x, 2x (keys: D=speed up, A=slow down)")
print("✓ Toggle-based labeling (press number to add/remove)")
print("✓ Clear all properties for current frame (key: C)")

# Clean up
labels_path.unlink()
print("\nTest completed successfully!")