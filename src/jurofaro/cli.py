"""Interface de terminal. Percentuais na CLI; frações na API Python."""

import argparse
from dataclasses import asdict
import json
import sys

from .comparison import compare_buy_rent
from .mortgage import simulate_mortgage
from .rates import annual_to_monthly, finite


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(
        prog="jurofaro", description="Simulações determinísticas de crédito imobiliário (valores em R$)."
    )
    sub = root.add_subparsers(dest="command", required=True)
    for command, help_text in (
        ("simulate", "Simular financiamento SAC ou Price"),
        ("compare", "Comparar patrimônio: comprar financiado versus alugar e investir"),
    ):
        p = sub.add_parser(command, help=help_text)
        p.add_argument("--property-price", type=float, required=True, help="Preço do imóvel em R$")
        p.add_argument("--down-payment", type=float, required=True, help="Entrada em R$")
        p.add_argument("--annual-rate", type=float, required=True, help="Juros EFETIVOS anuais em %% (ex.: 12)")
        p.add_argument("--months", type=int, required=True, help="Prazo do financiamento em meses")
        p.add_argument("--system", type=str.upper, choices=["SAC", "PRICE"], default="SAC")
        p.add_argument("--format", choices=["text", "json"], default="text")
        p.add_argument("--schedule", action="store_true", help="Exibir todas as linhas no relatório textual")
        if command == "compare":
            p.add_argument("--rent", type=float, required=True, help="Aluguel mensal inicial em R$")
            p.add_argument("--horizon-months", type=int, help="Horizonte da comparação; padrão: prazo do financiamento")
            p.add_argument("--investment-return", type=float, default=0, help="Retorno líquido efetivo anual em %% (padrão: 0)")
            p.add_argument("--property-growth", type=float, default=0, help="Valorização efetiva anual em %% (padrão: 0)")
            p.add_argument("--rent-growth", type=float, default=0, help="Reajuste equivalente mensal a taxa anual em %% (padrão: 0)")
            p.add_argument("--purchase-cost", type=float, default=0, help="Custos de aquisição em %% do imóvel (padrão: 0)")
            p.add_argument("--sale-cost", type=float, default=0, help="Custos de venda em %% do valor final (padrão: 0)")
            p.add_argument("--owner-cost", type=float, default=0, help="Manutenção/IPTU/etc. anuais em %% do imóvel (padrão: 0)")
            p.add_argument("--monthly-budget", type=float, help="Orçamento mensal fixo em R$; padrão: maior desembolso entre alternativas em cada mês")
    return root


def money(value: float) -> str:
    return "R$ " + f"{value:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")


def main(argv: list[str] | None = None) -> int:
    arg_parser = parser()
    args = arg_parser.parse_args(argv)
    try:
        finite(args.property_price, "preço do imóvel", minimum=0)
        finite(args.down_payment, "entrada", minimum=0)
        if args.property_price <= 0:
            raise ValueError("preço do imóvel deve ser positivo")
        if args.down_payment > args.property_price:
            raise ValueError("entrada não pode exceder o preço do imóvel")
        monthly_rate = annual_to_monthly(args.annual_rate / 100)
        inputs = vars(args).copy()
        inputs.pop("format")
        inputs.pop("schedule")
        if args.command == "simulate":
            mortgage = simulate_mortgage(
                args.property_price - args.down_payment, monthly_rate, args.months, args.system
            )
            summary = {
                "first_payment": mortgage.schedule[0].payment,
                "last_payment": mortgage.schedule[-1].payment,
                "total_interest": mortgage.total_interest,
                "total_installments": mortgage.total_paid,
                "down_payment_plus_installments": args.down_payment + mortgage.total_paid,
            }
            if args.format == "json":
                print(json.dumps({"inputs": inputs, "mortgage": asdict(mortgage), "summary": summary},
                                 ensure_ascii=False, indent=2, allow_nan=False))
                return 0
            print(f"Financiamento {mortgage.system} — {mortgage.months} meses")
            print(f"Imóvel: {money(args.property_price)} | Entrada: {money(args.down_payment)}")
            print(f"Principal financiado: {money(mortgage.principal)}")
            print(f"Taxa efetiva: {args.annual_rate:.6f}% a.a. = {monthly_rate * 100:.8f}% a.m.")
            print(f"Primeira prestação: {money(summary['first_payment'])}")
            print(f"Última prestação: {money(summary['last_payment'])}")
            print(f"Juros totais: {money(mortgage.total_interest)}")
            print(f"Soma das prestações: {money(mortgage.total_paid)}")
            print(f"Entrada + prestações: {money(summary['down_payment_plus_installments'])}")
            print("Hipóteses: taxa fixa; sem TR/IPCA, seguros ou tarifas. Não é CET nem oferta de crédito.")
            if args.schedule:
                print("Mês | Prestação | Juros | Amortização | Saldo devedor")
                for row in mortgage.schedule:
                    print(f"{row.month} | {money(row.payment)} | {money(row.interest)} | "
                          f"{money(row.amortization)} | {money(row.balance)}")
        else:
            result = compare_buy_rent(
                args.property_price, args.down_payment, monthly_rate, args.months, args.rent,
                system=args.system, horizon_months=args.horizon_months,
                annual_investment_return=args.investment_return / 100,
                annual_property_growth=args.property_growth / 100,
                annual_rent_growth=args.rent_growth / 100,
                purchase_cost_rate=args.purchase_cost / 100,
                sale_cost_rate=args.sale_cost / 100,
                annual_owner_cost_rate=args.owner_cost / 100,
                monthly_budget=args.monthly_budget,
            )
            final = result.schedule[-1]
            summary = {"buyer_wealth": final.buyer_wealth, "renter_wealth": final.renter_wealth,
                       "wealth_difference": result.wealth_difference}
            if args.format == "json":
                print(json.dumps({"inputs": inputs, "comparison": asdict(result), "summary": summary},
                                 ensure_ascii=False, indent=2, allow_nan=False))
                return 0
            print(f"Comprar versus alugar — horizonte de {len(result.schedule)} meses")
            print(f"Imóvel: {money(args.property_price)} | Entrada: {money(args.down_payment)} | Sistema: {args.system}")
            print(f"Juros efetivos: {args.annual_rate:.6f}% a.a. | Prazo: {args.months} meses")
            print(f"Capital inicial igual: {money(result.initial_capital)} (entrada + custos de aquisição)")
            print(f"Aluguel inicial: {money(args.rent)} | Investimento líquido: {args.investment_return:g}% a.a.")
            print(f"Valorização: {args.property_growth:g}% a.a. | Reajuste aluguel: {args.rent_growth:g}% a.a.")
            print(f"Aquisição: {args.purchase_cost:g}% | Venda: {args.sale_cost:g}% | Custos proprietário: {args.owner_cost:g}% a.a.")
            print("Orçamento mensal igual: " + (
                money(args.monthly_budget) if args.monthly_budget is not None
                else "maior desembolso entre as alternativas, recalculado a cada mês"
            ))
            print("Rendimentos sobre saldo anterior; aportes ao fim do mês. Valores nominais.")
            print(f"Valor final do imóvel: {money(final.property_value)} | Dívida: {money(final.debt)}")
            print(f"Investimentos do comprador: {money(final.buyer_investments)}")
            print(f"Patrimônio comprador, líquido de venda e dívida: {money(final.buyer_wealth)}")
            print(f"Patrimônio locatário: {money(final.renter_wealth)}")
            print(f"Diferença (comprar − alugar): {money(result.wealth_difference)}")
            print("Resultado condicionado às premissas; não considera risco, liquidez nem adequação à renda.")
            print("Financiamento sem TR/IPCA, seguros ou tarifas; custos adicionais só nos parâmetros explícitos.")
            if args.schedule:
                print("Mês | Orçamento | Prestação | Custos proprietário | Aluguel | Aporte comprador | Aporte locatário | Patrimônio comprador | Patrimônio locatário")
                for row in result.schedule:
                    print(f"{row.month} | " + " | ".join(money(v) for v in (
                        row.budget, row.mortgage_payment, row.owner_cost, row.rent,
                        row.buyer_contribution, row.renter_contribution,
                        row.buyer_wealth, row.renter_wealth,
                    )))
    except (ValueError, OverflowError) as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 2
    return 0
