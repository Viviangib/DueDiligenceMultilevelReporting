import logging
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from config import settings

# Configure logging
logger = logging.getLogger(__name__)

def rag_search(query: str, k: int = 8):
    logger.info(f"Starting RAG search for query: {query[:100]}...")
    logger.info(f"Retrieving top {k} documents")
    
    try:
        logger.info("Initializing OpenAI embeddings")
        embedder = OpenAIEmbeddings(
            model="text-embedding-ada-002",
            api_key=settings.OPENAI_API_KEY
        )
        logger.info("OpenAI embeddings initialized successfully")
        
        logger.info(f"Connecting to Pinecone index: {settings.PINECONE_INDEX_NAME}")
        logger.info(f"Using namespace: {settings.PINECONE_NAMESPACE}")
        
        vector_store = PineconeVectorStore.from_existing_index(
            index_name=settings.PINECONE_INDEX_NAME,
            embedding=embedder,
            namespace=settings.PINECONE_NAMESPACE
        )
        logger.info("Pinecone vector store connected successfully")
        
        logger.info("Creating retriever")
        retriever = vector_store.as_retriever(search_kwargs={"k": k})
        logger.info("Retriever created successfully")
        
        logger.info("Performing similarity search")
        docs = retriever.get_relevant_documents(query)
        logger.info(f"Search completed. Retrieved {len(docs)} documents")
        
        evidence = [doc.page_content for doc in docs]
        logger.info(f"Extracted evidence from {len(evidence)} documents")
        
        # Log some sample evidence for debugging
        for i, ev in enumerate(evidence[:2]):  # Log first 2 pieces
            logger.info(f"Evidence {i+1}: {ev[:200]}...")
        
        logger.info("RAG search completed successfully")
        return evidence
        
    except Exception as e:
        logger.error(f"RAG search failed: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        raise Exception(f"RAG search failed: {str(e)}") 