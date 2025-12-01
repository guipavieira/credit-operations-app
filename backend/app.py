from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import sys
import os
import numpy as np

# Add backend to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from services.simulation import get_default_params, run_simulation, generate_plotly_chart

app = Flask(__name__, 
            template_folder='../frontend/templates',
            static_folder='../frontend/static')
CORS(app)

@app.route("/")
def index():
    """Página principal com formulário de simulação"""
    return render_template('index.html')

@app.route("/parametros", methods=["GET"])
def get_parametros():
    """Retorna os parâmetros padrão da simulação"""
    return jsonify(get_default_params())

@app.route("/simulate", methods=["POST"])
def simulate():
    """Executa a simulação com os parâmetros fornecidos"""
    try:
        # Recebe parâmetros do frontend
        data = request.get_json()
        
        # Se não houver dados, usa parâmetros padrão
        if not data:
            params = get_default_params()
        else:
            # Mescla parâmetros recebidos com padrões
            params = get_default_params()
            params.update(data)
        
        # Executa simulação
        df_carteira, df_fundo, df_operacoes = run_simulation(params)
        
        # Gera gráfico interativo
        chart = generate_plotly_chart(df_carteira, df_fundo)
        
        # Prepara resumo dos resultados
        ultimo_mes_carteira = df_carteira.iloc[-1]
        ultimo_mes_fundo = df_fundo.iloc[-1]
        
        # Conta meses com paused=True (restrições operacionais)
        meses_com_restricoes = int(df_carteira["paused"].sum())
        
        # Conta total de operações inadimplentes acumuladas
        total_inadimplentes = int(df_carteira["operacoes_inadimplentes_novas"].sum())
        
        # Calcula ticket médio das operações (desembolso acumulado / total de operações)
        total_ops = int(ultimo_mes_carteira["operacoes_realizadas_acum"])
        desembolso_total = float(ultimo_mes_carteira["desembolso_acum"])
        ticket_medio = desembolso_total / total_ops if total_ops > 0 else 0.0
        
        resumo = {
            "saldo_final_fundo": float(ultimo_mes_fundo["saldo_final"]),
            "total_operacoes": total_ops,
            "honras_acumuladas": float(ultimo_mes_carteira["honras_acumuladas"]),
            "recuperacoes_acumuladas": float(ultimo_mes_carteira["recuperacoes_acumuladas"]),
            "desembolso_acumulado": desembolso_total,
            "ticket_medio": ticket_medio,
            "meses_restricoes_operacionais": meses_com_restricoes,
            "indice_sgc": float(ultimo_mes_carteira["indice_sgc"]),
            "taxa_inadimplencia_qtd": float(ultimo_mes_carteira["taxa_inadimplencia_qtd"]),
            "taxa_inadimplencia_valor": float(ultimo_mes_carteira["taxa_inadimplencia_valor"]),
            "operacoes_inadimplentes": total_inadimplentes
        }
        
        # Converte DataFrames para dict, substituindo NaN por None
        carteira_dict = df_carteira.replace({np.nan: None}).to_dict(orient='records')
        fundo_dict = df_fundo.replace({np.nan: None}).to_dict(orient='records')
        operacoes_dict = df_operacoes.replace({np.nan: None}).to_dict(orient='records')
        
        # Retorna dados completos para visualização
        return jsonify({
            "success": True,
            "resumo": resumo,
            "chart": chart,
            "carteira": carteira_dict,
            "fundo": fundo_dict,
            "operacoes": operacoes_dict
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 400

@app.route("/api")
def api_info():
    """Informações sobre a API"""
    return {"message": "API de Simulação de Operações de Crédito"}

if __name__ == "__main__":
    # Para acesso pela rede local, use host='0.0.0.0'
    # Para acesso apenas local, use host='127.0.0.1' (padrão)
    app.run(debug=True, host='0.0.0.0', port=5000)