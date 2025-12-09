#!/usr/bin/env python3
"""Basic Demand Response Optimization Example.

This module demonstrates demand response optimization using real historical
price and demand data from Finland. It shows how energy consumption can be
shifted from expensive to cheaper time periods to minimize total costs.

Features:
- Real historical price data (hourly) from Finnish energy market
- Real historical demand data (15-minute resolution aggregated to hourly)
- Creates a typical year profile by averaging corresponding hours across years
- VirtualStorage optimization with configurable parameters
- Cost savings visualization using mpl-panel-builder

"""
from __future__ import annotations

import mpl_panel_builder as mpb
import numpy as np
import numpy.typing as npt
import pandas as pd
from utils import plot_optimized_demand

from demand_response import VirtualStorage

# Configuration constants
SELECTED_DATE = "2021-01-05"
MAX_DEMAND_ADVANCE = 2
MAX_DEMAND_DELAY = 3
SOLVER_TYPE = "mip"
PRICE_CONVERSION_FACTOR = 10  # Convert from €/MWh to c/kWh


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


def run_optimization(selected_date: str = SELECTED_DATE) -> None:
    """Run demand response optimization for a typical 24-hour profile.
    
    Args:
        selected_date: Not used anymore, kept for compatibility
        
    Returns:
        Dictionary containing optimization results and visualization figure
        
    Raises:
        ValueError: If optimization fails or returns invalid results
        
    """
    # Load and prepare real data
    price_data, hourly_demand = load_and_prepare_data()
    
    # Average across entire year to create a typical 24-hour profile
    price_data['hour'] = price_data.index.hour
    hourly_demand['hour'] = hourly_demand.index.hour
    
    # Group by hour of day and take the mean
    avg_prices = price_data.groupby('hour')['price'].mean()
    avg_demand = hourly_demand.groupby('hour')['demand'].mean()
    
    # Create a single typical day with 24 hours
    base_date = '2021-01-01'
    hours = pd.date_range(base_date, periods=24, freq='h')
    
    prices = avg_prices.values / PRICE_CONVERSION_FACTOR
    demand = avg_demand.values
    
    # Configure with appropriate limits based on actual demand values
    config = {
        "max_demand_advance": MAX_DEMAND_ADVANCE,
        "max_demand_delay": MAX_DEMAND_DELAY,
        "max_hourly_purchase": float(demand.max() * 2),
        "max_rate": float(demand.max()),
        "solver": SOLVER_TYPE,
    }
    
    # Configure and run optimization
    virtual_storage = VirtualStorage(**config)
    result = virtual_storage.optimize_demand(prices, demand)
    
    # Validate results
    if "optimal_demand" not in result:
        msg = "Invalid optimization result: missing 'optimal_demand'"
        raise ValueError(msg)
    
    optimized_demand = result["optimal_demand"]
    
    # Calculate costs
    _, _, cost_savings, savings_percent = calculate_costs(
        prices, demand, optimized_demand
    )
    
    # Create visualization
    fig, axs = plot_optimized_demand(demand, optimized_demand, prices, hours)
    axs[0].set_title(
        f"Demand Response Optimization (Typical Day)\n"
        f"Cost Savings: {cost_savings:,.2f} € ({savings_percent:.1f}%)"
    )
    
    output_path = "output/real_data_optimization"
    mpb.save_panel(fig, output_path)

def main() -> None:
    run_optimization(SELECTED_DATE)


if __name__ == "__main__":
    main()