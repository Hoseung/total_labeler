#!/usr/bin/env python3
"""
Generalized script for comparing algorithm detection results with ground truth annotations.
Supports multiple properties through configurable mappings.
"""

import json
import argparse
import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
from typing import List, Dict, Any, Tuple


def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration file containing property mappings."""
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_ground_truth(filepath: str, property_name: str, config: Dict[str, Any]) -> Tuple[List[str], Dict]:
    """
    Load ground truth annotations from key frames and reconstruct for all frames.

    Args:
        filepath: Path to ground truth JSON file
        property_name: Name of the property to extract (e.g., 'driver_seatbelt')
        config: Configuration containing mappings

    Returns:
        Tuple of (list of states for all frames, metadata dict)
    """
    print(f"Loading ground truth from {filepath}...")

    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    frames_data = data.get('frames', {})
    metadata = data.get('metadata', {})
    total_frames = metadata.get('total_frames', 1792)

    # Get value mapping for this property
    property_config = config['properties'][property_name]
    value_map = property_config['gt_to_algo_mapping']

    # Convert string keys to int if needed
    value_map = {int(k) if k.isdigit() else k: v for k, v in value_map.items()}

    # Extract key frames and their states
    key_frames = []
    for filename, frame_data in frames_data.items():
        # Extract frame number from filename
        frame_num_str = filename.split('_')[-1].replace('.bmp', '').replace('.jpg', '').replace('.png', '')
        try:
            frame_num = int(frame_num_str)
        except ValueError:
            print(f"Warning: Could not extract frame number from {filename}")
            continue

        if property_name in frame_data:
            state_value = frame_data[property_name]
            if isinstance(state_value, list):
                state_value = state_value[0]
            state = value_map.get(state_value, 'unknown')
            key_frames.append((frame_num, state))

    # Sort key frames by frame number
    key_frames.sort(key=lambda x: x[0])

    print(f"Found {len(key_frames)} key frames with state transitions for {property_name}")
    for frame_num, state in key_frames:
        print(f"  Frame {frame_num:5d}: {state}")

    # Reconstruct full timeline
    states = []
    for i in range(total_frames):
        state = 'unknown'

        # Find the last key frame before or at this frame
        for frame_num, frame_state in reversed(key_frames):
            if i >= frame_num:
                state = frame_state
                break

        # If no key frame found, use first key frame's state if available
        if state == 'unknown' and key_frames:
            state = key_frames[0][1]

        states.append(state)

    print(f"Reconstructed {len(states)} ground truth labels for all frames")

    # Calculate state distribution
    state_counts = {}
    for state in states:
        state_counts[state] = state_counts.get(state, 0) + 1

    print("\nGround truth state distribution:")
    for state, count in sorted(state_counts.items()):
        percentage = count / len(states) * 100
        print(f"  {state:15s}: {count:5d} ({percentage:5.1f}%)")

    return states, {
        'total_frames': total_frames,
        'key_frames': key_frames,
        'state_counts': state_counts
    }


def load_algorithm_results(directory: str, property_name: str, config: Dict[str, Any]) -> Tuple[List[str], Dict]:
    """
    Load algorithm detection results from individual frame JSON files.

    Args:
        directory: Directory containing per-frame JSON files
        property_name: Name of the property to extract
        config: Configuration containing extraction paths

    Returns:
        Tuple of (list of states, metadata dict)
    """
    results_dir = Path(directory)
    json_files = sorted(results_dir.glob("img_*.json"))

    print(f"Loading algorithm results from {len(json_files)} files...")

    property_config = config['properties'][property_name]
    extraction_path = property_config['algo_extraction_path']

    states = []
    error_count = 0

    for json_file in json_files:
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)

            # Navigate through the extraction path
            value = data
            for key in extraction_path:
                if key.startswith('[') and key.endswith(']'):
                    # Array index
                    idx = int(key[1:-1])
                    value = value[idx]
                else:
                    # Dictionary key
                    value = value[key]

            states.append(value)

        except (KeyError, IndexError, TypeError) as e:
            error_count += 1
            states.append('unknown')
            if error_count <= 5:  # Only show first 5 errors
                print(f"Error extracting from {json_file.name}: {e}")

    if error_count > 5:
        print(f"... and {error_count - 5} more errors")

    print(f"Loaded {len(states)} algorithm results ({error_count} errors)")

    # Calculate state distribution
    state_counts = {}
    for state in states:
        state_counts[state] = state_counts.get(state, 0) + 1

    print("\nAlgorithm state distribution:")
    for state, count in sorted(state_counts.items()):
        percentage = count / len(states) * 100
        print(f"  {state:15s}: {count:5d} ({percentage:5.1f}%)")

    return states, {
        'total_files': len(json_files),
        'error_count': error_count,
        'state_counts': state_counts
    }


def calculate_metrics(algo_states: List[str], gt_states: List[str]) -> Dict:
    """Calculate comparison metrics between algorithm and ground truth."""

    if len(algo_states) != len(gt_states):
        print(f"Warning: Sequence length mismatch (algo={len(algo_states)}, gt={len(gt_states)})")
        min_len = min(len(algo_states), len(gt_states))
        algo_states = algo_states[:min_len]
        gt_states = gt_states[:min_len]

    # Calculate overall agreement
    matches = sum(1 for a, g in zip(algo_states, gt_states) if a == g)
    total = len(algo_states)
    agreement_rate = (matches / total * 100) if total > 0 else 0

    # Build confusion matrix
    unique_states = sorted(set(algo_states + gt_states))
    confusion = pd.DataFrame(0, index=unique_states, columns=unique_states)

    for algo, gt in zip(algo_states, gt_states):
        confusion.loc[algo, gt] += 1

    # Calculate per-state metrics
    state_metrics = {}
    for state in unique_states:
        tp = confusion.loc[state, state]
        fp = confusion.loc[state, :].sum() - tp  # Predicted as state but wasn't
        fn = confusion.loc[:, state].sum() - tp  # Was state but not predicted
        tn = confusion.values.sum() - tp - fp - fn

        precision = (tp / (tp + fp) * 100) if (tp + fp) > 0 else 0
        recall = (tp / (tp + fn) * 100) if (tp + fn) > 0 else 0
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0

        state_metrics[state] = {
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'support': int(confusion.loc[:, state].sum())
        }

    return {
        'agreement_rate': agreement_rate,
        'matches': matches,
        'total': total,
        'confusion_matrix': confusion,
        'state_metrics': state_metrics
    }


def visualize_comparison(algo_states: List[str], gt_states: List[str], property_name: str, output_dir: str = None):
    """Create visualizations comparing algorithm results with ground truth."""

    # Create numeric mapping for visualization
    all_states = sorted(set(algo_states + gt_states))
    state_to_num = {state: i for i, state in enumerate(all_states)}

    algo_numeric = [state_to_num[s] for s in algo_states]
    gt_numeric = [state_to_num[s] for s in gt_states]

    # Create figure with subplots
    fig = plt.figure(figsize=(16, 12))

    # Timeline comparison
    ax1 = plt.subplot(4, 1, 1)
    time_points = np.arange(len(algo_states))
    ax1.plot(time_points, algo_numeric, 'b-', linewidth=0.8, alpha=0.7, label='Algorithm')
    ax1.set_ylabel('State')
    ax1.set_title(f'{property_name}: Algorithm Detection Results')
    ax1.set_yticks(range(len(all_states)))
    ax1.set_yticklabels(all_states)
    ax1.grid(True, alpha=0.3)
    ax1.legend()

    ax2 = plt.subplot(4, 1, 2)
    ax2.plot(time_points, gt_numeric, 'g-', linewidth=0.8, alpha=0.7, label='Ground Truth')
    ax2.set_ylabel('State')
    ax2.set_title(f'{property_name}: Ground Truth Labels')
    ax2.set_yticks(range(len(all_states)))
    ax2.set_yticklabels(all_states)
    ax2.grid(True, alpha=0.3)
    ax2.legend()

    # Agreement visualization
    ax3 = plt.subplot(4, 1, 3)
    agreement = [1 if a == g else 0 for a, g in zip(algo_states, gt_states)]

    # Color regions by agreement
    for i in range(len(agreement) - 1):
        color = 'green' if agreement[i] == 1 else 'red'
        ax3.axvspan(i, i+1, alpha=0.2, color=color)

    ax3.plot(time_points, agreement, 'k-', linewidth=0.5, alpha=0.5)
    ax3.set_ylabel('Agreement')
    ax3.set_xlabel('Frame Index')
    ax3.set_title('Agreement (Green=Match, Red=Mismatch)')
    ax3.set_yticks([0, 1])
    ax3.set_yticklabels(['Disagree', 'Agree'])
    ax3.set_ylim([-0.1, 1.1])

    # State distribution comparison
    ax4 = plt.subplot(4, 2, 7)
    algo_counts = pd.Series(algo_states).value_counts()
    gt_counts = pd.Series(gt_states).value_counts()

    all_states_sorted = sorted(all_states)
    algo_counts = algo_counts.reindex(all_states_sorted, fill_value=0)
    gt_counts = gt_counts.reindex(all_states_sorted, fill_value=0)

    x_pos = np.arange(len(all_states_sorted))
    width = 0.35

    ax4.bar(x_pos - width/2, algo_counts.values, width, label='Algorithm', color='blue', alpha=0.7)
    ax4.bar(x_pos + width/2, gt_counts.values, width, label='Ground Truth', color='green', alpha=0.7)
    ax4.set_xlabel('State')
    ax4.set_ylabel('Count')
    ax4.set_title('State Distribution')
    ax4.set_xticks(x_pos)
    ax4.set_xticklabels(all_states_sorted, rotation=45, ha='right')
    ax4.legend()
    ax4.grid(True, alpha=0.3)

    # Percentage distribution
    ax5 = plt.subplot(4, 2, 8)
    algo_pct = (algo_counts / algo_counts.sum() * 100)
    gt_pct = (gt_counts / gt_counts.sum() * 100)

    ax5.bar(x_pos - width/2, algo_pct.values, width, label='Algorithm', color='blue', alpha=0.7)
    ax5.bar(x_pos + width/2, gt_pct.values, width, label='Ground Truth', color='green', alpha=0.7)
    ax5.set_xlabel('State')
    ax5.set_ylabel('Percentage (%)')
    ax5.set_title('State Distribution (%)')
    ax5.set_xticks(x_pos)
    ax5.set_xticklabels(all_states_sorted, rotation=45, ha='right')
    ax5.legend()
    ax5.grid(True, alpha=0.3)

    plt.tight_layout()

    if output_dir:
        output_path = Path(output_dir) / f'{property_name}_comparison.png'
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        print(f"Saved visualization to {output_path}")

    plt.show()


def print_results(metrics: Dict, property_name: str):
    """Print detailed comparison results."""

    print("\n" + "="*70)
    print(f"RESULTS FOR {property_name.upper()}")
    print("="*70)

    print(f"\nOverall Agreement: {metrics['agreement_rate']:.2f}% ({metrics['matches']}/{metrics['total']})")

    print("\nPer-State Metrics:")
    print(f"{'State':<15} {'Precision':<12} {'Recall':<12} {'F1':<12} {'Support':<10}")
    print("-" * 65)

    for state, state_metrics in sorted(metrics['state_metrics'].items()):
        print(f"{state:<15} {state_metrics['precision']:>10.2f}% {state_metrics['recall']:>10.2f}% "
              f"{state_metrics['f1']:>10.2f}% {state_metrics['support']:>10d}")

    print("\nConfusion Matrix (Rows=Algorithm, Columns=Ground Truth):")
    print(metrics['confusion_matrix'])

    # Calculate and print common errors
    confusion = metrics['confusion_matrix']
    errors = []
    for algo in confusion.index:
        for gt in confusion.columns:
            if algo != gt and confusion.loc[algo, gt] > 0:
                errors.append((confusion.loc[algo, gt], algo, gt))

    if errors:
        errors.sort(reverse=True)
        print("\nMost Common Errors:")
        for count, algo, gt in errors[:5]:
            print(f"  {algo} → {gt}: {int(count)} times")


def main():
    parser = argparse.ArgumentParser(description='Compare algorithm results with ground truth annotations')
    parser.add_argument('--gt', required=True, help='Path to ground truth annotation file')
    parser.add_argument('--results', required=True, help='Directory containing algorithm result files')
    parser.add_argument('--config', required=True, help='Path to configuration JSON file')
    parser.add_argument('--property', required=True, help='Property name to compare')
    parser.add_argument('--output', help='Directory to save visualization outputs')
    parser.add_argument('--no-viz', action='store_true', help='Skip visualization')

    args = parser.parse_args()

    # Load configuration
    config = load_config(args.config)

    if args.property not in config['properties']:
        print(f"Error: Property '{args.property}' not found in configuration")
        print(f"Available properties: {', '.join(config['properties'].keys())}")
        return 1

    # Load data
    gt_states, gt_meta = load_ground_truth(args.gt, args.property, config)
    algo_states, algo_meta = load_algorithm_results(args.results, args.property, config)

    # Ensure same length
    if len(algo_states) != len(gt_states):
        print(f"\nResampling to match lengths (algo={len(algo_states)}, gt={len(gt_states)})")
        if len(gt_states) < len(algo_states):
            # Resample GT to match algorithm length
            indices = np.linspace(0, len(gt_states) - 1, len(algo_states))
            gt_states = [gt_states[int(np.round(idx))] for idx in indices]
        else:
            # Resample algorithm to match GT length
            indices = np.linspace(0, len(algo_states) - 1, len(gt_states))
            algo_states = [algo_states[int(np.round(idx))] for idx in indices]

    # Calculate metrics
    metrics = calculate_metrics(algo_states, gt_states)

    # Print results
    print_results(metrics, args.property)

    # Visualize if requested
    if not args.no_viz:
        visualize_comparison(algo_states, gt_states, args.property, args.output)

    return 0


if __name__ == '__main__':
    exit(main())