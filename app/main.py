import os
import shutil
import tempfile

from fastapi import (
    FastAPI,
    UploadFile,
    File,
    HTTPException
)

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from pydantic import BaseModel

from dotenv import load_dotenv

from groq import Groq

from pypdf import PdfReader
from docx import Document

from app.rag import (
    create_vector_database,
    search_private_data,
    add_document,
    list_documents,
    delete_document
)


load_dotenv()


app = FastAPI(
    title="Private Data Chatbot"
)


client = Groq(
    api_key=os.getenv(
        "GROQ_API_KEY"
    )
)


class ChatRequest(BaseModel):

    message: str


@app.on_event("startup")
def startup():

    create_vector_database()


@app.get("/")
def home():

    return FileResponse(
        "frontend/index.html"
    )


@app.post("/chat")
def chat(
    request: ChatRequest
):

    user_question = request.message

    search_result = search_private_data(
        user_question,
        n_results=3
    )

    documents = search_result[
        "documents"
    ]

    metadatas = search_result[
        "metadatas"
    ]

    if not documents:

        return {
            "question": user_question,
            "answer": (
                "I couldn't find this information "
                "in the provided private data."
            ),
            "sources": []
        }


    context_parts = []

    for document, metadata in zip(
        documents,
        metadatas
    ):

        source = metadata.get(
            "source",
            "Unknown"
        )

        context_parts.append(
            f"Source: {source}\n"
            f"{document}"
        )


    context_text = "\n\n".join(
        context_parts
    )


    prompt = f"""
You are a private company and hospital
knowledge assistant.

Answer the user's question ONLY using
the private data provided below.

Do not use outside knowledge.

Do not invent information.

If the answer cannot be found in the
provided private data, say:

"I couldn't find this information in the
provided private data."

Private Data:
{context_text}

User Question:
{user_question}
"""


    response = client.chat.completions.create(

        model="openai/gpt-oss-20b",

        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],

        temperature=0
    )


    answer = (
        response
        .choices[0]
        .message
        .content
    )


    sources = list(
        dict.fromkeys(
            metadata.get(
                "source",
                "Unknown"
            )
            for metadata in metadatas
        )
    )


    return {

        "question": user_question,

        "answer": answer,

        "sources": sources
    }


@app.post("/upload")
async def upload_document(
    file: UploadFile = File(...)
):

    allowed_extensions = {
        ".txt",
        ".pdf",
        ".docx"
    }


    filename = file.filename or ""

    extension = os.path.splitext(
        filename
    )[1].lower()


    if extension not in allowed_extensions:

        raise HTTPException(
            status_code=400,
            detail=(
                "Only TXT, PDF and DOCX "
                "files are supported."
            )
        )


    temp_path = os.path.join(
        tempfile.gettempdir(),
        filename
    )


    with open(
        temp_path,
        "wb"
    ) as buffer:

        shutil.copyfileobj(
            file.file,
            buffer
        )


    try:

        # TXT
        if extension == ".txt":

            with open(
                temp_path,
                "r",
                encoding="utf-8"
            ) as f:

                text = f.read()


        # PDF
        elif extension == ".pdf":

            reader = PdfReader(
                temp_path
            )

            pages = []

            for page in reader.pages:

                page_text = (
                    page.extract_text()
                    or ""
                )

                pages.append(
                    page_text
                )

            text = "\n\n".join(
                pages
            )


        # DOCX
        elif extension == ".docx":

            document = Document(
                temp_path
            )

            paragraphs = []

            for paragraph in document.paragraphs:

                paragraphs.append(
                    paragraph.text
                )

            text = "\n".join(
                paragraphs
            )


        if not text.strip():

            raise HTTPException(
                status_code=400,
                detail=(
                    "The uploaded document "
                    "contains no readable text."
                )
            )


        chunks_added = add_document(
            text,
            filename
        )


        return {

            "message": (
                "Document uploaded successfully."
            ),

            "filename": filename,

            "chunks_added": chunks_added
        }


    finally:

        if os.path.exists(
            temp_path
        ):

            os.remove(
                temp_path
            )


@app.get("/documents")
def get_documents():

    return {
        "documents": list_documents()
    }


@app.delete("/documents")
def remove_document(
    source: str
):

    deleted_chunks = delete_document(
        source
    )


    return {

        "message":
            "Document deleted successfully.",

        "source":
            source,

        "chunks_deleted":
            deleted_chunks
    }



app.mount(
    "/static",
    StaticFiles(
        directory="frontend"
    ),
    name="static"
)