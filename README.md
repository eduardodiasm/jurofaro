# JuroFaro

Inteligência independente de crédito, começando por financiamento imobiliário.
A versão **0.1.0** simula SAC/Price e compara o patrimônio de comprar financiado com
alugar e investir. Os cálculos são determinísticos, executados em Python, sem LLM.

## Começar

Requer Python 3.11+ e `pip`. Não há dependências externas de execução ou de testes,
serviço externo obrigatório, banco de dados ou credencial. A instalação usa setuptools.

```bash
# Na raiz do repositório
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python -m unittest discover -s tests -v
jurofaro --help
```

Também é possível usar `python -m jurofaro` no lugar de `jurofaro` após instalar.
Os comandos abaixo usam ponto como separador decimal e números sem separador de milhar.
**Percentuais na CLI são percentuais, não frações:** `--annual-rate 12` = 12% efetivos a.a.

## Simular um financiamento

Dados fictícios: imóvel de R$ 500 mil, entrada de R$ 100 mil, juros efetivos de
12% a.a., prazo de 360 meses. Não são condições de mercado verificadas.

```bash
jurofaro simulate \
  --property-price 500000 --down-payment 100000 \
  --annual-rate 12 --months 360 --system SAC
```

Resultado de referência:

| Medida | Valor |
| --- | ---: |
| Principal financiado | R$ 400.000,00 |
| Taxa efetiva mensal equivalente | 0,94887929% |
| Primeira prestação | R$ 4.906,63 |
| Última prestação | R$ 1.121,65 |
| Juros totais | R$ 685.090,85 |
| Soma das prestações | R$ 1.085.090,85 |
| Entrada + prestações | R$ 1.185.090,85 |

Troque `--system SAC` por `--system PRICE` para comparar os sistemas.
Use `--schedule` para ver cada prestação, juros, amortização e saldo devedor.
`--format json` exporta premissas, resumo e cronograma completo, com números sem
arredondamento de apresentação:

```bash
mkdir -p results
jurofaro simulate --property-price 500000 --down-payment 100000 \
  --annual-rate 12 --months 360 --system PRICE --format json > results/price.json
```

A soma das prestações não inclui entrada; entrada + prestações não inclui seguros,
tarifas, impostos nem indexadores. Esses valores **não são CET**.

## Comprar versus alugar e investir

Antes de comparar, escolha o **horizonte de permanência**, que pode ser diferente
do prazo do financiamento. O comprador começa usando a entrada e os custos de
compra; o locatário investe exatamente esse mesmo capital. Ambos têm o mesmo
orçamento mensal e investem o excedente de cada mês. O patrimônio do comprador
inclui o imóvel líquido de custos hipotéticos de venda, menos a dívida restante,
mais seus investimentos. O locatário termina com sua carteira de investimentos.

```bash
jurofaro compare \
  --property-price 500000 --down-payment 100000 \
  --annual-rate 12 --months 360 --system SAC \
  --rent 2500 --investment-return 8 \
  --property-growth 4 --rent-growth 4 \
  --purchase-cost 4 --sale-cost 6 --owner-cost 1 \
  --horizon-months 120
```

Nesse cenário fictício, em 10 anos:

| Medida | Valor |
| --- | ---: |
| Capital inicial de cada alternativa | R$ 120.000,00 |
| Valor do imóvel | R$ 740.122,14 |
| Dívida remanescente | R$ 266.666,67 |
| Patrimônio líquido do comprador | R$ 429.048,15 |
| Patrimônio do locatário | R$ 596.950,05 |
| Diferença (comprar − alugar) | R$ -167.901,91 |

A diferença é calculada antes de arredondar os resultados individuais.
Esse resultado vale apenas para essas hipóteses; não recomenda alugar em qualquer
situação. Retorno, valorização, aluguel, custos e horizonte podem inverter a conclusão.

### Parâmetros da comparação

| Parâmetro | Unidade / comportamento |
| --- | --- |
| `--rent` | Aluguel mensal inicial em R$, obrigatório |
| `--horizon-months` | Horizonte em meses; padrão: prazo do financiamento |
| `--investment-return` | Retorno efetivo anual **líquido** dos investimentos, em % |
| `--property-growth` | Valorização efetiva anual nominal do imóvel, em % |
| `--rent-growth` | Taxa anual de reajuste do aluguel, em %, distribuída mensalmente |
| `--purchase-cost` | Custos pagos à vista na compra, em % do preço do imóvel |
| `--sale-cost` | Custos hipotéticos de venda, em % do imóvel no horizonte |
| `--owner-cost` | Manutenção, IPTU e outros custos exclusivos do proprietário: % anual do valor corrente do imóvel, dividido por 12 |
| `--monthly-budget` | Orçamento mensal fixo em R$; rejeita qualquer mês com orçamento insuficiente |

Todos os percentuais opcionais têm padrão **zero**, sem custos ou retornos ocultos.
Sem `--monthly-budget`, o orçamento é o maior desembolso entre comprar e alugar em
cada mês e pode variar. Isso iguala o fluxo entre as alternativas, mas **não verifica
sua capacidade de pagamento**. Com orçamento fixo, ambos investem o saldo após
seus desembolsos; não são permitidos aportes negativos ou empréstimos adicionais.
Custos iguais nas duas alternativas podem ser omitidos; inclua em `--rent` os
custos específicos da locação que desejar representar. Evite contar condomínio
ou IPTU duas vezes. O reajuste mensal suavizado não representa contratos com reajuste anual em degraus.

Use `--schedule` para inspecionar orçamentos, desembolsos, aportes e patrimônio
mensais; `--format json` inclui todos os saldos e premissas para auditoria.
Execute `bash examples/run.sh` para gerar cenários reproduzíveis em `results/`.
O script compara SAC, Price e uma taxa menor com o mesmo imóvel, entrada e
orçamento fixo de R$ 6.000 mensais, para manter os recursos iguais entre cenários.

## Arquitetura mínima

```text
src/jurofaro/
  rates.py         # validação e conversão de taxas efetivas
  mortgage.py      # SAC/Price e cronograma, sem I/O
  comparison.py    # fluxos iguais e evolução patrimonial, sem I/O
  cli.py           # argumentos, relatório textual e JSON
  __main__.py      # python -m jurofaro
tests/             # unittest: referências manuais, invariantes e CLI
examples/run.sh    # cenários fictícios executáveis
docs/              # fórmulas, limites e investigação do BCB
```

Os motores recebem números e devolvem dataclasses imutáveis. A API Python usa
**frações** (`0.12` = 12%), enquanto a CLI usa percentuais (`12` = 12%). Exemplo:

```python
from jurofaro import annual_to_monthly, simulate_mortgage

loan = simulate_mortgage(400_000, annual_to_monthly(0.12), 360, "PRICE")
print(loan.total_interest)
print(loan.schedule[0])
```

Outras modalidades poderão reaproveitar o cronograma e as conversões. Novas fontes
de dados devem ficar fora dos motores; um serviço, framework ou camada de abstração
adicional só será necessário quando houver outro caso concreto.

## Matemática, dados e limites

- [Fórmulas, convenções e exemplos verificáveis](docs/modelo-financeiro.md).
- [Investigação da API do BCB e pendência de integração](docs/dados-bcb.md).
- Testes: `python -m unittest discover -s tests -v`. CI configurado para Python 3.11, 3.12 e 3.13.

O financiamento usa juros fixos, sem TR/IPCA, carência, seguros, tarifas, CET,
amortizações extras ou renegociação. A comparação representa alguns custos por
percentuais explícitos; não calcula tributos individuais, imposto sobre ganho de
capital nem risco de investimento. O retorno informado deve ser líquido de custos
e tributos. Valores são nominais, sem desconto por inflação. Não há análise de
renda, aprovação de crédito ou recomendação personalizada. O patrimônio modelado
é o das alternativas, não um inventário completo do patrimônio pessoal.

O BCB não é dependência do simulador. Nenhuma série foi integrada sem validação.
Taxas médias do BCB não representam ofertas personalizadas nem crédito garantido.
