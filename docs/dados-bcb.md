# Dados do Banco Central: investigação e pendência

## Situação na v0.1

**Não há integração com API do BCB nesta versão.** O simulador funciona offline,
com taxas efetivas anuais fornecidas explicitamente pelo usuário. Os exemplos
são fictícios; nenhuma taxa foi rotulada como dado atual de mercado.

Foram tentadas consultas HTTP ao catálogo oficial de dados abertos, à página
de taxas de juros e ao serviço SGS. O proxy retornou `Tunnel connection failed:
403 Forbidden` nos três domínios. Isso identifica uma restrição de acesso deste
ambiente; não demonstra que as APIs oficiais estão indisponíveis.

Não foi possível validar um identificador de série de crédito imobiliário,
sua unidade, periodicidade ou resposta. Por isso nenhum código de série nem
endpoint de dados foi incorporado ao produto. Uma resposta JSON isolada, sem
metadados, também não bastaria para identificar a modalidade correta.

## Fontes oficiais para retomar

- [Portal de dados abertos do BCB](https://dadosabertos.bcb.gov.br/): pesquisar financiamento imobiliário, PF, recursos direcionados/livres e metadados da série.
- [Estatísticas de taxas de juros](https://www.bcb.gov.br/estatisticas/txjuros): consultar metodologia, modalidades e cobertura das médias por instituição.
- [SGS — Sistema Gerenciador de Séries Temporais](https://www3.bcb.gov.br/sgspub/): conferir código, título, unidade e periodicidade da série candidata.

Domínios necessários para retomar a pesquisa: `dadosabertos.bcb.gov.br`,
`www.bcb.gov.br`, `www3.bcb.gov.br`, `api.bcb.gov.br`. A política do ambiente
precisa permitir o acesso; esta implementação não alterou a política de rede.

## Critérios para uma integração futura

1. Obter metadados oficiais que identifiquem financiamento imobiliário para PF,
   distinguindo linhas reguladas, taxas de mercado e modalidades de funding.
2. Validar o endpoint HTTPS documentado, o código de série, a periodicidade,
   unidade (% a.a./% a.m.), convenção da taxa e o período coberto.
3. Fazer uma consulta pequena com intervalo explícito; guardar URL, data de
   consulta, competência e observações em uma amostra sanitizada de referência.
4. Conferir se a média inclui indexador, tarifas ou CET; nunca presumir que a
   taxa publicada represente custo completo de uma operação individual.
5. Implementar um adaptador separado dos motores com timeout, validação de
   esquema/unidade, tratamento de ausência de dados e testes com amostras.
   Usar TLS com verificação habilitada. Falha da API não deve quebrar simulações
   com taxa manual, nem substituir silenciosamente dados faltantes por taxas inventadas.
6. Exibir fonte, modalidade, unidade, competência e eventual defasagem, mantendo
   os valores originais para auditoria antes de converter taxas.

Médias do BCB não são ofertas personalizadas, não garantem aprovação de crédito
e não substituem a análise do contrato e de seu CET.
