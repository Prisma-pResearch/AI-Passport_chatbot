import streamlit as st
from langchain_community.llms import OpenAI
import pyperclip

st.set_page_config(
    layout="wide",
    page_title="AI Passport Chatbot",
    page_icon="assistant"
)

openai_api_key = 'sk-proj-Eec74bdsB7LGLAOmzKJyT3BlbkFJvpgKKsyvxGi2AHJMVEdY'

# Define LLM model
def generate_response(input_text):
    llm = OpenAI(
        model_name='gpt-3.5-turbo-instruct',
        temperature=0.7,
        max_tokens=100,
        openai_api_key=openai_api_key
    )
    return llm(input_text)

# Initialize session state for messages
if "messages" not in st.session_state:
    st.session_state.messages = []

# CSS to ensure buttons are of the same size, text is centered, and spacing is equal
st.markdown("""
<style>
    .stSubheader {
        margin-bottom: -30px;
    }
    .stMarkdown {
        margin-bottom: -20px;
    }
    .stTextArea {
        margin-top: -10px;
    }
    .reportview-container .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    /* Styling for buttons to ensure uniformity and spacing */
    div[data-testid="stColumns"] > div {
        padding-right: 10px; /* Right padding on each column except the last one */
    }
    div[data-testid="stColumns"] > div:last-child {
        padding-right: 0px; /* No padding on the right for the last column */
    }
    div[data-testid="stColumns"] > div > div.stButton > button {
        height: 50px; /* Consistent height */
        width: 100%; /* Full width */
        line-height: 50px; /* Center text vertically */
        text-align: center; /* Center text horizontally */
        font-size: 16px; /* Consistent font size */
        margin-top: 5px; /* Top margin for visual spacing */
        border-radius: 5px; /* Rounded corners */
        box-shadow: 0 4px 6px rgba(0,0,0,0.1); /* Subtle shadow for 3D effect */
    }
</style>
""", unsafe_allow_html=True)

st.subheader("MedChat LLM")

# Displaying example prompts
example_prompts = [
    "What are common treatments for Type-2 Diabetes?",
    "Summarize the key findings from a recent medical research.",
    "Create a detailed clinical case study for severe heart failure."
]

st.markdown("***Example Prompts***")
prompt_col = st.columns([1, 1, 1])  # Equal distribution of space among columns
for i, example_prompt in enumerate(example_prompts):
    with prompt_col[i]:
        button_pressed = st.button(example_prompt, key=f'prompt_{i}')
        if button_pressed:
            response = generate_response(example_prompt)
            st.session_state.messages.append({"role": "user", "content": example_prompt})
            st.session_state.messages.append({"role": "assistant", "content": response})

# Display chat history
st.markdown("***Chat History***")
for i, message in enumerate(reversed(st.session_state.messages)):
    if message["role"] == "user":
        col1, col2 = st.columns([4, 1])
        col1.markdown(f"<span style='color: blue;'>**You:** {message['content']}</span>", unsafe_allow_html=True)
    elif message["role"] == "assistant":
        col1, col2 = st.columns([4, 1])
        col1.markdown(f"<span style='color: green;'>**Assistant:** {message['content']}</span>", unsafe_allow_html=True)
        if col2.button("📋", key=f"copy_assistant_{i}"):
            pyperclip.copy(message['content'])
            st.success("Copied to clipboard!")
# Export conversation button
if st.session_state.messages:
    chat_history = "\n".join([f"{msg['role'].capitalize()}: {msg['content']}" for msg in st.session_state.messages])
    st.download_button(
        label="Export Conversation",
        data=chat_history,
        file_name='chat_history.txt',
        mime='text/plain'
    )
# User input and response form
with st.form(key='response_form'):
    user_input = st.text_area('Enter your question here:', 'How can I help you today?', label_visibility='collapsed')
    submit_button = st.form_submit_button("Respond")

    if submit_button and user_input:
        response = generate_response(user_input)
        st.session_state.messages.append({"role": "user", "content": user_input})
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.experimental_rerun()


