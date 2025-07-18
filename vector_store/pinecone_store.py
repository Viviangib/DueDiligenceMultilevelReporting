import logging
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from config import settings
import asyncio
from vector_store.pinecone import pc

logger = logging.getLogger(__name__)


def namespace_exists(namespace: str) -> bool:
    # List all namespaces for the configured index
    index_name = settings.PINECONE_INDEX_NAME
    try:
        index = pc.Index(index_name)
        stats = index.describe_index_stats()
        namespaces = stats.get("namespaces", {}).keys()
        return namespace in namespaces
    except Exception as e:
        logger.error(f"Error checking Pinecone namespace existence: {e}")
        return False


class RAGSearcher:
    def __init__(self, k=8, namespace=None):
        self.k = k
        self.namespace = namespace or settings.PINECONE_NAMESPACE
        logger.info(f"Initializing RAG searcher with namespace: {self.namespace}")
        embedder = OpenAIEmbeddings(
            model="text-embedding-ada-002", api_key=settings.OPENAI_API_KEY
        )
        vector_store = PineconeVectorStore.from_existing_index(
            index_name=settings.PINECONE_INDEX_NAME,
            embedding=embedder,
            namespace=self.namespace,
        )
        self.retriever = vector_store.as_retriever(search_kwargs={"k": self.k})
        logger.info("RAG searcher initialized successfully.")

    def search(self, query: str):
        logger.info(
            f"Running RAG search in namespace '{self.namespace}' for query: {query[:100]}..."
        )
        docs = self.retriever.get_relevant_documents(query)
        evidence = [doc.page_content for doc in docs]
        logger.info(f"Retrieved {len(evidence)} documents.")
        return evidence

    async def async_search(self, query: str):
        logger.info(
            f"Running async RAG search in namespace '{self.namespace}' for query: {query[:100]}..."
        )
        try:
            # Run synchronous get_relevant_documents in a thread to make it async-compatible
            loop = asyncio.get_event_loop()
            docs = await loop.run_in_executor(
                None, self.retriever.get_relevant_documents, query
            )
            evidence = [doc.page_content for doc in docs]
            logger.info(f"Retrieved {len(evidence)} documents.")
            return evidence
        except Exception as e:
            logger.error(
                f"RAG search failed for query '{query[:100]}...' in namespace '{self.namespace}': {e}"
            )
            return []


# Create one shared instance
rag_searcher = RAGSearcher()
