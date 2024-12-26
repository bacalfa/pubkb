from langchain_ollama import ChatOllama
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable, RunnablePassthrough
from langchain_core.runnables.base import Output, Iterator, Union


class PubManager:
    def __init__(self):
        self.llm: ChatOllama = ChatOllama(model="phi3:small")
        self.system_prompt: ChatPromptTemplate = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """
                    You are a knowledgeable assistant that answers questions about Bruno Abreu Calfa's publications.
                    If you do not know the answer to questions about certain topics, please respond that you are not 
                    aware of any publication by Bruno on those topics. You are given access to Bruno's publications as 
                    additional context to help you answer any questions related to his published work.
                    Context: {context}
                    Question: {question}
                    Answer: 
                    """
                )
            ]
        )
        self.chain: Runnable = None

        self._create_knowledge_base()

    def _create_knowledge_base(self):
        # TODO: Ingest all PDFs and construct vectorstore
        context_runnable = {"context": None}
        question_runnable = {"question": RunnablePassthrough()}

        self.chain = context_runnable | question_runnable | self.system_prompt | self.llm | StrOutputParser()

    def answer(self, question: str, is_stream: bool = True) -> Union[Output, Iterator[Output]]:
        question_dict = {"question": question}
        if is_stream:
            return self.chain.stream(question_dict)
        else:
            return self.chain.invoke(question_dict)
