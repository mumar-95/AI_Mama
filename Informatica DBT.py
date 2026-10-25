
import os
import json
import re
from pathlib import Path
from urllib.parse import quote

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

# 1. Load the API key from .env
load_dotenv()

api_key = os.getenv("GenAI_key")

if not api_key:
    st.error("OPENAI_API_KEY is missing. Check your .env file.")
    st.stop()

client = OpenAI(api_key=api_key)

# 2. Select a model
MODEL = "gpt-6-luna"

# 3. File to save chat history
HISTORY_FILE = Path("chat_history.json")

# 4. Instructions for the ETL assistant
SYSTEM_PROMPT = """
You are an expert in Informatica Powercenter.
1. Ask the user for XML file in front end UI
2. Analyse all the logics in XML file
3. Convert the XML file logic to DBT model and give the Ouput as here is your DBT Model"
"""

# 5. Load saved conversations from JSON
def load_history():
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as file:
                history = json.load(file)

            if isinstance(history, list):
                return [
                    message for message in history
                    if isinstance(message, dict)
                    and message.get("role") in ("user", "assistant")
                    and isinstance(message.get("content"), str)
                ]

        except (json.JSONDecodeError, OSError):
            return []

    return []


# 6. Save conversations to JSON
def save_history(messages):
    with open(HISTORY_FILE, "w", encoding="utf-8") as file:
        json.dump(messages, file, indent=4, ensure_ascii=False)


# 7. Configure the Streamlit page
st.set_page_config(
    page_title="Informatica to DBT Model Converter",
    page_icon="🛠️"
)

st.title("🛠️ Informatica to DBT Model Converter")
st.caption("Your friendly assistant to migrate Informatica to DBT Model")

# 8. Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = load_history()

# 9. Clear chat history button in the frontend
with st.sidebar:
    st.subheader("Chat History")

    if st.button("🗑️ Clear Chat History", use_container_width=True):
        st.session_state.messages = []
        save_history([])
        st.rerun()

# 10. Display previous messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# 11. Accept a new question
user_input = st.chat_input("Ask me anything about ETL migration to DBT Model...")

if user_input:

    # Display the user's message
    with st.chat_message("user"):
        st.write(user_input)

    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })

    # 12. Send recent messages to reduce token usage
    recent_messages = [
        {
            "role": message["role"],
            "content": message["content"]
        }
        for message in st.session_state.messages[-10:]
        if message.get("role") in ("user", "assistant")
        and isinstance(message.get("content"), str)
    ]

    try:
        with st.spinner("Preparing your answer..."):

            response = client.responses.create(
                model=MODEL,
                instructions=SYSTEM_PROMPT,
                input=recent_messages
            )

            answer = response.output_text

    except Exception as error:
        answer = (
            "Sorry, I could not get an answer right now. "
            "Please check your API configuration and try again."
        )
        print(f"OpenAI API error: {error}")

    # 13. Display the assistant's answer
    with st.chat_message("assistant"):
        st.write(answer)

    # 14. Save the conversation
    assistant_message = {
        "role": "assistant",
        "content": answer
    }

    st.session_state.messages.append(assistant_message)

    save_history(st.session_state.messages)