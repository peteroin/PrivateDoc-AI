import os
import glob
import hashlib

import chromadb

from sentence_transformers import SentenceTransformer


DATA_DIR = "data"
VECTOR_DIR = "vectorstore"


embedding_model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)


client = chromadb.PersistentClient(
    path=VECTOR_DIR
)


collection = client.get_or_create_collection(
    name="private_data"
)


def chunk_text(
    text,
    chunk_size=1000,
    overlap=150
):

    chunks = []

    start = 0

    while start < len(text):

        end = start + chunk_size

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        start += chunk_size - overlap

    return chunks


def make_document_id(source):

    return hashlib.sha256(
        source.encode("utf-8")
    ).hexdigest()[:16]


def make_chunk_id(
    source,
    chunk_index
):

    document_id = make_document_id(
        source
    )

    return (
        f"{document_id}_chunk_{chunk_index}"
    )


def add_document(
    text,
    source
):
    chunks = chunk_text(text)

    if not chunks:
        return 0

    # Create stable document ID
    document_id = make_document_id(source)

    # Remove any previous version
    old_results = collection.get(
        where={
            "source": source
        }
    )

    old_ids = old_results.get(
        "ids",
        []
    )

    if old_ids:
        collection.delete(
            ids=old_ids
        )

    # Create embeddings
    embeddings = (
        embedding_model
        .encode(chunks)
        .tolist()
    )

    ids = []

    metadatas = []

    for index in range(len(chunks)):

        ids.append(
            make_chunk_id(
                source,
                index
            )
        )

        metadatas.append({

            "source": source,

            "document_id": document_id,

            "chunk_index": index
        })

    collection.add(
        ids=ids,
        documents=chunks,
        embeddings=embeddings,
        metadatas=metadatas
    )

    return len(chunks)


def load_documents():

    files = glob.glob(
        os.path.join(
            DATA_DIR,
            "**",
            "*.txt"
        ),
        recursive=True
    )


    total_chunks = 0


    for file_path in files:

        with open(
            file_path,
            "r",
            encoding="utf-8"
        ) as file:

            text = file.read()


        chunks_added = add_document(
            text,
            file_path
        )


        total_chunks += chunks_added


    return total_chunks


def create_vector_database():

    total = load_documents()

    print(
        f"Indexed {total} document chunks."
    )


def search_private_data(
    query,
    n_results=3,
    distance_threshold=1.0
):

    query_embedding = (
        embedding_model
        .encode([query])
        .tolist()
    )


    results = collection.query(

        query_embeddings=query_embedding,

        n_results=n_results,

        include=[
            "documents",
            "metadatas",
            "distances"
        ]
    )


    documents = results.get(
        "documents",
        [[]]
    )[0]


    metadatas = results.get(
        "metadatas",
        [[]]
    )[0]


    distances = results.get(
        "distances",
        [[]]
    )[0]


    filtered_documents = []

    filtered_metadatas = []


    for (
        document,
        metadata,
        distance
    ) in zip(
        documents,
        metadatas,
        distances
    ):

        if distance <= distance_threshold:

            filtered_documents.append(
                document
            )

            filtered_metadatas.append(
                metadata
            )


    return {

        "documents":
            filtered_documents,

        "metadatas":
            filtered_metadatas
    }


def list_documents():

    results = collection.get(
        include=[
            "metadatas"
        ]
    )


    metadatas = results.get(
        "metadatas",
        []
    )


    document_counts = {}


    for metadata in metadatas:

        source = metadata.get(
            "source",
            "Unknown"
        )


        if source not in document_counts:

            document_counts[source] = 0


        document_counts[source] += 1


    return [

        {
            "source": source,

            "chunks": chunks
        }

        for source, chunks
        in document_counts.items()
    ]


def delete_document(source):

    results = collection.get(

        where={
            "source": source
        }
    )


    ids = results.get(
        "ids",
        []
    )


    if ids:

        collection.delete(
            ids=ids
        )


    return len(ids)