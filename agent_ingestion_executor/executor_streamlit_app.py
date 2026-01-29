# streamlit_app.py
import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from database_executor import run_database_agent
import json
import pandas as pd
import ast
import sqlite3



st.set_page_config(page_title="Table Ingestion Agent", page_icon="📊")


# ---------------- Session State ----------------
if "username" not in st.session_state:
    st.session_state.username = None

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


if not st.session_state.username:
    if session_username := st.text_input("Enter your username:"): 
        st.session_state.username = session_username
        st.rerun()

    
if st.session_state.username: 

    # ---------------- UI ----------------
    st.title("Table Ingestion Agent")

    if not st.session_state.chat_open:

        st.write(f"👋 Hello, **{st.session_state.username}**!")


        st.markdown(
        """
        This tool lets you **ingest a dataset and query it interactively**.  

        You can:
        - Specify a dataset to fetch
        - Pick columns or apply filters
        - Explore trends, summaries, or specific queries
        """
        )

        if st.button("➕ Create dataset specification"):
            st.session_state.chat_open = True
            st.rerun()

    else:

        if st.session_state.messages:
            for i, message in enumerate(st.session_state.messages):
                if isinstance(message, HumanMessage):
                    st.chat_message("user").write(message.content)
                elif isinstance(message, AIMessage):
                    st.chat_message("assistant").write(f"🤖 {message.content}")
                elif isinstance(message, pd.DataFrame):  # Check for DataFrame
                    st.dataframe(message)  # Print the DataFrame if it's pandas

        # ---- User input ----
        if prompt := st.chat_input("Type your ingestion command or query..."):
            st.chat_message("user").write(prompt)

            # Store user prompt in session state
            st.session_state.messages.append(HumanMessage(content=prompt))

            response = run_database_agent(prompt, st.session_state.username)

            messages = response.get("messages", [])
            
            # Get final AI message
            final_ai_message = next(
                (msg for msg in reversed(messages) if isinstance(msg, AIMessage) and msg.content),
                None
            )

            if final_ai_message:
                st.chat_message("assistant").write(f"🤖 {final_ai_message.content}")
                # Store AI message in session state
                st.session_state.messages.append(final_ai_message)

            # Optional: display tool outputs (tables)
            tool_outputs = [
                msg.content
                for msg in messages
                if isinstance(msg, ToolMessage) and msg.content
            ]

            for output in tool_outputs:
                # Directly use the output as a pandas DataFrame if it's valid
                try:
                    if isinstance(output, str):
                        # Trim any junk before/after the list
                        start = output.find('[')
                        end = output.rfind(']') + 1
                        trimmed = output[start:end]

                        # Convert to Python object
                        data = json.loads(trimmed)

                        # Convert to DataFrame
                        df = pd.DataFrame(data)

                        st.dataframe(df)
                        # Append DataFrame to messages
                        st.session_state.messages.append(df)

                        # Allow download of final AI response as JSON
                        df.to_sql('downloaded_data', sqlite3.connect('downloaded_data.db'), if_exists='replace', index=False)
                        with open('downloaded_data.db', 'rb') as db_file:
                            st.download_button(
                                label="Download DataFrame as DB file",
                                data=db_file,
                                file_name="downloaded_data.db",
                                mime="application/octet-stream",
                            )
                except Exception as e:
                    st.text(f"Error: Unable to display DataFrame. {str(e)}")

        
