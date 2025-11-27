"""
Debug do comportamento no mês 50+
"""
import sys
sys.path.insert(0, 'backend/services')
from simulation import get_default_params, run_simulation
import pandas as pd

print("="*80)
print("ANÁLISE DO COMPORTAMENTO A PARTIR DO MÊS 50")
print("="*80)

params = get_default_params()
print("\nParâmetros do cenário padrão:")
print(f"  Aporte Inicial: R$ {params['aporte_inicial_fundo']:,.2f}")
print(f"  Aportes Extras: {params['aportes_extra']}")
print(f"  Alavancagem Máxima: {params['alavancagem_maxima']}x")
print(f"  Operações Mensais Max: {params['Operacoes_qtd_mensal_max']}")
print(f"  Fator Retomada Pós-Trava: {params['Operacoes_fator_retomada_pos_trava']} (10%)")
print(f"  Meses até Max: {params['Operacoes_meses_ate_max']}")

print("\nExecutando simulação...")
df_carteira, df_fundo, df_operacoes = run_simulation(params)

print("\n" + "="*80)
print("ANÁLISE DOS MESES 45-60")
print("="*80)

colunas = ["mes", "operacoes_novas_mes", "valor_garantido_mes", "limite_operacional", 
           "saldo_fundo_depois_honra", "paused"]

df_analise = df_carteira[colunas].copy()
df_analise["uso_alavancagem_%"] = (df_analise["valor_garantido_mes"] / df_analise["limite_operacional"] * 100).round(1)
df_analise["folga"] = (df_analise["limite_operacional"] - df_analise["valor_garantido_mes"]).round(2)

print("\nMeses 45-60:")
print(df_analise.iloc[44:60].to_string(index=False))

print("\n" + "="*80)
print("DETALHAMENTO DO MÊS 50-55")
print("="*80)

for i in range(49, 55):
    mes_data = df_carteira.iloc[i]
    fundo_data = df_fundo.iloc[i]
    
    print(f"\n--- MÊS {mes_data['mes']} ---")
    print(f"  Operações geradas: {mes_data['operacoes_novas_mes']}")
    print(f"  Paused: {mes_data['paused']}")
    print(f"  Saldo Fundo: R$ {mes_data['saldo_fundo_depois_honra']:,.2f}")
    print(f"  Valor Garantido: R$ {mes_data['valor_garantido_mes']:,.2f}")
    print(f"  Limite Operacional: R$ {mes_data['limite_operacional']:,.2f}")
    print(f"  Uso Alavancagem: {mes_data['valor_garantido_mes']/mes_data['limite_operacional']*100:.1f}%")
    print(f"  Folga: R$ {mes_data['limite_operacional'] - mes_data['valor_garantido_mes']:,.2f}")
    print(f"  Aporte mês: R$ {fundo_data['aporte']:,.2f}")
    print(f"  Honras mês: R$ {fundo_data['pagamentos_honra']:,.2f}")
    print(f"  Recuperações mês: R$ {fundo_data['recuperacoes']:,.2f}")

print("\n" + "="*80)
print("RESUMO DAS RESTRIÇÕES")
print("="*80)

meses_com_restricoes = df_carteira[df_carteira["paused"] == True]
print(f"\nTotal de meses com restrições: {len(meses_com_restricoes)}")
print(f"Meses: {meses_com_restricoes['mes'].tolist()}")

# Identifica se há padrão de 10 operações (retomada)
meses_10_ops = df_carteira[df_carteira["operacoes_novas_mes"] == 10]
print(f"\nMeses com exatamente 10 operações (retomada): {len(meses_10_ops)}")
if len(meses_10_ops) > 0:
    print(f"Meses: {meses_10_ops['mes'].tolist()}")

print("\n" + "="*80)
