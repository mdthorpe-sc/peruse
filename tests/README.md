# Tests Directory

This directory contains test scripts for the Screenshot Monitor project.

## Available Tests

### `test_cache_performance.py`
Performance testing script that measures configuration loading times and validates caching optimizations.

**Features:**
- Measures baseline performance without caching
- Detects and reports performance improvements when caching is implemented
- Validates functionality to ensure optimizations don't break existing features
- Provides optimization tips and recommendations

**Usage:**
```bash
# Run from project root
python tests/test_cache_performance.py

# Or run from tests directory
cd tests
python test_cache_performance.py
```

**Sample Output:**
```
🧪 Testing Model Configuration Loading Performance
Caching Implementation: ❌ Not Implemented
Testing 10 consecutive configuration loads...
Load  1: 2087.61ms ✅
Load  2: 2017.71ms ✅
...
Performance ratio: 1.0x
📈 Minimal performance difference
```

## Running All Tests

To run all tests in the directory:

```bash
# From project root
python -m pytest tests/

# Or run individual tests
python tests/test_cache_performance.py
```

## Test Categories

- **Performance Tests**: Measure execution time and resource usage
- **Functionality Tests**: Validate that features work as expected
- **Integration Tests**: Test interactions between components

## Adding New Tests

When adding new test files:
1. Follow the naming convention: `test_*.py`
2. Include docstrings explaining the test purpose
3. Add usage instructions to this README
4. Ensure tests can run from both project root and tests directory 