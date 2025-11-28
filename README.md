<div align="center">
  <img src="assets/logo.svg" alt="Demand Response Logo"/>
</div>

<div align="center">

# Energy demand response optimization using virtual storage modeling

![Python](https://img.shields.io/badge/python-3.12%2B-blue)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
<!-- [![PyPI version](https://badge.fury.io/py/demand-response.svg)](https://badge.fury.io/py/demand-response) -->
[![Ruff Lint](https://github.com/NoviaIntSysGroup/mpl-panel-builder/actions/workflows/lint.yml/badge.svg)](https://github.com/NoviaIntSysGroup/mpl-panel-builder/actions/workflows/lint.yml)
[![Tests](https://github.com/ahmadimam657/demand-response/actions/workflows/tests.yml/badge.svg)](https://github.com/ahmadimam657/demand-response/actions/workflows/tests.yml)

</div>

`demand-response` helps you optimize energy costs by intelligently shifting electricity demand across time periods using Mixed Integer Linear Programming (MILP). The library models energy flexibility as a virtual battery that can store and release energy to minimize total purchasing costs while respecting physical and operational constraints.

## Features

• 🔋 **Virtual Storage Modeling**: Models demand response as a virtual battery without explicit storage level constraints  
• 💰 **Cost Optimization**: Minimizes total energy costs including spot prices and regulation market participation  
• 🔄 **Moving Horizon Control**: Implements receding horizon optimization for real-time decision making  
• 🔧 **Multiple Solver Support**: Compatible with both open-source (python-mip/CBC) and commercial (Gurobi) solvers  
• 📈 **Reserve Market Integration**: Supports upregulation and downregulation market participation  
• ⚙️ **Flexible Constraints**: Configurable demand advance/delay limits and transfer rates

## Requirements

• Python 3.12 or higher  
• NumPy and Pandas for data handling  
• tqdm for progress tracking  
• One of the following solvers:
  - **python-mip** (open-source, uses CBC solver)  
  - **Gurobi** (commercial, requires license)

## How It Works - Moving Horizon Transfer Optimization

The optimization engine uses a **moving horizon control** strategy with a **transfer matrix approach** to determine optimal energy movement between time periods. Each optimization horizon looks ahead `X` hours and makes decisions for a control period (typically 24 hours), then rolls forward to the next decision point.

<div align="center">
  <img src="assets/transfer_matrix_animation.gif" alt="Transfer Matrix Animation" width="600"/>
</div>

### Moving Horizon Concept

The moving horizon controller divides time into overlapping optimization windows:

```
Timeline: [Past Hours] [Control Period] [Lookahead Period]
          └─────────┘  └──────────────┘ └───────────────┘
          Fixed from    Current         Future hours
          previous      decisions       (constraints only)
          optimization  (optimized)
```

**Key Time Periods:**
- **Lookback Hours**: Historical decisions from previous optimizations (fixed constraints)
- **Control Period**: Hours being actively optimized (typically 24 hours) 
- **Lookahead Period**: Future hours providing price/demand context (48+ hours total)
- **Spillover Effects**: Energy transfers from control period that affect future hours

### Transfer Matrix Operation

Within each horizon, the optimization uses a transfer matrix `T[i,j]` to determine energy movement:

```
T[i,j] = Amount of energy originally demanded at time i,
         but purchased at time j to minimize total costs
```

**Physical Constraints:**
- **Demand Advance**: Can buy energy up to `max_demand_advance` hours early
- **Demand Delay**: Can buy energy up to `max_demand_delay` hours late  
- **Transfer Limits**: Maximum energy transfer per hour (`max_hourly_purchase`)
- **Rate Limits**: Maximum transfer rate (`max_rate`)

**Example Horizon Optimization:**
```python
# Hour:           [0, 1, 2, 3, 4, 5, 6, 7, 8]  (Local time)
# Global Index:   [3, 4, 5, 6, 7, 8, 9,10,11]  (Absolute position)
# Type:           [←─Control─→] [←─Lookahead─→]
Original demand:  [10,15, 8,12, 6, 9,14,11, 7] kWh
Energy prices:    [30,80,20,40,25,35,75,30,45] ct/kWh

# Optimal strategy: Move 10 kWh from expensive hour 1 (80 ct) to cheap hour 2 (20 ct)
Transfer matrix: T[4,5] = 10 kWh  (from global index 4 to 5)
Optimized demand: [10, 5,18,12, 6, 9,14,11, 7] kWh
Cost reduction:   10×(80-20) = 600 ct savings
```

### Horizon Rolling Process

The moving horizon algorithm works as follows:

1. **Decision Point**: At each daily decision hour (e.g., 6 AM)
2. **Horizon Setup**: Create optimization window (e.g., 48 hours ahead)
3. **Constraint Integration**: Apply spillover effects from previous optimization
4. **Matrix Optimization**: Solve transfer matrix to minimize costs
5. **Implementation**: Execute control period decisions (24 hours)
6. **Spillover Tracking**: Save energy transfers affecting future periods
7. **Roll Forward**: Move to next decision point and repeat

### Objective Function

Each horizon minimizes total energy costs:
```
Minimize: Σ[purchase[t] * price[t] + pos_dev[t] * down_price[t] -
              neg_dev[t] * up_price[t]]
```

Where:
- `purchase[t]`: actual energy purchased at time t
- `pos_dev[t]`: max(0, purchase[t] - reference[t]) (consuming more than reference)
- `neg_dev[t]`: max(0, reference[t] - purchase[t]) (consuming less than reference)
- `reference[t]`: target consumption profile (defaults to demand[t])
- `price[t]`: spot price (e.g., day-ahead market price)
- `down_price[t]`: downregulation price deviation from spot (≤0, discount)
- `up_price[t]`: upregulation price deviation from spot (≥0, payment)

Reserve Market Context:

    - Downregulation: Consuming more (pos_dev) gets discount: down_price[t] < 0
    - Upregulation: Consuming less (neg_dev) earns payment: -up_price[t] < 0

This approach enables **real-time decision making** while maintaining **global cost optimization** across multiple days of operation.

## Installation

### From PyPI (recommended)

To use `demand-response` in your project, install it from PyPI:

```bash
pip install demand-response
```

### From source (for examples and development)

If you want to explore the examples or contribute to the project, follow these
steps to install from source:

```bash
# Clone repository
git clone https://github.com/ahmadimam657/demand-response.git
cd demand-response

# Install package and development dependencies
uv sync
```
## Basic Usage

Optimize energy demand using simple function calls. You first create a `VirtualStorage` instance with your configuration, then either run single optimization or use the moving horizon controller for multi-period optimization.

### Configuration Options

The configuration dict supports four main sections:

• `daily_decision_hour`: Hour of day (0-23) for making optimization decisions  
• `n_lookahead_hours`: Length of optimization horizon (≥24 hours)  
• `virtual_storage`: Core settings for the virtual storage model  
• `solver_params`: Optional solver-specific parameters

You can view example configurations by checking the test files

### Simple Optimization Example

```python
import numpy as np
from demand_response import VirtualStorage
# Create pyramid price profile (9 values, peak in middle)
prices = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 4.0, 3.0, 2.0, 1.0])

# Create single peak demand at the center (time index 4)
demand = np.array([0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0])

storage = VirtualStorage(
    max_demand_advance=2,
    max_demand_delay=3,
    max_hourly_purchase=1.0,
    max_rate=1.0,
    solver='mip',
)

result = storage.optimize_demand(prices, demand)
optimized_demand = result["optimal_demand"]

```
Repository layout
================

```
├── src/demand_response/      # Library code
│   ├── __init__.py
│   ├── virtual_storage.py    # Core MILP optimization
│   ├── moving_horizon.py     # Multi-period controller
│   ├── solver_adapters.py    # Unified solver interface
│   ├── time_ranges.py        # Time indexing utilities
│   ├── transfer_indices.py   # Transfer matrix operations
│   └── utils.py             # Logging and utilities
├── tests/                   # Test suite
├── assets/                  # Documentation assets
│   ├── logo.svg
│   └── transfer_matrix_animation.gif
├── data/                    # Data files
├── examples/                # Usage examples
└── pyproject.toml          # Package configuration
```

## Development

Before committing or pushing run:

```bash
uv run ruff check .
uv run pytest
uv run pytest --cov=demand_response  # With coverage
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_virtual_storage.py

# Run with coverage
uv run pytest --cov=demand_response --cov-report=html
```

## Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/{some_name}`)
3. Make your changes
4. Run the test suite (`uv run pytest`)
5. Commit your changes (`git commit -m 'Add {some_name} feature'`)
6. Push to the branch (`git push origin feature/{some_name}`)
7. Open a Pull Request

Please ensure your code follows our style guidelines:

• Use Ruff for code formatting and linting  
• Include type annotations for all functions  
• Add tests for new functionality  
• Update documentation for API changes  
• Follow existing code patterns and conventions

## License

This project is released under the [MIT License](LICENSE).

## Authors

**Hafiz Muhammad Ahmad Imam**, **Johan Westö**

## Additional Links

- [Code](https://github.com/ahmadimam657/demand-response)
- [Issues](https://github.com/ahmadimam657/demand-response/issues)
- [Pull requests](https://github.com/ahmadimam657/demand-response/pulls)