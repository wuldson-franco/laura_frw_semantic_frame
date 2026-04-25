from pathlib import Path
from langchain_text_splitters import RecursiveCharacterTextSplitter
from transformers import pipeline
import fitz
import pandas as pd

# transforma o pdf em texto
PASTA_PADOS = Path(r"C:\Users\Euler\Documents\Projeto Anatel\frw_semantic_frame\53500.007555_2026-55\doc_15117751.pdf")

doc = fitz.open(PASTA_PADOS)
texto_extraido = ""
for pagina in doc:
    texto_extraido += pagina.get_text()

# trata o texto extraído para remover quebras de linha e outros caracteres indesejados
texto_limpo = texto_extraido.replace('\n', ' ')

# como o bert tem um limite de tokens, é necessário dividir o texto em partes menores
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
list_chunks = text_splitter.split_text(texto_limpo)

# carrega o modelo pré-treinado do BERT para português e cria um pipeline de reconhecimento de entidades nomeadas (NER)
modelo = 'neuralmind/bert-base-portuguese-cased'
anatel_requisitos = pipeline('ner', model=modelo)

lista_resultados = []
for chunk in list_chunks:
    # --- Passo A: Extrair Entidades (NER) ---
    entidades_encontradas = anatel_requisitos(chunk)
    for ent in entidades_encontradas:
           lista_resultados.append(ent)

if not lista_resultados:
    print('Nenhuma entidade encontrada.')
else:  
    print(f'Entidades encontradas: {len(lista_resultados)}')
    df_entidades = pd.DataFrame(lista_resultados)
    saida_csv = Path(r"C:\Users\Euler\Documents\Projeto Anatel\frw_semantic_frame\entidades_extraidas.csv")
    saida_txt = Path(r"C:\Users\Euler\Documents\Projeto Anatel\frw_semantic_frame\entidades_extraidas.txt")  
    
    saida_csv.parent.mkdir(parents=True, exist_ok=True)
    df_entidades.to_csv(saida_csv, index=False, encoding='utf-8-sig')

    entidades_unicas = df_entidades['word'].dropna().unique()
    saida_txt.write_text('\n'.join(entidades_unicas), encoding='utf-8')


''' 
Cada requisito corresponde a uma informação que deve estar presente no documento. Exemplos:

R1 — Identificação da empresa autuada

R2 — Descrição da obrigação descumprida

R3 — Base normativa citada

R4 — Período da infração

R5 — Notificação prévia registrada

R6 — Prazo para defesa indicado

R7 — Autoridade competente identificada
'''