import logging
import asyncio
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from core.config import settings
from vectorstores.pinecone_index import pc

logger = logging.getLogger(__name__)


def namespace_exists(namespace: str) -> bool:
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
    def __init__(self, k: int = 7, namespace: str | None = None):
        self.k = k
        self.namespace = namespace or settings.PINECONE_NAMESPACE
        embedder = OpenAIEmbeddings(model="text-embedding-ada-002", api_key=settings.OPENAI_API_KEY)
        vector_store = PineconeVectorStore.from_existing_index(
            index_name=settings.PINECONE_INDEX_NAME,
            embedding=embedder,
            namespace=self.namespace,
        )
        self.retriever = vector_store.as_retriever(search_kwargs={"k": self.k})

    def search(self, query: str):
        docs = self.retriever.get_relevant_documents(query)
        return [doc.page_content for doc in docs]

    async def async_search(self, query: str):
        try:
            loop = asyncio.get_event_loop()
            docs = await loop.run_in_executor(None, self.retriever.get_relevant_documents, query)
            return docs
        except Exception as e:
            logger.error(
                f"RAG search failed for query '{query[:100]}...' in namespace '{self.namespace}': {e}"
            )
            return []


rag_searcher = RAGSearcher()


