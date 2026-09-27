from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

def ingest_pipeline():

    loader = PyPDFLoader("heart_failure_Patient-Discharge-Packet_2022.pdf")
    documents = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    text_chunks = text_splitter.split_documents(documents)

    vector_store = Chroma.from_documents(
        documents=text_chunks,
        embedding=HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    )
    return vector_store
