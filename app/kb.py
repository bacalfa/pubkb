from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable, RunnableLambda
from langchain_community.document_transformers import LongContextReorder
from langchain_core.runnables.base import Output, Iterator, Union
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores.utils import filter_complex_metadata
from langchain_chroma import Chroma
import os
import glob

llm_model_name = os.environ.get("LLM_MODEL", "phi3:medium")
embedding_model_name = os.environ.get("EMBEDDING_MODEL", "nomic-embed-text")
base_url = os.environ.get("BASE_URL", "http://ollama:11434")


class PubManager:
    def __init__(self, llm_name: str = llm_model_name, is_stream: bool = False):
        self.is_stream: bool = is_stream
        self.llm: ChatOllama = ChatOllama(model=llm_name)
        self.system_prompt: ChatPromptTemplate = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """
                    You are a knowledgeable assistant that answers questions about Bruno Abreu Calfa's publications.
                    If you do not know the answer to questions about certain topics, please respond that you are not 
                    aware of any publication by Bruno on those topics. Questions or comments that are unrelated to 
                    Bruno's research topics are irrelevant; if asked about irrelevant topics, please politely respond 
                    that they are off-topic and you will not answer them. You are given access to Bruno's publications 
                    as additional context to help you answer any questions related to his published work. Only use 
                    information from the given context to generate your answers about Bruno's work. You may use your 
                    general knowledge of technical terms to explain their meaning if asked by the user. Only cite 
                    sources available in the context. Be succinct unless explicitly asked to expand on your answer.
                    Context: {context}
                    User question: {question}
                    Answer: 
                    """
                )
            ]
        )
        self.chain: Runnable = None
        self.text_splitter: RecursiveCharacterTextSplitter = RecursiveCharacterTextSplitter(chunk_size=1024,
                                                                                            chunk_overlap=100)

        self._create_knowledge_base()

    def _create_knowledge_base(self):
        # Load publications and create chunks
        pubs = glob.glob("../pubs/*.pdf")
        all_chunks = []
        for pub in pubs:
            doc = PyPDFLoader(file_path=pub).load()
            chunks = self.text_splitter.split_documents(doc)
            chunks = filter_complex_metadata(chunks)
            all_chunks.extend(chunks)

        # Instantiate embedder and vector store
        embedder = OllamaEmbeddings(model=embedding_model_name, base_url=base_url)
        vecstore = Chroma.from_documents(all_chunks, embedding=embedder)
        # client_settings = chromadb.config.Settings()
        # client_settings.chroma_server_host = "chromadb"
        # client_settings.chroma_server_http_port = 8000
        # client_settings.chroma_server_grpc_port = 8000
        # vecstore = Chroma(
        #     collection_name="pubs",
        #     embedding_function=embedder,
        #     persist_directory="./chroma_db",
        #     client_settings=client_settings
        # )
        vecstore.add_documents(all_chunks)

        # Define chain utilities
        long_reorder = RunnableLambda(
            LongContextReorder().transform_documents)  # Reorders longer documents to center of output text

        def docs2str(docs, title="Document"):
            """Useful utility for making chunks into context string."""
            out_str = ""
            for doc in docs:
                doc_name = getattr(doc, "metadata", {}).get("Title", title)
                if doc_name:
                    out_str += f"[Quote from {doc_name}] "
                out_str += getattr(doc, "page_content", str(doc)) + "\n"
            return out_str

        # Create RAG chain
        context_runnable = {"context": vecstore.as_retriever() | long_reorder | docs2str}
        question_runnable = {"question": (lambda x: x)}

        self.chain = (
                question_runnable |
                context_runnable |
                self.system_prompt |
                self.llm |
                StrOutputParser()
        )

    def answer(self, question: str) -> Union[Output, Iterator[Output]]:
        if self.is_stream:
            return self.chain.stream(question)
        else:
            return self.chain.invoke(question)
