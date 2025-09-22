# Frame Property Labeler

A GUI tool for labeling video frames with numeric properties.

## Features
- Load and display video frames
- Label frames with numeric properties (1-9)
- Each property can have only one value at a time (mutually exclusive)
- Keyboard shortcuts for efficient labeling
- Export labeled data for analysis

## Installation

```bash
pip install frame-property-labeler
```

## Usage

```bash
# Run the GUI labeler
frame-labeler

# Analyze labeled data
frame-labeler-analyze
```

## Development

This package is part of the `dis` monorepo. To set up for development:

```bash
# From the repository root
uv sync
```