import streamlit as st
from kb import PubManager


def main():
    st.title("Bruno Abreu Calfa's Publication Knowledge Base")

    if "pm" not in st.session_state:
        is_stream = True
        pm = PubManager(is_stream=is_stream)
        # pm = PubManager(llm_name="phi3:mini", is_stream=is_stream)
        st.session_state["pm"] = pm

    if "messages" not in st.session_state:
        st.session_state["messages"] = [
            {"role": "assistant",
             "content": "Hi, I'm a chatbot who knows about Bruno's publications. Ask me about them!"}
        ]

    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])

    if prompt := st.chat_input(placeholder="What research topics has Bruno published on?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.chat_message("user").write(prompt)
        if st.session_state["pm"].is_stream:
            response = st.write_stream(st.session_state["pm"].answer(prompt))
        else:
            response = st.session_state["pm"].answer(prompt)
            st.write(response)
        st.session_state.messages.append({"role": "assistant", "content": response})


if __name__ == "__main__":
    main()
