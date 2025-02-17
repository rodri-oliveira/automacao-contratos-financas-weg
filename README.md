# Automação de Contratos - Finanças

Sistema desenvolvido para automatizar a análise e validação de contratos financeiros, focando na comparação e identificação de divergências entre diferentes fontes de dados.

## 📋 Funcionalidades

- Processamento de arquivos R189
- Processamento de arquivos QPE (Quadro de Posições em Estoque)
- Processamento de arquivos SPB
- Processamento de arquivos NFSERV
- Validação de códigos municipais
- Geração de relatórios de divergências
- Interface gráfica intuitiva para operação

## 🚀 Começando

### Pré-requisitos

- Python 3.x
- Acesso ao SharePoint da WEG
- Credenciais de autenticação configuradas

### 🔧 Instalação

1. Clone o repositório
2. Crie um ambiente virtual:
```bash
python -m venv venv
```

3. Ative o ambiente virtual:
```bash
.\venv\Scripts\activate
```

4. Instale as dependências:
```bash
pip install -r requirements.txt
```

5. Configure o arquivo `.env` com as credenciais necessárias:
```
SITE_URL=seu_site_url_sharepoint
```

## 🛠️ Tecnologias Utilizadas

- Python
- Tkinter (Interface gráfica)
- Pandas (Processamento de dados)
- Office365-REST-Python-Client (Integração SharePoint)
- PyPDF2 e PDFPlumber (Processamento de PDFs)

## 📦 Estrutura do Projeto

```
├── application/          # Lógica de negócios e processamento
│   ├── extractors/      # Extratores de dados dos diferentes tipos de arquivo
│   │   ├── r189_extractor.py            # Extração de dados R189
│   │   ├── qpe_extractor.py             # Extração de dados QPE
│   │   ├── spb_extractor.py             # Extração de dados SPB
│   │   ├── nfserv_extractor.py          # Extração de dados NFSERV
│   │   └── municipality_code_extractor.py # Extração de códigos municipais
│   │
│   └── reports/         # Geração de relatórios de divergências
│       ├── divergence_report_r189.py         # Relatório base R189
│       ├── divergence_report_qpe_r189.py     # Divergências QPE vs R189
│       ├── divergence_report_spb_r189.py     # Divergências SPB vs R189
│       ├── divergence_report_nfserv_r189.py  # Divergências NFSERV vs R189
│       └── report_mun_code_r189.py           # Divergências códigos municipais
├── auth/                # Autenticação SharePoint
├── domain/             # Regras de domínio
├── infrastructure/     # Configurações e infraestrutura
├── interfaces/         # Interfaces e contratos
├── presentation/       # Interface gráfica
├── tests/             # Testes automatizados
└── main.py            # Ponto de entrada da aplicação
```

## 🔍 Fluxo de Trabalho

1. Selecione o tipo de arquivo a ser processado
2. Busque os arquivos no SharePoint
3. Processe os arquivos selecionados
4. Execute as validações necessárias
5. Visualize os relatórios de divergências

## 🔍 Funcionalidades Detalhadas

### Extratores de Dados
- **R189**: Processamento de arquivos R189 para contratos financeiros
- **QPE**: Extração de dados do Quadro de Posições em Estoque
- **SPB**: Processamento de arquivos do Sistema de Pagamentos Brasileiro
- **NFSERV**: Extração de dados de Notas Fiscais de Serviço
- **Códigos Municipais**: Validação e extração de códigos de municípios

### Relatórios de Divergências
- Análise comparativa entre R189 e demais fontes de dados
- Identificação de inconsistências em contratos
- Validação de códigos municipais
- Geração de relatórios detalhados por tipo de divergência

## ⚙️ Executando a Aplicação

Para iniciar a aplicação, execute:

```bash
python main.py
```

## 📄 Licença

Este projeto é propriedade da WEG S.A. - Todos os direitos reservados.

---
Desenvolvido pela equipe de TI WEG
