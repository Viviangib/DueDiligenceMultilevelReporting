import time
import uuid
from typing import List
from pinecone import Pinecone, ServerlessSpec
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from config import settings

# Initialize Pinecone
pc = Pinecone(api_key=settings.PINECONE_API_KEY.get_secret_value())


def ensure_index():
    """Ensure the Pinecone index exists and is ready."""
    if settings.PINECONE_INDEX_NAME not in pc.list_indexes().names():
        pc.create_index(
            name=settings.PINECONE_INDEX_NAME,
            dimension=1536,
            metric="cosine",
            spec=ServerlessSpec(cloud=settings.CLOUD, region=settings.REGION),
        )
        while not pc.describe_index(settings.PINECONE_INDEX_NAME).status["ready"]:
            print("Waiting for index to be ready...")
            time.sleep(2)


def get_embedder():
    """Return an OpenAI embedder instance."""
    return OpenAIEmbeddings(
        model="text-embedding-ada-002", api_key=settings.OPENAI_API_KEY
    )


def chunk_text(text: str, chunk_size=1500, chunk_overlap=250) -> List[Document]:
    """Split text into overlapping chunks."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap
    )
    texts = splitter.split_text(text)
    return [Document(page_content=chunk) for chunk in texts]


def embed_and_store_documents(
    documents: List[Document], namespace: str, batch_size: int = 100
):
    ensure_index()
    embedder = get_embedder()

    vs = PineconeVectorStore.from_existing_index(
        index_name=settings.PINECONE_INDEX_NAME, embedding=embedder, namespace=namespace
    )

    for i in range(0, len(documents), batch_size):
        batch = documents[i : i + batch_size]
        ids = [str(uuid.uuid4()) for _ in batch]
        try:
            vs.add_documents(documents=batch, ids=ids)
            print(f"Uploaded batch {i // batch_size + 1}")
        except Exception as e:
            print(f"Error uploading batch {i // batch_size + 1}: {e}")
