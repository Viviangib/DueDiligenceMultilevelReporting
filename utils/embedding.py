from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain.text_splitter import RecursiveCharacterTextSplitter
import pinecone
from pydantic import SecretStr
from typing import List
import os

class EmbeddingHelper:
    def __init__(self, openai_api_key: str, pinecone_index: str,pinecone_api_key: str):
        self.embeddings = OpenAIEmbeddings(model="text-embedding-ada-002", api_key=SecretStr(openai_api_key))
        self.index_name = pinecone_index
        self.pinecone_api_key = pinecone_api_key

    def chunk_text(self, text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[str]:
        splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        return splitter.split_text(text)

    def store_chunks(self, chunks: List[str], namespace: str):
        PineconeVectorStore.from_texts(
            texts=chunks,
            embedding=self.embeddings,
            index_name=self.index_name,
            namespace=namespace
        )

    def get_retriever(self, namespace: str, k: int = 5):
        vector_store = PineconeVectorStore.from_existing_index(
            index_name=self.index_name,
            embedding=self.embeddings,
            namespace=namespace
        )
        return vector_store.as_retriever(search_kwargs={"k": k}) 