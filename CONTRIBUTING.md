# Contributing

Contributions that improve controller validation, documentation, or parity
between the MATLAB, FIS, and Python implementations are welcome.

## Development setup

1. Create and activate a Python 3.10+ virtual environment.
2. Install dependencies with `python -m pip install -r requirements.txt`.
3. Run `python -m unittest -v test_hev_energy_management.py`.

Keep the definitions in `HEV_Energy_Management.m`,
`HEV_Energy_Management.fis`, and `hev_energy_management.py` synchronized.
The parity test must pass whenever membership functions or rules change.

MATLAB changes should also be checked with `HEV_Energy_Management_tests.m`
when MATLAB and Fuzzy Logic Toolbox are available.
