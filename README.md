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
- **Value Mappings**: Define what each number means (1='clear', 2='partial', 3='blocked')
- **Smart Property Handling**: Detects existing properties and asks whether to keep or replace
- **Variable Playback Speed**: 1x, 1.5x, 2x (D/A keys)
- **Toggle-based Labeling**: Press 1-9 to toggle property values on/off
- **State-based Workflow**: Property values mark transitions that persist until next change

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
- **State-based Visualization**: Shows property values as persistent state blocks
- **Value Mapping Display**: Shows meaningful labels (clear/partial/blocked) instead of numbers
- **Completeness Analysis**: See percentage of frames covered by defined states
- **Gap Detection**: Identify regions with undefined states
- **Multi-Property Support**: Analyze all properties with their mappings
- **Timeline Analysis**: Detailed state transition timeline with durations

#### Output:
- **State Block Plot**: Colored blocks showing state duration and transitions
- **Meaningful Legends**: Shows "1: clear", "2: partial" instead of just numbers
- **State Coverage Stats**: Percentage of sequence covered by defined states
- **Transition Analysis**: Lists state changes with readable descriptions
- **Gap Visualization**: Red areas show undefined state regions

## Data Format

Labels are stored in JSON format with value mappings:

```json
{
  "frames": {
    "frame001.jpg": {
      "motion": [1, 3, 5],
      "quality": [8, 9],
      "person": [2]
    },
    "frame002.jpg": {
      "motion": [1, 2],
      "quality": [7]
    }
  },
  "mappings": {
    "motion": {
      "1": "slow",
      "2": "medium", 
      "3": "fast",
      "5": "very fast"
    },
    "quality": {
      "7": "good",
      "8": "very good",
      "9": "excellent"
    },
    "person": {
      "1": "adult",
      "2": "child"
    }
  },
  "metadata": {
    "created_with": "frame_property_labeler",
    "version": "2.0",
    "total_frames": 150,
    "properties": ["motion", "quality", "person"]
  }
}
```

The format includes:
- **frames**: The actual frame labels (same as before)
- **mappings**: Defines what each numeric value means for each property
- **metadata**: File information and statistics
- **Backward compatible**: Tool handles both new and legacy formats

## Workflow Example

1. **First Pass - Motion Labeling**:
   ```bash
   python3 labeler_gui.py frames/ --property motion
   # Define mappings: 1='slow', 2='medium', 3='fast'
   # Label key transition points - states persist until next change
   ```

2. **Second Pass - Quality Assessment**:
   ```bash
   python3 labeler_gui.py frames/ --property quality  
   # Define mappings: 7='good', 8='very good', 9='excellent'
   # Motion labels remain untouched
   ```

3. **Refinement - Update Motion**:
   ```bash
   python3 labeler_gui.py frames/ --property motion
   # Choose "Keep existing" to see current labels with meanings
   # Modify state transitions as needed
   ```

4. **Analysis**:
   ```bash
   python3 analyze_labels.py frames/labels.json --image-dir frames/
   # View state-based timeline with meaningful labels
   # See transition efficiency and state coverage
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

