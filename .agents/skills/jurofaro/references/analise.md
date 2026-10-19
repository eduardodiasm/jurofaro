# Roteiro de análise

## Coleta mínima

Para financiamento:

> Qual o preço do imóvel, a entrada, o prazo e a taxa efetiva anual? Você quer
> SAC, Price ou comparar ambos? Se a oferta estiver em outra convenção, informe
> como a taxa está descrita para não confundir juros com CET ou indexador.

Para comprar versus alugar, acrescente:

> Qual seu aluguel atual e por quanto tempo deseja comparar as alternativas?
> Quais hipóteses quer usar para retorno líquido dos investimentos, valorização,
> reajuste do aluguel e custos de compra, venda e manutenção? Você tem um orçamento
> mensal fixo disponível para moradia e investimentos?

Adapte as perguntas aos dados já disponíveis. Se não houver estimativas opcionais,
explique o cenário simplificado com zeros, sem apresentar essa escolha como custo
real. Não reutilize as hipóteses fictícias abaixo em análises pessoais sem declarar.

## Mapeamento dos argumentos

| Dado | Argumento | Convenção |
| --- | --- | --- |
| Preço do imóvel | `--property-price` | R$ |
| Entrada | `--down-payment` | R$, sem incluir custos de aquisição |
| Juros | `--annual-rate` | % efetivos a.a.; `12` significa 12% |
| Prazo | `--months` | Inteiro positivo de meses |
| Sistema | `--system` | `SAC` ou `PRICE`; padrão SAC |
| Aluguel inicial | `--rent` | R$ por mês, obrigatório no compare |
| Horizonte | `--horizon-months` | Meses; padrão do motor é o prazo do financiamento |
| Retorno dos investimentos | `--investment-return` | % efetivos a.a., líquido de impostos e custos |
| Valorização | `--property-growth` | % efetivos a.a. |
| Reajuste de aluguel | `--rent-growth` | % anual, distribuído de forma equivalente a cada mês |
| Custos de aquisição | `--purchase-cost` | % do preço inicial, pago no instante zero |
| Custos de venda | `--sale-cost` | % do preço no horizonte, liquidação hipotética |
| Manutenção/IPTU/etc. | `--owner-cost` | % anual do valor corrente, rateado em 12 meses |
| Orçamento fixo | `--monthly-budget` | R$/mês, precisa cobrir desembolsos em todos os meses |

Percentuais opcionais têm padrão zero. Sem orçamento fixo, o motor usa um
orçamento comum variável. Valores monetários devem ser finitos, a entrada não
pode exceder o imóvel e a taxa de financiamento não pode ser negativa.

## Exemplos de execução

Estes comandos são executados **na raiz do clone** e usam apenas dados fictícios.
Em outros diretórios, use o caminho absoluto do runner conforme `SKILL.md`.

### Simular SAC

```bash
python3 .agents/skills/jurofaro/scripts/run.py simulate \
  --property-price 500000 --down-payment 100000 \
  --annual-rate 12 --months 360 --system SAC --format json
```

O resumo fica em `summary`; a taxa mensal em `mortgage.monthly_rate` é uma
fração, não percentual. Para exibir essa taxa em %, multiplique por 100 em Python.
A lista `mortgage.schedule` contém prestação, juros, amortização e saldo devedor.

### Comparar compra e aluguel

```bash
python3 .agents/skills/jurofaro/scripts/run.py compare \
  --property-price 500000 --down-payment 100000 \
  --annual-rate 12 --months 360 --system SAC \
  --rent 2500 --investment-return 8 --property-growth 4 --rent-growth 4 \
  --purchase-cost 4 --sale-cost 6 --owner-cost 1 \
  --horizon-months 120 --monthly-budget 6000 --format json
```

O JSON traz:

- `inputs`: argumentos efetivamente usados; percentuais estão em pontos percentuais.
- `summary.buyer_wealth` e `summary.renter_wealth`: patrimônio final de cada alternativa.
- `summary.wealth_difference`: comprador menos locatário, já calculado pelo motor.
- `comparison.initial_capital`: recursos iniciais iguais nas duas alternativas.
- `comparison.schedule`: orçamento, aportes, carteiras, imóvel e dívida por mês.
- `comparison.mortgage`: cronograma do financiamento, que pode ser mais longo que o horizonte.

As taxas internas em `comparison` e `mortgage` são frações; não misture suas unidades
com as de `inputs`. Use a última linha de `comparison.schedule` para imóvel e dívida
no horizonte, e não a última linha do cronograma completo do financiamento.

### Conferência manual de referência

```bash
python3 .agents/skills/jurofaro/scripts/run.py compare \
  --property-price 1200 --down-payment 200 --annual-rate 0 \
  --months 2 --rent 100 --format json
```

Nesse exemplo, prestações de 500 e aluguel de 100 deixam aporte mensal de 400 para
o locatário. O comprador termina com 1200; o locatário com 1000; diferença +200.
Esses são valores de referência para verificar a execução, não substituem novas
execuções para outras entradas.

## Sensibilidade

Depois de concluir o cenário base, quando isso ajudar a decisão, execute cenários
identificados variando uma premissa por vez. Use valores fornecidos ou hipóteses
explicitamente rotuladas. Mantenha recursos iguais e não chame cenários de
“previsão”. Não extrapole resultados de um horizonte para outro sem executar.

## Checklist do relatório

- Explicou SAC/Price e taxa efetiva antes da regra relevante?
- Identificou hipóteses e unidades, incluindo os padrões zero?
- Executou o Python, verificou sucesso e leu o JSON desta execução?
- Usou patrimônio líquido, dívida correta no horizonte e orçamento comum?
- Manteve juros, CET e indexador separados?
- Explicou quais custos e riscos ficaram de fora?
- Incluiu o comando reproduzível e uma conclusão condicionada às premissas?
