from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import Runnable, RunnableLambda, RunnablePassthrough
from langchain_community.document_transformers import LongContextReorder
from langchain_core.runnables.base import Output, Iterator, Union
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores.utils import filter_complex_metadata
from langchain_redis import RedisConfig, RedisVectorStore
from langchain_core.runnables.history import RunnableWithMessageHistory, BaseChatMessageHistory
from langchain_community.chat_message_histories import StreamlitChatMessageHistory
from langchain_core.messages.base import BaseMessage
import os
import glob

llm_model_name = os.environ.get("LLM_MODEL", "llama3:8b")
embedding_model_name = os.environ.get("EMBEDDING_MODEL", "nomic-embed-text")
base_url = os.environ.get("BASE_URL", "http://ollama:11434")
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")


class PubManager:
    def __init__(self, llm_name: str = llm_model_name, is_stream: bool = False,
                 chat_history: StreamlitChatMessageHistory = None):
        self.is_stream: bool = is_stream
        self.llm: ChatOllama = ChatOllama(model=llm_name, base_url=base_url, temperature=0.2, top_p=0.4)
        system_prompt_messages = [
            (
                "system",
                """
                You are a knowledgeable assistant that answers questions about Bruno Abreu Calfa's publications.
                Bruno Abreu Calfa is also known by Bruno or Dr. Calfa. If you do not know the answer to questions about 
                certain topics, please respond that you are not aware of any publication by Bruno on those topics. 
                Questions or comments that are unrelated to Bruno's research topics are irrelevant; if asked about 
                irrelevant topics, please politely respond that they are off-topic and you will not answer them. You 
                are given access to Bruno's publications as additional context to help you answer any questions related 
                to his published work. Only use information from the given context to generate your answers about 
                Bruno's work. You may use your general knowledge of technical terms to explain their meaning if asked 
                by the user. Only cite sources available in the context. Be succinct unless explicitly asked to expand 
                on your answer.
                Context: {context}
                User question: {question}
                Answer: 
                """
            ),
        ]
        self.system_prompt: ChatPromptTemplate = ChatPromptTemplate.from_messages(system_prompt_messages)
        self.chat_history_prompt: ChatPromptTemplate = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """
                    Given a chat history and the latest user question which might reference context in the 
                    chat history, formulate a standalone question which can be understood without the chat history. 
                    Do NOT answer the question, just reformulate it if needed and otherwise return it as is.
                    """
                ),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{question}"),
            ]
        )

        self.chain: Runnable = None
        self.chain_with_history: Runnable = None
        self.chat_history: StreamlitChatMessageHistory = chat_history
        self.text_splitter: RecursiveCharacterTextSplitter = RecursiveCharacterTextSplitter(chunk_size=2048,
                                                                                            chunk_overlap=200)

        self._create_knowledge_base()

    def get_redis_history(self, session_id: str = "") -> BaseChatMessageHistory:
        return self.chat_history

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
        config = RedisConfig(
            redis_url=redis_url,
        )
        vecstore = RedisVectorStore(embedder, config=config)
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
        # context_runnable = {"context": vecstore.as_retriever() | long_reorder | docs2str}
        # question_runnable = {"question": (lambda x: x)}

        def get_question(question):
            if not question:
                return None
            elif isinstance(question, str):
                return question
            elif isinstance(question, dict) and 'question' in question:
                return question['question']
            elif isinstance(question, BaseMessage):
                return question.content
            else:
                raise Exception("string or dict with 'question' key expected as RAG chain input.")

        self.chain = (
            # question_runnable |
            # context_runnable |
                {
                    "context": RunnableLambda(get_question) | vecstore.as_retriever() | long_reorder | docs2str,
                    "question": RunnablePassthrough(),
                }
                |
                self.system_prompt |
                self.llm |
                StrOutputParser()
        )

        # Create a runnable with message history
        runnable_history = self.chat_history_prompt | self.llm | self.chain
        self.chain_with_history = RunnableWithMessageHistory(
            runnable_history, self.get_redis_history, input_messages_key="question",
            history_messages_key="chat_history"
        )

    def answer(self, question: str) -> Union[Output, Iterator[Output]]:
        if self.chat_history is not None:
            chain = self.chain_with_history
            question = {"question": question}
            kwargs = dict(config={"configurable": {"session_id": "foo"}})
        else:
            chain = self.chain
            kwargs = {}

        if self.is_stream:
            return chain.stream(question, **kwargs)
        else:
            return chain.invoke(question, **kwargs)
