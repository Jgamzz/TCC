import numpy as np
import pandas as pd
import scipy.stats as st

# ==========================================
# 1. PARÂMETROS DO CATÁLOGO SINTÉTICO (12 PRODUTOS)
# ==========================================
# Custo, Margem Mínima (M%), Limiar Giro (L), Janela Validade (V), Estoque Inicial, Validade (Dias), Preço Concorrente (C)
catalogo = [
    {"id": 1, "nome": "Prod_01", "custo": 10.0, "preco_base": 14.0, "estoque": 100, "validade_dias": 15, "L": 15, "M": 15, "V": 7, "C": 13.5},
    {"id": 2, "nome": "Prod_02", "custo": 25.0, "preco_base": 35.0, "estoque": 50,  "validade_dias": 20, "L": 10, "M": 15, "V": 7, "C": 34.0},
    {"id": 3, "nome": "Prod_03", "custo": 5.0,  "preco_base": 8.0,  "estoque": 150, "validade_dias": 10, "L": 20, "M": 10, "V": 5, "C": 7.5},
    {"id": 4, "nome": "Prod_04", "custo": 18.0, "preco_base": 25.0, "estoque": 80,  "validade_dias": 25, "L": 12, "M": 20, "V": 7, "C": 24.0},
    {"id": 5, "nome": "Prod_05", "custo": 12.0, "preco_base": 17.5, "estoque": 90,  "validade_dias": 12, "L": 15, "M": 15, "V": 5, "C": 16.0},
    {"id": 6, "nome": "Prod_06", "custo": 40.0, "preco_base": 58.0, "estoque": 40,  "validade_dias": 30, "L": 5,  "M": 25, "V": 10, "C": 55.0},
    {"id": 7, "nome": "Prod_07", "custo": 8.0,  "preco_base": 11.5, "estoque": 120, "validade_dias": 18, "L": 18, "M": 15, "V": 5, "C": 11.0},
    {"id": 8, "nome": "Prod_08", "custo": 22.0, "preco_base": 31.0, "estoque": 60,  "validade_dias": 14, "L": 10, "M": 20, "V": 5, "C": 30.0},
    {"id": 9, "nome": "Prod_09", "custo": 15.0, "preco_base": 21.0, "estoque": 100, "validade_dias": 22, "L": 15, "M": 15, "V": 7, "C": 20.5},
    {"id": 10, "nome": "Prod_10", "custo": 30.0, "preco_base": 42.0, "estoque": 45,  "validade_dias": 28, "L": 8,  "M": 20, "V": 7, "C": 40.0},
    {"id": 11, "nome": "Prod_11", "custo": 7.0,  "preco_base": 10.0, "estoque": 130, "validade_dias": 16, "L": 20, "M": 10, "V": 5, "C": 9.5},
    {"id": 12, "nome": "Prod_12", "custo": 50.0, "preco_base": 72.0, "estoque": 30,  "validade_dias": 40, "L": 5,  "M": 25, "V": 10, "C": 70.0}
]

# ==========================================
# 2. MOTOR DE SIMULAÇÃO DE MONTE CARLO
# ==========================================
def simular_monte_carlo(
    elasticidade=1.5,
    n_repeticoes=100,
    dias=30,
    semente=42,
    truncar_demanda=True,
    usar_regra_1=True,
    usar_regra_2=True,
    usar_regra_3=True,
    usar_regra_4=True,
    usar_regra_5=True,
    retornar_detalhes=False,
    catalogo_simulacao=None,
    demanda_media=3,
    demanda_desvio=1.5,
):
    np.random.seed(semente)
    catalogo_atual = catalogo_simulacao or catalogo
    
    resultados_A = []
    resultados_B = []
    resultados_C = []
    unidades_vencidas = {"A": [], "B": [], "C": []}
    custos_vencidos = {"A": [], "B": [], "C": []}
    estoque_remanescente = {"A": [], "B": [], "C": []}
    custo_remanescente = {"A": [], "B": [], "C": []}
    unidades_vendidas = {"A": [], "B": [], "C": []}
    rupturas = {"A": [], "B": [], "C": []}
    disparos_regras = {nome: [] for nome in ("R1", "R2", "R3", "R4", "R5")}
    
    for _ in range(n_repeticoes):
        # Receitas acumuladas em cada cenário
        receita_A = 0
        receita_B = 0
        receita_C = 0

        # Custos acumulados das unidades vendidas e descartadas
        custo_A = 0
        custo_B = 0
        custo_C = 0
        unidades_vencidas_A = 0
        unidades_vencidas_B = 0
        unidades_vencidas_C = 0
        custo_vencido_A = 0
        custo_vencido_B = 0
        custo_vencido_C = 0
        vendidos_A = 0
        vendidos_B = 0
        vendidos_C = 0
        rupturas_A = 0
        rupturas_B = 0
        rupturas_C = 0
        disparos = {nome: 0 for nome in disparos_regras}
        
        # Copiar estoques para a iteração
        estoque_A = {p["id"]: p["estoque"] for p in catalogo_atual}
        estoque_B = {p["id"]: p["estoque"] for p in catalogo_atual}
        estoque_C = {p["id"]: p["estoque"] for p in catalogo_atual}
        
        # Giro acumulado para a Regra do SGPV (Scenario C)
        giro_C = {p["id"]: 0 for p in catalogo_atual}
        
        for dia in range(1, dias + 1):
            for p in catalogo_atual:
                dias_para_vencer = p["validade_dias"] - dia
                
                # Se o produto venceu hoje, descarta o estoque restante e cobra o custo
                if dias_para_vencer == -1:
                    unidades_vencidas_A += estoque_A[p["id"]]
                    unidades_vencidas_B += estoque_B[p["id"]]
                    unidades_vencidas_C += estoque_C[p["id"]]
                    custo_vencido_A += estoque_A[p["id"]] * p["custo"]
                    custo_vencido_B += estoque_B[p["id"]] * p["custo"]
                    custo_vencido_C += estoque_C[p["id"]] * p["custo"]
                    custo_A += estoque_A[p["id"]] * p["custo"]
                    custo_B += estoque_B[p["id"]] * p["custo"]
                    custo_C += estoque_C[p["id"]] * p["custo"]

                    estoque_A[p["id"]] = 0
                    estoque_B[p["id"]] = 0
                    estoque_C[p["id"]] = 0
                    continue
                elif dias_para_vencer < -1:
                    continue

                # ==========================
                # DEFINIÇÃO DOS PREÇOS DO DIA
                # ==========================
                # CENÁRIO A: Fixo
                preco_A = p["preco_base"]
                
                # CENÁRIO B: Regra Simples Progressiva (Forte)
                if dias_para_vencer <= 2:
                    preco_B = p["preco_base"] * 0.70 # -30%
                elif dias_para_vencer <= 5:
                    preco_B = p["preco_base"] * 0.80 # -20%
                elif dias_para_vencer <= 10:
                    preco_B = p["preco_base"] * 0.90 # -10%
                else:
                    preco_B = p["preco_base"]
                    
                # CENÁRIO C: Motor SGPV
                preco_C = p["preco_base"]
                g = giro_C[p["id"]]
                # R1: Baixo giro
                if usar_regra_1 and g < p["L"]:
                    preco_C *= 0.95
                    disparos["R1"] += 1
                # R2: Alto giro
                elif usar_regra_2 and g >= 2 * p["L"] and p["preco_base"] < p["C"]:
                    preco_C *= 1.02
                    disparos["R2"] += 1
                # R3: Validade próxima
                if usar_regra_3 and dias_para_vencer <= p["V"]:
                    preco_C *= 0.90
                    disparos["R3"] += 1
                # R4: Concorrência
                if usar_regra_4 and preco_C > p["C"]:
                    preco_C = p["C"]
                    disparos["R4"] += 1
                # R5: Trava de Margem
                piso = p["custo"] * (1 + p["M"]/100.0)
                if usar_regra_5 and preco_C < piso:
                    preco_C = piso
                    disparos["R5"] += 1
                preco_C = round(preco_C, 2)
                
                # ==========================
                # SIMULAÇÃO DE DEMANDA (COM ELASTICIDADE)
                # ==========================
                # Demanda base normal(3, 1.5)
                demanda_base = max(0, int(np.random.normal(demanda_media, demanda_desvio)))
                
                def calcular_venda(preco_praticado, estoque_atual):
                    if estoque_atual <= 0: return 0
                    variacao_preco = (preco_praticado - p["preco_base"]) / p["preco_base"]
                    # Formula da elasticidade: nova_demanda = base * (1 - elasticidade * variacao)
                    demanda_ajustada = demanda_base * (1 - elasticidade * variacao_preco)
                    demanda_efetiva = (
                        int(demanda_ajustada) if truncar_demanda else demanda_ajustada
                    )
                    venda_real = min(estoque_atual, max(0, demanda_efetiva))
                    return venda_real

                venda_A = calcular_venda(preco_A, estoque_A[p["id"]])
                venda_B = calcular_venda(preco_B, estoque_B[p["id"]])
                venda_C = calcular_venda(preco_C, estoque_C[p["id"]])

                vendidos_A += venda_A
                vendidos_B += venda_B
                vendidos_C += venda_C
                if dias_para_vencer >= 0:
                    rupturas_A += int(venda_A == 0 and demanda_base > 0 and estoque_A[p["id"]] == 0)
                    rupturas_B += int(venda_B == 0 and demanda_base > 0 and estoque_B[p["id"]] == 0)
                    rupturas_C += int(venda_C == 0 and demanda_base > 0 and estoque_C[p["id"]] == 0)
                
                # Atualiza estoques, receitas e custos das unidades vendidas
                estoque_A[p["id"]] -= venda_A
                estoque_B[p["id"]] -= venda_B
                estoque_C[p["id"]] -= venda_C
                
                giro_C[p["id"]] += venda_C
                
                receita_A += venda_A * preco_A
                receita_B += venda_B * preco_B
                receita_C += venda_C * preco_C

                custo_A += venda_A * p["custo"]
                custo_B += venda_B * p["custo"]
                custo_C += venda_C * p["custo"]

        # Estoque não vencido permanece como ativo e não impacta o resultado simulado
        resultados_A.append(receita_A - custo_A)
        resultados_B.append(receita_B - custo_B)
        resultados_C.append(receita_C - custo_C)
        unidades_vencidas["A"].append(unidades_vencidas_A)
        unidades_vencidas["B"].append(unidades_vencidas_B)
        unidades_vencidas["C"].append(unidades_vencidas_C)
        custos_vencidos["A"].append(custo_vencido_A)
        custos_vencidos["B"].append(custo_vencido_B)
        custos_vencidos["C"].append(custo_vencido_C)
        estoque_remanescente["A"].append(sum(estoque_A.values()))
        estoque_remanescente["B"].append(sum(estoque_B.values()))
        estoque_remanescente["C"].append(sum(estoque_C.values()))
        custo_remanescente["A"].append(sum(p["custo"] * estoque_A[p["id"]] for p in catalogo_atual))
        custo_remanescente["B"].append(sum(p["custo"] * estoque_B[p["id"]] for p in catalogo_atual))
        custo_remanescente["C"].append(sum(p["custo"] * estoque_C[p["id"]] for p in catalogo_atual))
        unidades_vendidas["A"].append(vendidos_A)
        unidades_vendidas["B"].append(vendidos_B)
        unidades_vendidas["C"].append(vendidos_C)
        rupturas["A"].append(rupturas_A)
        rupturas["B"].append(rupturas_B)
        rupturas["C"].append(rupturas_C)
        for nome in disparos_regras:
            disparos_regras[nome].append(disparos[nome])
        
    resultados = (np.array(resultados_A), np.array(resultados_B), np.array(resultados_C))
    if not retornar_detalhes:
        return resultados

    detalhes = {
        "unidades_vencidas": {
            nome: np.array(valores) for nome, valores in unidades_vencidas.items()
        },
        "custos_vencidos": {
            nome: np.array(valores) for nome, valores in custos_vencidos.items()
        },
        "estoque_remanescente": {
            nome: np.array(valores) for nome, valores in estoque_remanescente.items()
        },
        "custo_remanescente": {
            nome: np.array(valores) for nome, valores in custo_remanescente.items()
        },
        "unidades_vendidas": {
            nome: np.array(valores) for nome, valores in unidades_vendidas.items()
        },
        "rupturas": {nome: np.array(valores) for nome, valores in rupturas.items()},
        "disparos_regras": {
            nome: np.array(valores) for nome, valores in disparos_regras.items()
        },
    }
    return (*resultados, detalhes)

# ==========================================
# 3. RELATÓRIO REPRODUTÍVEL
# ==========================================
def intervalo_confianca(diferencas):
    media = np.mean(diferencas)
    margem = st.t.ppf(0.975, len(diferencas) - 1) * st.sem(diferencas)
    return media, media - margem, media + margem


def imprimir_tabela_principal(elasticidade, resultados):
    res_A, res_B, res_C, _ = resultados
    print(f"\n=== TABELA 1: RESULTADOS (Elasticidade = {elasticidade:.1f}) ===")
    for nome, valores in (("A (Controle)", res_A), ("B (Progressivo)", res_B), ("C (Motor SGPV)", res_C)):
        print(f"Cenário {nome}: Média = R$ {np.mean(valores):.2f} | Std = R$ {np.std(valores):.2f}")


def imprimir_intervalos(elasticidades, resultados_por_elasticidade):
    print("\n=== TABELA 2: INTERVALOS PAREADOS (IC 95%) ===")
    print("Elasticidade | A - B (média; IC) | A - C (média; IC)")
    for elasticidade in elasticidades:
        res_A, res_B, res_C, _ = resultados_por_elasticidade[elasticidade]
        media_ab, inferior_ab, superior_ab = intervalo_confianca(res_A - res_B)
        media_ac, inferior_ac, superior_ac = intervalo_confianca(res_A - res_C)
        print(
            f"{elasticidade:11.1f} | "
            f"R$ {media_ab:,.2f} [{inferior_ab:,.2f}; {superior_ab:,.2f}] | "
            f"R$ {media_ac:,.2f} [{inferior_ac:,.2f}; {superior_ac:,.2f}]"
        )


def imprimir_ablation(elasticidade, resultado_base):
    media_base = np.mean(resultado_base[2])
    ablations = {
        "sem R1": {"usar_regra_1": False},
        "sem R2": {"usar_regra_2": False},
        "sem R3": {"usar_regra_3": False},
        "sem R4": {"usar_regra_4": False},
        "sem R5": {"usar_regra_5": False},
    }
    print(f"\n=== TABELA 3: ABLAÇÃO DO CENÁRIO C (Elasticidade = {elasticidade:.1f}) ===")
    print("Configuração | Média C | Variação contra C completo")
    print(f"completo     | R$ {media_base:,.2f} | R$ 0,00")
    for nome, configuracao in ablations.items():
        resultado = simular_monte_carlo(
            elasticidade=elasticidade,
            retornar_detalhes=True,
            **configuracao,
        )
        media = np.mean(resultado[2])
        print(f"{nome:12} | R$ {media:,.2f} | R$ {media - media_base:,.2f}")


def imprimir_perdas_validade(elasticidade, resultados):
    detalhes = resultados[3]
    print(f"\n=== TABELA 4: PERDAS POR VALIDADE (Elasticidade = {elasticidade:.1f}) ===")
    print("Cenário | Unidades vencidas | Custo vencido")
    for nome in ("A", "B", "C"):
        unidades = np.mean(detalhes["unidades_vencidas"][nome])
        custo = np.mean(detalhes["custos_vencidos"][nome])
        print(f"{nome:7} | {unidades:17.2f} | R$ {custo:,.2f}")


def imprimir_metricas_operacionais(resultados):
    detalhes = resultados[3]
    print("\n=== TABELA 5: MÉTRICAS OPERACIONAIS (Elasticidade = 1.5) ===")
    print("Cenário | Vendidas | Vencidas | Estoque final | Custo estoque final | Rupturas")
    for nome in ("A", "B", "C"):
        vendidas = np.mean(detalhes["unidades_vendidas"][nome])
        vencidas = np.mean(detalhes["unidades_vencidas"][nome])
        estoque = np.mean(detalhes["estoque_remanescente"][nome])
        custo = np.mean(detalhes["custo_remanescente"][nome])
        rupturas = np.mean(detalhes["rupturas"][nome])
        print(f"{nome:7} | {vendidas:8.2f} | {vencidas:8.2f} | {estoque:13.2f} | R$ {custo:17.2f} | {rupturas:8.2f}")

    print("\n=== TABELA 6: DISPAROS DAS REGRAS NO CENÁRIO C ===")
    for nome in ("R1", "R2", "R3", "R4", "R5"):
        disparos = np.mean(detalhes["disparos_regras"][nome])
        print(f"{nome}: {disparos:.2f} disparos médios por repetição")


def imprimir_sensibilidades(elasticidade=1.5):
    print("\n=== TABELA 7: SENSIBILIDADES DO CENÁRIO C ===")
    print("Variação | Parâmetro | Média C")
    for fator in (0.5, 1.0, 1.5):
        catalogo_estoque = [
            {**produto, "estoque": produto["estoque"] * fator} for produto in catalogo
        ]
        resultado = simular_monte_carlo(
            elasticidade=elasticidade,
            catalogo_simulacao=catalogo_estoque,
            retornar_detalhes=True,
        )
        print(f"estoque x{fator:.1f} | {fator:.1f}              | R$ {np.mean(resultado[2]):.2f}")

    for media in (2, 3, 4):
        resultado = simular_monte_carlo(
            elasticidade=elasticidade,
            demanda_media=media,
            retornar_detalhes=True,
        )
        print(f"demanda μ={media} | {media:.1f}              | R$ {np.mean(resultado[2]):.2f}")

    for fator in (0.5, 1.0, 1.5):
        catalogo_validade = [
            {**produto, "V": max(1, round(produto["V"] * fator))}
            for produto in catalogo
        ]
        resultado = simular_monte_carlo(
            elasticidade=elasticidade,
            catalogo_simulacao=catalogo_validade,
            retornar_detalhes=True,
        )
        print(f"janela V x{fator:.1f} | {fator:.1f}              | R$ {np.mean(resultado[2]):.2f}")

    for margem in (10, 20, 30, 40):
        catalogo_margem = [{**produto, "M": margem} for produto in catalogo]
        resultado = simular_monte_carlo(
            elasticidade=elasticidade,
            catalogo_simulacao=catalogo_margem,
            retornar_detalhes=True,
        )
        print(f"margem M={margem}% | {margem:.1f}              | R$ {np.mean(resultado[2]):.2f}")


def imprimir_comparacao_truncamento(elasticidade):
    print(f"\n=== TABELA 8: DEMANDA COM E SEM TRUNCAMENTO (Elasticidade = {elasticidade:.1f}) ===")
    print("Demanda | Cenário A | Cenário B | Cenário C")
    for truncar in (True, False):
        resultados = simular_monte_carlo(
            elasticidade=elasticidade,
            truncar_demanda=truncar,
            retornar_detalhes=True,
        )
        nome = "truncada" if truncar else "contínua"
        medias = [np.mean(resultados[indice]) for indice in range(3)]
        print(f"{nome:8} | R$ {medias[0]:,.2f} | R$ {medias[1]:,.2f} | R$ {medias[2]:,.2f}")


print("=== APÊNDICE: PARÂMETROS DOS 12 PRODUTOS ===")
df_cat = pd.DataFrame(catalogo)
print(df_cat[["id", "custo", "preco_base", "estoque", "validade_dias", "L", "M", "V", "C"]].to_string(index=False))
print("\nSemente: 42 | Repetições: 100 | Dias: 30")

elasticidades = (0.5, 1.5, 3.0)
resultados_por_elasticidade = {
    elasticidade: simular_monte_carlo(
        elasticidade=elasticidade,
        retornar_detalhes=True,
    )
    for elasticidade in elasticidades
}

imprimir_tabela_principal(1.5, resultados_por_elasticidade[1.5])
imprimir_intervalos(elasticidades, resultados_por_elasticidade)
imprimir_ablation(1.5, resultados_por_elasticidade[1.5])
imprimir_perdas_validade(1.5, resultados_por_elasticidade[1.5])
imprimir_metricas_operacionais(resultados_por_elasticidade[1.5])
imprimir_sensibilidades(1.5)
imprimir_comparacao_truncamento(1.5)