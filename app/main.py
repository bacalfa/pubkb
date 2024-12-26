import streamlit as st
# from langchain.agents import initialize_agent, AgentType
# from langchain.callbacks import StreamlitCallbackHandler
# from langchain.chat_models import ChatOpenAI
from kb import PubManager

# with st.sidebar:
#     openai_api_key = st.text_input("OpenAI API Key", key="langchain_search_api_key_openai", type="password")
#     "[Get an OpenAI API key](https://platform.openai.com/account/api-keys)"
#     "[View the source code](https://github.com/streamlit/llm-examples/blob/main/pages/2_Chat_with_search.py)"
#     "[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/streamlit/llm-examples?quickstart=1)"

# st.title("🔎 LangChain - Chat with search")
st.title("Bruno Abreu Calfa's Publication Knowledge Base")

# """
# In this example, we're using `StreamlitCallbackHandler` to display the thoughts and actions of an agent in an interactive Streamlit app.
# Try more LangChain 🤝 Streamlit Agent examples at [github.com/langchain-ai/streamlit-agent](https://github.com/langchain-ai/streamlit-agent).
# """

pm = PubManager()
is_stream = False

if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "assistant", "content": "Hi, I'm a chatbot who knows about Bruno's publications. Ask me about them!"}
    ]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if prompt := st.chat_input(placeholder="What research topics has Bruno published on?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)
    if is_stream:
        for chunk in pm.answer(prompt, is_stream=is_stream):
            st.session_state.messages.append({"role": "assistant", "content": chunk})
            st.write_stream(chunk)
    else:
        response = pm.answer(prompt, is_stream=is_stream)
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.write(response)

    # if not openai_api_key:
    #     st.info("Please add your OpenAI API key to continue.")
    #     st.stop()

    # llm = ChatOpenAI(model_name="gpt-3.5-turbo", openai_api_key=openai_api_key, streaming=True)
    # search = DuckDuckGoSearchRun(name="Search")
    # search_agent = initialize_agent([search], llm, agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    #                                 handle_parsing_errors=True)
    # with st.chat_message("assistant"):
    #     st_cb = StreamlitCallbackHandler(st.container(), expand_new_thoughts=False)
    #     response = search_agent.run(st.session_state.messages, callbacks=[st_cb])
    #     st.session_state.messages.append({"role": "assistant", "content": response})
    #     st.write(response)
