#!/usr/bin/env python3
"""Real Data Demand Response Optimization Example.

This module demonstrates demand response optimization using real historical
price and demand data from Finland. It shows how energy consumption can be
shifted from expensive to cheaper time periods to minimize total costs.

The example uses:
- Real histo`rical price data (hourly) from Finnish energy market
- Real historical demand data (15-minute resolution aggregated to hourly)
- Creates a typical year profile by averaging corresponding hours across multiple years
- VirtualStorage optimization with configurable parameters
- Cost savings visualization with quarterly time axis using mpl-panel-builder

"""
from __future__ import annotations

import mpl_panel_builder as mpb
import numpy as np
import numpy.typing as npt
import pandas as pd
from utils import plot_optimized_demand

from demand_response import VirtualStorage

# Configuration constants
MAX_DEMAND_ADVANCE_HOURS = 2
MAX_DEMAND_DELAY_HOURS = 3
SOLVER_TYPE = "mip"


def load_and_prepare_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load and prepare real historical price and demand data.
    
    Creates a typical year (8760 hours) by averaging all corresponding hours
    within each season across multiple years of historical data.
    
    Returns:
        A tuple containing:
        - price_data: DataFrame with hourly prices for a typical year
        - hourly_demand: DataFrame with hourly demand for a typical year
        
    """
    # -------------------------
    # Load REAL historical price data (hourly)
    # -------------------------
    price_data = pd.read_csv("data/price_data.csv", parse_dates=True, index_col=0)
    price_data.columns = ["price"]
    
    # Ensure DatetimeIndex and convert to timezone-naive
    price_data.index = pd.to_datetime(price_data.index, utc=True).tz_localize(None)
    
    # -------------------------
    # Load REAL historical demand data (15-minute)
    # -------------------------
    df = pd.read_csv("data/demand_data.csv", sep=";", parse_dates=["startTime", "endTime"])
    
    # Convert to hourly resolution by grouping by startTime rounded to hour
    df["start_hour"] = df["startTime"].dt.floor("h")
    
    # 15-min values → hourly mean for consumption in MW/h
    hourly_demand = (
        df.groupby("start_hour")["Electricity consumption in Finland"]
        .mean()
        .to_frame(name="demand")
    )
    
    hourly_demand.index.name = None
    
    # Ensure DatetimeIndex and convert to timezone-naive
    hourly_demand.index = pd.to_datetime(hourly_demand.index, utc=True).tz_localize(None)
    
    hourly_demand = hourly_demand.reindex(price_data.index)
    
    # -------------------------
    # Fill missing values with forward fill
    # -------------------------
    hourly_demand = hourly_demand.ffill().bfill()
    
    # -------------------------
    # Align both datasets
    # -------------------------
    start = max(price_data.index.min(), hourly_demand.index.min())
    end = min(price_data.index.max(), hourly_demand.index.max())
    
    price_data = price_data.loc[start:end]
    hourly_demand = hourly_demand.loc[start:end]
    
    # -------------------------
    # Clean the data: remove any remaining NaN/None values
    # -------------------------
    valid_mask = ~(price_data['price'].isna() | hourly_demand['demand'].isna())
    price_data = price_data[valid_mask]
    hourly_demand = hourly_demand[valid_mask]
    
    # -------------------------
    # Create typical year profile using day-of-year and hour
    # This preserves seasonal patterns better than calendar dates
    # -------------------------
    # Add day of year (1-366) and hour of day
    price_data['dayofyear'] = price_data.index.dayofyear
    price_data['hour'] = price_data.index.hour
    
    hourly_demand['dayofyear'] = hourly_demand.index.dayofyear
    hourly_demand['hour'] = hourly_demand.index.hour
    
    # Group by day of year and hour, then take the median (more robust than mean)
    typical_price = (
        price_data.groupby(['dayofyear', 'hour'])['price']
        .mean()
        .reset_index()
    )
    
    typical_demand = (
        hourly_demand.groupby(['dayofyear', 'hour'])['demand']
        .mean()
        .reset_index()
    )
    
    # Create a datetime index for a typical non-leap year (2021)
    base_year = 2021
    
    # Create datetime from day of year
    typical_price['datetime'] = pd.to_datetime(
        typical_price['dayofyear'].astype(str) + f'-{base_year}', 
        format='%j-%Y'
    ) + pd.to_timedelta(typical_price['hour'], unit='h')
    
    typical_demand['datetime'] = pd.to_datetime(
        typical_demand['dayofyear'].astype(str) + f'-{base_year}', 
        format='%j-%Y'
    ) + pd.to_timedelta(typical_demand['hour'], unit='h')
    
    # Set datetime as index and keep only the value columns
    typical_price = typical_price.set_index('datetime')[['price']].sort_index()
    typical_demand = typical_demand.set_index('datetime')[['demand']].sort_index()
    
    # Ensure both have the same index
    common_index = typical_price.index.intersection(typical_demand.index)
    typical_price = typical_price.loc[common_index]
    typical_demand = typical_demand.loc[common_index]

    return typical_price, typical_demand


def analyze_demand_statistics(hourly_demand: pd.DataFrame) -> dict:
    """Analyze demand statistics to determine appropriate configuration.
    
    Args:
        hourly_demand: DataFrame with hourly demand values
        
    Returns:
        Dictionary containing demand statistics
        
    """
    stats = {
        'min': hourly_demand['demand'].min(),
        'max': hourly_demand['demand'].max(),
        'mean': hourly_demand['demand'].mean(),
        'median': hourly_demand['demand'].median(),
        'std': hourly_demand['demand'].std()
    }
    
    return stats


def create_virtual_storage(max_demand: float, mean_demand: float) -> VirtualStorage:
    """Create and configure VirtualStorage based on actual demand levels.
    
    Args:
        max_demand: Maximum observed demand value
        mean_demand: Mean demand value
        
    Returns:
        Configured VirtualStorage instance ready for optimization.
        
    """
    max_hourly_purchase = max_demand * 1.5  # Allow 150% of max demand
    max_rate = mean_demand * 0.3  # Can shift 30% of average demand per hour
    
    return VirtualStorage(
        max_demand_advance=MAX_DEMAND_ADVANCE_HOURS,
        max_demand_delay=MAX_DEMAND_DELAY_HOURS,
        max_hourly_purchase=max_hourly_purchase,
        max_rate=max_rate,
        solver=SOLVER_TYPE,
    )


def calculate_costs(
    prices: npt.NDArray[np.floating],
    original_demand: npt.NDArray[np.floating],
    optimized_demand: npt.NDArray[np.floating],
) -> tuple[float, float, float, float]:
    """Calculate original cost, optimal cost, savings, and savings percentage.
    
    Args:
        prices: Price profile array
        original_demand: Original demand profile array
        optimized_demand: Optimized demand profile array
        
    Returns:
        A tuple containing:
        - original_cost: Total cost with original demand
        - optimal_cost: Total cost with optimized demand  
        - cost_savings: Absolute cost savings
        - savings_percent: Percentage cost savings
        
    """
    original_cost = float(np.sum(prices * original_demand))
    optimal_cost = float(np.sum(prices * optimized_demand))
    cost_savings = original_cost - optimal_cost
    
    if original_cost > 0:
        savings_percent = (cost_savings / original_cost) * 100
    else:
        savings_percent = 0.0
        
    return original_cost, optimal_cost, cost_savings, savings_percent


def main() -> dict:
    """Run optimization with real data and create visualization plots.
    
    Returns:
        Optimization result dictionary from VirtualStorage.optimize_demand()
        
    Raises:
        ValueError: If optimization fails or returns invalid results
        
    """
    # Load and prepare real data
    price_data, hourly_demand = load_and_prepare_data()
    
    # Analyze demand to determine configuration
    stats = analyze_demand_statistics(hourly_demand)
    
    # Use a subset of data for faster optimization (e.g., first week)
    # Remove or adjust this if you want to optimize the full dataset
    # HOURS_TO_OPTIMIZE = 168  # One week
    prices = price_data['price']
    demand = hourly_demand['demand']
    hours = np.arange(len(prices))
    
    # print(f"\nOptimizing {HOURS_TO_OPTIMIZE} hours of data...")
    
    # Configure and run optimization
    storage = create_virtual_storage(stats['max'], stats['mean'])
    result = storage.optimize_demand(prices, demand)
    
    # Validate results
    if "optimal_demand" not in result:
        msg = "Invalid optimization result: missing 'optimal_demand'"
        raise ValueError(msg)
    
    optimized_demand = result["optimal_demand"]
    
    # Calculate costs
    _, _, cost_savings, savings_percent = calculate_costs(
        prices, demand, optimized_demand
    )
    
    # Create visualization: Original demand only
    fig1, axs1 = plot_optimized_demand(demand, None, prices, hours)
    axs1[0].set_title("Original Demand Profile (Real Data)")
    mpb.save_panel(fig1, "output/real_data_optimization_original")
    
    # Create visualization: Original vs Optimized demand
    fig2, axs2 = plot_optimized_demand(demand, optimized_demand, prices, hours)
    axs2[0].set_title(
        f"Demand Response Optimization (Real Data)\n"
        f"Cost Savings: {cost_savings:,.2f} € ({savings_percent:.1f}%)"
    )
    mpb.save_panel(fig2, "output/real_data_optimization_comparison")
    
    return result


if __name__ == "__main__":
    main()