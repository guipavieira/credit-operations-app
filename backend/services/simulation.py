"""
Simulação de operações de crédito com alavancagem, garantias e inadimplência
Adaptado para Flask web application
"""

import pandas as pd
import numpy as np
import uuid
import math
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict, List
import json


def get_default_params() -> Dict:
    """Parâmetros padrão da simulação"""
    return {
        # horizonte e aportes
        "simulation_months": 60,
        "aporte_inicial_fundo": 1_000_000.0,
        "aporte_mensal": 0.0,
        "aportes_extra": [{"mes": 6, "valor": 5_000_000.0}, {"mes": 12, "valor": 14_000_000.0}],

        # start year for SELIC mapping
        "start_year": 2026,

        # prazos médios por porte (meses)
        "prazo_operacao_MEI": 36,
        "prazo_operacao_ME": 36,
        "prazo_operacao_EPP": 36,

        # percentuais de garantia por porte
        "percentual_garantia_MEI": 0.8,
        "percentual_garantia_ME": 0.8,
        "percentual_garantia_EPP": 0.8,

        # taxas de inadimplencia (probabilidade por operação)
        "taxa_inadimplencia_MEI": 0.22,
        "taxa_inadimplencia_ME": 0.1,
        "taxa_inadimplencia_EPP": 0.05,

        # alavancagem e limites
        "alavancagem_maxima": 3.0,

        # recuperacao / renegociação
        "taxa_recuperacao": 0.30,
        "prazo_medio_renegociacao": 12,
        "prazo_honra": 2,
        "prazo_recuperacao": 6,

        # juros e taxas
        "taxa_juros_media_anual_MEI": 0.20,
        "taxa_juros_media_anual_ME": 0.18,
        "taxa_juros_media_anual_EPP": 0.15,
        "taxa_juros_cv": 0.03,
        "taxa_concessao": 0.0015,

        # operação / tickets / proporções
        "faixas_operacoes": [
            {"capital_ate": 1_000_000, "max_ops_mensal": 10},
            {"capital_ate": 3_000_000, "max_ops_mensal": 15},
            {"capital_ate": 6_000_000, "max_ops_mensal": 30},
            {"capital_ate": 9_000_000, "max_ops_mensal": 40},
            {"capital_ate": 12_000_000, "max_ops_mensal": 50},
            {"capital_ate": 15_000_000, "max_ops_mensal": 70},
            {"capital_ate": 20_000_000, "max_ops_mensal": 100},
            {"capital_ate": 40_000_000, "max_ops_mensal": 200},
        ],
        "meses_rampa_crescimento": 6,
        "multiplicador_volume_operacoes": 1.0,
        "prop_MEI": 0.8,
        "prop_ME": 0.15,
        "prop_EPP": 0.05,
        "ticket_medio_MEI": 20_000,
        "ticket_medio_ME": 80_000,
        "ticket_medio_EPP": 150_000,
        "ticket_cv": 0.2,

        # amortização
        "sistema_amortizacao_choices": ["PRICE", "SAC"],
        "prop_PRICE": 0.5,
        "prop_SAC": 0.5,

        # SELIC (por anos)
        "Taxa_SELIC_2026": 0.125,
        "Taxa_SELIC_2027": 0.105,
        "Taxa_SELIC_2028": 0.10,
        "percentual_rendimento_selic": 0.95,  # 95% da SELIC

        # aleatoriedade
        "random_seed": 42
    }


def juros_anual_para_mensal(i_anual: float) -> float:
    """Converte taxa anual para mensal"""
    return (1 + i_anual) ** (1/12) - 1


def amortizacao_price(v: float, i_m: float, n: int):
    """Calcula parcelas e saldos no sistema PRICE"""
    if n <= 0:
        return [], []
    if i_m == 0:
        parcela = v / n
    else:
        parcela = v * (i_m * (1 + i_m) ** n) / ((1 + i_m) ** n - 1)
    parcelas = []
    saldos = []
    saldo = v
    for k in range(1, n + 1):
        juros = saldo * i_m
        amort = parcela - juros
        saldo = max(0.0, saldo - amort)
        parcelas.append(parcela)
        saldos.append(saldo)
    return parcelas, saldos


def amortizacao_sac(v: float, i_m: float, n: int):
    """Calcula parcelas e saldos no sistema SAC"""
    if n <= 0:
        return [], []
    amort_const = v / n
    parcelas = []
    saldos = []
    saldo = v
    for k in range(1, n + 1):
        juros = saldo * i_m
        parcela = amort_const + juros
        saldo = max(0.0, saldo - amort_const)
        parcelas.append(parcela)
        saldos.append(saldo)
    return parcelas, saldos


def sigmoid_ramp(month: int, max_month: int, steepness: float = 0.9):
    """Rampa sigmoide para crescimento suave de operações"""
    mid = max_month * 0.6
    k = max(0.05, steepness)
    x = month - mid
    s = 1.0 / (1.0 + math.exp(-k * x))
    denom = 1.0 / (1.0 + math.exp(-k * (max_month - mid)))
    if denom == 0:
        return min(1.0, s)
    return min(1.0, s / denom)


def escolher_parcela_inadimplencia(prazo: int) -> int:
    """
    Distribui a parcela da inadimplência segundo:
      - 33% na 1ª parcela (First Payment Default)
      - 33% nas parcelas 2 e 3 (66% acumulado até a 3ª)
      - 20% nas parcelas 4 a 12 (86% acumulado até o 12º mês)
      - 14% restante distribuído uniformemente do mês 13 até o fim do prazo
    """
    r = np.random.rand()
    
    # 33% inadimplência na 1ª parcela (First Payment Default)
    if r < 0.33:
        return 1
    
    # 33% inadimplência nas parcelas 2 e 3 (acumulado: 66%)
    elif r < 0.66:
        max_parcela = min(3, prazo)
        if max_parcela >= 2:
            return np.random.randint(2, max_parcela + 1)
        else:
            return 1
    
    # 20% inadimplência nas parcelas 4 a 12 (acumulado: 86%)
    elif r < 0.86:
        max_parcela = min(12, prazo)
        if max_parcela >= 4:
            return np.random.randint(4, max_parcela + 1)
        elif max_parcela >= 2:
            return np.random.randint(2, max_parcela + 1)
        else:
            return 1
    
    # 14% inadimplência do mês 13 em diante
    else:
        if prazo >= 13:
            return np.random.randint(13, prazo + 1)
        elif prazo >= 4:
            return np.random.randint(4, prazo + 1)
        elif prazo >= 2:
            return np.random.randint(2, prazo + 1)
        else:
            return 1



def calcular_ops_max_por_capital(aportes_acumulados: float, faixas: List[Dict]) -> int:
    """
    Calcula o número máximo de operações mensais baseado no capital acumulado.
    Implementa o efeito 'stair step'.
    
    Args:
        aportes_acumulados: Valor total de aportes acumulados até o momento
        faixas: Lista de faixas de capital com seus respectivos limites de operações
    
    Returns:
        Número máximo de operações mensais para o capital atual
    """
    faixas_ordenadas = sorted(faixas, key=lambda x: x["capital_ate"])
    
    for faixa in faixas_ordenadas:
        if aportes_acumulados <= faixa["capital_ate"]:
            return int(faixa["max_ops_mensal"])
    
    # Se exceder todas as faixas, retorna o máximo da última faixa
    return int(faixas_ordenadas[-1]["max_ops_mensal"])


def run_simulation(params: Dict):
    """Executa a simulação completa"""
    np.random.seed(params["random_seed"])

    months = params["simulation_months"]
    start_year = params.get("start_year", 2026)

    # estruturas para operações
    ops: List[Dict] = []
    amort_map = {}
    parcelas_map = {}
    status_map = {}
    pointer_map = {}
    scheduled_honras = {}
    scheduled_recuperacoes = {}

    # indicadores acumulados
    carteira_rows = []
    fundo_rows = []

    # fund state
    saldo_fundo = params["aporte_inicial_fundo"]
    cumulative_desembolso = 0.0
    cumulative_honras = 0.0
    cumulative_recuperacoes = 0.0
    cumulative_inadimplentes = 0
    paused = False

    # set to avoid double counting defaults
    counted_defaults = set()
    
    # Histórico para índice SGC (janela móvel de 60 meses)
    honras_por_mes = {}  # {mes: valor_honrado}
    recuperacoes_por_mes = {}  # {mes: valor_recuperado}
    avais_concedidos_por_mes = {}  # {mes: valor_total_garantido_concedido}

    def generate_new_ops(n_new, mes, params):
        """Gera novas operações"""
        new_ids = []
        for _ in range(n_new):
            opid = str(uuid.uuid4())
            r = np.random.rand()
            if r < params["prop_MEI"]:
                porte = "MEI"
                ticket_mean = params["ticket_medio_MEI"]
                garantia_pct = params["percentual_garantia_MEI"]
                prazo_mean = params["prazo_operacao_MEI"]
                taxa_inad = params["taxa_inadimplencia_MEI"]
                taxa_juros_media = params["taxa_juros_media_anual_MEI"]
            elif r < params["prop_MEI"] + params["prop_ME"]:
                porte = "ME"
                ticket_mean = params["ticket_medio_ME"]
                garantia_pct = params["percentual_garantia_ME"]
                prazo_mean = params["prazo_operacao_ME"]
                taxa_inad = params["taxa_inadimplencia_ME"]
                taxa_juros_media = params["taxa_juros_media_anual_ME"]
            else:
                porte = "EPP"
                ticket_mean = params["ticket_medio_EPP"]
                garantia_pct = params["percentual_garantia_EPP"]
                prazo_mean = params["prazo_operacao_EPP"]
                taxa_inad = params["taxa_inadimplencia_EPP"]
                taxa_juros_media = params["taxa_juros_media_anual_EPP"]

            sigma = params["ticket_cv"] * ticket_mean
            valor_solicitado = max(500.0, np.random.normal(ticket_mean, sigma))
            valor_financiado = valor_solicitado * (1 + params["taxa_concessao"])
            prazo = max(1, int(round(np.random.normal(prazo_mean, max(1, prazo_mean * 0.1)))))
            taxa_juros_anual = max(0.0, np.random.normal(taxa_juros_media, 
                                                         params["taxa_juros_cv"] * taxa_juros_media))
            taxa_juros_mensal = juros_anual_para_mensal(taxa_juros_anual)
            
            # Escolhe sistema baseado nas proporções
            r_sistema = np.random.rand()
            if r_sistema < params.get("prop_PRICE", 0.5):
                sistema = "PRICE"
            else:
                sistema = "SAC"

            if sistema == "PRICE":
                parcelas, saldos = amortizacao_price(valor_financiado, taxa_juros_mensal, prazo)
            else:
                parcelas, saldos = amortizacao_sac(valor_financiado, taxa_juros_mensal, prazo)

            is_default = np.random.rand() < taxa_inad
            mes_inad = None
            parcela_inad = None
            saldo_devedor_inad = None
            valor_honrado = None
            status = "Ativa"
            
            if is_default:
                parcela_inad = escolher_parcela_inadimplencia(prazo)
                mes_inad = mes + parcela_inad - 1
                
                # Saldo devedor no momento da inadimplência (antes da parcela inadimplente)
                # Se inadimplência na 1ª parcela, o saldo é o valor financiado
                # Se inadimplência na parcela k>1, o saldo é saldos[k-2] (após pagar k-1 parcelas)
                if parcela_inad == 1:
                    saldo_devedor_inad = valor_financiado
                else:
                    saldo_devedor_inad = saldos[parcela_inad - 2]
                
                valor_honrado = saldo_devedor_inad * garantia_pct
                status = "Inadimplente"

            op = {
                "id_operacao": opid,
                "porte": porte,
                "mes_contratacao": mes,
                "valor_solicitado": round(float(valor_solicitado), 2),
                "valor_financiado": round(float(valor_financiado), 2),
                "percentual_garantia": garantia_pct,
                "prazo_operacao": int(prazo),
                "status_operacao_initial": status,
                "mes_inadimplencia": int(mes_inad) if mes_inad is not None else None,
                "sistema_amortizacao": sistema,
                "taxa_de_juros_mensal": round(float(taxa_juros_mensal), 8),
                "taxa_de_juros_anual": round(float(taxa_juros_anual), 6),
                "_parcelas_list": parcelas,
                "_saldos_list": saldos,
                "_parcela_inad": int(parcela_inad) if parcela_inad is not None else None,
                "_saldo_devedor_inad": float(saldo_devedor_inad) if saldo_devedor_inad is not None else None,
                "_valor_honrado": float(valor_honrado) if valor_honrado is not None else None
            }
            ops.append(op)
            amort_map[opid] = saldos
            parcelas_map[opid] = parcelas
            status_map[opid] = "Ativa" if status == "Ativa" else "Inadimplente"
            pointer_map[opid] = 0

            if status == "Inadimplente" and mes_inad is not None:
                mes_honra = mes_inad + params["prazo_honra"]
                scheduled_honras.setdefault(mes_honra, []).append((opid, float(valor_honrado)))

            new_ids.append(opid)
        return new_ids

    def compute_valor_garantido_mes(current_month):
        """Calcula valor garantido total no mês"""
        total_garantia = 0.0
        for op in ops:
            opid = op["id_operacao"]
            if op["mes_contratacao"] > current_month:
                continue
            st = status_map.get(opid, "Ativa")
            if st in ("Honrada", "Quitada"):
                continue
            saldos = amort_map.get(opid, [])
            ptr = pointer_map.get(opid, 0)
            if ptr >= len(saldos):
                continue
            saldo = saldos[ptr]
            garantia = saldo * float(op["percentual_garantia"])
            total_garantia += garantia
        return total_garantia

    # Pre-build map for extra aportes
    aportes_map = {}
    for ap in params.get("aportes_extra", []):
        m = int(ap["mes"])
        v = float(ap["valor"])
        aportes_map.setdefault(m, 0.0)
        aportes_map[m] += v

    # Controle de rampa dinâmica
    max_ops_faixa_anterior = 0  # Máximo da faixa anterior
    max_ops_faixa_atual = 0  # Máximo da faixa atual
    mes_mudanca_faixa = 0  # Mês em que ocorreu a última mudança de faixa
    meses_rampa = params.get("meses_rampa_crescimento", 6)

    # simulate months
    for mes in range(1, months + 1):
        # dynamic SELIC for this month
        year = start_year + (mes - 1) // 12
        selic_key = f"Taxa_SELIC_{year}"
        selic_anual = params.get(selic_key, params.get("Taxa_SELIC_2028", 0.10))
        selic_mensal = juros_anual_para_mensal(selic_anual)
        
        # Aplica percentual de rendimento (ex: 95% da SELIC)
        percentual_rendimento = params.get("percentual_rendimento_selic", 0.95)
        selic_mensal_efetiva = selic_mensal * percentual_rendimento

        # Calcula aportes acumulados até este mês
        aportes_acumulados = params["aporte_inicial_fundo"]
        aportes_acumulados += params.get("aporte_mensal", 0.0) * mes
        for ap in params.get("aportes_extra", []):
            if int(ap["mes"]) <= mes:
                aportes_acumulados += float(ap["valor"])

        # Determina o teto máximo baseado no capital (stair step)
        max_ops_faixa_nova = calcular_ops_max_por_capital(
            aportes_acumulados, 
            params.get("faixas_operacoes", [])
        )

        # Detecta mudança de faixa (novo aporte que eleva o teto)
        if max_ops_faixa_nova > max_ops_faixa_atual:
            max_ops_faixa_anterior = max_ops_faixa_atual
            max_ops_faixa_atual = max_ops_faixa_nova
            mes_mudanca_faixa = mes

        # Calcula rampa de crescimento gradual
        # Se mudou de faixa recentemente, cresce do nível anterior ao novo em 'meses_rampa' meses
        if mes < mes_mudanca_faixa + meses_rampa:
            meses_desde_mudanca = mes - mes_mudanca_faixa
            progresso = meses_desde_mudanca / meses_rampa  # 0 a 1
            # Interpolação linear entre faixa anterior e atual
            target_ops_this_month = int(round(
                max_ops_faixa_anterior + (max_ops_faixa_atual - max_ops_faixa_anterior) * progresso
            ))
        else:
            # Após rampa completa, usa o teto da faixa atual
            target_ops_this_month = max_ops_faixa_atual
        
        # Aplica multiplicador de volume de operações
        multiplicador = params.get("multiplicador_volume_operacoes", 1.0)
        target_ops_this_month = int(round(target_ops_this_month * multiplicador))

        limite_operacional = saldo_fundo * params["alavancagem_maxima"]
        valor_garantido_at_start = compute_valor_garantido_mes(mes)

        # Calcula quantas operações são viáveis baseado em capacidade
        # Se valor garantido já excedeu limite, não gera operações
        if valor_garantido_at_start > limite_operacional:
            ops_to_generate = 0
        else:
            ops_to_generate = target_ops_this_month

        # capacity cap based on average guarantee
        avg_ticket = (params["ticket_medio_MEI"] * params["prop_MEI"] +
                      params["ticket_medio_ME"] * params["prop_ME"] +
                      params["ticket_medio_EPP"] * params["prop_EPP"])
        avg_fin = avg_ticket * (1 + params["taxa_concessao"])
        avg_garantia_por_op = avg_fin * (params["prop_MEI"] * params["percentual_garantia_MEI"] +
                                         params["prop_ME"] * params["percentual_garantia_ME"] +
                                         params["prop_EPP"] * params["percentual_garantia_EPP"])
        capacidade_restante = max(0.0, limite_operacional - valor_garantido_at_start)
        max_ops_by_capacidade = int(capacidade_restante // max(1.0, avg_garantia_por_op))
        ops_to_generate = min(ops_to_generate, max_ops_by_capacidade)
        
        # Marca como restrito se não conseguiu gerar o volume pretendido
        paused = (ops_to_generate < target_ops_this_month) and (target_ops_this_month > 0)

        # generate operations
        new_ids = generate_new_ops(ops_to_generate, mes, params)

        # desembolso mes
        desembolso_mes = sum([op["valor_financiado"] for op in ops if op["mes_contratacao"] == mes])
        cumulative_desembolso += desembolso_mes
        
        # Calcula valor total de avais concedidos neste mês (para índice SGC)
        avais_concedidos_mes = 0.0
        for op in ops:
            if op["mes_contratacao"] == mes:
                # Aval concedido = valor financiado × percentual de garantia
                avais_concedidos_mes += op["valor_financiado"] * op["percentual_garantia"]
        avais_concedidos_por_mes[mes] = avais_concedidos_mes

        # Count new defaults this month
        novas_inadimplencias_this_month = 0
        for op in ops:
            mid = op.get("mes_inadimplencia")
            if mid == mes and op["id_operacao"] not in counted_defaults:
                novas_inadimplencias_this_month += 1
                counted_defaults.add(op["id_operacao"])

        # process payments
        parcelas_recebidas = 0.0
        operacoes_ativas_count = 0
        for op in ops:
            opid = op["id_operacao"]
            contrat_mes = int(op["mes_contratacao"])
            if contrat_mes > mes:
                continue
            st = status_map.get(opid, "Ativa")
            if st in ("Honrada", "Quitada"):
                continue
            parcelas = parcelas_map.get(opid, [])
            ptr = pointer_map.get(opid, 0)
            
            if op.get("status_operacao_initial") == "Inadimplente":
                payment_count = mes - contrat_mes + 1
                parcela_inad = op.get("_parcela_inad")
                if parcela_inad is not None and payment_count >= parcela_inad:
                    operacoes_ativas_count += 1
                    continue
                else:
                    parcela_val = parcelas[ptr] if ptr < len(parcelas) else 0.0
                    parcelas_recebidas += parcela_val
                    pointer_map[opid] = ptr + 1
                    if pointer_map[opid] >= len(parcelas):
                        status_map[opid] = "Quitada"
                    operacoes_ativas_count += 1
                    continue
            else:
                parcela_val = parcelas[ptr] if ptr < len(parcelas) else 0.0
                parcelas_recebidas += parcela_val
                pointer_map[opid] = ptr + 1
                if pointer_map[opid] >= len(parcelas):
                    status_map[opid] = "Quitada"
                operacoes_ativas_count += 1

        cumulative_inadimplentes += novas_inadimplencias_this_month

        # process scheduled honras
        honras_list = scheduled_honras.get(mes, [])
        honras_total = sum([h[1] for h in honras_list]) if honras_list else 0.0
        honras_por_mes[mes] = honras_total  # Armazena para índice SGC
        for (opid, valor_h) in honras_list:
            status_map[opid] = "Honrada"
            pointer_map[opid] = 10**9
            cumulative_honras += valor_h
            recuper_total = valor_h * params["taxa_recuperacao"]
            if recuper_total > 0:
                start_rec = mes + params["prazo_recuperacao"]
                parcelas_rec = max(1, int(params["prazo_medio_renegociacao"]))
                mensal_rec = recuper_total / parcelas_rec
                for t in range(parcelas_rec):
                    scheduled_recuperacoes.setdefault(start_rec + t, []).append((opid, mensal_rec))

        # process recoveries this month
        recuperacoes_list = scheduled_recuperacoes.get(mes, [])
        recuperacoes_total = sum([r[1] for r in recuperacoes_list]) if recuperacoes_list else 0.0
        recuperacoes_por_mes[mes] = recuperacoes_total  # Armazena para índice SGC
        cumulative_recuperacoes += recuperacoes_total

        # aporte(s) this month
        aporte = float(params.get("aporte_mensal", 0.0)) + float(aportes_map.get(mes, 0.0))

        # Fundo: rendimento + aporte + recuperações - honras
        rendimento = saldo_fundo * selic_mensal_efetiva
        saldo_antes = saldo_fundo + rendimento + aporte + recuperacoes_total
        saldo_fundo = max(0.0, saldo_antes - honras_total)

        # valor garantido atual
        valor_garantido_mes = compute_valor_garantido_mes(mes)
        limite_operacional = saldo_fundo * params["alavancagem_maxima"]

        # saldo devedor carteira
        soma_saldos = 0.0
        for oid, ptr in pointer_map.items():
            saldos = amort_map.get(oid, [])
            if ptr < len(saldos):
                soma_saldos += saldos[ptr]
        
        # Calcula taxa de inadimplência por quantidade e por valor
        qtd_ops_inadimplentes_materializadas = 0
        qtd_ops_contratadas_total = 0
        saldo_devedor_ops_inadimplentes = 0.0
        valor_ops_contratadas_total = 0.0
        
        for op in ops:
            opid = op["id_operacao"]
            contrat_mes = op["mes_contratacao"]
            
            # Só considera operações já contratadas até este mês
            if contrat_mes > mes:
                continue
            
            qtd_ops_contratadas_total += 1
            valor_ops_contratadas_total += op["valor_financiado"]
            
            # Verifica se operação é inadimplente e já inadimpliu de fato
            if op.get("status_operacao_initial") == "Inadimplente":
                mes_inad = op.get("mes_inadimplencia")
                
                # Conta apenas operações que JÁ INADIMPLIRAM
                if mes_inad is not None and mes_inad <= mes:
                    qtd_ops_inadimplentes_materializadas += 1
                    # Usa o saldo devedor no momento da inadimplência
                    saldo_devedor_inad = op.get("_saldo_devedor_inad", 0.0)
                    saldo_devedor_ops_inadimplentes += saldo_devedor_inad
        
        # Taxa de Inadimplência por Quantidade: operações que JÁ inadimpliram / total de operações contratadas
        taxa_inadimplencia_qtd = (qtd_ops_inadimplentes_materializadas / qtd_ops_contratadas_total) if qtd_ops_contratadas_total > 0 else 0.0
        
        # Taxa de Inadimplência por Valor: saldo devedor das operações inadimplentes / total de valores contratados
        taxa_inadimplencia_valor = (saldo_devedor_ops_inadimplentes / valor_ops_contratadas_total) if valor_ops_contratadas_total > 0 else 0.0
        
        # Índice SGC: janela móvel de 60 meses
        # Soma valores dos últimos 60 meses (ou desde o início se < 60 meses)
        janela_inicio = max(1, mes - 59)  # Últimos 60 meses incluindo o mês atual
        
        honras_janela = sum([honras_por_mes.get(m, 0.0) for m in range(janela_inicio, mes + 1)])
        recuperacoes_janela = sum([recuperacoes_por_mes.get(m, 0.0) for m in range(janela_inicio, mes + 1)])
        avais_janela = sum([avais_concedidos_por_mes.get(m, 0.0) for m in range(janela_inicio, mes + 1)])
        
        # Índice SGC = (Honras - Recuperações) / Avais Concedidos (últimos 60 meses)
        indice_sgc = ((honras_janela - recuperacoes_janela) / avais_janela) if avais_janela > 0 else 0.0

        # carteira row
        ticket_medio_mes = (desembolso_mes / max(1, len([o for o in ops if o["mes_contratacao"] == mes]))) \
                           if desembolso_mes > 0 else 0.0

        carteira_rows.append({
            "mes": mes,
            "operacoes_ativas": int(operacoes_ativas_count),
            "operacoes_inadimplentes_novas": int(novas_inadimplencias_this_month),
            "operacoes_realizadas_acum": int(len([o for o in ops if o["mes_contratacao"] <= mes])),
            "desembolso_mes": round(float(desembolso_mes), 2),
            "desembolso_acum": round(float(cumulative_desembolso), 2),
            "ticket_medio_mes": round(float(ticket_medio_mes), 2),
            "saldo_devedor_carteira": round(float(soma_saldos), 2),
            "valor_garantido_mes": round(float(valor_garantido_mes), 2),
            "valor_garantido_acum": round(float(valor_garantido_mes), 2),
            "valor_honrado_mes": round(float(honras_total), 2),
            "valor_recuperado_mes": round(float(recuperacoes_total), 2),
            "honras_acumuladas": round(float(cumulative_honras), 2),
            "recuperacoes_acumuladas": round(float(cumulative_recuperacoes), 2),
            "taxa_inadimplencia_qtd": round(float(taxa_inadimplencia_qtd), 4),
            "taxa_inadimplencia_valor": round(float(taxa_inadimplencia_valor), 4),
            "indice_sgc": round(float(indice_sgc), 4),
            "avais_concedidos_mes": round(float(avais_concedidos_mes), 2),
            "avais_concedidos_janela_60m": round(float(avais_janela), 2),
            "percentual_garantia_real": round(float((valor_garantido_mes / soma_saldos) if soma_saldos > 0 else 0), 4),
            "operacoes_novas_mes": int(len([o for o in ops if o["mes_contratacao"] == mes])),
            "quitadas_mes": int(len([oid for oid, s in status_map.items() if s == "Quitada"])),
            "parcelas_recebidas_mes": round(float(parcelas_recebidas), 2),
            "saldo_fundo_antes_honra": round(float(saldo_antes), 2),
            "saldo_fundo_depois_honra": round(float(saldo_fundo), 2),
            "limite_operacional": round(float(limite_operacional), 2),
            "paused": bool(paused)
        })

        # fundo row
        fundo_rows.append({
            "mes": mes,
            "aporte": round(float(aporte), 2),
            "rendimento": round(float(rendimento), 2),
            "pagamentos_honra": round(float(honras_total), 2),
            "recuperacoes": round(float(recuperacoes_total), 2),
            "saldo_final": round(float(saldo_fundo), 2),
            "saldo_garantido": round(float(valor_garantido_mes), 2),
            "alavancagem_real": round(float((valor_garantido_mes / saldo_fundo) if saldo_fundo > 0 else 0), 4),
            "limite_operacional": round(float(limite_operacional), 2)
        })

    df_carteira = pd.DataFrame(carteira_rows)
    df_fundo = pd.DataFrame(fundo_rows)
    
    # Cria DataFrame de operações completo
    df_ops_summary = []
    for op in ops:  # Todas as operações
        df_ops_summary.append({
            "id_operacao": op["id_operacao"][:8],  # Primeiros 8 caracteres do ID
            "porte": op["porte"],
            "mes_contratacao": op["mes_contratacao"],
            "valor_solicitado": op["valor_solicitado"],
            "valor_financiado": op["valor_financiado"],
            "prazo_operacao": op["prazo_operacao"],
            "taxa_juros_anual": op["taxa_de_juros_anual"],
            "sistema_amortizacao": op["sistema_amortizacao"],
            "percentual_garantia": op["percentual_garantia"],
            "status": op["status_operacao_initial"],
            "mes_inadimplencia": op.get("mes_inadimplencia") if op.get("mes_inadimplencia") is not None else "",
            "parcela_inadimplente": op.get("_parcela_inad") if op.get("_parcela_inad") is not None else "",
            "saldo_devedor_inad": round(op.get("_saldo_devedor_inad"), 2) if op.get("_saldo_devedor_inad") is not None else "",
            "valor_honrado": round(op.get("_valor_honrado"), 2) if op.get("_valor_honrado") is not None else ""
        })
    df_operacoes = pd.DataFrame(df_ops_summary)

    return df_carteira, df_fundo, df_operacoes


def generate_plotly_chart(df_carteira: pd.DataFrame, df_fundo: pd.DataFrame) -> dict:
    """Gera gráfico interativo com Plotly"""
    
    fig = make_subplots(
        rows=1, cols=1,
        specs=[[{"secondary_y": True}]]
    )

    # Converte para listas Python nativas para garantir serialização JSON
    months = df_carteira["mes"].tolist()
    saldo_fundo = df_fundo["saldo_final"].tolist()
    valor_garantido = df_carteira["valor_garantido_acum"].tolist()
    honras_acum = df_carteira["honras_acumuladas"].tolist()
    recuperacoes_acum = df_carteira["recuperacoes_acumuladas"].tolist()
    inad_cum = df_carteira["operacoes_inadimplentes_novas"].cumsum().tolist()
    indice_sgc = df_carteira["indice_sgc"].tolist()
    taxa_inad_qtd = df_carteira["taxa_inadimplencia_qtd"].tolist()
    taxa_inad_valor = df_carteira["taxa_inadimplencia_valor"].tolist()
    ops_novas_mes = df_carteira["operacoes_novas_mes"].tolist()
    paused_list = df_carteira["paused"].tolist()
    
    # Define cores das barras: laranja para meses com restrição, azul para normais
    bar_colors = ['orange' if p else 'lightblue' for p in paused_list]

    # IMPORTANTE: Adicionar barras PRIMEIRO para ficarem no fundo (atrás das linhas)
    fig.add_trace(
        go.Bar(x=months, y=ops_novas_mes, 
               name="Operações Novas (qtd/mês)", 
               marker=dict(color=bar_colors, opacity=0.4),
               hovertemplate='Operações: %{y}<br>Status: <i>%{customdata}</i><extra></extra>',
               customdata=['Com restrição' if p else 'Normal' for p in paused_list]),
        secondary_y=True
    )

    # Eixo esquerdo (valores monetários) - linhas com mais destaque
    fig.add_trace(
        go.Scatter(x=months, y=saldo_fundo, 
                   name="Saldo Fundo (R$)", 
                   line=dict(width=2.5, color='#1f77b4'),
                   mode='lines',
                   hovertemplate='Saldo Fundo: R$ %{y:,.2f}<extra></extra>'),
        secondary_y=False
    )

    fig.add_trace(
        go.Scatter(x=months, y=valor_garantido, 
                   name="Valor Garantido (R$)", 
                   line=dict(width=2.5, dash='dash', color='#ff7f0e'),
                   mode='lines',
                   hovertemplate='Valor Garantido: R$ %{y:,.2f}<extra></extra>'),
        secondary_y=False
    )

    fig.add_trace(
        go.Scatter(x=months, y=honras_acum, 
                   name="Honras Acumuladas (R$)", 
                   line=dict(width=2.5, dash='dot', color='#d62728'),
                   mode='lines',
                   hovertemplate='Honras Acumuladas: R$ %{y:,.2f}<extra></extra>'),
        secondary_y=False
    )
    
    fig.add_trace(
        go.Scatter(x=months, y=recuperacoes_acum, 
                   name="Recuperações Acumuladas (R$)", 
                   line=dict(width=2.5, dash='dashdot', color='#2ca02c'),
                   mode='lines',
                   hovertemplate='Recuperações Acumuladas: R$ %{y:,.2f}<extra></extra>'),
        secondary_y=False
    )

    # Eixo direito - Índice SGC e Taxas de Inadimplência
    fig.add_trace(
        go.Scatter(x=months, y=indice_sgc, 
                   name="Índice SGC (60m)", 
                   line=dict(width=2.5, color='purple', dash='dot'),
                   mode='lines',
                   hovertemplate='Índice SGC: %{customdata:.2f}%<extra></extra>',
                   customdata=[v * 100 for v in indice_sgc]),
        secondary_y=True
    )
    
    fig.add_trace(
        go.Scatter(x=months, y=taxa_inad_qtd, 
                   name="Taxa Inad. (Qtd)", 
                   line=dict(width=2.5, color='orangered', dash='solid'),
                   mode='lines',
                   hovertemplate='Taxa Inadimplência (Qtd): %{customdata:.2f}%<extra></extra>',
                   customdata=[v * 100 for v in taxa_inad_qtd]),
        secondary_y=True
    )
    
    fig.add_trace(
        go.Scatter(x=months, y=taxa_inad_valor, 
                   name="Taxa Inad. (Valor)", 
                   line=dict(width=2.5, color='red', dash='dashdot'),
                   mode='lines',
                   hovertemplate='Taxa Inadimplência (Valor): %{customdata:.2f}%<extra></extra>',
                   customdata=[v * 100 for v in taxa_inad_valor]),
        secondary_y=True
    )

    # Configurar eixos
    fig.update_xaxes(title_text="Mês")
    
    # Eixo Y esquerdo (valores monetários) - começa em zero
    fig.update_yaxes(
        title_text="Valores (R$)", 
        secondary_y=False,
        rangemode='tozero'
    )
    
    # Define valor máximo do eixo Y direito como 200% do máximo de operações
    # Isso dá bastante espaço visual e evita que as barras dominem o plot
    max_ops = max(ops_novas_mes) if ops_novas_mes else 100
    max_indice_sgc = max(indice_sgc) if indice_sgc else 1.0
    max_taxa_inad_qtd = max(taxa_inad_qtd) if taxa_inad_qtd else 1.0
    max_taxa_inad_valor = max(taxa_inad_valor) if taxa_inad_valor else 1.0
    max_indice = max(max_indice_sgc, max_taxa_inad_qtd, max_taxa_inad_valor)
    yaxis_right_max = max(max_ops * 2.0, max_indice * 1.1)
    
    # Eixo Y direito - força começar em zero para alinhar com eixo esquerdo
    fig.update_yaxes(
        title_text="Quantidade / Índice", 
        secondary_y=True,
        range=[0, yaxis_right_max]
    )

    fig.update_layout(
        title=f"Projeção do Fundo e Carteira - {len(months)} meses",
        hovermode='x unified',
        height=600,
        showlegend=True
    )

    return json.loads(fig.to_json())
