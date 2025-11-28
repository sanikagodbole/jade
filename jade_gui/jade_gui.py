"""
JADE - Asset Organization & Delivery Pipeline
A Streamlit app for managing USD assets in visual effects production.
Nature-themed interface with modular architecture.
"""

import streamlit as st
from pathlib import Path
from typing import List, Optional
from jade_api.create import create_new_asset, create_new_shot

# ======================== PAGE CONFIGURATION ========================
st.set_page_config(
    page_title="JADE",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# ======================== THEME & STYLING ========================
def apply_theme():
    """Apply nature-themed CSS with minimal whitespace"""
    st.markdown("""
    <style>
        /* Color palette - Forest & Nature theme */
        :root {
            --forest-dark: #1a3d2e;
            --forest-light: #2d5a3d;
            --sage-green: #339664;
            --leaf-green: #339664;
            --stone-gray: #8b8b7e;
            --cream: #f5f1e8;
        }
        
        /* Main layout */
        .main { background-color: #f9f8f5; }
        
        /* Reduce default Streamlit spacing */
        .stMarkdown { margin: 0; padding: 0; }
        .stButton { margin: 0.2rem 0; }
        .stSelectbox { margin: 0.2rem 0; }
        .stTextInput { margin: 0.2rem 0; }
        
        /* Title - Main */
        .title-main {
            color: #1a3d2e;
            font-size: 3.5em;
            font-weight: 700;
            text-align: center;
            margin: 0;
            padding: 0;
            letter-spacing: 0.15em;
        }
        
        /* Title - Description */
        .title-description {
            color: #7ba576;
            font-size: 1.1em;
            text-align: center;
            margin: 0 0 1.5rem 0;
            padding: 0;
            font-style: italic;
        }
        
        /* Section headers */
        .section-header {
            color: #1a3d2e;
            font-size: 1.2em;
            font-weight: 600;
            margin: 0 0 0.5rem 0;
            padding: 0 0 0 1rem;
            border-left: 4px solid #339664;
        }

        /* Directory tree styling */
        .dir-code {
            background-color: #f5f5f5 !important;
            border: 2px solid #339664 !important;
            border-radius: 0.5rem !important;
            padding: 1rem !important;
            font-family: 'Courier New', monospace !important;
            font-size: 0.85em !important;
            max-height: 500px !important;
            overflow-y: auto !important;
        }
        
        /* Button styling */
        .stButton > button {
            background-color: #339664 !important;
            color: white !important;
            font-weight: 600 !important;
            border-radius: 0.5rem !important;
            transition: all 0.3s ease !important;
        }
        
        .stButton > button:hover {
            background-color: #2a7a54 !important;
        }
        
        /* Input labels - hide when not needed */
        label {
            font-size: 0.85em;
            margin: 0;
        }
    </style>
    """, unsafe_allow_html=True)


# ======================== UTILITY FUNCTIONS ========================
def get_asset_types() -> List[str]:
    """Return available asset types"""
    return ["Character", "Prop", "Set"]


def get_asset_names(base_path: Path, asset_type: str) -> List[str]:
    """Get unique asset names for a given asset type from both publish and working dirs"""
    if not base_path.exists():
        return []
    
    asset_names = set()
    for mode in ["publish", "working"]:
        asset_dir = base_path / mode / asset_type.lower()
        if asset_dir.exists():
            for item in asset_dir.iterdir():
                if item.is_dir():
                    asset_names.add(item.name)
    
    return sorted(list(asset_names))


def build_directory_tree(path: Path, prefix: str = "") -> str:
    """Build a text-based directory tree visualization"""
    tree = ""
    try:
        items = sorted(path.iterdir())
    except (PermissionError, NotADirectoryError):
        return tree
    
    # Separate directories and files
    folders = [item for item in items if item.is_dir() and not item.name.startswith('.')]
    files = [item for item in items if item.is_file() and not item.name.startswith('.')]
    
    # Render folders
    for i, folder in enumerate(folders):
        is_last_folder = (i == len(folders) - 1) and len(files) == 0
        connector = "└── " if is_last_folder else "├── "
        tree += f"{prefix}{connector}📁 {folder.name}\n"
        
        extension = "    " if is_last_folder else "│   "
        tree += build_directory_tree(folder, prefix + extension)
    
    # Render files
    for i, file in enumerate(files):
        is_last = i == len(files) - 1
        connector = "└── " if is_last else "├── "
        tree += f"{prefix}{connector}📄 {file.name}\n"
    
    return tree


# ======================== RENDER FUNCTIONS ========================
def render_title():
    """Render app title and description"""
    st.markdown('<div class="title-main">🌿JADE</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="title-description">An App To Streamline USD Asset Organization & Delivery Pipeline</div>',
        unsafe_allow_html=True
    )
    
    # Display any pending messages from previous operations
    if "success_message" in st.session_state and st.session_state.success_message:
        st.success(st.session_state.success_message)
        st.session_state.success_message = None
    
    if "info_message" in st.session_state and st.session_state.info_message:
        st.info(st.session_state.info_message)
        st.session_state.info_message = None


def render_base_folder_input() -> Optional[Path]:
    """Render base folder path input and return validated path"""
    st.markdown('<div class="section-header">📁 Select Base Folder</div>', unsafe_allow_html=True)
    base_path = st.text_input(
        "Base Folder Path",
        value=r"D:\SANIKA\code\jadeTEST",
        label_visibility="collapsed",
        placeholder="Enter path to assets folder"
    )
    
    if base_path:
        base_path = Path(base_path)
        if base_path.exists():
            return base_path
        else:
            st.warning(f"Path not found: {base_path}")
            return None
    return None


def render_new_asset_form(base_path: Path):
    """Render form for creating a new asset"""
    st.markdown('<div class="container-box">', unsafe_allow_html=True)
    st.markdown('<div class="section-header">Create New Asset</div>', unsafe_allow_html=True)
    
    asset_type = st.selectbox(
        "Asset Type",
        options=get_asset_types(),
        key="new_asset_type",
        label_visibility="collapsed"
    )
    
    asset_name = st.text_input(
        "Asset Name",
        placeholder="e.g., lion, stone, forest",
        key="new_asset_name",
        label_visibility="collapsed"
    )
    
    if st.button("Create Asset", use_container_width=True, key="create_asset_btn"):
        handle_create_asset(base_path, asset_name, asset_type)
    
    st.markdown('</div>', unsafe_allow_html=True)


def render_publish_asset_form(base_path: Path):
    """Render form for publishing an asset"""
    st.markdown('<div class="container-box">', unsafe_allow_html=True)
    st.markdown('<div class="section-header">Publish Asset</div>', unsafe_allow_html=True)
    
    asset_type = st.selectbox(
        "Asset Type",
        options=get_asset_types(),
        key="publish_asset_type",
        label_visibility="collapsed"
    )
    
    asset_names = get_asset_names(base_path, asset_type.lower())
    asset_name = st.selectbox(
        "Asset Name",
        options=asset_names if asset_names else ["No assets found"],
        key="publish_asset_name",
        disabled=len(asset_names) == 0,
        label_visibility="collapsed"
    )
    
    department = st.selectbox(
        "Department",
        options=["Geo", "Rig", "Tex"],
        key="publish_department",
        label_visibility="collapsed"
    )
    
    if st.button("Publish Asset", use_container_width=True, key="publish_asset_btn"):
        handle_publish_asset(base_path, asset_name, asset_type, department)
    
    st.markdown('</div>', unsafe_allow_html=True)


def render_create_shot_form(base_path: Path):
    """Render form for creating a new shot"""
    st.markdown('<div class="container-box">', unsafe_allow_html=True)
    st.markdown('<div class="section-header">Create New Shot</div>', unsafe_allow_html=True)
    
    st.markdown("**Sequence #**")
    # Use plain text inputs so users can type integers or floats
    sequence_input = st.text_input(
        "",
        value="",
        placeholder="Enter integer or float (e.g. 1 or 1.5)",
        key="shot_sequence_input",
        label_visibility="collapsed",
    )

    st.markdown("**Shot #**")
    shot_input = st.text_input(
        "",
        value="",
        placeholder="Enter integer or float (e.g. 1 or 1.5)",
        key="shot_shot_input",
        label_visibility="collapsed",
    )

    if st.button("Create Shot", use_container_width=True, key="create_shot_btn"):
        handle_create_shot(base_path, sequence_input, shot_input)
    
    st.markdown('</div>', unsafe_allow_html=True)


def render_directory_viewer(base_path: Path):
    """Render directory tree viewer with expand/collapse controls"""
    st.markdown('<div class="container-box">', unsafe_allow_html=True)
    st.markdown('<div class="section-header">📂 Directory Structure</div>', unsafe_allow_html=True)
    
    
    # Directory tree - always read fresh from filesystem
    if base_path.exists():
        tree_text = f"📦 {base_path.name}\n"
        tree_text += build_directory_tree(base_path)
        st.code(tree_text, language="text")
    else:
        st.warning("Base folder not found. Please check the path.")
    
    st.markdown('</div>', unsafe_allow_html=True)


def render_actions_panel():
    """Render left panel with action buttons"""
    st.markdown('<div class="container-box">', unsafe_allow_html=True)
    st.markdown('<div class="section-header">Actions</div>', unsafe_allow_html=True)
    
    if st.button("Publish Asset", use_container_width=True, key="action_publish_asset"):
        st.session_state.selected_action = "publish_asset"
    
    if st.button("New Asset", use_container_width=True, key="action_new_asset"):
        st.session_state.selected_action = "new_asset"
    
    if st.button("Create New Shot", use_container_width=True, key="action_create_shot"):
        st.session_state.selected_action = "create_shot"
    
    st.markdown('</div>', unsafe_allow_html=True)


# ======================== EVENT HANDLERS ========================
def handle_create_asset(base_path: Path, asset_name: str, asset_type: str):
    """Handle create asset button click"""
    if not asset_name.strip():
        st.error("Please enter an asset name")
        return
    
    asset_type_map = {"Character": "char", "Prop": "prop", "Set": "set"}
    asset_type_key = asset_type_map[asset_type]
    
    try:
        # Create the asset using jade_api
        create_new_asset(asset_name, asset_type_key, base_path / "prod" / "asset")
        
        # Store messages in session state to persist across reruns
        st.session_state.success_message = f"Asset '{asset_name}' ({asset_type_key}) created successfully"
        st.session_state.info_message = f"Location: {base_path}"
        
        # Small delay to ensure files are written
        import time
        time.sleep(0.5)
        
        # Rerun to refresh the directory tree
        st.rerun()
        
    except Exception as e:
        st.error(f"Error creating asset: {str(e)}")



def handle_publish_asset(base_path: Path, asset_name: str, asset_type: str, department: str):
    """Handle publish asset button click"""
    st.success(f"Asset '{asset_name}' published to {department}")
    st.info(f"Location: {base_path}")
    # TODO: Implement actual asset publishing


def handle_create_shot(base_path: Path, sequence_input: str, shot_input: str):
    """Handle create shot button click; parse input strings to float/int and create shot."""
    # Validate inputs
    if not sequence_input or not sequence_input.strip() or not shot_input or not shot_input.strip():
        st.error("Please enter both Sequence and Shot numbers (integer or float)")
        return

    try:
        sequence_num = float(sequence_input)
        shot_num = float(shot_input)
    except ValueError:
        st.error("Invalid numbers — please enter integer or float values (e.g. 1 or 1.5)")
        return

    try:
        # Create the shot using jade_api
        create_new_shot(sequence_num, shot_num, base_path / "prod" / "sequences")

        # Format shot name for display using decimal slot convention (multiply by 10)
        seq_formatted = str(int(round(sequence_num * 10))).zfill(3)
        shot_formatted = str(int(round(shot_num * 10))).zfill(4)
        shot_name = f"seq_{seq_formatted}_shot_{shot_formatted}"

        # Store messages in session state to persist across reruns
        st.session_state.success_message = f"Shot '{shot_name}' created successfully"
        st.session_state.info_message = f"Location: {base_path / 'prod' / 'sequences'}"

        # Small delay to ensure files are written
        import time
        time.sleep(0.5)

        # Rerun to refresh the directory tree
        st.rerun()

    except Exception as e:
        st.error(f"Error creating shot: {str(e)}")


# ======================== MAIN APPLICATION ========================
def main():
    """Main application entry point"""
    # Apply styling
    apply_theme()
    
    # Render title
    render_title()
    
    # Initialize session state
    if "selected_action" not in st.session_state:
        st.session_state.selected_action = "publish_asset"
    if "expand_all" not in st.session_state:
        st.session_state.expand_all = False
    if "success_message" not in st.session_state:
        st.session_state.success_message = None
    if "info_message" not in st.session_state:
        st.session_state.info_message = None
    base_path = render_base_folder_input()
    
    if base_path:
        # Three-column layout: 15% | 35% | 50%
        col_left, col_middle, col_right = st.columns([15, 35, 50], gap="small")
        
        # LEFT COLUMN: Actions
        with col_left:
            render_actions_panel()
        
        # MIDDLE COLUMN: Forms (context-dependent)
        with col_middle:
            if st.session_state.selected_action == "new_asset":
                render_new_asset_form(base_path)
            elif st.session_state.selected_action == "publish_asset":
                render_publish_asset_form(base_path)
            elif st.session_state.selected_action == "create_shot":
                render_create_shot_form(base_path)
        
        # RIGHT COLUMN: Directory Viewer
        with col_right:
            render_directory_viewer(base_path)
    else:
        st.error("Please provide a valid base folder path to continue")


if __name__ == "__main__":
    main()
