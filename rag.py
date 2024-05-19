from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

model = SentenceTransformer('all-MiniLM-L6-v2')
index = None
chunks = []

def process_text(text):
    global model, index, chunks
    chunks = [text[i:i + 500] for i in range(0, len(text), 500)]
    vectors = model.encode(chunks)
    index = faiss.IndexFlatL2(model.get_sentence_embedding_dimension())
    index.add(np.array(vectors).astype('float32'))

def search_chunks(query):
    global model, index, chunks
    if model is not None and index is not None and chunks:
        query_vector = model.encode([query])
        scores, indices = index.search(np.array(query_vector).astype('float32'), 20)
        relevant_chunks = [chunks[i] for i in indices[0]]
        return relevant_chunks
    return []