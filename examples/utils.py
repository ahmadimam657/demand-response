import matplotlib.figure
import mpl_panel_builder as mpb
import numpy as np
import numpy.typing as npt

MPB_CONFIG = {
    "panel": {
        "dimensions": {"width_cm": 19, "height_cm": 8},
        "margins": {
            "left_cm": 2.0,
            "bottom_cm": 1.5,
            "right_cm": 1.5,
            "top_cm": 2.0,
        },
    },
    "style": {
        "theme": "presentation",
        "rc_params": {
            "figure.facecolor": "none",
            "axes.facecolor": "none",
            "legend.facecolor": "white",
            "font.size": 11,
        },
    },
    "output": {
        "format": "png",
    },
}

def plot_optimized_demand(
    hourly_demand: npt.NDArray[np.floating] | None,
    optimized_demand: npt.NDArray[np.floating] | None,
    hourly_price: npt.NDArray[np.floating],
    hours: npt.NDArray[np.integer],
) -> tuple[matplotlib.figure.Figure, list]:
    """Plot original demand, optimized demand, and price profiles.
    
    Args:
        hourly_demand: Original demand profile (can be None)
        optimized_demand: Optimized demand profile (can be None)
        hourly_price: Price profile
        hours: Hour indices for x-axis
        
    Returns:
        A tuple containing the figure and list of axes
        
    """
    bar_width = 0.8
    colors = mpb.helpers.get_default_colors()
    mpb.configure(MPB_CONFIG)
    mpb.set_rc_style()
    fig, axs = mpb.create_panel()
    ax_primary = axs[0][0]

    # Bar plots for the original and optimized demand
    if hourly_demand is not None:
        ax_primary.bar(
            hours,
            hourly_demand / 1000,  # Convert to GWh
            bar_width,
            color=colors[7],
            alpha=0.5,
            label="Original demand",
        )
    if optimized_demand is not None:
        ax_primary.bar(
            hours,
            optimized_demand / 1000,  # Convert to GWh
            bar_width,
            color=colors[2],
            alpha=0.5,
            label="Optimized demand",
        )
    
    # Axes settings
    ax_primary.set_ylabel("Demand (GWh)")
    ax_primary.set_xlabel("Time (Year)")
    
    # Set x-axis ticks to show quarterly positions (0, 1/4, 1/2, 3/4, 1)
    n_hours = len(hours)
    tick_positions = [0, n_hours // 4, n_hours // 2, 3 * n_hours // 4, n_hours - 1]
    tick_labels = ['0', '1/4', '1/2', '3/4', '1']
    ax_primary.set_xticks(tick_positions)
    ax_primary.set_xticklabels(tick_labels)

    # Add another axis for the price
    ax_ontop = ax_primary.twinx()
    ax_ontop.spines["right"].set_visible(True)

    # Plot the price
    ax_ontop.plot(hours, hourly_price, "k", linewidth=2, label="Price")
    ax_ontop.tick_params(axis="y", colors="black")
    ax_ontop.set_ylabel("Price (€/MWh)")
    ax_ontop.set_xlim(ax_primary.get_xlim())

    # Use one legend for both axes
    all_handles = []
    all_labels = []
    for ax in [ax_primary, ax_ontop]:
        handles, labels = ax.get_legend_handles_labels()
        all_handles.extend(handles)
        all_labels.extend(labels)
    ax_ontop.legend(all_handles, all_labels, loc="upper right")

    return fig, [ax_primary, ax_ontop]