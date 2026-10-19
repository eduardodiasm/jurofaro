"""Financiamento com taxa mensal efetiva fixa e pagamentos no fim do mês."""

from dataclasses import dataclass
import math

from .rates import finite, positive_integer


@dataclass(frozen=True)
class Installment:
    month: int
    payment: float
    interest: float
    amortization: float
    balance: float


@dataclass(frozen=True)
class Mortgage:
    principal: float
    monthly_rate: float
    months: int
    system: str
    schedule: tuple[Installment, ...]

    @property
    def total_interest(self) -> float:
        return math.fsum(row.interest for row in self.schedule)

    @property
    def total_paid(self) -> float:
        return math.fsum(row.payment for row in self.schedule)


def simulate_mortgage(
    principal: float, monthly_rate: float, months: int, system: str = "SAC"
) -> Mortgage:
    finite(principal, "principal", minimum=0)
    finite(monthly_rate, "taxa mensal", minimum=0)
    positive_integer(months, "prazo")
    if not isinstance(system, str) or system.upper() not in {"SAC", "PRICE"}:
        raise ValueError("sistema deve ser SAC ou PRICE")
    system = system.upper()
    # Forma estável de P*i / (1 - (1+i)**(-n)), inclusive para taxas pequenas.
    fixed_payment = (
        principal / months if monthly_rate == 0
        else principal * monthly_rate / -math.expm1(-months * math.log1p(monthly_rate))
    )
    if not math.isfinite(fixed_payment):
        raise ValueError("parâmetros excedem a capacidade numérica do modelo")
    balance = principal
    schedule = []
    for month in range(1, months + 1):
        interest = balance * monthly_rate
        amortization = principal / months if system == "SAC" else fixed_payment - interest
        # Quita o resíduo numérico na última prestação; sem arredondar a cada mês.
        amortization = balance if month == months else min(balance, max(0.0, amortization))
        payment = interest + amortization
        balance = max(0.0, balance - amortization)
        if not all(math.isfinite(v) for v in (interest, amortization, payment, balance)):
            raise ValueError("parâmetros excedem a capacidade numérica do modelo")
        schedule.append(Installment(month, payment, interest, amortization, balance))
    return Mortgage(principal, monthly_rate, months, system, tuple(schedule))
