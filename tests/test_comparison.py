import math
import unittest

from jurofaro import compare_buy_rent, monthly_to_annual


class ComparisonTests(unittest.TestCase):
    def test_hand_calculated_equal_budget(self):
        # Imóvel 1200; entrada 200; principal 1000; 2 parcelas sem juros de 500.
        # Aluguel 100: locatário investe 200 + 2*(500-100) = 1000.
        result = compare_buy_rent(1200, 200, 0, 2, 100)
        self.assertEqual(result.initial_capital, 200)
        final = result.schedule[-1]
        self.assertEqual(final.buyer_wealth, 1200)
        self.assertEqual(final.renter_wealth, 1000)
        self.assertEqual(result.wealth_difference, 200)

    def test_acquisition_sale_and_owner_costs(self):
        # Entrada 200 + aquisição 120: locatário começa com 320.
        # Prestação 1000 + manutenção 12, aluguel 100 => aporte locatário 912.
        # Comprador termina com imóvel líquido de 120 = 1080.
        result = compare_buy_rent(1200, 200, 0, 1, 100,
                                  purchase_cost_rate=0.1, sale_cost_rate=0.1,
                                  annual_owner_cost_rate=0.12)
        final = result.schedule[0]
        self.assertEqual(result.initial_capital, 320)
        self.assertEqual(final.owner_cost, 12)
        self.assertEqual(final.renter_wealth, 1232)
        self.assertEqual(final.buyer_wealth, 1080)
        self.assertEqual(result.wealth_difference, -152)

    def test_interest_before_end_of_month_contribution(self):
        result = compare_buy_rent(1200, 200, 0, 2, 100,
                                  annual_investment_return=monthly_to_annual(0.1))
        self.assertAlmostEqual(result.schedule[0].renter_investments, 200 * 1.1 + 400)
        self.assertAlmostEqual(result.schedule[1].renter_investments, 620 * 1.1 + 400)

    def test_rent_exceeding_payment_invests_for_buyer(self):
        result = compare_buy_rent(1200, 200, 0, 2, 600)
        self.assertEqual(result.schedule[-1].buyer_investments, 200)
        self.assertEqual(result.schedule[-1].renter_investments, 200)
        self.assertEqual(result.schedule[-1].buyer_wealth, 1400)
        self.assertTrue(all(r.budget == 600 for r in result.schedule))

    def test_short_horizon_subtracts_remaining_debt(self):
        final = compare_buy_rent(1200, 200, 0, 2, 100, horizon_months=1).schedule[-1]
        self.assertEqual(final.debt, 500)
        self.assertEqual(final.buyer_wealth, 700)
        self.assertEqual(final.renter_wealth, 600)

    def test_after_repayment_buyer_invests_rent_sized_budget(self):
        result = compare_buy_rent(1200, 200, 0, 2, 100, horizon_months=3)
        final = result.schedule[-1]
        self.assertEqual(final.debt, 0)
        self.assertEqual(final.mortgage_payment, 0)
        self.assertEqual(final.buyer_contribution, 100)
        self.assertEqual(final.buyer_wealth, 1300)
        self.assertEqual(final.renter_wealth, 1000)

    def test_fixed_budget_and_equal_cash_flow_identity(self):
        result = compare_buy_rent(1200, 200, 0.01, 2, 100, monthly_budget=1000)
        for row in result.schedule:
            self.assertEqual(row.budget, 1000)
            self.assertAlmostEqual(row.mortgage_payment + row.owner_cost + row.buyer_contribution, 1000)
            self.assertAlmostEqual(row.rent + row.renter_contribution, 1000)
        with self.assertRaisesRegex(ValueError, "mês 1"):
            compare_buy_rent(1200, 200, 0, 2, 100, monthly_budget=499)

    def test_growth_and_initial_rent_timing(self):
        result = compare_buy_rent(1200, 200, 0, 12, 100,
                                  annual_property_growth=0.12, annual_rent_growth=0.12,
                                  annual_owner_cost_rate=0.01)
        self.assertEqual(result.schedule[0].rent, 100)
        self.assertEqual(result.schedule[0].owner_cost, 1)
        self.assertAlmostEqual(result.schedule[-1].property_value, 1344)
        self.assertAlmostEqual(result.schedule[1].rent, 100 * 1.12 ** (1 / 12))

    def test_negative_returns_are_allowed(self):
        result = compare_buy_rent(1200, 1200, 0, 1, 0,
                                  annual_investment_return=-0.12, annual_property_growth=-0.12)
        self.assertLess(result.schedule[0].renter_wealth, 1200)
        self.assertLess(result.schedule[0].buyer_wealth, 1200)

    def test_invalid_inputs(self):
        for kwargs in (
            {"down_payment": 1300}, {"down_payment": -1}, {"property_price": 0},
            {"rent": -1}, {"rent": math.nan}, {"horizon_months": 0},
            {"horizon_months": 1.5}, {"annual_investment_return": -1},
            {"annual_property_growth": math.inf}, {"annual_rent_growth": math.nan},
            {"sale_cost_rate": 1}, {"purchase_cost_rate": -0.1},
            {"annual_owner_cost_rate": -0.1}, {"monthly_budget": math.nan},
        ):
            params = dict(property_price=1200, down_payment=200, monthly_rate=0, months=2, rent=100)
            params.update(kwargs)
            with self.subTest(kwargs=kwargs):
                with self.assertRaises(ValueError):
                    compare_buy_rent(**params)

    def test_budget_must_cover_later_months_too(self):
        with self.assertRaisesRegex(ValueError, "mês 2"):
            compare_buy_rent(1200, 1200, 0, 12, 100, monthly_budget=105,
                             annual_rent_growth=monthly_to_annual(0.1))

    def test_equal_extra_savings_do_not_change_wealth_difference(self):
        params = dict(property_price=1200, down_payment=200, monthly_rate=0.01,
                      months=12, rent=100, annual_investment_return=0.08)
        variable = compare_buy_rent(**params)
        fixed = compare_buy_rent(**params, monthly_budget=1000)
        self.assertAlmostEqual(variable.wealth_difference, fixed.wealth_difference)
        self.assertGreater(fixed.schedule[-1].buyer_investments, variable.schedule[-1].buyer_investments)
