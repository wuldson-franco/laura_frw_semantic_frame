# Notebooks — Para que serve e como usar

---

## `1_analise_SF_INST_pados.ipynb`
**Camada 1 — Verificação de Conformidade Documental**

### Para que serve
É o notebook principal do framework. Verifica se os **7 requisitos normativos (R1–R7)** da fase de Instauração estão presentes nos documentos de cada PADO.

Para cada requisito, o notebook responde: *"Este documento existe e contém o conteúdo obrigatório?"*

A verificação usa **Semantic Frames** com o modelo `paraphrase-multilingual-MiniLM-L12-v2` (sentence-transformers), que compara o conteúdo dos PDFs com sentenças de referência baseadas nos normativos (LGT, RASA e Lei 9.784/99). O threshold de similaridade de cosseno é 0.55.

Quando um requisito não é encontrado, o notebook identifica a **causa raiz** entre três possibilidades:
- PDF escaneado sem texto extraível (flag OCR)
- Etapa processual ausente na pasta do PADO
- Documento presente mas requisito não localizado pelo Semantic Frame

### Entradas
| Arquivo | Descrição |
|---------|-----------|
| `pdfs_anatel/XXXXX.XXXXXX_AAAA-DD/` | Pastas com os PDFs de cada PADO |

### Saídas
| Arquivo | Descrição |
|---------|-----------|
| `resultado_requisitos_pados_sf.xlsx` | Sheet **Matriz de Conformidade**: resultado R1–R7 por PADO |
| `resultado_requisitos_pados_sf.xlsx` | Sheet **Detalhes e Evidências**: evidências, etapas e explicações por requisito |
| `relatorio_XXXXX.XXXXXX_AAAA-DD.pdf` | Relatório individual por PADO (gerado na última célula) |

### Como usar
1. Ajuste o caminho `PASTA_PADOS` na célula 2 para apontar para a pasta raiz com os PDFs
2. Execute todas as células em ordem (1 → 11)
3. Para gerar o PDF individual de um PADO específico, altere `PADO_ALVO` na última célula e execute

> **Atenção:** As células 5 dependem das células 3 e 4. Execute sempre em sequência.

---

## `1b_analise_LDA_LSA_SF_pados.ipynb`
**Classificação Temática do Corpus**

### Para que serve
Notebook exploratório que aplica **LDA (Latent Dirichlet Allocation)** e **LSA (Latent Semantic Analysis)** sobre o corpus completo de PADOs para identificar o **tema regulatório dominante** de cada processo.

Os temas identificados correspondem às categorias da ANATEL: Consumidor, Universalização, Não Outorgado, Certificação, Irregularidade Técnica, entre outros.

O modelo LDA treinado é serializado e salvo em `modelo_lda_pados.pkl` para ser carregado pelo notebook 3 durante a geração do relatório XAI.

> **Nota:** Este notebook é uma etapa de experimentação. O número de tópicos LDA foi ajustado manualmente após análise da coerência dos tópicos. O resultado final utilizado pelo framework é o modelo salvo no `.pkl`.

### Entradas
| Arquivo | Descrição |
|---------|-----------|
| `pdfs_anatel/XXXXX.XXXXXX_AAAA-DD/` | Pastas com os PDFs de cada PADO |

### Saídas
| Arquivo | Descrição |
|---------|-----------|
| `modelo_lda_pados.pkl` | Modelo LDA serializado com vetorizador e mapeamento de tópicos |

### Como usar
1. Ajuste o caminho `PASTA_PADOS`
2. Execute todas as células em ordem
3. Avalie a coerência dos tópicos gerados e ajuste `N_TOPICOS_LDA` se necessário
4. Execute a célula de serialização para salvar o modelo atualizado

---

## `2_analise_RC_CC_INST_pados.ipynb`
**Camada 2 — Conformance Checking do Fluxo Processual**

### Para que serve
Enquanto o notebook 1 verifica se os documentos existem, este notebook verifica se o **fluxo processual seguiu a sequência correta**.

São perguntas diferentes:
- Notebook 1 pergunta: *"O documento de notificação existe?"*
- Notebook 2 pergunta: *"A notificação aconteceu depois do despacho de instauração, na ordem correta?"*

O notebook constrói um **Event Log** a partir dos PDFs — extraindo tipo de documento, data de assinatura e responsável — e verifica o fluxo em **4 perspectivas** usando `pm4py`:

| Perspectiva | O que verifica |
|-------------|----------------|
| **Fluxo** | A sequência A1→A2→A3→A4 foi respeitada conforme o tipo do PADO? |
| **Dados** | Todas as atividades obrigatórias estão presentes? |
| **Recursos** | Os documentos têm responsável identificado? |
| **Tempo** | Os prazos entre as etapas foram respeitados? (3 métricas) |

A sequência esperada varia pelo tipo:
- **Tipo A** (por Informe): A2 → A3 → A4
- **Tipo B** (Auto de Infração em campo): A1 → A3 → A4

### Entradas
| Arquivo | Descrição |
|---------|-----------|
| `pdfs_anatel/XXXXX.XXXXXX_AAAA-DD/` | Pastas com os PDFs de cada PADO |
| `resultado_requisitos_pados_sf.xlsx` | Matriz de Conformidade do notebook 1 (para obter o `Tipo_PADO`) |

### Saídas
| Arquivo | Descrição |
|---------|-----------|
| `event_log_instauracao.csv` | Event log completo com todos os eventos extraídos dos PDFs |

### Como usar
1. **Execute o notebook 1 primeiro** — este notebook lê o `Tipo_PADO` da matriz gerada por ele
2. Ajuste os caminhos `PASTA_PADOS` e `ARQUIVO_MATRIZ` na célula de configuração
3. Execute todas as células em ordem
4. O event log salvo em `event_log_instauracao.csv` é a entrada para o notebook 3

> **Nota sobre o fitness:** O fitness médio reportado pela Perspectiva 1 pode ser baixo (≈40–50%) porque o Alpha Miner descobre um modelo linear estrito que penaliza PADOs Tipo A (sem A1 separado) e Tipo B (sem A2). Isso é comportamento esperado — os resultados mais confiáveis estão nas **Perspectivas 2 e 4**.

---

## `3_analise_XAI_LDA_INST_pados.ipynb`
**Camada 3 — XAI: Integração, Score Composto e Relatório Final**

### Para que serve
Notebook de integração final. Combina os resultados das três camadas do framework em um **score composto único** por PADO e gera os relatórios de saída.

**Score Composto (ponderado):**

| Camada | Fonte | Peso |
|--------|-------|------|
| Conformidade R1–R7 | Notebook 1 | 50% |
| Fluxo Processual | Notebook 2 | 35% |
| Qualidade dos PDFs (OCR) | Notebook 1 | 15% |

O score classifica cada PADO em quatro níveis: **ALTO** (≥0.85) · **MEDIO** (≥0.65) · **BAIXO** (≥0.40) · **CRITICO** (<0.40)

Além do score, o notebook gera **explicações humanizadas** dos requisitos não conformes — convertendo as mensagens técnicas do Semantic Frame em linguagem acessível para auditores da ANATEL, referenciando os normativos aplicáveis.

### Entradas
| Arquivo | Descrição |
|---------|-----------|
| `resultado_requisitos_pados_sf.xlsx` | Saída do notebook 1 |
| `event_log_instauracao.csv` | Saída do notebook 2 |
| `modelo_lda_pados.pkl` | Modelo LDA salvo pelo notebook 1b |

### Saídas
| Arquivo | Descrição |
|---------|-----------|
| `relatorio_xai_pados.xlsx` | Sheet **Relatorio XAI**: score composto, status de fluxo, tema LDA e explicações por PADO |
| `relatorio_xai_pados.html` | Dashboard interativo com 5 gráficos (Chart.js), filtros e detalhamento por PADO |
| `relatorio_XXXXX.XXXXXX_AAAA-DD.pdf` | Relatório PDF individual por PADO (última célula) |

### Como usar
1. **Execute os notebooks 1, 1b e 2 primeiro** — este notebook depende das três saídas deles
2. Ajuste os caminhos na célula de configuração (`ARQUIVO_NB1`, `ARQUIVO_NB2`, `ARQUIVO_LDA`)
3. Execute todas as células em ordem (1 → 12)
4. Para gerar o PDF individual, altere `PADO_ALVO` na última célula e execute
5. Abra `relatorio_xai_pados.html` no Chrome ou Edge para visualizar o dashboard completo

---

## Ordem de execução recomendada

```
1b_analise_LDA_LSA_SF_pados.ipynb   →  gera modelo_lda_pados.pkl
         ↓
1_analise_SF_INST_pados.ipynb        →  gera resultado_requisitos_pados_sf.xlsx
         ↓
2_analise_RC_CC_INST_pados.ipynb     →  gera event_log_instauracao.csv
         ↓
3_analise_XAI_LDA_INST_pados.ipynb  →  gera relatorio_xai_pados.xlsx / .html / .pdf
```