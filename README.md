# Credit Operations App

## 📋 Sobre o Projeto
Aplicação web para simulação de operações de crédito, desenvolvida para o PMAE (Programa Municipal de Apoio ao Empreendedorismo). O sistema fornece uma interface interativa e um backend robusto construído com Flask, permitindo o gerenciamento completo de registros de crédito.

## 🚀 Funcionalidades
- ✅ Criação, consulta, atualização e exclusão de registros de crédito
- ✅ Validação de entradas para aplicações de crédito
- ✅ Interface responsiva e interativa
- ✅ Simulação de operações de crédito
- ✅ Cálculos financeiros automatizados

## 📁 Estrutura do Projeto
```
credit-operations-app/
├── backend/
│   ├── app.py                  # Aplicação principal Flask
│   ├── models/
│   │   ├── __init__.py
│   │   └── credit.py          # Modelos de dados de crédito
│   ├── routes/
│   │   ├── __init__.py
│   │   └── credit_routes.py   # Rotas da API
│   ├── services/
│   │   ├── __init__.py
│   │   ├── credit_service.py  # Lógica de negócio
│   │   └── simulation.py      # Serviços de simulação
│   └── utils/
│       ├── __init__.py
│       └── validators.py      # Validadores
├── frontend/
│   ├── static/
│   │   ├── css/
│   │   │   └── styles.css     # Estilos da aplicação
│   │   └── js/
│   │       ├── app.js         # Lógica do frontend
│   │       └── tooltips.js    # Funcionalidades de tooltips
│   └── templates/
│       └── index.html         # Interface principal
├── .env.example               # Template de variáveis de ambiente
├── .gitignore                 # Arquivos ignorados pelo Git
├── requirements.txt           # Dependências Python
└── README.md                  # Este arquivo
```

## 🔧 Requisitos
- Python 3.8 ou superior
- pip (gerenciador de pacotes Python)
- Navegador web moderno

## 📥 Instalação

### 1. Clone o repositório
```bash
git clone <url-do-seu-repositorio>
cd credit-operations-app
```

### 2. Crie um ambiente virtual (recomendado)
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux/Mac
python -m venv venv
source venv/bin/activate
```

### 3. Instale as dependências
```bash
pip install -r requirements.txt
```

### 4. Configure as variáveis de ambiente
```bash
# Copie o arquivo de exemplo
copy .env.example .env

# Edite o arquivo .env com suas configurações
# No mínimo, configure o SECRET_KEY
```

## ▶️ Como Executar

### Modo de Desenvolvimento
```bash
# Certifique-se de estar no diretório raiz do projeto
python backend/app.py
```

A aplicação estará disponível em: `http://localhost:5000`

### Modo de Produção
Para ambientes de produção, utilize um servidor WSGI como Gunicorn:
```bash
pip install gunicorn
gunicorn --bind 0.0.0.0:5000 backend.app:app
```

## 🔐 Configuração de Variáveis de Ambiente

Edite o arquivo `.env` com as seguintes configurações:

```env
FLASK_APP=backend/app.py
FLASK_ENV=development  # Mude para 'production' em produção
SECRET_KEY=sua-chave-secreta-aqui  # IMPORTANTE: Gere uma chave forte
DEBUG=True  # Mude para False em produção
API_HOST=0.0.0.0
API_PORT=5000
```

## 🧪 Testes
```bash
# Execute os testes (quando disponíveis)
pytest
```

## 📚 API Endpoints

### Operações de Crédito
- `GET /api/credits` - Lista todos os créditos
- `POST /api/credits` - Cria um novo crédito
- `GET /api/credits/<id>` - Obtém um crédito específico
- `PUT /api/credits/<id>` - Atualiza um crédito
- `DELETE /api/credits/<id>` - Remove um crédito

### Simulações
- `POST /api/simulate` - Simula uma operação de crédito

## 🤝 Contribuindo
Este é um projeto privado. Se você tem acesso ao repositório:

1. Crie uma branch para sua feature (`git checkout -b feature/MinhaFeature`)
2. Commit suas mudanças (`git commit -m 'Adiciona nova feature'`)
3. Push para a branch (`git push origin feature/MinhaFeature`)
4. Abra um Pull Request

## 📝 Notas Importantes
- **Não commite** o arquivo `.env` com credenciais reais
- Mantenha o `SECRET_KEY` seguro e único para cada ambiente
- Em produção, desative o modo DEBUG
- Revise o `.gitignore` para garantir que dados sensíveis não sejam versionados

## 👥 Equipe
Projeto desenvolvido para o PMAE - Programa Municipal de Apoio ao Empreendedorismo

## 📄 Licença
Este projeto é de uso interno e confidencial. Todos os direitos reservados.

---
**Nota:** Este é um repositório privado. O acesso é restrito apenas a colaboradores autorizados.