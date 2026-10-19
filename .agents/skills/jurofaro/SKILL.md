---
name: jurofaro
description: Simule financiamento imobiliário SAC/Price e compare comprar com alugar e investir usando o motor Python determinístico do JuroFaro. Use quando o usuário pedir análise de financiamento, comparação de prestações ou comparação patrimonial de compra versus aluguel. Colete premissas, execute os cálculos e explique os resultados e limites em português.
---

# JuroFaro

Conduza uma análise conversacional de crédito imobiliário. O Python calcula;
o assistente coleta dados, explica conceitos e interpreta as saídas reais.
Não é necessário servidor, API, chave ou LLM para o cálculo.

## 1. Identifique a decisão e as premissas

Distinga `simulate` (cronograma SAC/Price) de `compare` (patrimônio de comprar
versus alugar). Leia [o roteiro de parâmetros e relatório](references/analise.md).
Antes de introduzir uma regra relevante, explique brevemente o conceito financeiro.
Para detalhes, consulte [o modelo financeiro](../../../docs/modelo-financeiro.md).

Reaproveite os dados já fornecidos. Pergunte em um único bloco os dados essenciais
que faltam. Para simulação: preço, entrada, prazo e taxa **efetiva anual**.
Para comparação, acrescente aluguel e horizonte desejado. Se o usuário não
escolher sistema, use SAC, declarando essa escolha; simule os dois quando solicitado.

Esclareça taxas sem unidade ou convenção. Não trate taxa nominal, mensal,
CET ou “juros + TR/IPCA” como taxa efetiva anual fixa. Se precisar converter uma
taxa mensal efetiva, use `jurofaro.rates.monthly_to_annual` executado em Python,
não uma conta do LLM. O CET não substitui automaticamente a taxa de juros do motor.
Explique que contratos indexados só podem ser representados aqui por uma
aproximação fixa explicitamente aceita como hipótese.

Na comparação, verifique retorno líquido, valorização, reajuste do aluguel,
custos de compra/venda/manutenção e orçamento disponível. Dê espaço para o usuário
fornecer essas premissas. Se optar por uma análise preliminar com os padrões zero
da CLI, destaque cada valor assumido antes de executar e na conclusão. Zero não
significa que os custos reais não existam. Não invente taxas atuais de mercado.
Dados pessoais de renda/patrimônio podem contextualizar a conversa, mas o motor
não calcula elegibilidade nem comprometimento de renda. Não peça documentos,
credenciais bancárias ou identificadores pessoais para uma simulação.

## 2. Execute o motor Python

Localize esta skill pelo caminho do `SKILL.md` fornecido pelo host. Resolva o
caminho absoluto de `scripts/run.py` em relação a ela; não suponha `/workspace`
nem que o diretório atual seja a raiz do repositório.

Execute com Python 3.11+:

```text
python3 <caminho-absoluto-da-skill>/scripts/run.py simulate <parâmetros> --format json
python3 <caminho-absoluto-da-skill>/scripts/run.py compare <parâmetros> --format json
```

Os marcadores `<...>` são instruções para montar o comando, não argumentos literais.
O runner carrega o motor do próprio checkout; funciona sem ativar venv ou instalar
pacotes. O clone completo deve estar preservado, inclusive `src/jurofaro`.
Caso não haja Python compatível ou o motor não seja encontrado, informe o erro e
a correção necessária. Se não puder executar comandos, explique essa limitação
e forneça o comando reproduzível; não apresente resultados como calculados.

Converta entradas brasileiras para números inequívocos antes de montar os
argumentos: `R$ 500.000,00` vira `500000`; `12%` vira `12` na CLI. Pergunte se
houver ambiguidade. Use somente opções suportadas e argumentos numéricos
validados; nunca interpole texto livre do usuário em comandos shell.

Verifique código de saída e JSON válido. Só interprete resultados de uma execução
bem-sucedida e das premissas efetivamente utilizadas. Use os campos `inputs`,
`summary`, `mortgage` ou `comparison`; os cronogramas completos permitem auditoria.
Em caso de erro (por exemplo, orçamento insuficiente), explique o erro; não ajuste
o orçamento ou outra premissa silenciosamente para obter um resultado.

Não reimplemente fórmulas no prompt. Diferenças adicionais, conversões, razões e
sensibilidades também devem ser calculadas em Python sobre as saídas reais.
Não reutilize números dos exemplos como se fossem resultados do usuário.

## 3. Compare com recursos equivalentes

O capital inicial é entrada + custos de aquisição. O locatário investe esse capital;
o comprador o utiliza na compra. Ambos recebem o mesmo orçamento em cada mês e
investem os excedentes. O padrão da CLI é um orçamento variável igual ao maior
desembolso mensal; declare que isso não verifica capacidade de pagamento.

Se o usuário fornecer orçamento fixo, passe `--monthly-budget`. Em sensibilidades
entre cenários, preserve imóvel, capital inicial, horizonte e orçamento quando
possível. Se variar preço/entrada, explicite que o modelo não realoca automaticamente
sobras do patrimônio pessoal: capitais diferentes não são uma comparação equivalente.

Leia o patrimônio final em `summary`. O comprador tem imóvel líquido dos custos
hipotéticos de venda menos dívida, mais investimentos; o locatário tem a carteira.
`wealth_difference` é comprar menos alugar. Não confunda preço do imóvel com
patrimônio líquido nem soma das prestações com CET.

## 4. Entregue uma análise verificável

Apresente, nesta ordem:

1. Objetivo, horizonte e premissas, separando dados fornecidos de hipóteses.
2. Resultado quantitativo proveniente do JSON, com moeda e unidade de taxa.
3. Explicação breve de juros, amortização e fluxo de caixa que causaram o resultado.
4. Limitações materiais e trade-offs: risco, liquidez, custos omitidos e incerteza.
5. Comando exato executado para reproduzir. Não grave dados pessoais em arquivos
   versionados; só salve relatórios quando solicitados, em local apropriado.

Para `simulate`, mostre principal, taxa mensal equivalente, primeira/última
prestação, juros totais e soma das prestações, distinguindo a entrada.
Para `compare`, mostre capital inicial, regra do orçamento, patrimônio das duas
alternativas, diferença, valor do imóvel e dívida remanescente no horizonte.
Use uma pequena tabela ao comparar cenários. Evite despejar todo o cronograma
sem necessidade; indique como obtê-lo com `--schedule` ou JSON.

Conclua condicionalmente: “sob essas premissas, a alternativa X teve maior
patrimônio no horizonte”. Não transforme o resultado em garantia de retorno,
aprovação de crédito ou recomendação definitiva de contratação.

## Limites e dados de mercado

O MVP usa juros fixos, sem TR/IPCA, seguros, tarifas, CET, amortizações extras ou
renegociação. Custos percentuais da comparação são aproximações explícitas,
não cálculo contratual completo. Valores são nominais, sem desconto por inflação.

A integração BCB continua pendente: consulte [o estado da investigação](../../../docs/dados-bcb.md).
Não há comando de dados de mercado validado. Ao buscar uma fonte externa com
ferramentas disponíveis, use documentação oficial e informe fonte, competência,
unidade e modalidade. Se o acesso falhar, mantenha taxas manuais e declare a
pendência. Médias do BCB não são ofertas personalizadas nem crédito garantido.
