// Descrições dos parâmetros para tooltips
const parameterDescriptions = {
    // Horizonte e Aportes
    simulation_months: "Quantidade de meses que a simulação irá projetar. Recomendado: 60 meses (5 anos)",
    aporte_inicial_fundo: "Valor inicial disponível no fundo garantidor. Este é o capital inicial para cobrir inadimplências",
    aporte_mensal: "Valor que será aportado mensalmente no fundo. Use 0 se não houver aportes regulares",
    start_year: "Ano de início da simulação. Usado para aplicar as taxas SELIC correspondentes",
    aportes_extra: "Aportes pontuais em meses específicos. Útil para simular captações extraordinárias",
    
    // Prazos
    prazo_operacao_MEI: "Prazo médio de pagamento das operações de MEI (Microempreendedor Individual) em meses",
    prazo_operacao_ME: "Prazo médio de pagamento das operações de ME (Microempresa) em meses",
    prazo_operacao_EPP: "Prazo médio de pagamento das operações de EPP (Empresa de Pequeno Porte) em meses",
    
    // Garantias
    percentual_garantia_MEI: "Percentual do saldo devedor coberto pela garantia do fundo para MEI (0 a 1)",
    percentual_garantia_ME: "Percentual do saldo devedor coberto pela garantia do fundo para ME (0 a 1)",
    percentual_garantia_EPP: "Percentual do saldo devedor coberto pela garantia do fundo para EPP (0 a 1)",
    
    // Inadimplência
    taxa_inadimplencia_MEI: "Probabilidade de inadimplência para operações de MEI (0 a 1). Ex: 0.22 = 22%",
    taxa_inadimplencia_ME: "Probabilidade de inadimplência para operações de ME (0 a 1). Ex: 0.10 = 10%",
    taxa_inadimplencia_EPP: "Probabilidade de inadimplência para operações de EPP (0 a 1). Ex: 0.05 = 5%",
    
    // Operações
    Operacoes_qtd_mensal_max: "Quantidade máxima de operações que podem ser concedidas por mês",
    Operacoes_meses_ate_max: "Número de meses para atingir a quantidade máxima (rampa de crescimento)",
    Operacoes_fator_retomada_pos_trava: "Fator de redução na retomada após paralisação por limite (0 a 1)",
    alavancagem_maxima: "Quantas vezes o saldo do fundo pode ser usado em garantias. Ex: 3.0 = 3x",
    taxa_juros_media_anual: "Taxa de juros média anual das operações (0 a 1). Ex: 0.20 = 20% a.a.",
    taxa_juros_cv: "Coeficiente de variação da taxa de juros (desvio padrão / média)",
    taxa_concessao: "Taxa cobrada na concessão do crédito (0 a 1). Ex: 0.0015 = 0.15%",
    ticket_cv: "Coeficiente de variação do valor das operações (desvio padrão / média)",
    
    // Recuperação
    taxa_recuperacao: "Percentual do valor honrado que será recuperado (0 a 1). Ex: 0.30 = 30%",
    prazo_medio_renegociacao: "Número de parcelas para pagamento da recuperação renegociada",
    prazo_honra: "Meses entre a inadimplência e o pagamento da garantia pelo fundo",
    prazo_recuperacao: "Meses entre a honra e o início do recebimento da recuperação",
    
    // Tickets
    ticket_medio_MEI: "Valor médio das operações de MEI em R$",
    ticket_medio_ME: "Valor médio das operações de ME em R$",
    ticket_medio_EPP: "Valor médio das operações de EPP em R$",
    
    // Proporções
    prop_MEI: "Proporção de operações destinadas a MEI (0 a 1). Soma das proporções deve ser 1",
    prop_ME: "Proporção de operações destinadas a ME (0 a 1). Soma das proporções deve ser 1",
    prop_EPP: "Proporção de operações destinadas a EPP (0 a 1). Soma das proporções deve ser 1",
    prop_PRICE: "Proporção de operações no sistema PRICE (0 a 1). Soma deve ser 1 com SAC",
    prop_SAC: "Proporção de operações no sistema SAC (0 a 1). Soma deve ser 1 com PRICE",
    
    // SELIC
    Taxa_SELIC_2026: "Taxa SELIC anual para 2026 (0 a 1). Usada para rendimento do fundo",
    Taxa_SELIC_2027: "Taxa SELIC anual para 2027 (0 a 1). Usada para rendimento do fundo",
    Taxa_SELIC_2028: "Taxa SELIC anual para 2028+ (0 a 1). Usada para rendimento do fundo"
};

// Inicializa tooltips quando o DOM estiver carregado
document.addEventListener('DOMContentLoaded', function() {
    initializeTooltips();
    initializeCollapsibles();
});

function initializeTooltips() {
    const tooltip = document.createElement('div');
    tooltip.className = 'tooltip-box';
    tooltip.style.display = 'none';
    document.body.appendChild(tooltip);

    document.querySelectorAll('.info-icon').forEach(icon => {
        icon.addEventListener('mouseenter', function(e) {
            const info = this.getAttribute('data-info');
            tooltip.textContent = info;
            tooltip.style.display = 'block';
            
            const rect = this.getBoundingClientRect();
            tooltip.style.left = rect.left + 'px';
            tooltip.style.top = (rect.bottom + 5) + 'px';
        });

        icon.addEventListener('mouseleave', function() {
            tooltip.style.display = 'none';
        });
    });
}

function initializeCollapsibles() {
    document.querySelectorAll('.collapsible-header').forEach(header => {
        header.addEventListener('click', function() {
            const fieldset = this.parentElement;
            const content = fieldset.querySelector('.collapsible-content');
            const icon = this.querySelector('.toggle-icon');
            
            if (content.style.display === 'none') {
                content.style.display = 'block';
                icon.textContent = '▼';
                fieldset.classList.remove('collapsed');
            } else {
                content.style.display = 'none';
                icon.textContent = '▶';
                fieldset.classList.add('collapsed');
            }
        });
    });
}
