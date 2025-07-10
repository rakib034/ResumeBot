import os
import streamlit as st
from dotenv import load_dotenv
from groq import Groq
from lxml import html
import re

# Load Groq API key
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
groq_client = Groq(api_key=GROQ_API_KEY)

# Folder paths
UPLOAD_DIR = "uploads"
DOWNLOAD_DIR = "download"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

st.set_page_config(page_title="HTML Resume Editor (Preserve Format)", layout="wide")
st.title("📄 HTML Resume Editor with AI (Formatting Preserved)")

# Select file
html_files = [f for f in os.listdir(UPLOAD_DIR) if f.endswith(".html")]
selected_file = st.sidebar.selectbox("Select a resume", html_files)

def extract_editable_content(tree):
    editable_elements = []
    for element in tree.iter():
        if element.tag in ['script', 'style', 'meta', 'title', 'head']:
            continue
        if element.text and element.text.strip():
            label = get_element_label(element, element.text.strip())
            editable_elements.append({
                'element': element,
                'text': element.text.strip(),
                'parent': element,
                'parent_tag': element.tag,
                'label': label
            })
    return editable_elements

def get_element_label(element, text):
    cls = element.get('class') or []
    if isinstance(cls, str): cls = cls.split()
    id_ = element.get('id', '')

    if any('name' in c.lower() for c in cls) or 'name' in id_.lower():
        return f"👤 Name: {text[:30]}..."
    elif any('title' in c.lower() for c in cls) or 'title' in id_.lower():
        return f"💼 Job Title: {text[:30]}..."
    elif any('email' in c.lower() for c in cls) or 'email' in id_.lower():
        return f"📧 Email: {text[:30]}..."
    elif any('phone' in c.lower() for c in cls) or 'phone' in id_.lower():
        return f"📱 Phone: {text[:30]}..."
    elif any('summary' in c.lower() for c in cls) or 'summary' in id_.lower():
        return f"📝 Summary: {text[:30]}..."
    elif any('experience' in c.lower() for c in cls) or 'experience' in id_.lower():
        return f"💼 Experience: {text[:30]}..."
    elif any('education' in c.lower() for c in cls) or 'education' in id_.lower():
        return f"🎓 Education: {text[:30]}..."
    elif any('skill' in c.lower() for c in cls) or 'skill' in id_.lower():
        return f"⚡ Skill: {text[:30]}..."
    elif element.tag == 'h1':
        return f"📋 Main Heading: {text[:30]}..."
    elif element.tag == 'h2':
        return f"📄 Section: {text[:30]}..."
    elif element.tag == 'h3':
        return f"📝 Subsection: {text[:30]}..."
    elif element.tag == 'p':
        return f"📰 Paragraph: {text[:30]}..."
    elif element.tag in ['span', 'div']:
        return f"📄 Text: {text[:30]}..."
    else:
        return f"{element.tag.upper()}: {text[:30]}..."

def update_html_content(tree, updated_texts, editable_elements):
    for i, new_text in enumerate(updated_texts):
        if i < len(editable_elements):
            editable_elements[i]['element'].text = new_text
    return tree

def categorize_elements(editable_elements):
    categories = {
        'Personal Info': [],
        'Professional Summary': [],
        'Experience': [],
        'Education': [],
        'Skills': [],
        'Other': []
    }

    for i, element_info in enumerate(editable_elements):
        label = element_info['label'].lower()
        if any(k in label for k in ['name', 'email', 'phone', 'location', 'contact']):
            categories['Personal Info'].append((i, element_info))
        elif any(k in label for k in ['summary', 'objective', 'about']):
            categories['Professional Summary'].append((i, element_info))
        elif any(k in label for k in ['experience', 'work', 'job', 'position']):
            categories['Experience'].append((i, element_info))
        elif any(k in label for k in ['education', 'degree', 'university', 'school']):
            categories['Education'].append((i, element_info))
        elif any(k in label for k in ['skill', 'technology', 'tool']):
            categories['Skills'].append((i, element_info))
        else:
            categories['Other'].append((i, element_info))
    return categories

if selected_file:
    html_path = os.path.join(UPLOAD_DIR, selected_file)
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    tree = html.fromstring(html_content)

    if "edit_mode" not in st.session_state:
        st.session_state.edit_mode = False

    if not st.session_state.edit_mode:
        st.subheader("👀 Preview Original Resume")
        st.components.v1.html(html_content, height=800, scrolling=True)

        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("✏️ Edit Resume", type="primary"):
                st.session_state.edit_mode = True
                st.rerun()
        with col2:
            with open(html_path, 'rb') as f:
                st.download_button(
                    "📥 Download Original",
                    f,
                    file_name=selected_file,
                    mime="text/html"
                )
    else:
        st.subheader("📝 Edit Resume Content")
        editable_elements = extract_editable_content(tree)

        if "form_data" not in st.session_state:
            st.session_state.form_data = {i: elem['text'] for i, elem in enumerate(editable_elements)}

        col1, col2 = st.columns([2, 1])
        with col1:
            categories = categorize_elements(editable_elements)
            tab_names = [name for name, items in categories.items() if items]
            tabs = st.tabs(tab_names)

            updated_texts = [None] * len(editable_elements)
            for tab_idx, tab_name in enumerate(tab_names):
                with tabs[tab_idx]:
                    st.markdown(f"### {tab_name}")
                    for i, element_info in categories[tab_name]:
                        text = element_info['text']
                        label = element_info['label']
                        if len(text) > 100:
                            new_text = st.text_area(label, value=st.session_state.form_data.get(i, text), key=f"element_{i}", height=100)
                        else:
                            new_text = st.text_input(label, value=st.session_state.form_data.get(i, text), key=f"element_{i}")
                        st.session_state.form_data[i] = new_text
                        updated_texts[i] = new_text

            for i in range(len(editable_elements)):
                if updated_texts[i] is None:
                    updated_texts[i] = st.session_state.form_data.get(i, editable_elements[i]['text'])

        with col2:
            st.markdown("**💬 AI Assistant**")
            chat_query = st.text_area("Ask AI for help:", height=100)

            if st.button("🤖 Get AI Advice"):
                if chat_query:
                    try:
                        response = groq_client.chat.completions.create(
                            model="llama3-70b-8192",
                            messages=[
                                {"role": "system", "content": "You are a professional resume writing assistant. Provide concise, actionable advice for resume improvement."},
                                {"role": "user", "content": chat_query}
                            ]
                        )
                        st.session_state.ai_response = response.choices[0].message.content
                    except Exception as e:
                        st.error(f"AI service error: {str(e)}")
                else:
                    st.warning("Please enter a question first.")

            if "ai_response" in st.session_state:
                st.markdown("**🤖 AI Advice:**")
                st.info(st.session_state.ai_response)

        st.markdown("---")
        action_col1, action_col2, action_col3, action_col4 = st.columns([1, 1, 1, 1])
        with action_col1:
            if st.button("👀 Preview Changes", use_container_width=True):
                updated_tree = update_html_content(tree, updated_texts, editable_elements)
                html_preview = html.tostring(updated_tree, encoding='unicode', pretty_print=True)
                st.subheader("📋 Preview of Updated Resume:")
                st.components.v1.html(html_preview, height=600, scrolling=True)

        with action_col2:
            output_name = st.text_input("Filename:", value=f"edited_{selected_file}")

        with action_col3:
            if st.button("💾 Save Resume", type="primary", use_container_width=True):
                if output_name:
                    updated_tree = update_html_content(tree, updated_texts, editable_elements)
                    save_path = os.path.join(DOWNLOAD_DIR, output_name)
                    with open(save_path, 'w', encoding='utf-8') as f:
                        f.write(html.tostring(updated_tree, encoding='unicode', pretty_print=True))
                    st.success(f"✅ Resume saved successfully!")
                    with open(save_path, 'rb') as f:
                        st.download_button("📥 Download Updated Resume", f, file_name=output_name, mime="text/html", use_container_width=True)
                else:
                    st.error("Please enter a filename.")

        with action_col4:
            if st.button("🔙 Back to Preview", use_container_width=True):
                st.session_state.edit_mode = False
                st.session_state.pop("form_data", None)
                st.session_state.pop("ai_response", None)
                st.rerun()

'''# --- File Upload Section ---
st.sidebar.markdown("---")
st.sidebar.subheader("📁 Upload New Resume")
uploaded_file = st.sidebar.file_uploader("Choose an HTML file", type=['html'])

if uploaded_file is not None:
    file_path = os.path.join(UPLOAD_DIR, uploaded_file.name)
    with open(file_path, 'wb') as f:
        f.write(uploaded_file.getbuffer())
    st.sidebar.success(f"✅ Uploaded: {uploaded_file.name}")
    st.sidebar.info("Please refresh the page to see the new file.")'''

# --- Sidebar Help ---
st.sidebar.markdown("---")
st.sidebar.subheader("📖 How to Use")
st.sidebar.markdown("""
1. **Select** your HTML resume from dropdown  
2. **Preview** the original formatting  
3. **Click "Edit Resume"** to start editing  
4. **Edit content** organized by sections  
5. **Use AI assistant** for writing help  
6. **Preview changes** before saving  
7. **Save and download** your updated resume  
""")
