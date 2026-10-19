"""Taxas efetivas em frações: 0.12 representa 12%, nunca 12."""

import math


def finite(value: float, name: str, *, minimum: float | None = None) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{name} deve ser um número finito")
    if minimum is not None and value < minimum:
        raise ValueError(f"{name} deve ser >= {minimum}")


def positive_integer(value: int, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} deve ser um inteiro positivo")


def annual_to_monthly(annual_rate: float) -> float:
    finite(annual_rate, "taxa anual")
    if annual_rate <= -1:
        raise ValueError("taxa anual deve ser maior que -100%")
    return math.expm1(math.log1p(annual_rate) / 12)


def monthly_to_annual(monthly_rate: float) -> float:
    finite(monthly_rate, "taxa mensal")
    if monthly_rate <= -1:
        raise ValueError("taxa mensal deve ser maior que -100%")
    return math.expm1(12 * math.log1p(monthly_rate))
