import os
import streamlit as st
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from groq import Groq
import re

# Load Groq API key
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
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

def extract_editable_content(soup):
    """Extract editable text content from HTML while preserving structure"""
    editable_elements = []
    
    # Find all text-containing elements (excluding script, style, meta, etc.)
    for element in soup.find_all(text=True):
        parent = element.parent
        if (parent.name not in ['script', 'style', 'meta', 'title', 'head'] and 
            element.strip() and 
            parent.name not in ['html', 'body']):
            
            # Get a more descriptive label
            label = get_element_label(parent, element.strip())
            
            editable_elements.append({
                'element': element,
                'text': element.strip(),
                'parent': parent,
                'parent_tag': parent.name,
                'label': label
            })
    
    return editable_elements

def get_element_label(parent, text):
    """Generate a descriptive label for the element"""
    # Check for common patterns to create meaningful labels
    parent_classes = parent.get('class', [])
    parent_id = parent.get('id', '')
    
    # Common resume section identifiers
    if any('name' in str(cls).lower() for cls in parent_classes) or 'name' in parent_id.lower():
        return f"👤 Name: {text[:30]}..."
    elif any('title' in str(cls).lower() for cls in parent_classes) or 'title' in parent_id.lower():
        return f"💼 Job Title: {text[:30]}..."
    elif any('email' in str(cls).lower() for cls in parent_classes) or 'email' in parent_id.lower():
        return f"📧 Email: {text[:30]}..."
    elif any('phone' in str(cls).lower() for cls in parent_classes) or 'phone' in parent_id.lower():
        return f"📱 Phone: {text[:30]}..."
    elif any('summary' in str(cls).lower() for cls in parent_classes) or 'summary' in parent_id.lower():
        return f"📝 Summary: {text[:30]}..."
    elif any('experience' in str(cls).lower() for cls in parent_classes) or 'experience' in parent_id.lower():
        return f"💼 Experience: {text[:30]}..."
    elif any('education' in str(cls).lower() for cls in parent_classes) or 'education' in parent_id.lower():
        return f"🎓 Education: {text[:30]}..."
    elif any('skill' in str(cls).lower() for cls in parent_classes) or 'skill' in parent_id.lower():
        return f"⚡ Skill: {text[:30]}..."
    elif parent.name == 'h1':
        return f"📋 Main Heading: {text[:30]}..."
    elif parent.name == 'h2':
        return f"📄 Section: {text[:30]}..."
    elif parent.name == 'h3':
        return f"📝 Subsection: {text[:30]}..."
    elif parent.name == 'p':
        return f"📰 Paragraph: {text[:30]}..."
    elif parent.name in ['span', 'div']:
        return f"📄 Text: {text[:30]}..."
    else:
        return f"{parent.name.upper()}: {text[:30]}..."

def update_html_content(soup, updated_texts, editable_elements):
    """Update HTML content with new text while preserving formatting"""
    for i, new_text in enumerate(updated_texts):
        if i < len(editable_elements):
            # Replace the text content
            editable_elements[i]['element'].replace_with(new_text)
    
    return soup

def categorize_elements(editable_elements):
    """Categorize elements for better organization"""
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
        
        if any(keyword in label for keyword in ['name', 'email', 'phone', 'location', 'contact']):
            categories['Personal Info'].append((i, element_info))
        elif any(keyword in label for keyword in ['summary', 'objective', 'about']):
            categories['Professional Summary'].append((i, element_info))
        elif any(keyword in label for keyword in ['experience', 'work', 'job', 'position']):
            categories['Experience'].append((i, element_info))
        elif any(keyword in label for keyword in ['education', 'degree', 'university', 'school']):
            categories['Education'].append((i, element_info))
        elif any(keyword in label for keyword in ['skill', 'technology', 'tool']):
            categories['Skills'].append((i, element_info))
        else:
            categories['Other'].append((i, element_info))
    
    return categories

if selected_file:
    html_path = os.path.join(UPLOAD_DIR, selected_file)
    
    # Read HTML file
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Parse HTML
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Session state for edit mode
    if "edit_mode" not in st.session_state:
        st.session_state.edit_mode = False
    
    if not st.session_state.edit_mode:
        st.subheader("👀 Preview Original Resume")
        
        # Display HTML preview
        st.components.v1.html(html_content, height=800, scrolling=True)
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("✏️ Edit Resume", type="primary"):
                st.session_state.edit_mode = True
                st.rerun()
        
        with col2:
            # Download original file
            with open(html_path, 'rb') as f:
                st.download_button(
                    "📥 Download Original",
                    f,
                    file_name=selected_file,
                    mime="text/html"
                )
    
    else:
        st.subheader("📝 Edit Resume Content")
        
        # Extract editable content
        editable_elements = extract_editable_content(soup)
        
        # Initialize session state for form data
        if "form_data" not in st.session_state:
            st.session_state.form_data = {i: elem['text'] for i, elem in enumerate(editable_elements)}
        
        # Create main layout
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Categorize elements for better organization
            categories = categorize_elements(editable_elements)
            
            # Create tabs for different sections
            tab_names = [name for name, items in categories.items() if items]
            tabs = st.tabs(tab_names)
            
            updated_texts = [None] * len(editable_elements)
            
            for tab_idx, tab_name in enumerate(tab_names):
                with tabs[tab_idx]:
                    st.markdown(f"### {tab_name}")
                    
                    for i, element_info in categories[tab_name]:
                        text = element_info['text']
                        label = element_info['label']
                        
                        # Different input types based on content length
                        if len(text) > 100:
                            new_text = st.text_area(
                                label,
                                value=st.session_state.form_data.get(i, text),
                                key=f"element_{i}",
                                height=100
                            )
                        else:
                            new_text = st.text_input(
                                label,
                                value=st.session_state.form_data.get(i, text),
                                key=f"element_{i}"
                            )
                        
                        # Update form data
                        st.session_state.form_data[i] = new_text
                        updated_texts[i] = new_text
            
            # Fill in any remaining elements not categorized
            for i in range(len(editable_elements)):
                if updated_texts[i] is None:
                    updated_texts[i] = st.session_state.form_data.get(i, editable_elements[i]['text'])
        
        with col2:
            # --- AI Chat Box ---
            st.markdown("**💬 AI Assistant**")
            
            
            
            # Custom AI query
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
            
            # Display AI response
            if "ai_response" in st.session_state:
                st.markdown("**🤖 AI Advice:**")
                st.info(st.session_state.ai_response)
        
        # --- Action buttons ---
        st.markdown("---")
        action_col1, action_col2, action_col3, action_col4 = st.columns([1, 1, 1, 1])
        
        with action_col1:
            if st.button("👀 Preview Changes", use_container_width=True):
                # Show preview of updated content
                updated_soup = update_html_content(soup, updated_texts, editable_elements)
                st.subheader("📋 Preview of Updated Resume:")
                st.components.v1.html(str(updated_soup), height=600, scrolling=True)
        
        with action_col2:
            output_name = st.text_input("Filename:", value=f"edited_{selected_file}")
        
        with action_col3:
            if st.button("💾 Save Resume", type="primary", use_container_width=True):
                if output_name:
                    # Update HTML content
                    updated_soup = update_html_content(soup, updated_texts, editable_elements)
                    
                    # Save updated HTML
                    save_path = os.path.join(DOWNLOAD_DIR, output_name)
                    with open(save_path, 'w', encoding='utf-8') as f:
                        f.write(str(updated_soup))
                    
                    st.success(f"✅ Resume saved successfully!")
                    
                    # Auto-download
                    with open(save_path, 'rb') as f:
                        st.download_button(
                            "📥 Download Updated Resume",
                            f,
                            file_name=output_name,
                            mime="text/html",
                            use_container_width=True
                        )
                else:
                    st.error("Please enter a filename.")
        
        with action_col4:
            if st.button("🔙 Back to Preview", use_container_width=True):
                st.session_state.edit_mode = False
                if "form_data" in st.session_state:
                    del st.session_state.form_data
                if "ai_response" in st.session_state:
                    del st.session_state.ai_response
                st.rerun()

# --- File Upload Section ---
st.sidebar.markdown("---")
st.sidebar.subheader("📁 Upload New Resume")
uploaded_file = st.sidebar.file_uploader("Choose an HTML file", type=['html'])

if uploaded_file is not None:
    # Save uploaded file
    file_path = os.path.join(UPLOAD_DIR, uploaded_file.name)
    with open(file_path, 'wb') as f:
        f.write(uploaded_file.getbuffer())
    st.sidebar.success(f"✅ Uploaded: {uploaded_file.name}")
    st.sidebar.info("Please refresh the page to see the new file.")

# --- Instructions ---
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

# --- Tips ---
st.sidebar.markdown("---")
st.sidebar.subheader("💡 Pro Tips")
st.sidebar.markdown("""
- **Organize by sections**: Use tabs to edit different resume sections
- **Use AI help**: Get suggestions for better content
- **Preview often**: Check how changes look before saving
- **Keep it concise**: Use action verbs and quantify achievements
- **Tailor content**: Customize for each job application
""")



