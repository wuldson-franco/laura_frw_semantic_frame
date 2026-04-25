from sentence_transformers import SentenceTransformer, util
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pathlib import Path
import fitz
import pandas as pd
import torch

# carrega o modelo 
modelo = SentenceTransformer('neuralmind/bert-base-portuguese-cased')

# definindo os requisitos
requisitos = {
    "R1": "O documento identifica o nome da empresa autuada, sua razão social ou CNPJ.",
    "R2": "O texto descreve qual foi a infração cometida, a obrigação que foi descumprida ou a conduta irregular da empresa.",
    "R3": "O documento cita a base normativa, artigos de lei, resoluções da Anatel ou regras violadas.", 
    "R4": "O texto menciona o período da infração, como datas ou duração da conduta irregular.",
    "R5": "O documento indica se houve notificação prévia registrada, como um aviso formal ou comunicação anterior à empresa sobre a infração.", 
    "R6": "O texto apresenta evidências ou provas que sustentam a acusação, como registros de chamadas, relatórios técnicos ou outras formas de documentação.", 
    "R7": "O documento menciona as penalidades ou sanções aplicáveis, como multas, suspensão de serviços ou outras medidas punitivas previstas na legislação.",
}

# gera os embeddings
embeddings = modelo.encode(list(requisitos.values()), convert_to_tensor=True)
nomes_requisitos = list(requisitos.keys())

# transforma o pdf em texto
PASTA_PADOS = Path(r"C:\Users\Euler\Documents\Projeto Anatel\frw_semantic_frame\53500.007555_2026-55\doc_15117751.pdf")
doc = fitz.open(PASTA_PADOS)
texto_limpo = "".join([pagina.get_text() for pagina in doc]).replace('\n', ' ')

# como o bert tem um limite de tokens, é necessário dividir o texto em partes menores
text_splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=150)
text_chunks = text_splitter.split_text(texto_limpo)

#Gerar Embeddings dos Chunks
print(f"Gerando embeddings para {len(text_chunks)} trechos do documento...")
chunks = modelo.encode(text_chunks, convert_to_tensor=True)

# Calcular Similaridade e Avaliar Conformidade

THRESHOLD = 0.70

resultados_documento = []

# Matriz de similaridade entre os chunks do documento e os requisitos
cosine_scores = util.cos_sim(chunks, embeddings)

for req_idx, requisito in enumerate(nomes_requisitos):
    scores_requisito = cosine_scores[:, req_idx]
    
    melhor_score = torch.max(scores_requisito).item()
    melhor_chunk_idx = torch.argmax(scores_requisito).item()
    
    conforme = "Sim" if melhor_score >= THRESHOLD else "Não"
    
    resultados_documento.append({
        "Documento": PASTA_PADOS.name,
        "Requisito": requisito,
        "Sonda": requisitos[requisito],
        "Score Maximo": round(melhor_score, 4),
        "Status": conforme,
        "Trecho Mais Relevante": text_chunks[melhor_chunk_idx][:150] + "..." 
    })

df_resultados = pd.DataFrame(resultados_documento)
print(df_resultados[['Requisito', 'Status', 'Score Maximo']])

saida_csv = Path(r"C:\Users\Euler\Documents\Projeto Anatel\frw_semantic_frame\analise_requisitos.csv")
df_resultados.to_csv(saida_csv, index=False, encoding='utf-8-sig')
print(f"\nSalvo em: {saida_csv}")