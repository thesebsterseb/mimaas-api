"""
MIMaaS Visualization Module

Optional visualization tools for power consumption analysis.
Requires: pandas, plotly

Install with: pip install mimaas[viz]
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def plot_power_analysis(power_samples_csv: str, voltage_v: float = 3.3) -> go.Figure:
    """
    Create an interactive power consumption analysis dashboard.

    Args:
        power_samples_csv: Path to the power_samples.csv file
        voltage_v: MCU voltage for power calculations (default: 3.3V)

    Returns:
        Plotly Figure object (call .show() to display)

    Example:
        from mimaas.viz import plot_power_analysis
        fig = plot_power_analysis('power_samples.csv')
        fig.show()
    """
    df = pd.read_csv(power_samples_csv)

    # Calculate statistics across all segments
    segment_stats = df.groupby('time_ms')['current_uA'].agg(['mean', 'std', 'min', 'max']).reset_index()

    # Create figure with subplots
    fig = make_subplots(
        rows=2, cols=2,
        specs=[[{"colspan": 2}, None], [{}, {}]],
        row_heights=[0.55, 0.45],
        vertical_spacing=0.22,
        horizontal_spacing=0.12
    )

    # Color palette for segments
    colors = [
        '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
        '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
    ]

    # Track traces for dropdown control
    trace_indices_by_run = {}
    all_trace_count = 0

    # Plot 1: All segments overlaid with mean and confidence band
    for seg_id in df['segment_id'].unique():
        seg_data = df[df['segment_id'] == seg_id]
        trace_indices_by_run[seg_id] = all_trace_count
        fig.add_trace(
            go.Scatter(
                x=seg_data['time_ms'],
                y=seg_data['current_uA'],
                mode='lines',
                name=f'Run {seg_id}',
                line=dict(color=colors[seg_id % len(colors)], width=1.5),
                opacity=0.5,
                showlegend=False,
                hovertemplate='Run %{text}<br>Time: %{x:.2f} ms<br>Current: %{y:.1f} uA<extra></extra>',
                text=[seg_id] * len(seg_data),
                visible=True,
            ),
            row=1, col=1
        )
        all_trace_count += 1

    # Index for confidence band and mean traces
    confidence_band_idx = all_trace_count
    # Add confidence band (mean +/- std)
    fig.add_trace(
        go.Scatter(
            x=pd.concat([segment_stats['time_ms'], segment_stats['time_ms'][::-1]]),
            y=pd.concat([segment_stats['mean'] + segment_stats['std'],
                         (segment_stats['mean'] - segment_stats['std'])[::-1]]),
            fill='toself',
            fillcolor='rgba(31, 119, 180, 0.2)',
            line=dict(color='rgba(255,255,255,0)'),
            name='+/-1 Std Dev',
            showlegend=True,
            hoverinfo='skip',
            visible=True
        ),
        row=1, col=1
    )
    all_trace_count += 1

    mean_trace_idx = all_trace_count
    # Add mean line
    fig.add_trace(
        go.Scatter(
            x=segment_stats['time_ms'],
            y=segment_stats['mean'],
            mode='lines',
            name='Mean Current',
            line=dict(color='#1f77b4', width=3),
            showlegend=True,
            hovertemplate='Time: %{x:.2f} ms<br>Mean: %{y:.1f} uA<extra></extra>',
            visible=True
        ),
        row=1, col=1
    )
    all_trace_count += 1

    histogram_idx = all_trace_count
    # Plot 2: Distribution histogram
    fig.add_trace(
        go.Histogram(
            y=df['current_uA'],
            nbinsy=50,
            name='Distribution',
            marker_color='#1f77b4',
            opacity=0.7,
            showlegend=False,
            hovertemplate='Current: %{y:.0f} uA<br>Count: %{x}<extra></extra>'
        ),
        row=2, col=1
    )
    all_trace_count += 1

    # Add mean and std lines to histogram
    mean_current = df['current_uA'].mean()
    std_current = df['current_uA'].std()
    fig.add_hline(y=mean_current, line_dash="dash", line_color="red",
                  annotation_text=f"Mean: {mean_current:.0f} uA", row=2, col=1)
    fig.add_hline(y=mean_current + std_current, line_dash="dot", line_color="orange",
                  annotation_text=f"+1s: {mean_current + std_current:.0f} uA", row=2, col=1)
    fig.add_hline(y=mean_current - std_current, line_dash="dot", line_color="orange",
                  annotation_text=f"-1s: {mean_current - std_current:.0f} uA", row=2, col=1)

    # Track box plot indices
    box_plot_start_idx = all_trace_count
    # Plot 3: Box plot per segment
    for seg_id in df['segment_id'].unique():
        seg_data = df[df['segment_id'] == seg_id]
        fig.add_trace(
            go.Box(
                y=seg_data['current_uA'],
                name=f'Run {seg_id}',
                marker_color=colors[seg_id % len(colors)],
                showlegend=False,
                boxmean='sd',
                hovertemplate='Run %{x}<br>Current: %{y:.1f} uA<extra></extra>'
            ),
            row=2, col=2
        )
        all_trace_count += 1

    # Calculate power metrics for annotation
    avg_power_uw = mean_current * voltage_v
    total_time_ms = segment_stats['time_ms'].max()
    energy_uj = avg_power_uw * total_time_ms / 1000

    # Create dropdown buttons for run selection
    n_segments = df['segment_id'].nunique()
    buttons = []

    # "All Runs" button - show everything
    buttons.append(dict(
        label='All Runs',
        method='update',
        args=[{'visible': [True] * all_trace_count}]
    ))

    # Individual run buttons
    for seg_id in df['segment_id'].unique():
        visibility = [False] * all_trace_count
        # Show selected run trace
        visibility[trace_indices_by_run[seg_id]] = True
        # Always show confidence band, mean, histogram
        visibility[confidence_band_idx] = True
        visibility[mean_trace_idx] = True
        visibility[histogram_idx] = True
        # Show corresponding box plot
        visibility[box_plot_start_idx + seg_id] = True

        buttons.append(dict(
            label=f'Run {seg_id}',
            method='update',
            args=[{'visible': visibility}]
        ))

    # "Mean Only" button
    mean_only_visibility = [False] * all_trace_count
    mean_only_visibility[confidence_band_idx] = True
    mean_only_visibility[mean_trace_idx] = True
    mean_only_visibility[histogram_idx] = True
    # Show all box plots for comparison
    for i in range(n_segments):
        mean_only_visibility[box_plot_start_idx + i] = True
    buttons.append(dict(
        label='Mean Only',
        method='update',
        args=[{'visible': mean_only_visibility}]
    ))

    # Update layout
    fig.update_layout(
        height=900,
        width=1100,
        title=dict(
            text=f'<b>Power Consumption Analysis</b><br>'
                 f'<sup>Avg Power: {avg_power_uw/1000:.2f} mW | '
                 f'Inference Time: {total_time_ms:.2f} ms | '
                 f'Energy per Inference: {energy_uj:.2f} uJ</sup>',
            x=0.5,
            font=dict(size=16)
        ),
        template='plotly_white',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        hovermode='x unified',
        updatemenus=[
            dict(
                active=0,
                buttons=buttons,
                direction='down',
                showactive=True,
                x=0.0,
                xanchor='left',
                y=1.12,
                yanchor='top',
                bgcolor='white',
                bordercolor='#ccc',
                font=dict(size=11),
                pad=dict(l=10, r=10)
            )
        ],
        # Add subplot titles as annotations with proper positioning
        annotations=[
            dict(
                text='<b>Current Draw Over Time (All Inference Runs)</b>',
                x=0.5, y=0.95,
                xref='paper', yref='paper',
                showarrow=False,
                font=dict(size=13)
            ),
            dict(
                text='<b>Current Distribution</b>',
                x=0.22, y=0.38,
                xref='paper', yref='paper',
                showarrow=False,
                font=dict(size=13)
            ),
            dict(
                text='<b>Per-Segment Statistics</b>',
                x=0.78, y=0.38,
                xref='paper', yref='paper',
                showarrow=False,
                font=dict(size=13)
            )
        ]
    )

    # Update axes
    fig.update_xaxes(title_text='Time (ms)', row=1, col=1,
                     rangeslider=dict(visible=True, thickness=0.05))
    fig.update_yaxes(title_text='Current (uA)', row=1, col=1)
    fig.update_xaxes(title_text='Count', row=2, col=1)
    fig.update_yaxes(title_text='Current (uA)', row=2, col=1)
    fig.update_xaxes(title_text='Inference Run', row=2, col=2)
    fig.update_yaxes(title_text='Current (uA)', row=2, col=2)

    return fig
