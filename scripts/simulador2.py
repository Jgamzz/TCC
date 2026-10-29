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
def simular_monte_carlo(elasticidade=1.5, n_repeticoes=100, dias=30, semente=42):
    np.random.seed(semente)
    
    resultados_A = []
    resultados_B = []
    resultados_C = []
    
    for _ in range(n_repeticoes):
        # Custo total de aquisição (investimento inicial, descartado se não vendido)
        custo_total_lote = sum(p["custo"] * p["estoque"] for p in catalogo)
        
        # Receitas acumuladas em cada cenário
        receita_A = 0
        receita_B = 0
        receita_C = 0
        
        # Copiar estoques para a iteração
        estoque_A = {p["id"]: p["estoque"] for p in catalogo}
        estoque_B = {p["id"]: p["estoque"] for p in catalogo}
        estoque_C = {p["id"]: p["estoque"] for p in catalogo}
        
        # Giro acumulado para a Regra do SGPV (Scenario C)
        giro_C = {p["id"]: 0 for p in catalogo}
        
        for dia in range(1, dias + 1):
            for p in catalogo:
                dias_para_vencer = p["validade_dias"] - dia
                
                # Se o produto venceu, zera o estoque (descarte)
                if dias_para_vencer < 0:
                    estoque_A[p["id"]] = 0
                    estoque_B[p["id"]] = 0
                    estoque_C[p["id"]] = 0
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
                if g < p["L"]: preco_C *= 0.95
                # R2: Alto giro
                elif g >= 2 * p["L"] and p["preco_base"] < p["C"]: preco_C *= 1.02
                # R3: Validade próxima
                if dias_para_vencer <= p["V"]: preco_C *= 0.90
                # R4: Concorrência
                preco_C = min(preco_C, p["C"])
                # R5: Trava de Margem
                piso = p["custo"] * (1 + p["M"]/100.0)
                preco_C = max(preco_C, piso)
                preco_C = round(preco_C, 2)
                
                # ==========================
                # SIMULAÇÃO DE DEMANDA (COM ELASTICIDADE)
                # ==========================
                # Demanda base normal(3, 1.5)
                demanda_base = max(0, int(np.random.normal(3, 1.5)))
                
                def calcular_venda(preco_praticado, estoque_atual):
                    if estoque_atual <= 0: return 0
                    variacao_preco = (preco_praticado - p["preco_base"]) / p["preco_base"]
                    # Formula da elasticidade: nova_demanda = base * (1 - elasticidade * variacao)
                    demanda_ajustada = demanda_base * (1 - elasticidade * variacao_preco)
                    venda_real = min(estoque_atual, max(0, int(demanda_ajustada)))
                    return venda_real

                venda_A = calcular_venda(preco_A, estoque_A[p["id"]])
                venda_B = calcular_venda(preco_B, estoque_B[p["id"]])
                venda_C = calcular_venda(preco_C, estoque_C[p["id"]])
                
                # Atualiza estoques e receitas
                estoque_A[p["id"]] -= venda_A
                estoque_B[p["id"]] -= venda_B
                estoque_C[p["id"]] -= venda_C
                
                giro_C[p["id"]] += venda_C
                
                receita_A += venda_A * preco_A
                receita_B += venda_B * preco_B
                receita_C += venda_C * preco_C
                
        # Fim dos 30 dias: Resultado = Receita - Investimento Inicial (Descartes = perda de custo)
        resultados_A.append(receita_A - custo_total_lote)
        resultados_B.append(receita_B - custo_total_lote)
        resultados_C.append(receita_C - custo_total_lote)
        
    return np.array(resultados_A), np.array(resultados_B), np.array(resultados_C)

# ==========================================
# 3. EXECUÇÃO E ANÁLISE ESTATÍSTICA
# ==========================================
print("=== APÊNDICE: PARÂMETROS DOS 12 PRODUTOS ===")
df_cat = pd.DataFrame(catalogo)
print(df_cat[['id', 'custo', 'preco_base', 'estoque', 'validade_dias', 'L', 'M', 'V', 'C']].to_string(index=False))
print("\n" + "="*50)

# Executar Simulação Principal (Elasticidade 1.5)
res_A, res_B, res_C = simular_monte_carlo(elasticidade=1.5)

media_A, std_A = np.mean(res_A), np.std(res_A)
media_B, std_B = np.mean(res_B), np.std(res_B)
media_C, std_C = np.mean(res_C), np.std(res_C)

print("\n=== RESULTADOS PRINCIPAIS (Tabela 1) - Elasticidade = 1.5 ===")
print(f"Cenário A (Controle) : Média = R$ {media_A:.2f} | Std = R$ {std_A:.2f}")
print(f"Cenário B (Progressivo): Média = R$ {media_B:.2f} | Std = R$ {std_B:.2f}")
print(f"Cenário C (Motor SGPV) : Média = R$ {media_C:.2f} | Std = R$ {std_C:.2f}")

# Intervalo de Confiança das Diferenças Pareadas (C - B)
diferencas = res_C - res_B
ci_95 = st.t.interval(0.95, len(diferencas)-1, loc=np.mean(diferencas), scale=st.sem(diferencas))
print(f"\n=== ESTATÍSTICA (Ponto 7) ===")
print(f"Ganho Médio (C - B): R$ {np.mean(diferencas):.2f}")
print(f"Intervalo de Confiança 95% do Ganho: (R$ {ci_95[0]:.2f}, R$ {ci_95[1]:.2f})")

# ==========================================
# 4. ANÁLISE DE SENSIBILIDADE (Ponto 1)
# ==========================================
print("\n=== ANÁLISE DE SENSIBILIDADE (Elasticidade Variável) ===")
for e in [0.5, 3.0]:
    _, rb, rc = simular_monte_carlo(elasticidade=e)
    ganho_perc = ((np.mean(rc) - np.mean(rb)) / abs(np.mean(rb))) * 100
    print(f"Elasticidade {e:.1f} -> Cenário B: R$ {np.mean(rb):.2f} | Cenário C: R$ {np.mean(rc):.2f} | Diferença: {ganho_perc:.2f}%")