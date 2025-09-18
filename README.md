# Frame Property Labeler

A comprehensive tool for labeling frame properties in image sequences with visualization and analysis capabilities.

## Tools

### 1. `labeler_gui.py` - Interactive Frame Labeler

Label frames with multiple properties using an OpenCV-based GUI.

```bash
# Start labeling with property name
python3 labeler_gui.py /path/to/frames --property motion

# Interactive property name selection
python3 labeler_gui.py /path/to/frames

# Custom FPS and labels file
python3 labeler_gui.py /path/to/frames --property quality --fps 10 --labels custom_labels.json
```

#### Features:
- **Multiple Properties**: Each frame can have multiple values per property (e.g., motion=[1,3,5])
- **Property Sessions**: Name your properties (motion, quality, person, etc.)
- **Smart Property Handling**: Detects existing properties and asks whether to keep or replace
- **Variable Playback Speed**: 1x, 1.5x, 2x (D/A keys)
- **Toggle-based Labeling**: Press 1-9 to toggle property values on/off

#### Controls:
- **1-9**: Toggle property value for current frame
- **Left/Right Arrow**: Navigate frames
- **Space**: Play/Pause automatic playback
- **D**: Increase playback speed
- **A**: Decrease playback speed
- **C**: Clear all properties for current frame
- **S**: Save labels
- **Q/ESC**: Quit

### 2. `analyze_labels.py` - Label Analysis and Visualization

Analyze and visualize labeled data to understand completeness and patterns.

```bash
# Basic analysis
python3 analyze_labels.py /path/to/labels.json

# Include image directory for complete frame analysis
python3 analyze_labels.py /path/to/labels.json --image-dir /path/to/frames

# Save plot to file
python3 analyze_labels.py /path/to/labels.json --save analysis.png

# Save only (don't show)
python3 analyze_labels.py /path/to/labels.json --save analysis.png --no-show
```

#### Features:
- **Line Plots**: Visualize property values across frame sequence
- **Completeness Analysis**: See percentage of labeled frames per property
- **Gap Detection**: Identify unlabeled regions in sequences
- **Multi-Property Support**: Analyze all properties in one view
- **Statistics**: Detailed statistics about labeling completeness

#### Output:
- **Visual Plot**: Line plot showing property values over time
- **Completeness Stats**: Percentage of frames labeled per property
- **Gap Analysis**: Lists of consecutive unlabeled frame ranges
- **Value Distribution**: Average values per labeled frame

## Data Format

Labels are stored in JSON format:

```json
{
  "frame001.jpg": {
    "motion": [1, 3, 5],
    "quality": [8, 9],
    "person": [2]
  },
  "frame002.jpg": {
    "motion": [1, 2],
    "quality": [7]
  }
}
```

## Workflow Example

1. **First Pass - Motion Labeling**:
   ```bash
   python3 labeler_gui.py frames/ --property motion
   ```

2. **Second Pass - Quality Assessment**:
   ```bash
   python3 labeler_gui.py frames/ --property quality
   ```

3. **Refinement - Update Motion**:
   ```bash
   python3 labeler_gui.py frames/ --property motion
   # Choose "Keep existing" to see and modify previous labels
   ```

4. **Analysis**:
   ```bash
   python3 analyze_labels.py frames/labels.json --image-dir frames/
   ```

## Requirements
- Python 3.7+
- OpenCV (cv2)
- NumPy  
- Matplotlib (for analysis tool)

Install dependencies:

```bash
pip install -r requirements.txt
```

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

