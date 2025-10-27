#!/usr/bin/env python3
"""
Moving Horizon Solver Speed Comparison

This example compares the speed performance of different MILP solvers
for moving horizon optimization:
- python-mip (open-source, CBC backend)
- Gurobi (commercial, if available)

Focuses on solve time comparison for moving horizon optimization.
"""

import importlib.util
import time
from typing import Any

import numpy as np
import pandas as pd

from demand_response import moving_horizon


def generate_test_data(n_hours: int = 72) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Generate simple test data for moving horizon optimization."""
    
    dates = pd.date_range("2024-01-01", periods=n_hours, freq="h")
    
    # Simple daily price pattern
    hours = np.arange(n_hours)
    prices = 30 + 25 * np.sin(2 * np.pi * hours / 24 - np.pi/2)
    prices = np.maximum(15.0, prices)
    
    # Simple daily demand pattern (inverse of prices)
    demand = 12 + 4 * np.sin(2 * np.pi * hours / 24 + np.pi)
    demand = np.maximum(5.0, demand)
    
    price_data = pd.DataFrame({"price": prices}, index=dates)
    demand_data = pd.DataFrame({"demand": demand}, index=dates)
    
    return price_data, demand_data


def test_moving_horizon_solver(solver_name: str, price_data: pd.DataFrame, demand_data: pd.DataFrame) -> dict[str, Any]:
    """Test a solver with moving horizon optimization."""
    
    print(f"   >>> Testing {solver_name} solver...")
    
    config = {
        "daily_decision_hour": 6,
        "n_lookahead_hours": 24,
        "virtual_storage": {
            "max_demand_advance": 8,
            "max_demand_delay": 8,
            "max_hourly_purchase": 15.0,
            "max_rate": 8.0,
            "solver": solver_name,
        },
    }
    
    try:
        start_time = time.time()
        result = moving_horizon(price_data, demand_data, config)
        solve_time = time.time() - start_time
        
        if "results" in result:
            optimized_demand = result["results"]["demand"]
            original_cost = (price_data["price"] * demand_data["demand"]).sum()
            optimized_cost = (price_data["price"] * optimized_demand).sum()
            cost_savings = original_cost - optimized_cost
            savings_percent = (cost_savings / original_cost) * 100 if original_cost > 0 else 0.0
            
            return {
                "solver": solver_name,
                "success": True,
                "solve_time": solve_time,
                "original_cost": original_cost,
                "optimal_cost": optimized_cost,
                "cost_savings": cost_savings,
                "savings_percent": savings_percent,
                "error": None,
            }
        else:
            return {
                "solver": solver_name,
                "success": False,
                "solve_time": solve_time,
                "error": "No results in moving horizon output",
            }
            
    except Exception as e:
        return {
            "solver": solver_name,
            "success": False,
            "solve_time": None,
            "error": str(e),
        }


def main() -> list[dict[str, Any]]:
    """Run moving horizon solver speed comparison."""
    
    print("*** Moving Horizon Solver Speed Comparison ***")
    print("=" * 50)
    
    # List of solvers to test
    solvers_to_test = ["mip"]
    
    # Check if Gurobi is available
    if importlib.util.find_spec("gurobipy") is not None:
        solvers_to_test.append("gurobi")
        print("[OK] Gurobi solver detected and will be tested")
    else:
        print("[i] Gurobi solver not available, testing only python-mip")
    
    print(f"\n>>> Solvers to test: {', '.join(solvers_to_test)}")
    
    # Generate test data
    print("\n>>> Generating test data...")
    price_data, demand_data = generate_test_data(n_hours=72)
    print(f"Generated {len(price_data)} hours of test data")
    print(f"Price range: {price_data['price'].min():.1f} - {price_data['price'].max():.1f} ct/kWh")
    print(f"Demand range: {demand_data['demand'].min():.1f} - {demand_data['demand'].max():.1f} kWh")
    
    # Test each solver
    results = []
    for solver in solvers_to_test:
        print(f"\n>>> Testing {solver} solver:")
        result = test_moving_horizon_solver(solver, price_data, demand_data)
        results.append(result)
        
        if result["success"]:
            print(f"   [OK] Solve time: {result['solve_time']:.3f}s")
            print(f"   [OK] Cost savings: {result['savings_percent']:.2f}%")
        else:
            print(f"   [X] Failed: {result['error']}")
    
    # Speed comparison results
    successful_results = [r for r in results if r["success"]]
    
    if len(successful_results) > 1:
        print("\n" + "="*50)
        print(">>> SPEED COMPARISON RESULTS")
        print("="*50)
        
        print(f"\n{'Solver':<12} {'Time (s)':<12} {'Savings %':<12}")
        print("-" * 40)
        
        for result in successful_results:
            print(f"{result['solver']:<12} {result['solve_time']:<12.3f} {result['savings_percent']:<12.2f}")
        
        # Find fastest
        fastest = min(successful_results, key=lambda x: x["solve_time"])
        print(f"\n>>> Fastest solver: {fastest['solver']} ({fastest['solve_time']:.3f}s)")
        
        # Speed comparison
        if len(successful_results) == 2:
            times = [r["solve_time"] for r in successful_results]
            speedup = max(times) / min(times)
            faster_solver = fastest["solver"]
            slower_solver = next(r["solver"] for r in successful_results if r["solver"] != faster_solver)
            print(f">>> {faster_solver} is {speedup:.1f}x faster than {slower_solver}")
    
    elif len(successful_results) == 1:
        result = successful_results[0]
        print(f"\n>>> Only {result['solver']} solver succeeded")
        print(f">>> Solve time: {result['solve_time']:.3f}s, Savings: {result['savings_percent']:.2f}%")
    
    else:
        print("\n[X] No solvers succeeded")
    
    print("\n*** Speed comparison completed!")
    
    return results


if __name__ == "__main__":
    main()