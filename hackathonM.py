import streamlit as st
import google.generativeai as genai
import smtplib
from email.message import EmailMessage

# Configure the Gemini API
genai.configure(api_key=st.secrets["api"]["key"])

# Email server settings
SMTP_SERVER = st.secrets["email"]["smtp_server"]
SMTP_PORT = st.secrets["email"]["smtp_port"]

st.set_page_config(page_title="AI Email Generator", page_icon="📧", layout="wide")

# Sidebar with sender details
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/4/4e/Mail_%28iOS%29.svg", use_container_width=True)
st.sidebar.title("AI Email Generator")
st.sidebar.markdown("Generate and send professional emails instantly!")

SENDER_EMAIL = st.sidebar.text_input("📧 Sender Email", placeholder="Enter sender email")
SENDER_PASSWORD = st.sidebar.text_input("🔑 App Password", placeholder="Enter app password", type="password")
remember = st.sidebar.checkbox("Remember details")

# Custom Styling
st.markdown("""
    <style>
        body { background: linear-gradient(to right, #f8c291, #6a89cc); font-family: Arial, sans-serif; }
        .main { background: #ffffff; padding: 30px; border-radius: 12px; 
                box-shadow: 0px 4px 15px rgba(0, 0, 0, 0.2); }
        .email-preview { background: #fdfdfd; padding: 20px; border-radius: 10px; 
                         box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.15); margin-top: 20px; color: #333; }
        .stButton>button { background: linear-gradient(to right, #007BFF, #00C6FF); color: white; border-radius: 8px; border: none; padding: 10px; }
        .stButton>button:hover { background: linear-gradient(to right, #0056b3, #0091ea); }
    </style>
""", unsafe_allow_html=True)

st.title("📧 AI-Powered Email Generator")

# Input Fields
recipient_names = st.text_area("👤 Recipient Names", placeholder="Enter recipient names (one per line)")
recipient_emails = st.text_area("📧 Recipient Emails", placeholder="Enter email addresses (one per line)")
subject = st.text_input("📝 Subject", placeholder="Enter email subject")
content_length = st.selectbox("📏 Email Length", ["Short (300-400 words)", "Medium (400-700 words)", "Long (700-1500 words)", "Very Long (1500+ words)"])
file_attachment = st.file_uploader("📎 Attach a File (Optional)", type=["pdf", "docx", "jpg", "png", "txt"])

# Buttons
generate = st.button("🚀 Generate Email")
reset = st.button("🔄 Reset")

if reset:
    st.session_state.clear()
    st.rerun()

if generate:
    recipient_names_list = [name.strip() for name in recipient_names.split("\n") if name.strip()]
    recipient_emails_list = [email.strip() for email in recipient_emails.split("\n") if email.strip()]
    
    if not subject or not recipient_names or not recipient_emails:
        st.error("⚠ Please fill all required fields.")
    elif len(recipient_names_list) != len(recipient_emails_list):
        st.error("⚠ The number of names and emails must match.")
    else:
        email_body_list = []
        model = genai.GenerativeModel("gemini-pro")
        
        for name in recipient_names_list:
            prompt = f"Write a professional email with the subject: '{subject}'. Address the recipient as {name}. "
            if "Short" in content_length:
                prompt += "Keep the email concise within 300-400 words."
            elif "Medium" in content_length:
                prompt += "Ensure the email remains within 400-700 words."
            elif "Long" in content_length:
                prompt += "Provide detailed content within 700-1500 words."
            else:
                prompt += "Allow comprehensive explanation beyond 1500 words."
            
            response = model.generate_content(prompt)
            email_body = response.text if response else "⚠ Could not generate email. Try again."
            email_body_list.append(f"Dear {name},\n\n" + email_body)
        
        # Store email body in session state
        st.session_state["generated_email"] = email_body_list
        st.session_state["recipient_emails_list"] = recipient_emails_list

        # Display email preview
        for name, email, body in zip(recipient_names_list, recipient_emails_list, email_body_list):
            st.markdown(f"""
                <div class='email-preview'>
                    <h4>📩 Email Preview</h4>
                    <b>Recipient:</b> {name} ({email})<br>
                    <b>Subject:</b> {subject}<br>
                    <p>{body}</p>
                </div>
            """, unsafe_allow_html=True)
        st.success("✅ Emails Generated Successfully!")

# Show "Send Email" button only after generation
if "generated_email" in st.session_state:
    send_email = st.button("📤 Send Email")

    if send_email:
        def send_email_func(to_emails, subject, body_list, attachment):
            try:
                with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                    server.starttls()
                    server.login(SENDER_EMAIL, SENDER_PASSWORD)
                    for to_email, body in zip(to_emails, body_list):
                        msg = EmailMessage()
                        msg.set_content(body)
                        msg["Subject"] = subject
                        msg["From"] = SENDER_EMAIL
                        msg["To"] = to_email

                        if attachment is not None:
                            file_data = attachment.read()
                            file_name = attachment.name
                            msg.add_attachment(file_data, maintype='application', subtype='octet-stream', filename=file_name)
                        
                        server.send_message(msg)
                return True
            except Exception as e:
                st.error(f"❌ Failed to send email: {e}")
                return False

        if send_email_func(st.session_state["recipient_emails_list"], subject, st.session_state["generated_email"], file_attachment):
            st.success("✅ Emails Sent Successfully!")
        else:
            st.error("❌ Emails could not be sent.")
