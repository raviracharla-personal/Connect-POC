import streamlit as st
import requests
import json

# --- Page Configuration ---
st.set_page_config(
    page_title="Police Manual Q&A",
    page_icon="👮",
    layout="wide"
)

st.title("👮 Police Manual Q&A System")
st.caption("Ask a question about the procedures in the training manual.")

# --- API Endpoint ---
API_URL = "http://127.0.0.1:8000/ask"

# --- User Interface ---
question = st.text_input(
    "Enter your question:",
    placeholder="e.g., How do I create a new investigation report?"
)

if st.button("Get Answer"):
    if question:
        with st.spinner("Searching the manual and generating an answer..."):
            try:
                # Call the FastAPI backend
                response = requests.post(API_URL, json={"question": question})
                response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
                
                api_response = response.json()
                
                # Display the answer
                st.subheader("Answer:")
                st.write(api_response['answer'])

                # Display the sources used for the answer
                with st.expander("Show Sources Used"):
                    st.json(api_response['source_chunks'])

            except requests.exceptions.RequestException as e:
                st.error(f"Could not connect to the API. Make sure the backend is running. Error: {e}")
            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")
    else:
        st.warning("Please enter a question.")