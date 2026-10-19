"""Compra e aluguel sob o mesmo capital inicial e orçamento mensal."""

from dataclasses import dataclass
import math

from .mortgage import Mortgage, simulate_mortgage
from .rates import annual_to_monthly, finite, positive_integer


@dataclass(frozen=True)
class ComparisonMonth:
    month: int
    property_value: float
    debt: float
    mortgage_payment: float
    owner_cost: float
    rent: float
    budget: float
    buyer_contribution: float
    renter_contribution: float
    buyer_investments: float
    renter_investments: float
    buyer_wealth: float
    renter_wealth: float


@dataclass(frozen=True)
class Comparison:
    mortgage: Mortgage
    initial_capital: float
    purchase_cost: float
    sale_cost_rate: float
    monthly_budget: float | None
    annual_investment_return: float
    annual_property_growth: float
    annual_rent_growth: float
    annual_owner_cost_rate: float
    initial_rent: float
    schedule: tuple[ComparisonMonth, ...]

    @property
    def wealth_difference(self) -> float:
        """Patrimônio do comprador menos patrimônio do locatário no horizonte."""
        final = self.schedule[-1]
        return final.buyer_wealth - final.renter_wealth


def compare_buy_rent(
    property_price: float,
    down_payment: float,
    monthly_rate: float,
    months: int,
    rent: float,
    *,
    system: str = "SAC",
    horizon_months: int | None = None,
    annual_investment_return: float = 0.0,
    annual_property_growth: float = 0.0,
    annual_rent_growth: float = 0.0,
    purchase_cost_rate: float = 0.0,
    sale_cost_rate: float = 0.0,
    annual_owner_cost_rate: float = 0.0,
    monthly_budget: float | None = None,
) -> Comparison:
    finite(property_price, "preço do imóvel", minimum=0)
    if property_price == 0:
        raise ValueError("preço do imóvel deve ser positivo")
    finite(down_payment, "entrada", minimum=0)
    if down_payment > property_price:
        raise ValueError("entrada não pode exceder o preço do imóvel")
    finite(rent, "aluguel", minimum=0)
    finite(purchase_cost_rate, "custos de aquisição", minimum=0)
    finite(sale_cost_rate, "custos de venda", minimum=0)
    if sale_cost_rate >= 1:
        raise ValueError("custos de venda devem ser menores que 100%")
    finite(annual_owner_cost_rate, "custos anuais do proprietário", minimum=0)
    if monthly_budget is not None:
        finite(monthly_budget, "orçamento mensal", minimum=0)
    if horizon_months is None:
        horizon_months = months
    positive_integer(horizon_months, "horizonte")
    investment_rate = annual_to_monthly(annual_investment_return)
    property_growth = annual_to_monthly(annual_property_growth)
    rent_growth = annual_to_monthly(annual_rent_growth)
    mortgage = simulate_mortgage(property_price - down_payment, monthly_rate, months, system)
    purchase_cost = property_price * purchase_cost_rate
    initial_capital = down_payment + purchase_cost
    buyer_investments = 0.0
    renter_investments = initial_capital
    property_value = property_price
    current_rent = rent
    schedule = []
    for month in range(1, horizon_months + 1):
        # Custo de manutenção usa o valor do imóvel no início do mês.
        owner_cost = property_value * annual_owner_cost_rate / 12
        row = mortgage.schedule[month - 1] if month <= months else None
        payment, debt = (row.payment, row.balance) if row else (0.0, 0.0)
        buyer_outflow = payment + owner_cost
        budget = max(buyer_outflow, current_rent) if monthly_budget is None else monthly_budget
        if budget < max(buyer_outflow, current_rent):
            raise ValueError(f"orçamento mensal insuficiente no mês {month}")
        buyer_contribution = budget - buyer_outflow
        renter_contribution = budget - current_rent
        buyer_investments = buyer_investments * (1 + investment_rate) + buyer_contribution
        renter_investments = renter_investments * (1 + investment_rate) + renter_contribution
        property_value *= 1 + property_growth
        buyer_wealth = property_value * (1 - sale_cost_rate) - debt + buyer_investments
        values = (owner_cost, payment, debt, budget, buyer_investments, renter_investments,
                  property_value, buyer_wealth, current_rent, buyer_contribution, renter_contribution)
        if not all(math.isfinite(v) for v in values):
            raise ValueError("parâmetros excedem a capacidade numérica do modelo")
        schedule.append(ComparisonMonth(
            month, property_value, debt, payment, owner_cost, current_rent, budget,
            buyer_contribution, renter_contribution, buyer_investments,
            renter_investments, buyer_wealth, renter_investments,
        ))
        current_rent *= 1 + rent_growth
    return Comparison(
        mortgage, initial_capital, purchase_cost, sale_cost_rate, monthly_budget,
        annual_investment_return, annual_property_growth, annual_rent_growth,
        annual_owner_cost_rate, rent, tuple(schedule),
    )
