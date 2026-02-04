# import os
import streamlit as st
# from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
# import pinecone
from pinecone import Pinecone, ServerlessSpec
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnablePassthrough
# import langchain
from langchain_pinecone import PineconeVectorStore
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document

# load_dotenv()

# initialize pinecone database
pc = Pinecone(api_key = st.secrets["PINECONE_API_KEY"], environment = st.secrets["PINECONE_ENV"])

# set the pinecone index

index_name = 'my-index'
dimension = 3072
metric = 'cosine'
index = pc.Index(index_name)

# initialize embeddings model + vector store

embeddings = OpenAIEmbeddings(model="text-embedding-3-large",api_key=st.secrets["OPENAI_API_KEY"])
vector_store = PineconeVectorStore(index=index, embedding=embeddings)

# retrieval
retriever = vector_store.as_retriever(
    search_type="similarity_score_threshold",
    search_kwargs={"k": 1, "score_threshold": 0.5},
)


chat = ChatOpenAI(model_name = 'gpt-3.5-turbo',
                  api_key= st.secrets["OPENAI_API_KEY"],
                 temperature = 0,
                 max_tokens = 100)
# Approach 1: The Minimalist Way — Manually call retriever then LLM.

# question = "Tell me about the company's leave policy."
# results = retriever.invoke(question)
# context = "\n\n".join(d.page_content for d in results)
# response = chat.invoke(f"Use this context:\n{context}\n\nAnswer the question:{question}.")
#=======================

# Approach 2: The Modern, Clean Way — Use RunnablePassthrough + a small formatting function

prompt = ChatPromptTemplate.from_template(""" 
                                          You are a helpful HR executive who is answering questions for an interviewee about HR policies. 
                                          Use the following context to answer the question: {context} Question: {question} 
                                          """)
def format_docs(docs): 
    print("Formatting documents for prompt...")
    print(docs)
    return "\n\n".join(d.page_content for d in docs)


# chain = (
#     {
#         "context": lambda x: (retriever | format_docs).invoke(x["question"]),
#         "question": lambda x: x["question"],
#         "userName": lambda x: x["userName"]
#     }
#     | prompt
#     | chat
# )


chain = (
    {
        # Process context while keeping the question separate
        "context": retriever | format_docs, 
        "question": RunnablePassthrough()
    } 
    | prompt 
    | chat
)

def retrieve(question):
    print("Retrieving answer for question:", question)  
    # response = chain.invoke({"question": question, "userName": userName})
    response= chain.invoke(question)
    return response.content


if __name__ == "__main__": 
    retrieve("leave policy?")