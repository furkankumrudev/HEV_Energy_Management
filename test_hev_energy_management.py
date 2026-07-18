"""Regression tests for the pure-Python HEV fuzzy controller."""

from __future__ import annotations

import itertools
import re
import unittest
from pathlib import Path

import numpy as np

from hev_energy_management import (
    HEVEnergyManagementController,
    INPUTS,
    OUTPUT,
    RULES,
)


class ControllerRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.controller = HEVEnergyManagementController()

    def test_reference_scenarios(self) -> None:
        inputs = np.array(
            [
                [0, 60, 200],
                [50, 0, 0],
                [50, 0, 200],
                [50, 60, 200],
                [100, 0, 0],
                [100, 0, 200],
                [100, 100, 200],
                [60, 60, 100],
            ],
            dtype=float,
        )
        actual = self.controller.evaluate(inputs)
        expected = np.array(
            [0.1333325, 0.8666675, 0.5, 0.5, 0.8666675, 0.5, 0.1333325, 0.5]
        )

        self.assertLess(actual[0], 0.25)
        self.assertGreater(actual[1], 0.75)
        self.assertTrue(0.35 < actual[2] < 0.65)
        self.assertTrue(0.35 < actual[3] < 0.65)
        self.assertGreater(actual[4], 0.75)
        self.assertTrue(0.35 < actual[5] < 0.65)
        self.assertLess(actual[6], 0.25)
        self.assertAlmostEqual(actual[7], 0.5, places=6)
        np.testing.assert_allclose(actual, expected, rtol=0.0, atol=2e-6)

    def test_representative_grid_is_finite_and_bounded(self) -> None:
        grid = np.array(
            list(
                itertools.product(
                    range(0, 101, 10),
                    range(0, 101, 10),
                    range(0, 201, 20),
                )
            ),
            dtype=float,
        )
        actual = self.controller.evaluate(grid)

        self.assertEqual(len(actual), 1331)
        self.assertTrue(np.isfinite(actual).all())
        self.assertTrue(((0.0 <= actual) & (actual <= 1.0)).all())

    def test_invalid_input_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "SoC"):
            self.controller.evaluate([-1, 50, 50])
        with self.assertRaisesRegex(ValueError, "shape"):
            self.controller.evaluate([50, 50])

    def test_rule_base_is_complete(self) -> None:
        antecedents = {rule[0] for rule in RULES}
        self.assertEqual(len(RULES), 27)
        self.assertEqual(antecedents, set(itertools.product(range(1, 4), repeat=3)))


class FisParityTests(unittest.TestCase):
    def test_python_definition_matches_fis_file(self) -> None:
        fis_text = Path(__file__).with_name("HEV_Energy_Management.fis").read_text(
            encoding="utf-8-sig"
        )
        variables = (*INPUTS, OUTPUT)
        section_names = ("Input1", "Input2", "Input3", "Output1")

        for section_name, variable in zip(section_names, variables):
            block = re.search(
                rf"\[{section_name}\](.*?)(?=\n\[|\Z)",
                fis_text,
                re.DOTALL,
            ).group(1)
            self.assertIn(f"Name='{variable.name}'", block)
            parsed = [
                (name, tuple(float(value) for value in parameters.split()))
                for name, parameters in re.findall(
                    r"MF\d+='([^']+)':'trimf',\[([^]]+)\]",
                    block,
                )
            ]
            expected = [
                (membership.name, membership.parameters)
                for membership in variable.memberships
            ]
            self.assertEqual(parsed, expected)

        rule_block = re.search(r"\[Rules\](.*)\Z", fis_text, re.DOTALL).group(1)
        parsed_rules = [
            ((int(a), int(b), int(c)), int(output_index))
            for a, b, c, output_index in re.findall(
                r"^(\d+)\s+(\d+)\s+(\d+),\s+(\d+)",
                rule_block,
                re.MULTILINE,
            )
        ]
        self.assertEqual(tuple(parsed_rules), RULES)


if __name__ == "__main__":
    unittest.main()
