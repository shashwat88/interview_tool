# from dotenv import load_dotenv
import streamlit as st

from langchain_community.document_loaders import Docx2txtLoader
from langchain_text_splitters.markdown import MarkdownHeaderTextSplitter
from langchain_text_splitters.character import CharacterTextSplitter
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
import os
import uuid
from sentence_transformers import SentenceTransformer

# load_dotenv()
# loader_docx = Docx2txtLoader("HR_Policy_1.docx")
# documents = loader_docx.load()

def check_pinecone_index_exists(index_name):
    pc = Pinecone(api_key = st.secrets["PINECONE_API_KEY"], environment = st.secrets["PINECONE_ENV"])
    if index_name in [index_name for i in pc.list_indexes()]:
        return True
    return False

def create_pinecone_index():
    pc= Pinecone(api_key = st.secrets["PINECONE_API_KEY"], environment = st.secrets("PINECONE_ENV"))
    index_name = 'my-index'
    dimension = 3072
    metric = 'cosine'

    pc.create_index(
        name = index_name,
        dimension = dimension,
        metric = metric,
        spec = ServerlessSpec(
            cloud = 'aws',
            region = 'us-east-1'
        )
    )

    return pc.Index(index_name)


def load_and_chunk(filepath): 
    print(f"Loading document: {filepath}") 
    loader = Docx2txtLoader(filepath) 
    docs = loader.load() 
    print("Splitting into chunks...") 
    splitter = RecursiveCharacterTextSplitter( chunk_size=500, chunk_overlap=80, separators=["\n\n", "\n", ".", " "] ) 
    chunks = splitter.split_documents(docs) 
    print(f"Total chunks created: {len(chunks)}") 
    for chunk in chunks:
        print(chunk.page_content)
    return chunks

def embed_and_upsert(chunks, index): 
    print("Initializing embedding model...") 
    embedder = OpenAIEmbeddings(model="text-embedding-3-large",api_key=st.secrets["OPENAI_API_KEY"])
    vectors = [] 
    print("Embedding and preparing vectors...") 
    for _, chunk in enumerate(chunks): 
        text = chunk.page_content 
        metadata = { 
            "source": chunk.metadata.get("source", "unknown"), 
            "chunk_id": str(uuid.uuid4()), 
            "text": text[:200] # preview for debugging 
            } 
        embedding = embedder.embed_query(text) 
        vectors.append({ "id": metadata["chunk_id"], "values": embedding, "metadata": metadata }) 
        print(f"Upserting {len(vectors)} vectors into Pinecone...") 
        index.upsert(vectors) 
        print("Upsert complete!")

def ingest(filepath): 
    if check_pinecone_index_exists('my-index'):
        print("Pinecone index already exists. Document ingestion skipped.")
    else:    
        index = create_pinecone_index()
        chunks = load_and_chunk(filepath) 
        embed_and_upsert(chunks, index) 
        print("Ingestion pipeline completed successfully.")

if __name__ == "__main__": 
    ingest("HR_Policy_1.docx")