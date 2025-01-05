import streamlit as st
from langchain_community.chat_message_histories import StreamlitChatMessageHistory
from langchain_core.messages import HumanMessage, AIMessage
from kb import PubManager


def main():
    st.title("Bruno Abreu Calfa's Publication Knowledge Base")

    if "messages" not in st.session_state:
        st.session_state["messages"] = [
            AIMessage("Hi, I'm a chatbot who knows about Bruno's publications. Ask me about them!")
        ]

    if "pm" not in st.session_state:
        is_stream = True
        # is_stream = False
        chat_history = StreamlitChatMessageHistory(key="messages")
        # chat_history = None
        pm = PubManager(is_stream=is_stream, chat_history=chat_history)
        # pm = PubManager(llm_name="llama3:8b", is_stream=is_stream, chat_history=chat_history)
        st.session_state["pm"] = pm

    for msg in st.session_state.messages:
        st.chat_message(msg.type).write(msg.content)

    if prompt := st.chat_input(placeholder="What research topics has Bruno published on?"):
        # st.session_state.messages.append(HumanMessage(prompt))
        st.chat_message("user").write(prompt)
        if st.session_state["pm"].is_stream:
            response = st.write_stream(st.session_state["pm"].answer(prompt))
        else:
            response = st.session_state["pm"].answer(prompt)
            # st.write(response)
        # st.session_state.messages.append(AIMessage(response))

        # formatted_history = []
        # for message in st.session_state.messages:
        #     if not isinstance(message, dict):
        #         message_dict = message_to_dict(message)
        #         # if message_dict["type"] == "human":
        #         #     message = {"role": "user", "content": message_dict["data"]["content"]}
        #         if message_dict["type"] == "human":
        #             continue
        #         if message_dict["type"] == "ai":
        #             message = {"role": "assistant", "content": message_dict["data"]["content"]}
        #     formatted_history.append(message)
        # st.session_state.messages = formatted_history


if __name__ == "__main__":
    main()
