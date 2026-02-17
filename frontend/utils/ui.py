
import streamlit as st
import os

def load_css():
    """
    Loads the global CSS file (frontend/assets/style.css) and injects it into the Streamlit app.
    Uses absolute paths to ensure it works from any page or execution context.
    """
    # Get the absolute path to the project root (assuming this file is in frontend/utils/)
    # frontend/utils/ui.py -> frontend/utils -> frontend -> root
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
    
    css_path = os.path.join(project_root, "frontend", "assets", "style.css")
    
    try:
        # Inject Fonts explicitly to ensure loading
        st.markdown(
            """
            <link rel="preconnect" href="https://fonts.googleapis.com">
            <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
            <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
            """,
            unsafe_allow_html=True
        )

        try:
            # Robust reading with errors='replace' to prevent crashes
            with open(css_path, "r", encoding="utf-8", errors="replace") as f:
                st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
        except Exception:
            # Fallback to ansi/latin-1 if needed, though replace should handle it
            try:
                with open(css_path, "r", encoding="latin-1", errors="replace") as f:
                     st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
            except:
                pass

    except FileNotFoundError:
        # Fallback for different directory structures or docker
        try:
             # Try relative from where python was run
            with open("frontend/assets/style.css", "r", encoding="utf-8", errors="replace") as f:
                st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Erro ao carregar tema visual (style.css): {e}")

def setup_page(title="IAudit", icon=None, layout="wide"):
    """
    Configures the page settings and loads global CSS.
    Should be called at the start of every Streamlit script.
    """
    try:
        st.set_page_config(
            page_title=title,
            page_icon=icon,
            layout=layout,
            initial_sidebar_state="expanded"
        )
    except:
        # set_page_config can only be called once. 
        # If it was already called (e.g. by another import), ignore the error but still load CSS.
        pass
        
    # Initialize session state for robustness
    if 'search_history' not in st.session_state:
        st.session_state['search_history'] = []
    if 'mock_companies' not in st.session_state:
        # Import lazily to avoid circular dependencies
        from components.mock_data import get_mock_companies
        st.session_state['mock_companies'] = get_mock_companies(150)
    if 'detail_empresa_id' not in st.session_state:
        st.session_state['detail_empresa_id'] = None
        
    load_css()
