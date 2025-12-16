import numpy as np
import mpl_panel_builder as mpb
from demand_response import VirtualStorage
import pandas as pd

hourly_profile_be03 = pd.read_csv('data/hourly_profile_be03.csv')


MAX_DEMAND_ADVANCE = 2
MAX_DEMAND_DELAY = 3
SOLVER_TYPE = "mip"

mpb_config = {
    "panel": {
        "dimensions": {"width_cm": 14, "height_cm": 6},
        "margins": {
            "left_cm": 1,
            "bottom_cm": 0.75,
            "right_cm": 1.25,
            "top_cm": 1.25,
        },
    },
    "style": {
        "theme": "presentation",
        "rc_params": {
            "figure.facecolor": "white",
            "axes.facecolor": "none",
            "legend.facecolor": "white",
            "font.size": 11,
        },
    },
    "output": {
        "format": "png",
    },
}
config = {
        "max_demand_advance": MAX_DEMAND_ADVANCE,
        "max_demand_delay": MAX_DEMAND_DELAY,
        "max_hourly_purchase": float(hourly_profile_be03['average_value'].values.max() * 2),
        "max_rate": 1,
        "solver": SOLVER_TYPE,
    }
    

    
red = "#EB6D44"
gray = "#9EADB2"
green = "#50AA46"
 
hours = np.arange(24)
demand = hourly_profile_be03['average_value'].values
price = hourly_profile_be03['average_price'].values


# Configure and run optimization
virtual_storage = VirtualStorage(**config)
result = virtual_storage.optimize_demand(price, demand)

# Extract results from optimization
shifts = result['optimal_shift']
optimal_demand = result['optimal_demand']

# Calculate hourly additions and removals from shifts
# Positive shifts = added demand (green), Negative shifts = removed demand (red)
add = np.maximum(shifts, 0)
remove = np.minimum(shifts, 0)
 
mpb.configure(mpb_config)
mpb.set_rc_style()
fig, axs = mpb.create_panel(rows=2)
 
ax = axs[0][0]
ax.plot(hours, price, 'k-o')
ax.set(xlim=[-1, 24], xticks=[], yticks=[], ylabel="Price")
ax.spines['left'].set_visible(False)
ax.spines['bottom'].set_visible(False)
 
ax = axs[1][0]
ax.bar(hours, demand, 0.75, fc=gray, label='Original')
ax.bar(hours, add, 0.75, bottom=demand, fc=green, label='Added')
ax.bar(hours, remove, 0.75, bottom=demand, fc=red, label='Removed')
 
ax.set(xlim=[-1, 24], xticks=[], xlabel="Hour", yticks=[], ylabel="Demand")
ax.spines['left'].set_visible(False)
ax.spines['bottom'].set_linewidth(3)
ax.legend(loc='upper right', bbox_to_anchor=(1.1, 3))
output_path = "output/real_data_optimization"
mpb.save_panel(fig, output_path)