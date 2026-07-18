"""Pure-Python Mamdani controller matching HEV_Energy_Management.fis.

The implementation intentionally depends only on NumPy. It uses the same
three inputs, triangular membership functions, 27 rules, min implication,
max aggregation, and centroid defuzzification as the MATLAB controller.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import Iterable

import numpy as np


@dataclass(frozen=True)
class MembershipFunction:
    name: str
    parameters: tuple[float, float, float]


@dataclass(frozen=True)
class Variable:
    name: str
    minimum: float
    maximum: float
    memberships: tuple[MembershipFunction, ...]


INPUTS = (
    Variable(
        "SoC",
        0.0,
        100.0,
        (
            MembershipFunction("Low", (0.0, 0.0, 40.0)),
            MembershipFunction("Medium", (30.0, 50.0, 70.0)),
            MembershipFunction("High", (60.0, 100.0, 100.0)),
        ),
    ),
    Variable(
        "Torque",
        0.0,
        100.0,
        (
            MembershipFunction("Cruising", (0.0, 0.0, 40.0)),
            MembershipFunction("Accelerating", (30.0, 60.0, 80.0)),
            MembershipFunction("Heavy_Load", (70.0, 100.0, 100.0)),
        ),
    ),
    Variable(
        "Trip_Distance",
        0.0,
        200.0,
        (
            MembershipFunction("Short", (0.0, 0.0, 30.0)),
            MembershipFunction("Medium", (20.0, 60.0, 100.0)),
            MembershipFunction("Long", (80.0, 200.0, 200.0)),
        ),
    ),
)

OUTPUT = Variable(
    "Power_Split",
    0.0,
    1.0,
    (
        MembershipFunction("Electric", (0.6, 1.0, 1.0)),
        MembershipFunction("Hybrid", (0.3, 0.5, 0.7)),
        MembershipFunction("ICE_Charge", (0.0, 0.0, 0.4)),
    ),
)

# Each rule is ((SoC MF, Torque MF, Trip MF), Output MF). Indices are 1-based
# to stay directly comparable with the MATLAB rule matrix and .fis file.
RULES = (
    ((1, 1, 1), 3), ((1, 1, 2), 3), ((1, 1, 3), 3),
    ((1, 2, 1), 3), ((1, 2, 2), 3), ((1, 2, 3), 3),
    ((1, 3, 1), 3), ((1, 3, 2), 3), ((1, 3, 3), 3),
    ((2, 1, 1), 1), ((2, 1, 2), 1), ((2, 1, 3), 2),
    ((2, 2, 1), 2), ((2, 2, 2), 2), ((2, 2, 3), 2),
    ((2, 3, 1), 2), ((2, 3, 2), 3), ((2, 3, 3), 3),
    ((3, 1, 1), 1), ((3, 1, 2), 1), ((3, 1, 3), 2),
    ((3, 2, 1), 1), ((3, 2, 2), 2), ((3, 2, 3), 2),
    ((3, 3, 1), 2), ((3, 3, 2), 2), ((3, 3, 3), 3),
)

REFERENCE_SCENARIOS = (
    ("Low SoC / acceleration / long trip", (10.0, 60.0, 180.0)),
    ("Medium SoC / cruise / long trip", (50.0, 10.0, 180.0)),
    ("Medium SoC / acceleration / long trip", (50.0, 60.0, 180.0)),
    ("High SoC / cruise / short trip", (90.0, 10.0, 10.0)),
    ("High SoC / heavy load / long trip", (90.0, 90.0, 180.0)),
    ("Report reference scenario", (60.0, 60.0, 100.0)),
)


def triangular_membership(
    values: np.ndarray | float,
    parameters: tuple[float, float, float],
) -> np.ndarray:
    """Evaluate a triangular membership function, including shoulder cases."""

    x = np.asarray(values, dtype=float)
    a, b, c = parameters
    result = np.zeros_like(x, dtype=float)

    if a == b:
        result[x == a] = 1.0
        descending = (x > b) & (x <= c)
        result[descending] = (c - x[descending]) / (c - b)
    elif b == c:
        ascending = (x >= a) & (x < b)
        result[ascending] = (x[ascending] - a) / (b - a)
        result[x == c] = 1.0
    else:
        ascending = (x >= a) & (x <= b)
        descending = (x >= b) & (x <= c)
        result[ascending] = (x[ascending] - a) / (b - a)
        result[descending] = np.maximum(
            result[descending],
            (c - x[descending]) / (c - b),
        )

    return np.clip(result, 0.0, 1.0)


def _trapezoid(values: np.ndarray, grid: np.ndarray) -> float:
    integration = getattr(np, "trapezoid", None)
    if integration is None:
        integration = np.trapz
    return float(integration(values, grid))


class HEVEnergyManagementController:
    """Mamdani HEV supervisory controller with centroid defuzzification."""

    def __init__(self, output_samples: int = 1001) -> None:
        if output_samples < 101:
            raise ValueError("output_samples must be at least 101.")
        self.output_grid = np.linspace(OUTPUT.minimum, OUTPUT.maximum, output_samples)
        self.output_memberships = np.stack(
            [
                triangular_membership(self.output_grid, membership.parameters)
                for membership in OUTPUT.memberships
            ]
        )

    @staticmethod
    def _validate(samples: np.ndarray) -> None:
        if samples.ndim != 2 or samples.shape[1] != len(INPUTS):
            raise ValueError("Inputs must have shape (3,) or (n, 3): SoC, Torque, Trip_Distance.")
        if not np.isfinite(samples).all():
            raise ValueError("All input values must be finite.")
        for index, variable in enumerate(INPUTS):
            outside = (samples[:, index] < variable.minimum) | (
                samples[:, index] > variable.maximum
            )
            if outside.any():
                raise ValueError(
                    f"{variable.name} must be within "
                    f"[{variable.minimum:g}, {variable.maximum:g}]."
                )

    def evaluate(self, values: Iterable[float] | np.ndarray) -> float | np.ndarray:
        """Return the electric-motor contribution for one or more input rows."""

        samples = np.asarray(values, dtype=float)
        single_sample = samples.ndim == 1
        if single_sample:
            samples = samples.reshape(1, -1)
        self._validate(samples)

        results = np.empty(samples.shape[0], dtype=float)
        for sample_index, sample in enumerate(samples):
            input_degrees = [
                np.array(
                    [
                        triangular_membership(sample[index], membership.parameters).item()
                        for membership in variable.memberships
                    ]
                )
                for index, variable in enumerate(INPUTS)
            ]

            aggregate = np.zeros_like(self.output_grid)
            for antecedents, consequence in RULES:
                strength = min(
                    input_degrees[input_index][membership_index - 1]
                    for input_index, membership_index in enumerate(antecedents)
                )
                if strength > 0.0:
                    implied = np.minimum(
                        strength,
                        self.output_memberships[consequence - 1],
                    )
                    aggregate = np.maximum(aggregate, implied)

            denominator = _trapezoid(aggregate, self.output_grid)
            if denominator <= np.finfo(float).eps:
                raise RuntimeError("No fuzzy rule was activated for the supplied input.")
            numerator = _trapezoid(aggregate * self.output_grid, self.output_grid)
            results[sample_index] = numerator / denominator

        return float(results[0]) if single_sample else results

    @staticmethod
    def operating_mode(power_share: float) -> str:
        """Convert the continuous output to a readable supervisory mode."""

        if not 0.0 <= power_share <= 1.0:
            raise ValueError("power_share must be within [0, 1].")
        if power_share < 0.35:
            return "ICE-dominant / charging"
        if power_share > 0.65:
            return "Electric-dominant"
        return "Hybrid"


def _print_result(
    controller: HEVEnergyManagementController,
    label: str,
    values: tuple[float, float, float],
) -> None:
    power_share = controller.evaluate(values)
    print(
        f"{label}: SoC={values[0]:g}%, torque={values[1]:g}%, "
        f"trip={values[2]:g} km -> electric share={power_share:.6f} "
        f"({controller.operating_mode(power_share)})"
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluate the HEV Mamdani fuzzy energy-management controller."
    )
    parser.add_argument("--soc", type=float, help="Battery state of charge in percent.")
    parser.add_argument("--torque", type=float, help="Normalized positive torque demand in percent.")
    parser.add_argument("--trip-distance", type=float, help="Estimated remaining trip distance in km.")
    parser.add_argument(
        "--all-scenarios",
        action="store_true",
        help="Print the built-in reference scenarios.",
    )
    arguments = parser.parse_args()

    supplied = [arguments.soc, arguments.torque, arguments.trip_distance]
    if any(value is not None for value in supplied) and not all(
        value is not None for value in supplied
    ):
        parser.error("--soc, --torque, and --trip-distance must be supplied together.")
    if arguments.all_scenarios and all(value is not None for value in supplied):
        parser.error("--all-scenarios cannot be combined with a single operating point.")

    controller = HEVEnergyManagementController()
    if all(value is not None for value in supplied):
        values = (arguments.soc, arguments.torque, arguments.trip_distance)
        _print_result(controller, "Requested scenario", values)
    else:
        for label, values in REFERENCE_SCENARIOS:
            _print_result(controller, label, values)


if __name__ == "__main__":
    main()
