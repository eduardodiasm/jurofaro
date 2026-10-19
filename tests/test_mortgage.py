import math
import unittest

from jurofaro import annual_to_monthly, monthly_to_annual, simulate_mortgage


class RatesTests(unittest.TestCase):
    def test_effective_conversion_reference(self):
        # (1 + 1% a.m.)**12 - 1 = 12,68250301319698% a.a.
        self.assertAlmostEqual(monthly_to_annual(0.01), 0.1268250301319698)
        self.assertAlmostEqual(annual_to_monthly(0.1268250301319698), 0.01)
        self.assertNotAlmostEqual(annual_to_monthly(0.12), 0.12 / 12)

    def test_zero_negative_and_invalid_rates(self):
        self.assertEqual(annual_to_monthly(0), 0)
        self.assertAlmostEqual(monthly_to_annual(annual_to_monthly(-0.2)), -0.2)
        for rate in (-1, -2, math.inf, math.nan, True):
            with self.subTest(rate=rate):
                with self.assertRaises(ValueError):
                    annual_to_monthly(rate)


class MortgageTests(unittest.TestCase):
    def test_sac_hand_calculation(self):
        loan = simulate_mortgage(1200, 0.01, 3, "SAC")
        self.assertEqual([r.amortization for r in loan.schedule], [400, 400, 400])
        self.assertEqual([r.interest for r in loan.schedule], [12, 8, 4])
        self.assertEqual([r.payment for r in loan.schedule], [412, 408, 404])
        self.assertEqual([r.balance for r in loan.schedule], [800, 400, 0])
        self.assertEqual(loan.total_interest, 24)
        self.assertEqual(loan.total_paid, 1224)

    def test_price_two_month_reference_and_present_value(self):
        # 100 = A/1.1 + A/1.1**2 => A = 121/2.1.
        loan = simulate_mortgage(100, 0.1, 2, "price")
        self.assertAlmostEqual(loan.schedule[0].payment, 57.61904761904762)
        self.assertAlmostEqual(loan.schedule[1].payment, 57.61904761904762)
        self.assertAlmostEqual(loan.schedule[0].amortization, 47.61904761904762)
        self.assertAlmostEqual(loan.total_interest, 15.23809523809524)
        pv = sum(r.payment / 1.1 ** r.month for r in loan.schedule)
        self.assertAlmostEqual(pv, 100)

    def test_zero_rate_and_cash_purchase(self):
        for system in ("SAC", "PRICE"):
            loan = simulate_mortgage(1200, 0, 3, system)
            self.assertEqual([r.payment for r in loan.schedule], [400, 400, 400])
            self.assertEqual(loan.total_interest, 0)
            self.assertEqual(simulate_mortgage(0, 0.01, 12, system).total_paid, 0)

    def test_one_month(self):
        for system in ("SAC", "PRICE"):
            row = simulate_mortgage(100, 0.01, 1, system).schedule[0]
            self.assertEqual((row.payment, row.interest, row.amortization, row.balance), (101, 1, 100, 0))

    def test_realistic_invariants(self):
        for system in ("SAC", "PRICE"):
            loan = simulate_mortgage(400_000, annual_to_monthly(0.12), 360, system)
            self.assertEqual(len(loan.schedule), 360)
            self.assertAlmostEqual(math.fsum(r.amortization for r in loan.schedule), 400_000, places=6)
            self.assertAlmostEqual(loan.total_paid, 400_000 + loan.total_interest, places=6)
            previous = 400_000
            for row in loan.schedule:
                self.assertAlmostEqual(row.interest, previous * loan.monthly_rate, places=7)
                self.assertAlmostEqual(previous - row.amortization, row.balance, places=7)
                self.assertGreaterEqual(row.balance, 0)
                previous = row.balance
            self.assertEqual(previous, 0)
            if system == "PRICE":
                self.assertLess(max(r.payment for r in loan.schedule) - min(r.payment for r in loan.schedule), 1e-5)
            else:
                self.assertAlmostEqual(loan.total_interest, 400_000 * loan.monthly_rate * 361 / 2, places=6)
                self.assertTrue(all(a.payment >= b.payment for a, b in zip(loan.schedule, loan.schedule[1:])))

    def test_tiny_rate_is_stable(self):
        loan = simulate_mortgage(1200, 1e-15, 12, "PRICE")
        self.assertAlmostEqual(loan.schedule[0].payment, 100)
        self.assertEqual(loan.schedule[-1].balance, 0)

    def test_invalid_inputs(self):
        for principal, rate, months, system in [
            (-1, 0, 12, "SAC"), (100, -0.01, 12, "SAC"),
            (100, 0, 0, "SAC"), (100, 0, 1.5, "SAC"), (100, 0, True, "SAC"),
            (math.nan, 0, 12, "SAC"), (100, math.inf, 12, "SAC"), (100, 0, 12, "OTHER"),
        ]:
            with self.subTest(params=(principal, rate, months, system)):
                with self.assertRaises(ValueError):
                    simulate_mortgage(principal, rate, months, system)
