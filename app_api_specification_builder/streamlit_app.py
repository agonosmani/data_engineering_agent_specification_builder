# streamlit_app.py
import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from api_agent import app
import json

st.set_page_config(page_title="Ingestion Config Builder", page_icon="📊")

# ---------------- Session State ----------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "document_content" not in st.session_state:
    st.session_state.document_content = {}

if "chat_open" not in st.session_state:
    st.session_state.chat_open = False


def reset_chat():
    st.session_state.messages = []
    st.session_state.document_content = {}
    st.session_state.chat_open = False


# ---------------- UI ----------------
st.title("Ingestion Config Builder")


if not st.session_state.chat_open:
    st.markdown(
    """
    This tool helps you define a **governed dataset access specification**.

    You can describe:
    - Public dataset name
    - Columns to expose
    - Optional row-level filters
    - Allowed users

    The agent will convert this into a structured spec.
    """
    )

    if st.button("➕ Create dataset specification"):
        st.session_state.chat_open = True
        st.rerun()
        
else:
    # # ---- Chat history ----
    # Render new messages
    for msg in st.session_state.messages:
        if isinstance(msg, HumanMessage) and msg.content:
            st.chat_message("user").write(msg.content)
        if isinstance(msg, AIMessage) and msg.content.strip():
            st.chat_message("assistant").write(f"🤖 {msg.content}")


     # ---- User input ----
    if prompt := st.chat_input("Describe the dataset spec..."):
        st.session_state.messages.append(HumanMessage(content=prompt))
        st.chat_message("user").write(prompt)

        # Run graph until terminal
        state = {
            "messages": st.session_state.messages,
            "document_content": st.session_state.document_content,
        }

        result = app.invoke(state)

        # Update state
        st.session_state.messages = result.get("messages", [])
        st.session_state.document_content = result.get(
            "document_content", {}
        )

        latest_ai_message = next(
            (msg for msg in reversed(st.session_state.messages) 
             if isinstance(msg, AIMessage) and msg.content), 
            None
        )

        if latest_ai_message:
            st.chat_message("assistant").write(f"🤖 {latest_ai_message.content}")
            
        # ---- Terminal detection ----
        if any(
            isinstance(m, ToolMessage)
            and m.name == "save"
            and m.status != "error"
            for m in st.session_state.messages
        ):
            st.success("Specification completed.")
            st.json(st.session_state.document_content)

            # Convert to JSON string
            json_str = json.dumps(
                st.session_state.document_content,
                indent=2
            )
            st.download_button(
                label="Download JSON",
                data=json_str,
                file_name=f"{st.session_state.document_content['dataset']}_document.json",
                mime="application/json",
            )
            reset_chat()

        else:
            # st.info("Specification updated. Let me know if there's feedback or if you want to save.")
            st.info("Specification updated.")
            st.json(st.session_state.document_content)
