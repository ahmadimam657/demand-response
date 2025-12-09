<div align="center">
  <img src="assets/logo2.svg" alt="Demand Response Logo" width="400" height="400"/>
</div>
<div align="center">

# Energy demand response optimization using virtual storage modeling

![Python](https://img.shields.io/badge/python-3.12%2B-blue)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
<!-- [![PyPI version](https://badge.fury.io/py/demand-response.svg)](https://badge.fury.io/py/demand-response) -->
[![Ruff Lint](https://github.com/NoviaIntSysGroup/mpl-panel-builder/actions/workflows/lint.yml/badge.svg)](https://github.com/NoviaIntSysGroup/mpl-panel-builder/actions/workflows/lint.yml)
[![Tests](https://github.com/ahmadimam657/demand-response/actions/workflows/tests.yml/badge.svg)](https://github.com/ahmadimam657/demand-response/actions/workflows/tests.yml)

</div>

`demand-response` helps you optimize energy costs by intelligently shifting electricity demand across time periods using Mixed Integer Linear Programming (MILP). The library minimizes total purchasing costs while respecting physical and operational constraints through flexible demand scheduling.

## Example

## Requirements

• Python 3.12 or higher  
• NumPy and Pandas for data handling  
• tqdm for progress tracking  
• One of the following solvers:
  - **python-mip** (open-source, uses CBC solver)  
  - **Gurobi** (commercial, requires license)
  
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