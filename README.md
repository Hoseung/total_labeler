# dis Monorepo

A UV-managed monorepo for multiple independent subpackages under the `disx` namespace.

## Structure

This repository follows a monorepo structure with:
- `packages/`: Individual subpackages
- `meta/`: Umbrella distribution metadata
- Root `pyproject.toml`: Development environment configuration

## Current Packages

### frame-property-labeler

A comprehensive tool for labeling frame properties in image sequences with visualization and analysis capabilities.

## Development Setup

This project uses [uv](https://docs.astral.sh/uv/) for dependency management. 

### Quick Start

```bash
# Clone the repository
git clone <repository-url>
cd total_labeler

# Set up development environment
uv sync

# Run tools from any subpackage
uv run frame-labeler /path/to/frames
uv run frame-labeler-analyze /path/to/labels.json
```

### Development Workflow

1. **Activate the environment**:
   ```bash
   uv shell
   # Or use uv run for individual commands
   ```

2. **Install development dependencies**:
   The root `pyproject.toml` includes dev dependencies (pytest, mypy, ruff, pre-commit).

3. **Run tests**:
   ```bash
   uv run pytest
   ```

4. **Type checking**:
   ```bash
   uv run mypy packages/
   ```

5. **Linting**:
   ```bash
   uv run ruff check packages/
   uv run ruff format packages/
   ```

## Package Documentation

### Frame Property Labeler

Interactive tool for labeling video frames with numeric properties.

#### Installation (for end users)

```bash
# Once published to private index
pip install frame-property-labeler
```

#### Usage

**Interactive Frame Labeler**:
```bash
# Start labeling with property name
frame-labeler /path/to/frames --property motion

# Interactive property name selection
frame-labeler /path/to/frames

# Custom FPS and labels file
frame-labeler /path/to/frames --property quality --fps 10 --labels custom_labels.json
```

**Label Analysis**:
```bash
# Basic analysis
frame-labeler-analyze /path/to/labels.json

# Include image directory for complete frame analysis
frame-labeler-analyze /path/to/labels.json --image-dir /path/to/frames

# Save plot to file
frame-labeler-analyze /path/to/labels.json --save analysis.png
```

#### Features

- **Multiple Properties**: Support for multiple named properties per frame
- **Exclusive Values**: Each property can have only one value (1-9) at a time
- **Property Sessions**: Name your properties (motion, quality, person, etc.)
- **Value Mappings**: Define what each number means (1='clear', 2='partial', 3='blocked')
- **Smart Property Handling**: Detects existing properties and asks whether to keep or replace
- **Variable Playback Speed**: 1x, 1.5x, 2x
- **State-based Workflow**: Property values mark transitions that persist until next change
- **Analysis Tools**: Visualize labeled data with state blocks and transitions

#### Controls (GUI)

- **1-9**: Set property value for current frame (exclusive - only one value per property)
- **Left/Right Arrow**: Navigate frames
- **Space**: Play/Pause automatic playback
- **D/A**: Increase/Decrease playback speed
- **C**: Clear all properties for current frame
- **S**: Save labels
- **Q/ESC**: Quit

## Adding New Subpackages

To add a new subpackage to the monorepo:

1. Create package structure:
   ```bash
   mkdir -p packages/<new_package>/src/disx/<new_package>
   ```

2. Add package `pyproject.toml`:
   ```toml
   [project]
   name = "new-package"
   version = "0.1.0"
   # ... other metadata
   ```

3. Update root `pyproject.toml` to include the new package:
   ```toml
   [tool.uv.sources]
   new-package = { path = "packages/new_package", editable = true }
   ```

4. Run `uv sync` to update the environment

## Data Format

The frame property labeler uses a JSON format with value mappings:

```json
{
  "frames": {
    "frame001.jpg": {
      "motion": [3],
      "quality": [8]
    }
  },
  "mappings": {
    "motion": {
      "1": "slow",
      "3": "medium",
      "5": "fast"
    },
    "quality": {
      "8": "very good",
      "9": "excellent"
    }
  },
  "metadata": {
    "created_with": "frame_property_labeler",
    "version": "2.0",
    "total_frames": 150
  }
}
```

## Requirements

- Python >= 3.10
- uv package manager
- Package-specific dependencies are handled by uv

## License

See LICENSE file for details.