from __future__ import annotations

import matplotlib.dates as mdates
import matplotlib.figure
import mpl_panel_builder as mpb
import numpy as np
import numpy.typing as npt

mpb_config = {
    "panel": {
        "dimensions": {"width_cm": 19, "height_cm": 8},
        "margins": {
            "left_cm": 2.1,
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
    hourly_demand: npt.NDArray[np.floating],
    optimized_demand: npt.NDArray[np.floating],
    hourly_price: npt.NDArray[np.floating],
    hours: npt.NDArray,
) -> tuple[matplotlib.figure.Figure, list]:
    bar_width = 1 / 24 * 0.9
    # Custom colors: RGB values normalized to 0-1 range
    color_original = (242/255, 125/255, 89/255)  # RGB {242,125,89}
    color_optimized = (166/255, 206/255, 103/255)  # RGB {166,206,103}
    
    mpb.configure(mpb_config)
    mpb.set_rc_style()
    fig, axs = mpb.create_panel()
    ax_primary = axs[0][0]

    # Bar plots for the original and optimized demand
    if hourly_demand is not None:
        ax_primary.bar(
            hours,
            hourly_demand,
            bar_width,
            color=color_original,
            alpha=0.5,
            label="Ori. demand",
        )
    if optimized_demand is not None:
        ax_primary.bar(
            hours,
            optimized_demand,
            bar_width,
            color=color_optimized,
            alpha=0.5,
            label="Opt. demand",
        )
    # Axes settings
    ax_primary.set_ylabel("Demand (MW)")
    ax_primary.set_xlabel("Hour")
    ax_primary.xaxis.set_major_formatter(mdates.DateFormatter("%H"))

    # Add another axis for the price
    # ax_ontop = mpl_helper.get_axes_ontop(fig, ax_main)
    # move_y_axis_to_right(ax_ontop)
    ax_ontop = ax_primary.twinx()
    ax_ontop.spines["right"].set_visible(True)

    # Plot the price
    ax_ontop.plot(hours, hourly_price, "k", label="Price")
    ax_ontop.tick_params(axis="y", colors="black")
    ax_ontop.set_ylabel("Price (€/MWh)")
    ax_ontop.set_xlim(ax_primary.get_xlim())

    # Use one legend for both axis
    all_handles = []
    all_labels = []
    for ax in [ax_primary, ax_ontop]:
        handles, labels = ax.get_legend_handles_labels()
        all_handles.extend(handles)
        all_labels.extend(labels)
    ax_ontop.legend(all_handles, all_labels, loc="upper right")

    return fig, [ax_primary, ax_ontop]