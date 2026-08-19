# Case Técnico de Risco de Crédito

## Objetivo

A solução estima a probabilidade de inadimplência de solicitações de crédito, propõe uma política inicial de decisão e gera o arquivo `submissao_case.csv`.

O fluxo foi dividido em quatro notebooks executados sequencialmente:

1. `01_entendimento_e_qualidade_dos_dados.ipynb`
2. `02_construcao_e_selecao_do_target.ipynb`
3. `03_base_analitica_e_engenharia_de_features.ipynb`
4. `04_modelagem_politica_scoring.ipynb`

## Estrutura da entrega

```text
.
├── 01_entendimento_e_qualidade_dos_dados.ipynb
├── 02_construcao_e_selecao_do_target.ipynb
├── 03_base_analitica_e_engenharia_de_features.ipynb
├── 04_modelagem_politica_scoring.ipynb
├── run_pipeline.py
├── validar_ambiente.py
├── requirements.txt
├── README.md
└── submissao_case.csv
```

As bases de entrada e as saídas intermediárias não fazem parte do pacote de submissão.

## Ambiente

Ambiente de referência utilizado na validação:

- Python 3.13.5
- Java 21
- PySpark 4.1.2

A solução foi estruturada para execução local, em Jupyter/VS Code ou em Databricks. Para execução local, é necessário ter Java instalado e disponível no `PATH` ou por meio da variável `JAVA_HOME`.

### Instalação

Linux/macOS:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Validação rápida do ambiente:

```bash
python validar_ambiente.py
```

## Bases de entrada

Crie a pasta `data/` na raiz do projeto e inclua os arquivos fornecidos no case com estes nomes:

```text
data/
├── base_cadastral.parquet
├── base_submissao.parquet
├── historico_emprestimos.parquet
├── historico_parcelas.parquet
└── dicionario_dados.xlsx
```

O dicionário também pode ser fornecido como `dicionario_dados.csv`. Sua leitura é auxiliar e não bloqueia o pipeline principal.

Os caminhos podem ser alterados pelas variáveis de ambiente:

```text
CREDIT_RISK_DATA_PATH
CREDIT_RISK_OUTPUT_PATH
```

## Execução

### Opção 1 — execução automatizada

```bash
python run_pipeline.py --data-path data --output-path outputs
```

O script lê e executa as células de código dos quatro notebooks na ordem correta, sem exigir um servidor Jupyter. O fluxo é interrompido em caso de erro e o CSV final é validado automaticamente.

### Opção 2 — execução manual

Abra os notebooks em Jupyter, VS Code, Colab ou Databricks e execute-os integralmente na ordem de 01 a 04.

As saídas intermediárias são reconstruídas em `outputs/`:

```text
outputs/
├── base_target_final.parquet
├── base_desenvolvimento_features.parquet
├── base_scoring_features.parquet
└── submissao_case.csv
```

O processamento de contratos e parcelas utiliza Spark e pode levar alguns minutos em ambiente local, conforme os recursos disponíveis.

## Resumo da abordagem

- **Target:** FPD com atraso na primeira obrigação observável, selecionado após comparação com alternativas de maior maturidade e análise do comportamento posterior.
- **Features:** operação atual, cadastro e históricos de crédito e pagamento construídos de forma point-in-time.
- **Modelo:** regressão logística com regularização L1, selecionada por discriminação, estabilidade, interpretabilidade e menor risco de sobreajuste.
- **Calibração:** Platt ajustada com predições out-of-fold do treino.
- **Política:** limites P50, P70 e P90 definidos sobre a probabilidade calibrada no teste e aplicados sem redefinição ao out-of-time e ao scoring.
- **Scoring:** aplicação do pipeline congelado aos 40.000 registros da base de submissão.

## Arquivo de submissão

O arquivo `submissao_case.csv` contém somente:

```text
id_cliente
probabilidade_inadimplencia
```

As probabilidades são numéricas, estão entre 0 e 1 e preservam uma linha por cliente.

## Limitações e monitoramento

O target é observado apenas para contratos concedidos e com performance disponível. Portanto, a solução está sujeita a viés de aprovação. Não foi atribuído target artificial aos contratos recusados.

Como evolução, recomenda-se avaliar inferência de rejeitados como análise de sensibilidade. Em produção, devem ser acompanhados qualidade dos dados, estabilidade populacional, calibração, discriminação, cobertura das decisões e taxa de maus após a maturação dos contratos.

## Reprodutibilidade

- semente global: `42`;
- separação temporal preservada antes das decisões de modelagem;
- pré-processamento ajustado dentro dos folds;
- teste e out-of-time não utilizados no ajuste do modelo ou do calibrador;
- limites da política definidos no teste e aplicados sem redefinição às populações posteriores;
- validações de estrutura, unicidade e domínio executadas antes da gravação do CSV.
