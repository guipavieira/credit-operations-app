let defaultParams = null;
let currentData = null; // Armazena dados da última simulação

// Carrega parâmetros padrão ao iniciar
document.addEventListener('DOMContentLoaded', async function() {
    // Buscar parâmetros padrão
    try {
        const response = await fetch('/parametros');
        defaultParams = await response.json();
        console.log('Parâmetros padrão carregados:', defaultParams);
    } catch (error) {
        console.error('Erro ao carregar parâmetros padrão:', error);
    }

    const form = document.getElementById('simulation-form');
    const resetBtn = document.getElementById('reset-btn');
    const addAporteBtn = document.getElementById('add-aporte');
    const aportesContainer = document.getElementById('aportes-container');
    const loadingDiv = document.getElementById('loading');
    const errorDiv = document.getElementById('error-output');
    const resumoDiv = document.getElementById('resumo-output');
    const chartDiv = document.getElementById('chart-output');
    const tablesSection = document.getElementById('tables-section');

    // Inicializa sistema de abas
    initializeTabs();
    
    // Inicializa botões de download
    initializeDownloads();
    
    // Inicializa botão de recolher/expandir todos
    initializeToggleAllSections();

    // Adicionar novo aporte extra
    addAporteBtn.addEventListener('click', function() {
        const aporteItem = document.createElement('div');
        aporteItem.className = 'aporte-item';
        aporteItem.innerHTML = `
            <label class="aporte-label">Mês:</label>
            <input type="number" class="aporte-mes" placeholder="Mês" min="1" value="1">
            <label class="aporte-label">Valor do Aporte (R$):</label>
            <input type="number" class="aporte-valor" placeholder="Valor (R$)" step="10000" value="0">
            <button type="button" class="remove-aporte">Remover</button>
        `;
        aportesContainer.appendChild(aporteItem);
    });

    // Remover aporte (delegação de eventos)
    aportesContainer.addEventListener('click', function(e) {
        if (e.target.classList.contains('remove-aporte')) {
            e.target.parentElement.remove();
        }
    });

    // Restaurar valores padrão
    resetBtn.addEventListener('click', function() {
        if (defaultParams) {
            loadFormValues(defaultParams);
            // Recarregar aportes extras padrão
            aportesContainer.innerHTML = `
                <div class="aporte-item">
                    <label class="aporte-label">Mês:</label>
                    <input type="number" class="aporte-mes" placeholder="Mês" value="6" min="1">
                    <label class="aporte-label">Valor do Aporte (R$):</label>
                    <input type="number" class="aporte-valor" placeholder="Valor (R$)" value="5000000" step="10000">
                    <button type="button" class="remove-aporte">Remover</button>
                </div>
                <div class="aporte-item">
                    <label class="aporte-label">Mês:</label>
                    <input type="number" class="aporte-mes" placeholder="Mês" value="12" min="1">
                    <label class="aporte-label">Valor do Aporte (R$):</label>
                    <input type="number" class="aporte-valor" placeholder="Valor (R$)" value="14000000" step="10000">
                    <button type="button" class="remove-aporte">Remover</button>
                </div>
            `;
        }
    });

    // Submeter formulário
    form.addEventListener('submit', async function(event) {
        event.preventDefault();
        
        // Limpa resultados anteriores
        errorDiv.style.display = 'none';
        resumoDiv.innerHTML = '';
        chartDiv.innerHTML = '';
        tablesSection.style.display = 'none';
        loadingDiv.style.display = 'block';

        // Coleta dados do formulário
        const formData = new FormData(form);
        const params = {};
        
        for (let [key, value] of formData.entries()) {
            // Converte para número se apropriado
            if (value && !isNaN(value)) {
                params[key] = parseFloat(value);
            } else {
                params[key] = value;
            }
        }

        // Coleta aportes extras
        const aportesExtras = [];
        const aporteItems = document.querySelectorAll('.aporte-item');
        aporteItems.forEach(item => {
            const mes = parseInt(item.querySelector('.aporte-mes').value);
            const valor = parseFloat(item.querySelector('.aporte-valor').value);
            if (mes && valor) {
                aportesExtras.push({"mes": mes, "valor": valor});
            }
        });
        params.aportes_extra = aportesExtras;

        // Adiciona parâmetros fixos
        params.sistema_amortizacao_choices = ["PRICE", "SAC"];
        params.random_seed = 42;

        console.log('Parâmetros enviados:', params);

        try {
            const response = await fetch('/simulate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(params),
            });

            loadingDiv.style.display = 'none';

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Erro na simulação');
            }

            const result = await response.json();
            
            if (!result.success) {
                throw new Error(result.error || 'Erro desconhecido na simulação');
            }

            // Armazena dados globalmente
            currentData = result;

            // Exibe resumo
            displayResumo(result.resumo);

            // Exibe gráfico
            displayChart(result.chart);

            // Exibe tabelas
            displayAllTables(result);

        } catch (error) {
            loadingDiv.style.display = 'none';
            errorDiv.style.display = 'block';
            errorDiv.innerHTML = `
                <div style="color: red; padding: 20px; border: 1px solid red; border-radius: 5px;">
                    <h3>Erro na Simulação</h3>
                    <p>${error.message}</p>
                </div>
            `;
            console.error('Erro completo:', error);
        }
    });
});

function loadFormValues(params) {
    for (let key in params) {
        const input = document.getElementById(key);
        if (input && typeof params[key] !== 'object') {
            input.value = params[key];
        }
    }
}

function displayResumo(resumo) {
    const resumoDiv = document.getElementById('resumo-output');
    
    resumoDiv.innerHTML = `
        <div class="resumo-container">
            <h3>Resumo da Simulação</h3>
            <div class="resumo-grid">
                <div class="resumo-item">
                    <span class="label">Saldo Final do Fundo:</span>
                    <span class="value">R$ ${formatMoney(resumo.saldo_final_fundo)}</span>
                </div>
                <div class="resumo-item">
                    <span class="label">Total de Operações:</span>
                    <span class="value">${resumo.total_operacoes}</span>
                </div>
                <div class="resumo-item">
                    <span class="label">Operações Inadimplentes:</span>
                    <span class="value">${resumo.operacoes_inadimplentes}</span>
                </div>
                <div class="resumo-item">
                    <span class="label">Meses com Restrições Operacionais:</span>
                    <span class="value">${resumo.meses_restricoes_operacionais}</span>
                </div>
                <div class="resumo-item">
                    <span class="label">Honras Acumuladas:</span>
                    <span class="value">R$ ${formatMoney(resumo.honras_acumuladas)}</span>
                </div>
                <div class="resumo-item">
                    <span class="label">Valor Recuperado:</span>
                    <span class="value">R$ ${formatMoney(resumo.recuperacoes_acumuladas)}</span>
                </div>
                <div class="resumo-item">
                    <span class="label">Índice SGC (60 meses):</span>
                    <span class="value">${(resumo.indice_sgc * 100).toFixed(2)}%</span>
                </div>
                <div class="resumo-item">
                    <span class="label">Taxa Inadimplência (Qtd):</span>
                    <span class="value">${(resumo.taxa_inadimplencia_qtd * 100).toFixed(2)}%</span>
                </div>
                <div class="resumo-item">
                    <span class="label">Desembolso Acumulado:</span>
                    <span class="value">R$ ${formatMoney(resumo.desembolso_acumulado)}</span>
                </div>
            </div>
        </div>
    `;
}

function displayChart(chartData) {
    const chartDiv = document.getElementById('chart-output');
    
    // Usa Plotly para renderizar o gráfico
    Plotly.newPlot(chartDiv, chartData.data, chartData.layout, {responsive: true});
}

function displayAllTables(data) {
    const tablesSection = document.getElementById('tables-section');
    tablesSection.style.display = 'block';
    
    // Exibe cada tabela
    displayTableInTab('carteira', data.carteira);
    displayTableInTab('fundo', data.fundo);
    displayTableInTab('operacoes', data.operacoes);
}

function displayTableInTab(tableName, tableData) {
    const container = document.getElementById(`table-${tableName}`);
    
    if (!tableData || tableData.length === 0) {
        container.innerHTML = '<p>Nenhum dado disponível.</p>';
        return;
    }

    // Obtém colunas
    const columns = Object.keys(tableData[0]);
    
    // Mostra apenas as 20 primeiras linhas
    let dataToShow = tableData;
    let showingMessage = '';
    
    if (tableData.length > 20) {
        dataToShow = tableData.slice(0, 20);
        showingMessage = `<p style="text-align: center; margin: 10px 0; color: #666;">
            Exibindo primeiras 20 linhas de ${tableData.length} totais. 
            Use o botão de download para visualizar todos os dados.
        </p>`;
    }

    let tableHTML = '<div class="table-container"><table class="data-table"><thead><tr>';
    
    // Cabeçalho
    columns.forEach(col => {
        const label = col.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
        tableHTML += `<th>${label}</th>`;
    });
    tableHTML += '</tr></thead><tbody>';

    // Dados
    dataToShow.forEach((row, idx) => {
        tableHTML += '<tr>';
        columns.forEach(col => {
            let value = row[col];
            // Formata valores monetários (exceto parcela_inadimplente)
            if (typeof value === 'number' && !col.includes('parcela_inadimplente') && 
                (col.includes('valor') || col.includes('saldo') || 
                col.includes('desembolso') || col.includes('garantido') || col.includes('honra') || 
                col.includes('limite') || col.includes('recupera'))) {
                value = 'R$ ' + formatMoney(value);
            } else if (typeof value === 'number' && !col.includes('mes') && !col.includes('prazo') && 
                       !col.includes('operacoes') && !col.includes('taxa') && !col.includes('prop') && 
                       !col.includes('alavancagem') && !col.includes('percentual') && 
                       !col.includes('parcela_inadimplente')) {
                value = value.toFixed(2);
            }
            tableHTML += `<td>${value !== null && value !== undefined && value !== '' ? value : '-'}</td>`;
        });
        tableHTML += '</tr>';
    });

    tableHTML += '</tbody></table></div>';
    tableHTML += showingMessage;

    container.innerHTML = tableHTML;
}

function initializeTabs() {
    document.querySelectorAll('.tab-button').forEach(button => {
        button.addEventListener('click', function() {
            const tabName = this.getAttribute('data-tab');
            
            // Remove active de todos
            document.querySelectorAll('.tab-button').forEach(btn => btn.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
            
            // Adiciona active ao clicado
            this.classList.add('active');
            document.getElementById(`tab-${tabName}`).classList.add('active');
        });
    });
}

function initializeDownloads() {
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('download-btn')) {
            const tableName = e.target.getAttribute('data-table');
            downloadCSV(tableName);
        }
    });
}

function downloadCSV(tableName) {
    if (!currentData || !currentData[tableName]) {
        alert('Dados não disponíveis para download.');
        return;
    }

    const data = currentData[tableName];
    const csv = convertToCSV(data);
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    
    link.setAttribute('href', url);
    link.setAttribute('download', `simulacao_${tableName}_${new Date().toISOString().slice(0,10)}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

function convertToCSV(data) {
    if (!data || data.length === 0) return '';
    
    const headers = Object.keys(data[0]);
    const csvRows = [];
    
    // Cabeçalho
    csvRows.push(headers.join(','));
    
    // Dados
    for (const row of data) {
        const values = headers.map(header => {
            const value = row[header];
            // Escapa vírgulas e aspas
            const escaped = ('' + value).replace(/"/g, '""');
            return `"${escaped}"`;
        });
        csvRows.push(values.join(','));
    }
    
    return csvRows.join('\n');
}

function displayTable(carteiraData) {
    const tableDiv = document.getElementById('table-output');
    
    if (!carteiraData || carteiraData.length === 0) {
        tableDiv.innerHTML = '<p>Nenhum dado de carteira disponível.</p>';
        return;
    }

    // Colunas principais para exibir
    const columns = [
        'mes', 'operacoes_ativas', 'operacoes_novas_mes', 'operacoes_inadimplentes_novas',
        'desembolso_mes', 'desembolso_acum', 'saldo_devedor_carteira', 
        'valor_garantido_mes', 'honras_acumuladas', 'parcelas_recebidas_mes'
    ];

    const columnLabels = {
        'mes': 'Mês',
        'operacoes_ativas': 'Op. Ativas',
        'operacoes_novas_mes': 'Novas',
        'operacoes_inadimplentes_novas': 'Inadimpl.',
        'desembolso_mes': 'Desembolso Mês',
        'desembolso_acum': 'Desemb. Acum.',
        'saldo_devedor_carteira': 'Saldo Devedor',
        'valor_garantido_mes': 'Valor Garantido',
        'honras_acumuladas': 'Honras Acum.',
        'parcelas_recebidas_mes': 'Parcelas Receb.'
    };

    let tableHTML = '<h3>Carteira Mensal</h3>';
    tableHTML += '<div class="table-container"><table class="data-table"><thead><tr>';
    
    // Cabeçalho
    columns.forEach(col => {
        tableHTML += `<th>${columnLabels[col] || col}</th>`;
    });
    tableHTML += '</tr></thead><tbody>';

    // Dados (mostra últimos 12 meses por padrão)
    const dataToShow = carteiraData.slice(-12);
    dataToShow.forEach(row => {
        tableHTML += '<tr>';
        columns.forEach(col => {
            let value = row[col];
            // Formata valores monetários
            if (['desembolso_mes', 'desembolso_acum', 'saldo_devedor_carteira', 
                 'valor_garantido_mes', 'honras_acumuladas', 'parcelas_recebidas_mes'].includes(col)) {
                value = 'R$ ' + formatMoney(value);
            }
            tableHTML += `<td>${value !== null && value !== undefined ? value : '-'}</td>`;
        });
        tableHTML += '</tr>';
    });

    tableHTML += '</tbody></table></div>';
    tableHTML += `<p style="text-align: center; margin-top: 10px; color: #666;">
        Exibindo últimos ${dataToShow.length} meses de ${carteiraData.length} meses totais
    </p>`;

    tableDiv.innerHTML = tableHTML;
}

function formatMoney(value) {
    if (value >= 1_000_000_000) {
        return (value / 1_000_000_000).toFixed(2) + ' bi';
    }
    if (value >= 1_000_000) {
        return (value / 1_000_000).toFixed(2) + ' mi';
    }
    return value.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2});
}

// Função para recolher/expandir todas as seções
function initializeToggleAllSections() {
    const toggleBtn = document.getElementById('toggle-all-sections');
    let allCollapsed = false;
    
    if (toggleBtn) {
        toggleBtn.addEventListener('click', function() {
            const fieldsets = document.querySelectorAll('fieldset.collapsible');
            
            fieldsets.forEach(fieldset => {
                const content = fieldset.querySelector('.collapsible-content');
                const icon = fieldset.querySelector('.toggle-icon');
                
                if (!allCollapsed) {
                    // Recolher todos
                    content.style.display = 'none';
                    fieldset.classList.add('collapsed');
                    if (icon) icon.textContent = '▶';
                } else {
                    // Expandir todos
                    content.style.display = 'block';
                    fieldset.classList.remove('collapsed');
                    if (icon) icon.textContent = '▼';
                }
            });
            
            // Alterna o estado e o texto do botão
            allCollapsed = !allCollapsed;
            toggleBtn.textContent = allCollapsed ? 'Expandir Todos' : 'Recolher Todos';
        });
    }
}