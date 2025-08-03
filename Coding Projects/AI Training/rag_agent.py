import os
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from langchain.llms import OpenAI
from langchain.chains import RetrievalQA
from ebooklib import epub
import PyPDF2

# Step 2: Extract text from ePub and PDF
def extract_text_from_library(directory):
    texts = []
    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        if filename.endswith('.epub'):
            book = epub.read_epub(filepath)
            for item in book.get_items_of_type(epub.EPUB_HTML):
                texts.append(item.get_content().decode('utf-8'))
        elif filename.endswith('.pdf'):
            with open(filepath, 'rb') as f:
                pdf = PyPDF2.PdfReader(f)
                text = ''.join(page.extract_text() for page in pdf.pages)
                texts.append(text)
    return texts

# Step 3: Index the library
texts = extract_text_from_library('path/to/your/library')
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
vector_store = FAISS.from_texts(texts, embeddings)

# Step 4: Set up RAG with local LLM
llm = OpenAI(base_url="http://localhost:1234/v1", api_key="not-needed")  # LM Studio API
qa_chain = RetrievalQA.from_chain_type(llm=llm, chain_type="stuff", retriever=vector_store.as_retriever(search_kwargs={"k": 5}))

# Step 5: Simple CLI interface
def run_agent():
    while True:
        query = input("Enter your query (or 'exit' to quit): ")
        if query.lower() == 'exit':
            break
        response = qa_chain.run(query)
        print("Response:", response)

if __name__ == "__main__":
    run_agent()