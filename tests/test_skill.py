"""O contrato da skill é chamar o mesmo motor, sem instalação ou diretório fixo."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


RUNNER = Path(__file__).resolve().parents[1] / ".agents/skills/jurofaro/scripts/run.py"


class SkillExecutionTests(unittest.TestCase):
    base = ["--property-price", "1200", "--down-payment", "200",
            "--annual-rate", "0", "--months", "2", "--format", "json"]

    def run_skill(self, command, *extra):
        with tempfile.TemporaryDirectory() as directory:
            # -I ignora PYTHONPATH; -S desabilita site-packages. O runner precisa
            # encontrar o motor no clone, sem depender da instalação editável.
            return subprocess.run(
                [sys.executable, "-I", "-S", str(RUNNER), command, *self.base, *extra],
                cwd=directory, capture_output=True, text=True,
            )

    def test_simulation_without_installation_from_another_directory(self):
        result = self.run_skill("simulate", "--system", "PRICE")
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["mortgage"]["system"], "PRICE")
        self.assertEqual(report["summary"]["first_payment"], 500)
        self.assertEqual(report["summary"]["total_installments"], 1000)

    def test_comparison_matches_manual_reference(self):
        result = self.run_skill("compare", "--rent", "100")
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["summary"], {
            "buyer_wealth": 1200, "renter_wealth": 1000, "wealth_difference": 200,
        })

    def test_invalid_budget_propagates_failure_without_fake_json(self):
        result = self.run_skill("compare", "--rent", "100", "--monthly-budget", "400")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertIn("orçamento mensal insuficiente", result.stderr)

    def test_user_installation_symlink_keeps_engine_location(self):
        with tempfile.TemporaryDirectory() as directory:
            linked_skill = Path(directory) / "jurofaro"
            linked_skill.symlink_to(RUNNER.parent.parent, target_is_directory=True)
            result = subprocess.run(
                [sys.executable, "-I", "-S", str(linked_skill / "scripts/run.py"),
                 "simulate", *self.base],
                cwd=directory, capture_output=True, text=True,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["summary"]["first_payment"], 500)
