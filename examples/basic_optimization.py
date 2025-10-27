#!/usr/bin/env python3
"""Basic Demand Response Optimization Example.

This module demonstrates a simple demand response optimization using a pyramid
price profile and single peak demand. It shows how energy can be shifted from
expensive to cheaper time periods to minimize total costs.

The example uses:
- Simple VirtualStorage optimization
- Clear price and demand patterns
- Cost savings calculation

Example:
    Run the optimization example::

        $ python basic_optimization.py

"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from demand_response import VirtualStorage

if TYPE_CHECKING:
    import numpy.typing as npt


# Configuration constants
MAX_DEMAND_ADVANCE_HOURS = 2
MAX_DEMAND_DELAY_HOURS = 3
MAX_HOURLY_PURCHASE_KWH = 1.0
MAX_TRANSFER_RATE_KWH = 1.0
SOLVER_TYPE = "mip"

# Display formatting constants
SEPARATOR_LENGTH = 50
DECIMAL_PLACES = 2
PERCENT_DECIMAL_PLACES = 1


def create_test_data() -> tuple[npt.NDArray[np.floating], npt.NDArray[np.floating]]:
    """Create test price and demand profiles for optimization.
    
    Returns:
        A tuple containing:
        - prices: Pyramid-shaped price profile with peak in middle
        - demand: Single peak demand at the highest price hour
        
    """
    # Create pyramid price profile (peak in middle)
    # This represents expensive energy during peak hours
    prices = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 4.0, 3.0, 2.0, 1.0])
    
    # Create single peak demand at the center (time index 4)
    # This demand occurs exactly when prices are highest
    demand = np.array([0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0])
    
    return prices, demand


def create_virtual_storage() -> VirtualStorage:
    """Create and configure VirtualStorage with predefined parameters.
    
    Returns:
        Configured VirtualStorage instance ready for optimization.
        
    """
    return VirtualStorage(
        max_demand_advance=MAX_DEMAND_ADVANCE_HOURS,
        max_demand_delay=MAX_DEMAND_DELAY_HOURS,
        max_hourly_purchase=MAX_HOURLY_PURCHASE_KWH,
        max_rate=MAX_TRANSFER_RATE_KWH,
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


def display_configuration(storage: VirtualStorage) -> None:
    """Display optimization configuration parameters.
    
    Args:
        storage: VirtualStorage instance to display configuration for
        
    """
    print("\n>>> Optimization Configuration:")
    print(f"   Max demand advance: {storage.max_demand_advance} hours")
    print(f"   Max demand delay: {storage.max_demand_delay} hours") 
    print(f"   Max hourly purchase: {storage.max_hourly_purchase} kWh")
    print(f"   Max transfer rate: {storage.max_rate} kWh")


def display_results(
    prices: npt.NDArray[np.floating],
    original_demand: npt.NDArray[np.floating],
    optimized_demand: npt.NDArray[np.floating],
    original_cost: float,
    optimal_cost: float,
    cost_savings: float,
    savings_percent: float,
) -> None:
    """Display optimization results and analysis.
    
    Args:
        prices: Price profile array
        original_demand: Original demand profile array
        optimized_demand: Optimized demand profile array
        original_cost: Total cost with original demand
        optimal_cost: Total cost with optimized demand
        cost_savings: Absolute cost savings
        savings_percent: Percentage cost savings
        
    """
    demand_shift = optimized_demand - original_demand
    
    print("\n>>> Optimization Results:")
    print(f"   Original demand:    {original_demand}")
    print(f"   Optimized demand:   {optimized_demand}")
    print(f"   Demand shift:       {demand_shift}")
    
    print("\n>>> Cost Analysis:")
    print(f"   Original cost:      {original_cost:.{DECIMAL_PLACES}f} ct")
    print(f"   Optimized cost:     {optimal_cost:.{DECIMAL_PLACES}f} ct")
    print(f"   *** Cost savings:   {cost_savings:.{DECIMAL_PLACES}f} ct")
    print(f"   >>> Savings percent: {savings_percent:.{PERCENT_DECIMAL_PLACES}f}%")


def display_optimization_strategy(
    prices: npt.NDArray[np.floating],
    original_demand: npt.NDArray[np.floating], 
    optimized_demand: npt.NDArray[np.floating],
) -> None:
    """Display detailed optimization strategy explanation.
    
    Args:
        prices: Price profile array
        original_demand: Original demand profile array
        optimized_demand: Optimized demand profile array
        
    """
    print("\n>>> Optimization Strategy:")
    
    # Find where energy was moved from and to
    shifts = optimized_demand - original_demand
    positive_shifts = np.where(shifts > 0)[0]
    negative_shifts = np.where(shifts < 0)[0]
    
    if len(positive_shifts) > 0:
        for idx in positive_shifts:
            shift_amount = shifts[idx]
            price = prices[idx]
            print(f"   [+] Added {shift_amount:.{DECIMAL_PLACES}f} kWh at hour {idx} "
                  f"(price: {price:.1f} ct/kWh)")
    
    if len(negative_shifts) > 0:
        for idx in negative_shifts:
            shift_amount = abs(shifts[idx])
            price = prices[idx]
            print(f"   [-] Removed {shift_amount:.{DECIMAL_PLACES}f} kWh from hour {idx} "
                  f"(price: {price:.1f} ct/kWh)")
    
    print("\n*** Energy was shifted from expensive hours to cheaper hours!")


def main() -> dict:
    """Run basic optimization example with simple test data.
    
    Returns:
        Optimization result dictionary from VirtualStorage.optimize_demand()
        
    Raises:
        ValueError: If optimization fails or returns invalid results
        
    """
    print("*** Basic Demand Response Optimization Example ***")
    print("=" * SEPARATOR_LENGTH)
    
    # Create test data
    prices, demand = create_test_data()
    print(f"Price profile: {prices}")
    print(f"Demand profile: {demand}")
    
    # Configure virtual storage
    storage = create_virtual_storage()
    display_configuration(storage)
    
    # Run optimization
    print("\n>>> Running optimization...")
    try:
        result = storage.optimize_demand(prices, demand)
    except Exception as e:
        error_msg = f"Optimization failed: {e}"
        raise ValueError(error_msg) from e
    
    # Validate results
    if "optimal_demand" not in result:
        msg = "Invalid optimization result: missing 'optimal_demand'"
        raise ValueError(msg)
    
    # Extract and validate results
    optimized_demand = result["optimal_demand"]
    if not isinstance(optimized_demand, np.ndarray):
        msg = "Invalid optimization result: 'optimal_demand' is not a numpy array"
        raise ValueError(msg)
    
    # Calculate costs
    original_cost, optimal_cost, cost_savings, savings_percent = calculate_costs(
        prices, demand, optimized_demand
    )
    
    # Display results
    display_results(
        prices, demand, optimized_demand,
        original_cost, optimal_cost, cost_savings, savings_percent
    )
    
    # Explain optimization strategy
    display_optimization_strategy(prices, demand, optimized_demand)
    
    return result


if __name__ == "__main__":
    main()