# ingest_to_qdrant.py

import json
import os
import time
from qdrant_client import QdrantClient, models
from openai import AzureOpenAI
from dotenv import load_dotenv
from tqdm import tqdm

# --- Configuration ---
# Load environment variables from the .env file
load_dotenv()

# Qdrant configuration
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
COLLECTION_NAME = "Connect_Investigation_Training_Manual_v25.0" # Using a new name to avoid conflicts

# Azure OpenAI configuration
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
AZURE_API_VERSION = "2023-05-15" # A common, stable API version

# Model-specific configuration
# The 'text-embedding-3-large' model has a fixed dimension of 3072.
EMBEDDING_SIZE = 3072

# Path to your extracted data
JSON_FILE_PATH = "C:/connect/L-D/doc-chunker/extracted_content_2.json"

def ingest_data_with_azure():
    """
    Reads data from the JSON file, generates embeddings using Azure OpenAI,
    and ingests it into a Qdrant collection.
    """
    
    # --- Step 1: Validate Azure Configuration ---
    print("Step 1: Validating Azure OpenAI configuration...")
    if not all([AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, AZURE_OPENAI_DEPLOYMENT_NAME]):
        raise ValueError(
            "Azure OpenAI environment variables are not set. "
            "Please create a .env file with AZURE_OPENAI_ENDPOINT, "
            "AZURE_OPENAI_API_KEY, and AZURE_OPENAI_DEPLOYMENT_NAME."
        )
    print("Azure configuration loaded successfully.")

    # --- Step 2: Initialize Azure OpenAI Client ---
    print("\nStep 2: Initializing Azure OpenAI client...")
    azure_client = AzureOpenAI(
        api_key=AZURE_OPENAI_API_KEY,
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        api_version=AZURE_API_VERSION,
    )
    print("Azure OpenAI client initialized.")

    # --- Step 3: Initialize Qdrant Client and Create Collection ---
    print("\nStep 3: Initializing Qdrant client and setting up collection...")
    qdrant_client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    
    qdrant_client.recreate_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=models.VectorParams(
            size=EMBEDDING_SIZE,
            distance=models.Distance.COSINE
        )
    )
    print(f"Qdrant collection '{COLLECTION_NAME}' created with vector size {EMBEDDING_SIZE}.")

    # --- Step 4: Load and Prepare Data ---
    print(f"\nStep 4: Loading data from '{JSON_FILE_PATH}'...")
    if not os.path.exists(JSON_FILE_PATH):
        print(f"Error: JSON file not found at '{JSON_FILE_PATH}'")
        return
        
    with open(JSON_FILE_PATH, 'r', encoding='utf-8') as f:
        chunks = json.load(f)
    
    # Filter for chunks that have text content to embed
    text_chunks = [chunk for chunk in chunks if 'content' in chunk and chunk.get('content')]
    print(f"Loaded {len(chunks)} chunks, found {len(text_chunks)} with content to embed.")

    # --- Step 5: Generate Embeddings and Upload to Qdrant ---
    print(f"\nStep 5: Generating embeddings via Azure and uploading to Qdrant...")
    points_to_upload = []
    
    # Process chunks one by one to respect API rate limits and show progress
    for idx, chunk in enumerate(tqdm(text_chunks, desc="Embedding Chunks")):
        try:
            # Get the embedding from Azure OpenAI
            response = azure_client.embeddings.create(
                input=chunk['content'],
                model=AZURE_OPENAI_DEPLOYMENT_NAME
            )
            embedding_vector = response.data[0].embedding

            # Create the Qdrant point
            point = models.PointStruct(
                id=idx,
                vector=embedding_vector,
                payload=chunk
            )
            points_to_upload.append(point)

        except Exception as e:
            print(f"\nError processing chunk {idx}: {e}")
            print("Skipping this chunk.")
            # Optional: Add a small delay and retry logic here if needed
            time.sleep(1)
    
    # Upsert all collected points in a single batch
    if points_to_upload:
        print(f"\nUploading {len(points_to_upload)} points to Qdrant...")
        qdrant_client.upsert(
            collection_name=COLLECTION_NAME,
            points=points_to_upload,
            wait=True
        )

    print("\n--- Ingestion Complete! ---")
    print(f"Successfully uploaded {len(points_to_upload)} data points to the '{COLLECTION_NAME}' collection.")
    print("You can now verify the data in the Qdrant Dashboard: http://localhost:5173/")


if __name__ == '__main__':
    ingest_data_with_azure()