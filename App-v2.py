import streamlit as st
# openai version=1.1.1 is required
import openai
from openai import OpenAI
import io
import os
import base64
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from pdfrw import PdfReader, PdfWriter, IndirectPdfDict, PdfDict
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics

st.set_page_config(
    layout="wide",
    page_title="AI Passport Chatbot",
    page_icon="assistant"
)

os.environ['OPENAI_API_KEY'] = st.secrets['OPENAI_API_KEY']
client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])

# Function to encode the image
def encode_image(image_file):
    return base64.b64encode(image_file.read()).decode('utf-8')

# Define LLM model
def generate_response(prompt, image=None, pdf=None):
    messages = st.session_state.messages
    messages.append({"role": "system", "content": "You are a helpful assistant with expertise in medicine."})
    if image:
        base64_image = encode_image(uploaded_file)
        messages.append(
            {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
            ]
        })
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=4096,
            temperature=0.3
        )
        return response.choices[0].message.content.strip()
    elif pdf:
        reader = PdfReader(uploaded_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        
        messages.append(
            {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "text", "text": text}
            ]
        })
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=4096,
            temperature=0.3
        )
        return response.choices[0].message.content.strip()
    else:    
        messages.append(
            {"role": "user", "content": prompt}
            )
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=4096,
            temperature=0.3
        )
        return response.choices[0].message.content.strip()

# Initialize session state for messages
if "messages" not in st.session_state:
    st.session_state.messages = []

st.subheader("MedChat LLM")

with st.sidebar:
    st.subheader("Attach your files.")
    # Streamlit file uploader to upload an image
    uploaded_file = st.file_uploader("Upload an Image", type=["pdf","jpg", "jpeg", "png"])


# User input and response form
with st.form(key='response_form'):
    user_input = st.text_area('Enter your question here:', 'How can I help you today?', label_visibility='collapsed')
    button_container = st.container()

    with button_container:
        col1, col2 = st.columns([0.09, 1])  # Adjust column widths as needed

        with col1:
            submit_button = st.form_submit_button("Submit")

        # with col2:
        #     reset_button = st.form_submit_button("Clear chat history")

    if submit_button and user_input:
        if uploaded_file is not None:
            file_type = uploaded_file.type
            if file_type == "application/pdf":
                with st.spinner("Generating response..."):
                    response = generate_response(user_input, pdf=uploaded_file)
            elif file_type in ["image/jpeg", "image/png"]:
                with st.spinner("Generating response..."):
                    response = generate_response(user_input, image=uploaded_file)
            else:
                with st.spinner("Generating response..."):
                    response = generate_response(user_input)
        else:
            with st.spinner("Generating response..."):
                response = generate_response(user_input)
        
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun()
    
    # if reset_button:
    #     st.session_state.messages = []

# Display chat history
st.markdown("***Chat History***")
for i, message in enumerate(reversed(st.session_state.messages)):
    col1, col2 = st.columns([0.7, 0.3])  # Adjust the column width as needed

    if message["role"] == "user":
        with col2:
            st.markdown(f"<span style='color: blue;'>**You:** {message['content']}</span>", unsafe_allow_html=True)
    elif message["role"] == "assistant":
        with col1:
            st.markdown(f"<span style='color: green;'>**Assistant :robot_face::** {message['content']}</span>", unsafe_allow_html=True)

def create_pdf(chat_history):
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    pdf.setFont("Helvetica", 10)

    pdfmetrics.registerFont(TTFont('Arial', 'Arial.ttf'))

    y = 750  # Initial y position
    margin = 50
    line_height = 12
    max_line_width = letter[0] - 2 * margin  # Calculate the maximum line width

    def split_line(line, max_width):
        words = line.split()
        lines = []
        current_line = ""
        for word in words:
            test_line = f"{current_line} {word}".strip()
            if pdf.stringWidth(test_line, "Helvetica", 10) <= max_width:  # Adjusted font size
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word
        lines.append(current_line)
        return lines

    for line in chat_history.splitlines():
        wrapped_lines = split_line(line, max_line_width)
        for wrapped_line in wrapped_lines:
            if y <= margin:
                pdf.showPage()  # Start a new page if needed
                y = 750  # Reset y position on new page
                pdf.setFont("Helvetica", 10)
            
            if wrapped_line.startswith("User:"):
                pdf.setFillColor(colors.blue)
            elif wrapped_line.startswith("Assistant:"):
                pdf.setFillColor(colors.green)
            else:
                pdf.setFillColor(colors.black)
            
            pdf.drawString(margin, y, wrapped_line)
            y -= line_height

    pdf.setFillColor(colors.black)
    if y - 250 < margin:  # Adjusted for larger text box height
        pdf.showPage()
        y = 750
    pdf.drawString(margin, y - 20, "Please comment your answers to Activity below:")

    # Increase the height of the text box
    text_box_height = 250  # Increased height to accommodate more text

    pdf.rect(margin, y - (text_box_height + 40), 400, text_box_height, fill=1)

    # Add a multi-line text box with large space and remove character limit
    pdf.acroForm.textfield(
        name='comment',
        tooltip='Enter your comments',
        x=margin, y=y - (text_box_height + 40),
        width=500, height=text_box_height,
        borderStyle='inset',
        borderColor=colors.black,
        fillColor=colors.white,
        textColor=colors.black,
        forceBorder=True,
        fieldFlags='multiline',
        maxlen=None
    )

    pdf.showPage()
    pdf.save()

    buffer.seek(0)
    return buffer.getvalue()

if st.session_state.messages:
    chat_history = "\n".join([f"{msg['role'].capitalize()}: {msg['content']}" for msg in st.session_state.messages])
    pdf_content = create_pdf(chat_history)
    st.download_button(
        label="Export Conversation as PDF",
        data=pdf_content,
        file_name='chat_history.pdf',
        mime='application/pdf'
    )
