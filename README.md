# DataVision

Plataforma web para **análise, exploração e interpretação de dados**,
desenvolvida em Python com Flask. O DataVision transforma arquivos CSV e
Excel em perfis de qualidade, dashboards, indicadores, insights
estatísticos e sinais de anomalia, mantendo o dataset original
preservado durante o processo.

> Projeto pessoal de portfólio. Versão estável atual: **v1.0.0**.

## Visão geral

O DataVision foi criado para tornar a análise de dados mais estruturada
e acessível em diferentes contextos de negócio. Ao criar um projeto, o
usuário escolhe um segmento --- Financeiro, Comércio, Empresarial ou
Análise Geral --- e pode importar um dataset para iniciar o fluxo de
análise.

A aplicação realiza profiling dos dados, sugere um mapeamento semântico
das colunas, calcula um Data Quality Score, oferece limpeza assistida e
gera dashboards e insights a partir da estrutura identificada.

Na camada de inteligência, o projeto também possui um mecanismo
determinístico de detecção de anomalias. O **Anomaly Score representa
desvio em relação ao padrão observado e não probabilidade de fraude**.

## Funcionalidades atuais

-   Criação, edição, duplicação, arquivamento e exclusão de projetos.
-   Importação de datasets CSV, XLSX e XLSM.
-   Preservação do arquivo original e geração separada do dataset
    processado.
-   Profiling automático de colunas, tipos, valores ausentes,
    duplicidades e possíveis outliers.
-   Data Quality Score baseado em completude, duplicidade, validade e
    consistência.
-   Smart Column Mapper para identificação semântica de campos como
    cliente, valor, data/hora, status, produto, quantidade, departamento
    e funcionário.
-   Confirmação manual do mapeamento sugerido.
-   Limpeza assistida com remoção de duplicidades e tratamento de
    valores ausentes.
-   Dashboards automáticos com KPIs e gráficos.
-   Insights determinísticos baseados em estatística, distribuição,
    concentração e comportamento temporal.
-   Anomaly Engine com análise de desvio de valor, velocity, horário e
    status.
-   Comparação entre diferentes execuções de um mesmo projeto.
-   Personalização básica dos módulos exibidos no dashboard.
-   Persistência local dos projetos e execuções.

## Tecnologias

### Backend e dados

-   Python
-   Flask
-   Flask-SQLAlchemy
-   Pandas
-   NumPy
-   Matplotlib
-   OpenPyXL
-   SQLite

### Frontend

-   HTML
-   CSS
-   JavaScript
-   Jinja2
-   Chart.js

### Qualidade

-   Pytest
-   Git / GitHub
-   python-dotenv

## Arquitetura

O projeto utiliza o padrão **Application Factory** do Flask e Blueprints
para separar as responsabilidades da aplicação.

``` text
DataVision/
├── app/
│   ├── models/                 # Entidades persistidas com SQLAlchemy
│   ├── routes/                 # Rotas e fluxos HTTP
│   ├── services/
│   │   ├── data_engine.py      # Importação, profiling, mapping e limpeza
│   │   ├── analytics_engine.py # KPIs, gráficos e insights
│   │   ├── anomaly_engine.py   # Detecção determinística de desvios
│   │   └── comparison_engine.py# Comparação entre execuções
│   ├── templates/              # Templates Jinja2
│   ├── static/                 # CSS e JavaScript
│   ├── extensions.py
│   └── __init__.py             # Application Factory
├── instance/                   # Banco SQLite local (não versionado)
├── storage/
│   └── projects/               # Datasets por projeto/execução
├── tests/                      # Testes automatizados
├── config.py
├── run.py
├── requirements.txt
└── pytest.ini
```

## Fluxo de análise

``` text
Criar projeto
     ↓
Importar CSV / Excel
     ↓
Data Profiling
     ↓
Data Quality Score
     ↓
Smart Column Mapper
     ↓
Confirmação do usuário
     ↓
Limpeza assistida
     ↓
Analytics Engine
     ↓
Dashboard + KPIs + Insights
     ↓
Anomaly Engine
     ↓
Comparação entre execuções
```

## Data Quality Score

O DataVision calcula um indicador de qualidade utilizando componentes
explícitos:

-   **Completude:** impacto de valores ausentes.
-   **Duplicidade:** impacto de registros duplicados.
-   **Validade:** estrutura/tipagem analisada pelo profiler.
-   **Consistência:** impacto de possíveis valores extremos.

O objetivo é fornecer um indicador interpretável do estado do dataset
antes da análise.

## Smart Column Mapper

O mapper tenta identificar automaticamente a função de cada coluna
combinando:

-   nome da coluna;
-   aliases conhecidos;
-   tipo semântico inferido;
-   mapeamentos utilizados em execuções anteriores.

As sugestões possuem confiança qualitativa e podem ser corrigidas pelo
usuário antes da análise.

## Analytics e Insight Engine

Após o mapeamento, o Analytics Engine utiliza a semântica das colunas
para gerar automaticamente KPIs e visualizações adequadas ao dataset.

O Insight Engine trabalha com regras e cálculos determinísticos. Entre
os sinais atualmente explorados estão:

-   distribuição e mediana de valores;
-   concentração por categorias;
-   status predominantes;
-   picos temporais;
-   relações estatísticas entre variáveis numéricas.

Os insights apresentam evidências observadas nos dados e evitam
transformar correlação em causalidade.

## Anomaly Engine

A V1.4 adicionou um mecanismo de identificação de registros que se
desviam do padrão observado.

Os componentes atualmente utilizados incluem:

-   **Velocity:** repetição de operações do mesmo cliente em uma janela
    de até 10 minutos.
-   **Value deviation:** distância robusta do valor em relação ao
    comportamento central.
-   **Denial:** presença de status associados a negação ou recusa.
-   **Time behavior:** operações realizadas em horários considerados
    pouco usuais pela regra atual.

Os componentes são combinados em um **Anomaly Score de 0 a 100**.

> O Anomaly Score mede desvio do padrão observado. Ele não deve ser
> interpretado como probabilidade de fraude, diagnóstico ou decisão
> automática.

## Executando localmente

### 1. Clone o repositório

``` bash
git clone https://github.com/IgorMzt/DataVision.git
cd DataVision
```

### 2. Crie o ambiente virtual

Windows:

``` powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Linux/macOS:

``` bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Instale as dependências

``` bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure o ambiente

Crie um arquivo `.env` a partir do `.env.example`:

``` env
SECRET_KEY=change-me-in-production
DATABASE_URL=sqlite:///datavision.db
```

### 5. Execute

``` bash
python run.py
```

A aplicação estará disponível localmente em:

``` text
http://127.0.0.1:5000
```

## Testes

Execute:

``` bash
python -m pytest -q
```

A suíte cobre componentes do Data Engine, Analytics Engine, rotas
principais e Intelligence/Anomaly Engine.

## Roadmap

### Concluído

-   **V1.1 --- Core:** estrutura Flask, projetos e persistência.
-   **V1.2 --- Data Engine:** importação, profiling, Data Quality, Smart
    Column Mapper e limpeza.
-   **V1.3 --- Analytics:** dashboards, KPIs, gráficos e Insight Engine.
-   **V1.4 --- Intelligence:** Anomaly Engine, velocity e comparação
    entre execuções.

-   **V1.5 --- Finalização:** infraestrutura para PostgreSQL/MySQL, exportação de relatórios e dados, refinamento responsivo, segurança, desempenho e ampliação dos testes.
-   **v1.0.0 --- Release estável:** consolidação da primeira versão pública do projeto.

### Futuro

-   evolução da customização dos dashboards;
-   novas fontes de dados;
-   evolução da camada de insights com novas regras analíticas e métricas rastreáveis.

## Decisões de projeto

Alguns princípios orientam o desenvolvimento do DataVision:

1.  **O dado original é preservado.** Transformações são aplicadas sobre
    uma cópia processada.
2.  **O usuário confirma decisões semânticas.** O mapper sugere; o
    usuário pode corrigir.
3.  **Anomalia não significa fraude.** O sistema apresenta sinais e
    evidências, sem produzir acusações automáticas.
4.  **Insights devem ser rastreáveis.** A camada atual é baseada em
    regras e estatística.
5.  **O projeto é modular.** Data processing, analytics, anomaly
    detection e comparação são serviços separados.

## Status

**Versão atual:** v1.0.0  
**Estado:** release estável de portfólio.

## Autor

**Igor Mazeti de Oliveira**

-   GitHub: `IgorMzt`
-   LinkedIn: `igor-mazeti`

------------------------------------------------------------------------

Se este projeto for útil como referência, fique à vontade para explorar
o código e acompanhar sua evolução.
