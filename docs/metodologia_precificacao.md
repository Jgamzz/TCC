# Metodologia do motor de precificação

Este documento descreve a regra implementada pelo SGPV e pode ser usado como
base metodológica do artigo. Os valores abaixo são os valores efetivamente
executados por `PrecificacaoAppService`; eles não representam resultados
experimentais.

## Variáveis

- `P0`: preço atual do produto.
- `Custo`: custo unitário do produto.
- `G`: quantidade vendida nos últimos 30 dias corridos.
- `L`: limiar de giro configurado.
- `V`: quantidade de dias configurada para o alerta de validade.
- `D`: data de validade do produto.
- `C`: preço mais recente de concorrente, quando existir.
- `M`: margem mínima configurada, em percentual.
- `Hoje`: data da avaliação.

## Fórmula e ordem de aplicação

O preço intermediário começa em `P = P0`.

1. **Giro baixo:** se `G < L`, aplica-se `P = P * 0,95`.
2. **Giro alto:** caso o giro não seja baixo, se `L > 0`, `G >= 2L`,
   existir `C` e `P0 < C`, aplica-se `P = P * 1,02`.
3. **Validade próxima:** se existir `D` e
   `Hoje <= D < Hoje + V`, aplica-se `P = P * 0,90`. A comparação é estrita
   no limite superior; produtos vencidos não entram nessa condição.
4. **Limite competitivo:** se existir `C` e `P > C`, aplica-se
   `P = min(P, C)`.
5. **Piso de margem:** `P = max(P, Custo * (1 + M / 100))`.
6. **Arredondamento:** o resultado é arredondado para duas casas decimais
   usando arredondamento comercial (`ROUND_HALF_UP`).

O aumento de 2% por giro alto só ocorre quando há preço de concorrente e o
preço atual está abaixo dele. O piso de margem é aplicado depois dos descontos,
portanto uma redução nunca pode levar o preço aprovado abaixo da margem mínima.

## Exemplos reprodutíveis

Com `P0 = 20,00`, `Custo = 10,00`, `M = 15%` e `L = 10`:

- `G = 5`: `20,00 * 0,95 = 19,00`.
- `G = 20` e `C = 25,00`: `20,00 * 1,02 = 20,40`.
- validade em seis dias e `V = 7`: `20,00 * 0,90 = 18,00`.
- validade em sete dias: não aplica o desconto, pois o limite superior é
  exclusivo.
- piso de margem: `10,00 * (1 + 15 / 100) = 11,50`.

Os testes automatizados cobrem os limites de validade, o aumento condicionado
ao concorrente, o piso de margem, o giro móvel de 7/30 dias e a geração em lote.

## Avaliação experimental

Não se deve declarar aumento de lucro ou redução de perdas sem uma execução
controlada. Para produzir resultados acadêmicos, deve-se comparar, no mesmo
conjunto de produtos e no mesmo período, pelo menos:

- **Baseline:** preço fixo por margem, sem as regras de giro, validade e
  concorrência.
- **SGPV:** preço gerado pela fórmula acima.

Para cada cenário, registrar demanda observada, receita, custo, margem bruta,
perdas por validade e quantidade de alterações de preço. Informar tamanho da
amostra, período, dados de entrada, parâmetros (`L`, `V`, `M`), tratamento de
estoque e método de cálculo. A variação deve ser calculada por
`(resultado_SGPV - resultado_baseline) / resultado_baseline * 100`.

Até que esse experimento seja executado e arquivado, os valores de 14,5% de
lucro líquido e 30% de redução de perdas devem ser removidos do artigo ou
identificados explicitamente como hipótese/simulação, nunca como resultado
observado.

## Correção dos requisitos

Para eliminar a duplicidade identificada na especificação:

- **RF04:** registrar e consultar o histórico de movimentações de estoque,
  com produto, quantidade, tipo, data, motivo e usuário responsável.
- **RF10:** registrar e consultar o histórico de preços e decisões de
  precificação, com preço anterior, preço novo, motivo, data e usuário.

Assim, RF04 trata de movimentação física de estoque e RF10 trata da evolução
dos preços, sem sobreposição textual ou funcional.