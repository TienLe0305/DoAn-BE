import pdfplumber
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

model = None
index = None
chunks = []

def load_rag_model(pdf_contents):
    global model, index, chunks

    # Load the pre-trained sentence transformer model
    model = SentenceTransformer('all-MiniLM-L6-v2')

    # Extract text from the PDF file
    with pdfplumber.open(pdf_contents) as pdf:
        text = " ".join(page.extract_text() for page in pdf.pages)

    # Split the text into chunks
    chunks = [text[i:i+500] for i in range(0, len(text), 500)]  # Adjust chunk size as needed

    # Encode the chunks into vectors
    vectors = model.encode(chunks)

    # Create a FAISS index and add the vectors
    index = faiss.IndexFlatL2(model.get_sentence_embedding_dimension())
    index.add(np.array(vectors).astype('float32'))

def search_chunks(query):
    global model, index, chunks
    if model is None or index is None or not chunks:
        return []

    query_vector = model.encode([query])
    scores, indices = index.search(np.array(query_vector).astype('float32'), 5)  # Adjust the number of results as needed
    relevant_chunks = [chunks[i] for i in indices[0]]
    return relevant_chunks