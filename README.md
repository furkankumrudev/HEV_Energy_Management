# HEV Fuzzy Energy Management

A Mamdani fuzzy supervisory controller for a simplified hybrid-electric-vehicle 
power-split decision. Equivalent MATLAB, `.fis`, and pure-Python
implementations are included and kept synchronized by regression tests.

## Highlights

- Three inputs: battery state of charge, normalized positive torque demand,
  and estimated remaining trip distance.
- One normalized output representing the electric-motor contribution.
- Twelve triangular membership functions and a complete 27-rule base.
- MATLAB Fuzzy Logic Toolbox and independent NumPy implementations.
- Scenario, operating-grid, and MATLAB/FIS/Python parity checks.

## Repository contents

| Path | Purpose |
| --- | --- |
| `HEV_Energy_Management.m` | Builds and evaluates the MATLAB Mamdani FIS. |
| `HEV_Energy_Management.fis` | Portable fuzzy-controller definition. |
| `HEV_Energy_Management_tests.m` | MATLAB scenario and grid regression checks. |
| `hev_energy_management.py` | Independent NumPy Mamdani implementation and CLI. |
| `test_hev_energy_management.py` | Python regression and FIS parity tests. |
| `generate_report_figures.m` | Recreates MATLAB figures used by the report. |
| `docs/HEV_Fuzzy_Energy_Management_Report.docx` | Corrected technical report. |

## Requirements

- MATLAB and Fuzzy Logic Toolbox for the MATLAB implementation.
- Python 3.10+ and NumPy for the independent Python implementation.

## Inputs and output

- `SoC`: battery state of charge, 0-100 percent.
- `Torque`: normalized positive traction-torque demand, 0-100 percent.
- `Trip_Distance`: estimated remaining trip distance, 0-200 km.
- `Power_Split`: electric-motor contribution ratio, 0-1.
  - Values near 0: ICE-dominant / battery-charging operation.
  - Values near 0.5: hybrid operation.
  - Values near 1: electric-dominant operation.

## MATLAB implementation

Run `HEV_Energy_Management.m` to build the controller, display reference
scenarios, write `HEV_Energy_Management.fis`, and open Fuzzy Logic Designer in
an interactive desktop session.

Run `HEV_Energy_Management_tests.m` to check eight reference scenarios and a
representative 1,331-point operating grid. The code uses the current
`fuzzyLogicDesigner` entry point rather than the legacy `ruleview` and
`surfview` functions.

Generate reproducible report figures with `generate_report_figures.m`. Output
is written to the ignored `report_figures/` directory.

## Python implementation

Create a virtual environment and install the dependency:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Evaluate one operating point:

```powershell
python hev_energy_management.py --soc 60 --torque 60 --trip-distance 100
```

Running the module without arguments prints all built-in reference scenarios:

```powershell
python hev_energy_management.py
```

Run the Python regression and MATLAB/FIS parity tests:

```powershell
python -m unittest -v test_hev_energy_management.py
```

The Python implementation does not require MATLAB or `scikit-fuzzy`. NumPy is
used to reproduce the same triangular membership functions, min implication,
max aggregation, 27-rule Mamdani inference, and centroid defuzzification.

## Technical report

The corrected report is available at
[`docs/HEV_Fuzzy_Energy_Management_Report.docx`](docs/HEV_Fuzzy_Energy_Management_Report.docx).
It documents the controller definition, rule base, scenarios, limitations,
and references.

## Limitations

This is a static supervisory prototype, not a complete closed-loop HEV model.
It does not model longitudinal vehicle dynamics, regenerative braking,
component efficiency maps, fuel consumption, emissions, actuator constraints,
or battery ageing. The included tests validate controller logic and numerical
bounds, not vehicle-level fuel economy or durability improvements.

## Citation

Academic users can cite the project using the metadata in `CITATION.cff`.
Contribution guidance is available in `CONTRIBUTING.md`.
