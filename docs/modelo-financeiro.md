# Modelo financeiro v0.1

## Convenções antes das fórmulas

**Juros** remuneram o capital emprestado. **Amortização** reduz a dívida. Uma
prestação é a soma de ambos neste modelo; em contratos reais, pode incluir outros
itens. **Saldo devedor** é o principal ainda não amortizado, não a soma de todas
as prestações futuras.

**Taxa efetiva** inclui a capitalização no período informado. As taxas efetivas
anual e mensal equivalentes obedecem a:

```text
i_m = (1 + i_a)^(1/12) - 1
i_a = (1 + i_m)^12 - 1
```

Exemplo: 1% efetivo a.m. equivale a aproximadamente 12,682503% efetivos a.a.
Já 12% efetivos a.a. equivalem a aproximadamente 0,94887929% a.m.

**Taxa nominal anual**, quando expressa com capitalização mensal, pode representar
12 vezes a taxa mensal. Por exemplo, 12% nominais a.a. com capitalização mensal
correspondem a 1% a.m., e não a 12% efetivos a.a. Confira sempre a convenção do
contrato. A CLI aceita exclusivamente taxa **efetiva anual**; não converte ofertas
bancárias ambíguas automaticamente.

**CET (Custo Efetivo Total)** expressa o custo dos fluxos de crédito, incluindo
os encargos aplicáveis, como juros, tarifas, tributos e seguros. Não se obtém
simplesmente somando percentuais. Exige os fluxos e suas datas para calcular a
taxa que iguala valores presentes. Este MVP não calcula CET; custos genéricos da
comparação não transformam a taxa de juros em CET.

**Indexadores**, como TR e IPCA, atualizam valores conforme regras contratuais.
São distintos da taxa de juros. Aqui o saldo não é corrigido por indexador; um
contrato “juros + TR” não é reproduzido apenas pela taxa de juros informada.
A valorização do imóvel e o reajuste de aluguel na comparação são hipóteses
independentes, não indexadores da dívida.

## Financiamento

Sejam `P = preço - entrada`, `n` o prazo em meses, `i` a taxa efetiva mensal,
`B_0 = P` o saldo inicial, e `t` o mês de 1 até n. O primeiro pagamento ocorre
um mês depois da contratação. Períodos mensais são iguais; não há convenção de
dias úteis ou datas irregulares.

### SAC — Sistema de Amortização Constante

```text
A_t = P / n
J_t = B_(t-1) * i
M_t = A_t + J_t
B_t = B_(t-1) - A_t
```

A amortização é constante, os juros caem com o saldo e as prestações decrescem.
Para `P = 1200`, `i = 1% a.m.`, `n = 3`:

| Mês | Juros | Amortização | Prestação | Saldo |
| --- | ---: | ---: | ---: | ---: |
| 1 | 12 | 400 | 412 | 800 |
| 2 | 8 | 400 | 408 | 400 |
| 3 | 4 | 400 | 404 | 0 |

Juros totais: 24. A fórmula fechada de conferência é `P * i * (n + 1) / 2`.

### Price — Sistema Francês

```text
M = P * i / (1 - (1 + i)^(-n))       se i > 0
M = P / n                           se i = 0
J_t = B_(t-1) * i
A_t = M - J_t
B_t = B_(t-1) - A_t
```

A prestação é constante; no início, uma parcela maior dela paga juros. Com a
redução do saldo, a amortização cresce. O valor presente das prestações é `P`.
Para `P = 100`, `i = 10% a.m.`, `n = 2`:

```text
100 = M / 1.1 + M / 1.1²
M = 57.61904761904762
J_1 = 10
A_1 = 47.61904761904762
B_1 = 52.38095238095238
J_2 = 5.238095238095238
Juros totais = 15.23809523809524
```

Esse caso é deliberadamente pequeno para conferência, não uma taxa recomendada.

Sob mesmo principal, taxa positiva e prazo maior que um mês, SAC amortiza mais
cedo e tem menos juros totais que Price, com prestação inicial maior. O custo
nominal acumulado não substitui análise de valor do dinheiro no tempo.

### Precisão e validação

Os cálculos usam `float` de dupla precisão, `log1p`/`expm1` para estabilidade da
conversão e da fórmula Price, e `math.fsum` nos totais. Não há arredondamento
mensal para centavos; o texto arredonda só ao apresentar. O JSON preserva a
precisão numérica disponível. A última prestação quita o resíduo de ponto
flutuante e pode diferir minimamente das anteriores em Price.

Isso é suficiente para análise de cenários, mas **não é um livro contábil**.
Bancos podem arredondar mensalmente, usar datas, regras de atualização e encargos
que mudam os resultados. Uma futura conciliação contratual precisará explicitar
essas regras e provavelmente usar decimal para fluxos monetários.

São aceitos principal zero (compra à vista), taxa zero e prazo de um mês. Prazos
precisam ser inteiros positivos, financiamento não admite juros negativos,
entrada deve estar entre zero e o preço e todos os valores devem ser finitos.
Taxas de retorno, valorização e aluguel podem ser negativas, mas precisam ser
maiores que -100% efetivos anuais. Cálculos não finitos são rejeitados.

## Comprar versus alugar: patrimônio com recursos iguais

`V_0` é o preço do imóvel, `E` a entrada, `c` o custo proporcional de aquisição,
`s` o custo proporcional de venda, `m` o custo anual do proprietário, `R_1` o
aluguel inicial. As taxas efetivas mensais de investimento `r`, valorização `g`
e reajuste `h` são convertidas das anuais. A entrada não inclui os custos de
compra: o capital necessário é `K = E + c * V_0`.

No instante zero:

- Comprador paga entrada e custos; possui imóvel `V_0`, dívida `V_0 - E` e
  carteira `I_C,0 = 0`.
- Locatário mantém carteira `I_L,0 = K`, com o mesmo capital inicial disponível.

Em cada mês `t`:

```text
V_t = V_(t-1) * (1 + g)
R_t = R_1 * (1 + h)^(t-1)
O_t = V_(t-1) * m / 12                         # custo do proprietário
D_C,t = M_t + O_t                              # desembolso comprador
D_L,t = R_t                                   # desembolso locatário
Q_t = max(D_C,t, D_L,t)                        # orçamento comum padrão
aporte_C,t = Q_t - D_C,t
aporte_L,t = Q_t - D_L,t
I_C,t = I_C,(t-1) * (1 + r) + aporte_C,t
I_L,t = I_L,(t-1) * (1 + r) + aporte_L,t
W_C,t = V_t * (1 - s) - B_t + I_C,t
W_L,t = I_L,t
ΔW_t = W_C,t - W_L,t
```

O custo `m/12` é um rateio de despesas anuais, não conversão de uma taxa de juros.
O investimento rende sobre o saldo do mês anterior; os aportes ocorrem ao fim
do mês. O aluguel inicial vale para o primeiro mês, reajustando nos seguintes.
O valor do imóvel usado na avaliação final já inclui a valorização do mês.

Se houver orçamento mensal fixo, `Q_t` é esse valor em todos os meses e deve
cobrir os dois desembolsos. Mesmo quando alugar custa mais que pagar a prestação,
o comprador investe a diferença. Depois de quitar, `M_t = B_t = 0`; o comprador
continua pagando os custos do imóvel e pode investir o excedente. No horizonte
anterior à quitação, a dívida remanescente é deduzida integralmente.

`W_C` representa liquidação hipotética do imóvel no horizonte, sem obrigar uma
venda real. Pode ser negativo se a dívida superar o valor líquido do imóvel.
`ΔW > 0` favorece comprar apenas na métrica patrimonial e nas premissas usadas.
Custos de aquisição saem no início; custos de venda reduzem a avaliação terminal.
Prestações **não** são descontadas de novo do patrimônio: seus juros já consumiram
fluxo e a amortização já reduziu a dívida.

### Referência manual

Imóvel 1200, entrada 200, aquisição/venda/manutenção zero, juros zero, prazo
2 meses, aluguel 100, retornos e crescimento zero:

```text
Capital inicial de ambos: 200
Prestação comprador: 500 por mês
Orçamento comum: 500 por mês
Locatário investe: 400 por mês
Patrimônio comprador no mês 2: 1200 - 0 = 1200
Patrimônio locatário no mês 2: 200 + 400 + 400 = 1000
Diferença: +200 para comprar
```

Esse exemplo e os casos SAC/Price acima são verificados nos testes, além de
horizontes antes/depois da quitação, custos, retornos negativos e aportes dos dois lados.

## Limites da decisão

Retornos e crescimentos são constantes e conhecidos no cenário, sem incerteza.
Use retorno líquido de tributos e taxas; todos os resultados são nominais.
Imposto sobre ganho de capital na venda não é calculado. Custos de venda e de
aquisição são aproximações explícitas, não tabelas legais de ITBI/cartório.
Não há uso de FGTS, subsídios, crédito fiscal, restrições de concessão,
comprometimento de renda, aluguel evitado como recebimento adicional ou avaliação
de preferências pessoais. O modelo já captura morar no imóvel pela ausência de
aluguel no fluxo do comprador: adicionar “aluguel economizado” novamente duplicaria o benefício.

Para comparar imóveis ou entradas diferentes, confira se os cenários partem de
igual patrimônio total disponível: este modelo inclui apenas entrada + custos de
cada simulação. Sobras de um patrimônio pessoal maior precisam ser consideradas
explicitamente em uma evolução; não classifique cenários com capitais iniciais
diferentes como se tivessem os mesmos recursos.

## Referências institucionais para consulta

- [BCB — Calculadora do Cidadão: financiamento com prestações fixas](https://www3.bcb.gov.br/CALCIDADAO/publico/exibirFormFinanciamentoPrestacoesFixas.do?method=exibirFormFinanciamentoPrestacoesFixas): ferramenta institucional de referência para a modalidade Price.
- [Resolução CMN nº 4.881/2020 — CET](https://www.bcb.gov.br/estabilidadefinanceira/exibenormativo?tipo=Resolu%C3%A7%C3%A3o%20CMN&numero=4881): referência normativa sobre cálculo e informação do CET; não implementado neste MVP.
- [BCB — Taxas de juros](https://www.bcb.gov.br/estatisticas/txjuros) e [portal de dados abertos](https://dadosabertos.bcb.gov.br/): consulta de estatísticas e metodologia.

O proxy bloqueou o acesso aos domínios do BCB durante esta implementação. Portanto,
estas referências não representam validação online da versão atual das páginas,
dos endpoints ou comparação automatizada com a calculadora. Os resultados de
referência do MVP são derivados das fórmulas explícitas e contas manuais acima.
