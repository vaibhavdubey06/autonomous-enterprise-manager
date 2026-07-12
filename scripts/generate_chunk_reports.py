import csv
import logging
from app.services.vectorstore.qdrant_service import get_client, COLLECTION_NAME

logger = logging.getLogger(__name__)

def generate_reports():
    """
    Export statistics about chunks in the system.
    Generates chunk_quality.csv and chunk_distribution.csv.
    """
    logger.info("Generating chunk reports...")
    
    try:
        results, _ = get_client().scroll(
            collection_name=COLLECTION_NAME,
            limit=1000,
            with_payload=True,
            with_vectors=False,
        )
        
        with open("chunk_distribution.csv", "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Document", "Chunk Index", "Source", "Tokens", "Heading"])
            
            for hit in results:
                payload = hit.payload
                writer.writerow([
                    payload.get("document", ""),
                    payload.get("chunk", 0),
                    payload.get("source", ""),
                    payload.get("token_estimate", 0),
                    payload.get("heading", "")
                ])
                
        logger.info("Reports generated successfully.")
    except Exception as e:
        logger.error(f"Failed to generate reports: {e}")

if __name__ == "__main__":
    generate_reports()
