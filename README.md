# Analisador de Conformidade em PADOs — ANATEL
> Framework de Transparência em IA aplicado à fase de Instauração de Processos Administrativos de Apuração de Descumprimento de Obrigações (PADOs) da ANATEL.

---

## Visão Geral

Este projeto implementa o modelo **LAURA** (*Legal AUtomated Regulatory conformance by semantic frAmes*), um pipeline de verificação de conformidade documental para a fase de  **Instauração** de PADOs da ANATEL, combinando três abordagens complementares:

- **Abordagem A** (linha de base) — correspondência por expressões regulares combinada com similaridade semântica via `sentence-transformers` (`paraphrase-multilingual-MiniLM-L12-v2`)
- **Abordagem B** (proposta) — similaridade de cosseno no espaço semântico LSA (*Latent Semantic Analysis*) construído sobre o corpus dos PADOs, capturando sinonímia de domínio sem dicionários externos
- **Conformance Checking** via `pm4py` — verificação do fluxo processual esperado (Token-based Replay sobre rede de Petri)
- **Classificação Temática** via LDA — identificação do tipo documental e ativação dos requisitos normativos correspondentes

O framework verifica **7 Requisitos de Conformidade** normativos (R1–R7) com base na LGT, RASA e Lei 9.784/99, e gera relatórios individuais em PDF por PADO com explicação das não-conformidades.

Adaptado do framework **DERECHA** (Amaral Cejas et al., 2023, IEEE TSE vol. 49, n. 9).

---

## Estrutura do Repositório

```
.
├── 1_analise_SF_INST_pados.ipynb        # Notebook principal — Semantic Frames + 7 Requisitos
├── 1b_analise_LDA_LSA_SF_pados.ipynb   # Classificação temática (LDA/LSA) - teste para uso do LDA
├── 2_analise_RC_CC_INST_pados.ipynb   # Conformance Checking — fluxo processual (pm4py)
├── 3_analise_XAI_LDA_INST_pados.ipynb  # Integração XAI — score composto e relatório final
├── requirements.txt
└── README.md
```
Para saber mais sobre o uso e para que serve cada um deles acesse o arquivo readme_notebooks.md
---

## Os 7 Requisitos de Conformidade (R1–R7)

| Req. | Nome | Base Legal |
|------|------|------------|
| R1 | Documento Motivador Presente | LGT Art. 173 |
| R2 | Análise Prévia Realizada | RASA Art. 15 |
| R3 | Despacho de Instauração Formal | Lei 9.784/99 |
| R4 | Notificação ao Autuado | CF/88 Art. 5º LV |
| R5 | Base Legal Citada | Lei 9.784/99 Art. 50 |
| R6 | Prazo para Defesa Estabelecido | RASA Art. 33 |
| R7 | Identificação Clara do Processo | Lei 9.784/99 |

---

## Pipeline de Execução

### 1. Coleta dos dados base (SEI em Números)

Os dados públicos do SEI da ANATEL estão disponíveis em:
👉 https://dados.gov.br/dados/conjuntos-dados/sei-em-numeros

O notebook `1_analise_seicsv_processos_doc_pado` (não incluído neste repositório) realiza a leitura dos CSVs, filtra apenas processos do tipo PADO e salva a base filtrada localmente.

### 2. Identificação dos processos

O arquivo `CSV_PROCESSO_SANCIONADOR` (fonte: portal público da ANATEL) é usado para identificar os números de processo SEI no formato `XXXXX.XXXXXX/AAAA-DD` e mapear empresa, tema e fase processual.

### 3. Download dos PDFs

Os PDFs dos PADOs são coletados via SEI público:
👉 https://sei.anatel.gov.br/sei/modulos/pesquisa/md_pesq_processo_pesquisar.php

> **Nota:** O portal gera tokens aleatórios por sessão, o que exigiu coleta semi-manual dos links. O script `extracao_sei_v2` automatiza o download após a coleta dos tokens, salvando os documentos no formato:
> ```
> XXXXX.XXXXXX_AAAA-DD/
> └── doc_XXXXXXX.pdf
> ```

### 4. Verificação de Conformidade (`1_analise_SF_INST_pados.ipynb`)

Notebook principal. Para cada pasta de PADO:

- Extrai texto dos PDFs via `PyMuPDF`
- Detecta o tipo de cada documento (Informe, Despacho, Ofício, AR, etc.)
- Classifica o PADO como Tipo A (por Informe) ou Tipo B (Auto de Infração em campo)
- Verifica os 7 requisitos via **Semantic Frames** com `paraphrase-multilingual-MiniLM-L12-v2`
- Identifica a causa raiz das não-conformidades
- Exporta a **Matriz de Conformidade** e os **Detalhes e Evidências** em Excel
- Gera relatório PDF individual por PADO

### 5. Classificação Temática (`1b_analise_LDA_LSA_SF_pados.ipynb`)

Aplica LDA e LSA sobre o corpus de PADOs para identificar o tema regulatório dominante (Consumidor, Universalização, Não Outorgado, etc.).

### 6. Conformance Checking (`1b_analise_RC_CC_INST_pados.ipynb`)

Verifica a sequência processual esperada via `pm4py`:

- **Tipo A:** A2 → A3 → A4
- **Tipo B:** A1 → A3 → A4

Gera o campo `Status_Fluxo` (CONFORME / PARCIAL / NÃO CONFORME) exportado em `relatorio_xai_pados.xlsx`.

### 7. Relatório XAI (`3_analise_XAI_LDA_INST_pados.ipynb`)

Integra os resultados dos notebooks anteriores e gera o relatório final consolidado.

---

## Arquivos Gerados (não versionados)

Os arquivos abaixo são gerados localmente durante a execução e **não estão incluídos no repositório**:

| Arquivo | Descrição |
|---------|-----------|
| `resultado_requisitos_pados_sf.xlsx` | Matriz de Conformidade + Detalhes e Evidências |
| `relatorio_xai_pados.xlsx` | Score composto e Status do Fluxo Processual |
| `relatorio_xai_pados.html` | Visualização HTML do relatório XAI |
| `relatorio_XXXXX.XXXXXX_AAAA-DD.pdf` | Relatório PDF individual por PADO |
| `event_log_instauracao.csv` | Event log para Process Mining |
| `modelo_lda_pados.pkl` | Modelo LDA serializado |
| `pdfs_anatel/` | PDFs dos PADOs coletados |
| `csvs_anatel/` | Bases brutas do SEI em Números |

---

## Instalação

```bash
# Clone o repositório
git clone <url-do-repositorio>
cd <nome-do-repositorio>

# Crie um ambiente virtual (recomendado)
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac

# Instale as dependências
pip install -r requirements.txt

# Baixe o modelo spaCy para português
python -m spacy download pt_core_news_sm
```

---

## Configuração

Antes de executar o notebook principal, ajuste os caminhos no início do `1_analise_SF_INST_pados.ipynb`:

```python
PASTA_PADOS    = r"caminho\para\pdfs_anatel"
ARQUIVO_SAIDA  = "resultado_requisitos_pados_sf.xlsx"
```

---

## Limitações Conhecidas

- **PDFs escaneados:** O pipeline NLP opera sobre texto extraído. Documentos digitalizados sem OCR retornam páginas vazias. Nesses casos, o campo `flag_ocr` é marcado como `SIM` e a verificação dos requisitos fica comprometida. Uma etapa de OCR com `pytesseract` está prevista como trabalho futuro.
- **Token do SEI:** O portal público da ANATEL gera tokens de sessão criptografados, o que impede o download totalmente automatizado dos PDFs sem coleta prévia dos links.
- **Corpus:** O corpus atual cobre a fase de Instauração. As demais fases processuais (Instrução, Decisória, Recursal) não estão contempladas nesta versão.

---

## Referências

- Amaral Cejas et al. (2023). *DERECHA: A Framework for GDPR Compliance Checking of Data Processing Activities*. IEEE Transactions on Software Engineering, vol. 49, n. 9.
- van der Aalst, W. (2016). *Process Mining: Data Science in Action*. Springer.
- Silveira et al. (2021). Aplicação de LDA em corpus jurídico brasileiro.
- ANATEL. *Regulamento de Aplicação de Sanções Administrativas (RASA)*.
- Lei nº 9.472/1997 — Lei Geral de Telecomunicações (LGT).
- Lei nº 9.784/1999 — Processo Administrativo Federal.
- Os resultados deste pipeline foram publicados no artigo:
> Silva, W. F. F. et al. (2026). *Compliance in Administrative 
> Procedural Flows: a Semantic Frame-based Approach*. 
> ENIAC 2026 — BRACIS.

---

## Contexto Acadêmico

Este projeto é parte do projeto de pesquisa ANATEL - Eixo 6 Controle, na linha de pesquisa de Transparência em Inteligência Artificial aplicada à Administração Pública.
