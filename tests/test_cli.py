from contextlib import redirect_stderr, redirect_stdout
import io
import json
import subprocess
import sys
import unittest

from jurofaro.cli import main


class CliTests(unittest.TestCase):
    base = ["--property-price", "1200", "--down-payment", "200", "--annual-rate", "0", "--months", "2"]

    def invoke(self, args):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            status = main(args)
        return status, out.getvalue(), err.getvalue()

    def test_simulate_json(self):
        status, out, err = self.invoke(["simulate", *self.base, "--format", "json"])
        self.assertEqual(status, 0, err)
        data = json.loads(out)
        self.assertEqual(data["mortgage"]["principal"], 1000)
        self.assertEqual(data["summary"]["total_installments"], 1000)
        self.assertEqual(len(data["mortgage"]["schedule"]), 2)

    def test_compare_json(self):
        status, out, err = self.invoke(["compare", *self.base, "--rent", "100", "--format", "json"])
        self.assertEqual(status, 0, err)
        self.assertEqual(json.loads(out)["summary"]["wealth_difference"], 200)

    def test_invalid_values_return_error_without_traceback(self):
        for extra in (["--down-payment", "1300"], ["--annual-rate", "nan"],
                      ["--down-payment", "-1"], ["--months", "0"], ["--annual-rate", "-2"]):
            with self.subTest(extra=extra):
                status, out, err = self.invoke(["simulate", *self.base, *extra])
                self.assertEqual(status, 2)
                self.assertEqual(out, "")
                self.assertIn("Erro:", err)

    def test_module_entrypoint_real_process(self):
        completed = subprocess.run(
            [sys.executable, "-m", "jurofaro", "simulate", *self.base, "--system", "price", "--schedule"],
            text=True, capture_output=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("Financiamento PRICE", completed.stdout)
        self.assertIn("Saldo devedor", completed.stdout)

    def test_compare_text_discloses_assumptions(self):
        status, out, err = self.invoke(["compare", *self.base, "--rent", "100", "--schedule"])
        self.assertEqual(status, 0, err)
        self.assertIn("Capital inicial igual", out)
        self.assertIn("Valores nominais", out)
        self.assertIn("Aporte locatário", out)
