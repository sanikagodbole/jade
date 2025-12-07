import sys
import time
from pathlib import Path
from typing import List, Optional
import re         # For regular expression matching
import shutil     # For file copy operations

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QComboBox, QPlainTextEdit,
    QFileDialog, QSizePolicy, QMessageBox, QTreeView
)
from PyQt6.QtCore import Qt, QSize, QDir, QModelIndex
from PyQt6.QtGui import QFont, QColor, QPalette
from PyQt6.QtGui import QFileSystemModel # This is the key new import

from jade_api.create import create_new_asset, create_new_shot


# ======================== THEME & STYLING (QSS) ========================
# Equivalent of apply_theme() in Streamlit
QSS_THEME = """
    /* Color palette - Forest & Nature theme */
    :root {
        --forest-dark: #1a3d2e;
        --forest-light: #2d5a3d;
        --sage-green: #339664;
        --leaf-green: #339664;
        --stone-gray: #8b8b7e;
        --cream: #f9f8f5; /* Light background color */
    }

    /* Main Window Background */
    QMainWindow, QWidget {
        background-color: var(--cream);
    }
    
    /* Global Label/Text Styles */
    QLabel {
        color: var(--forest-dark);
    }
    
    /* Title - Main (🌿JADE) */
    #titleMain {
        color: var(--forest-dark);
        font-size: 30pt;
        font-weight: bold;
        padding-top: 10px;
        padding-bottom: 0px;
        letter-spacing: 2px;
    }
    
    /* Title - Description */
    #titleDescription {
        color: #7ba576;
        font-size: 10pt;
        font-style: italic;
        padding-top: 0px;
        padding-bottom: 20px;
    }

    /* Section Header */
    .SectionHeader {
        color: var(--forest-dark);
        font-size: 14pt;
        font-weight: 600;
        margin-bottom: 5px;
        border-left: 4px solid var(--sage-green);
        padding-left: 8px;
    }

    /* Directory Viewer */
    #directoryViewer {
        background-color: #f5f5f5;
        border: 2px solid var(--sage-green);
        border-radius: 8px;
        padding: 10px;
        font-family: 'Courier New', monospace;
        font-size: 9pt;
    }

    /* Buttons (Action Panel & Forms) */
    QPushButton {
        background-color: var(--sage-green);
        color: white;
        font-weight: 600;
        border-radius: 8px;
        padding: 8px 15px;
        min-height: 30px; /* Ensure sufficient height */
        margin-bottom: 5px;
    }
    
    QPushButton:hover {
        background-color: #2a7a54; /* Darker green on hover */
    }

    /* Inputs (QLineEdit, QComboBox) */
    QLineEdit, QComboBox {
        background-color: white;
        border: 1px solid #ccc;
        border-radius: 5px;
        padding: 5px;
        min-height: 25px;
    }
    
    /* Container Box Styling (like Streamlit containers) */
    .ContainerBox {
        background-color: white;
        border: 1px solid #eee;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 15px;
    }

    /* Small/Collapsed Label for Inputs (Placeholder for Streamlit label_visibility="collapsed") */
    .InputLabel {
        font-size: 8pt;
        color: #888;
        margin-bottom: 2px;
    }
"""

# ======================== UTILITY FUNCTIONS ========================
def get_asset_types() -> List[str]:
    """Return available asset types"""
    return ["Character", "Prop", "Set"]

def get_asset_names(base_path: Path, asset_type: str) -> List[str]:
    """Get unique asset names for a given asset type from both publish and working dirs"""
    if not base_path.exists():
        return []
    
    asset_names = set()
    # Mocking the folder structure implied by the Streamlit app
    # (base_path / "prod" / "asset" / mode / asset_type_key / asset_name)
    asset_type_key_map = {"Character": "char", "Prop": "prop", "Set": "set"}
    asset_type_key = asset_type_key_map.get(asset_type)
    
    if not asset_type_key:
        return []

    for mode in ["publish", "working"]:
        asset_dir = base_path / "prod" / "asset" / mode / asset_type_key
        if asset_dir.exists():
            for item in asset_dir.iterdir():
                if item.is_dir():
                    asset_names.add(item.name)
    
    return sorted(list(asset_names))

def build_directory_tree(path: Path, prefix: str = "") -> str:
    """Build a text-based directory tree visualization (Streamlit function preserved)"""
    tree = ""
    try:
        # Sort items: directories first, then files, both alphabetically
        items = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
    except (PermissionError, NotADirectoryError):
        return tree
    except FileNotFoundError:
        return tree
    
    # Filter out hidden files/dirs
    items = [item for item in items if not item.name.startswith('.')]
    
    # Separate directories and files
    folders = [item for item in items if item.is_dir()]
    files = [item for item in items if item.is_file()]
    
    # Render folders
    for i, folder in enumerate(folders):
        is_last_folder = (i == len(folders) - 1) and len(files) == 0
        connector = "└── " if is_last_folder else "├── "
        tree += f"{prefix}{connector}📁 {folder.name}\n"
        
        extension = "    " if is_last_folder else "│   "
        tree += build_directory_tree(folder, prefix + extension)
    
    # Render files
    for i, file in enumerate(files):
        is_last = i == len(files) - 1
        connector = "└── " if is_last else "├── "
        tree += f"{prefix}{connector}📄 {file.name}\n"
    
    return tree


def find_highest_version_file(export_path: Path, asset_name: str, department: str, file_extension: str) -> Optional[
    Path]:
    """
    Identifies the file with the highest numerical version in the given directory.
    Pattern: <asset_name>_<department>_v<numerical_version>_<user_initials>.<file_extension>

    The file_extension should include the leading dot, e.g., '.usd'.
    """
    if not export_path.is_dir():
        return None

    # Create the expected file prefix, standardizing to lower case
    name_prefix = f"{asset_name.lower()}_{department.lower()}_v"

    # List to store (version_number, file_path) tuples
    versioned_files = []

    # Ensure the extension starts with a dot for accurate filtering
    ext = file_extension if file_extension.startswith('.') else f".{file_extension}"

    for file_path in export_path.iterdir():
        filename = file_path.name

        # Check if the file starts with the prefix and ends with the specified extension
        if filename.startswith(name_prefix) and filename.endswith(ext):
            try:
                # Look for digits between 'v' and the next '_'
                # This regex captures the version number: e.g., 'v' followed by digits, followed by '_'
                # We use re.escape in case the prefix contains regex special characters (safer practice)
                match = re.search(f"{re.escape(name_prefix)}(\\d+)_", filename)
                if match:
                    version = int(match.group(1))
                    versioned_files.append((version, file_path))
            except Exception:
                # Skip files that don't perfectly conform to the version pattern
                continue

    if not versioned_files:
        return None

    # Find the file path associated with the maximum version number
    highest_version_file = max(versioned_files, key=lambda x: x[0])[1]
    return highest_version_file


# ======================== UI WIDGET CLASSES ========================

class NewAssetForm(QWidget):
    """Widget for creating a new asset."""
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setObjectName("newAssetForm")
        self.setStyleSheet(".ContainerBox {background-color: #f0fff0;}") # Light green tint for this form
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        header = QLabel("Create New Asset")
        header.setProperty("class", "SectionHeader")
        layout.addWidget(header)
        
        # Asset Type Select
        layout.addWidget(QLabel("Asset Type"))
        self.asset_type_combo = QComboBox()
        self.asset_type_combo.addItems(get_asset_types())
        layout.addWidget(self.asset_type_combo)

        # Asset Name Input
        layout.addWidget(QLabel("Asset Name"))
        self.asset_name_input = QLineEdit()
        self.asset_name_input.setPlaceholderText("e.g., lion, stone, forest")
        layout.addWidget(self.asset_name_input)
        
        # Create Button
        self.create_button = QPushButton("Create Asset")
        self.create_button.clicked.connect(self.handle_create_asset)
        layout.addWidget(self.create_button)
        
        layout.addStretch(1)

    def handle_create_asset(self):
        base_path = self.main_window.base_path
        if not base_path:
            QMessageBox.warning(self, "Error", "Base folder path is invalid.")
            return

        asset_name = self.asset_name_input.text().strip()
        asset_type = self.asset_type_combo.currentText()
        
        if not asset_name:
            QMessageBox.critical(self, "Error", "Please enter an asset name.")
            return

        asset_type_map = {"Character": "char", "Prop": "prop", "Set": "set"}
        asset_type_key = asset_type_map.get(asset_type)
        
        try:
            # The base path for asset creation is assumed to be 'prod/asset'
            create_new_asset(asset_name, asset_type_key, base_path / "prod" / "asset")
            
            self.main_window.show_message(
                f"Asset '{asset_name}' ({asset_type_key}) created successfully", 
                "success"
            )
            self.main_window.show_message(
                f"Location: {base_path}", 
                "info", 
                delay=3000
            )
            self.asset_name_input.clear() # Clear input after success
            self.main_window.directory_viewer.refresh_tree()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error creating asset: {str(e)}")


class PublishAssetForm(QWidget):
    """Widget for publishing an asset."""
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setObjectName("publishAssetForm")
        self.setStyleSheet(".ContainerBox {background-color: #fffff0;}") # Light yellow tint
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        header = QLabel("Publish Asset")
        header.setProperty("class", "SectionHeader")
        layout.addWidget(header)
        
        # Asset Type Select
        layout.addWidget(QLabel("Asset Type"))
        self.asset_type_combo = QComboBox()
        self.asset_type_combo.addItems(get_asset_types())
        self.asset_type_combo.currentIndexChanged.connect(self.update_asset_names)
        layout.addWidget(self.asset_type_combo)
        
        # Asset Name Select
        layout.addWidget(QLabel("Asset Name"))
        self.asset_name_combo = QComboBox()
        layout.addWidget(self.asset_name_combo)
        
        # Department Select
        layout.addWidget(QLabel("Department"))
        self.department_combo = QComboBox()
        self.department_combo.addItems(["Geo", "Rig", "Tex"])
        layout.addWidget(self.department_combo)
        
        # Publish Button
        self.publish_button = QPushButton("Publish Asset")
        self.publish_button.clicked.connect(self.handle_publish_asset)
        layout.addWidget(self.publish_button)
        
        layout.addStretch(1)
        self.update_asset_names() # Initial population

    def update_asset_names(self):
        base_path = self.main_window.base_path
        asset_type = self.asset_type_combo.currentText()
        asset_names = []
        if base_path and base_path.exists():
            asset_names = get_asset_names(base_path, asset_type)
        
        self.asset_name_combo.clear()
        if asset_names:
            self.asset_name_combo.addItems(asset_names)
            self.publish_button.setEnabled(True)
        else:
            self.asset_name_combo.addItem("No assets found")
            self.publish_button.setEnabled(False)

    def handle_publish_asset(self):
        """Handle publish asset button click: finds highest version and copies it to the publish folder."""
        base_path = self.main_window.base_path
        asset_name = self.asset_name_combo.currentText()
        asset_type = self.asset_type_combo.currentText()
        department = self.department_combo.currentText()

        # Map asset type (e.g., 'Character') to its key (e.g., 'char')
        asset_type_map = {"Character": "char", "Prop": "prop", "Set": "set"}
        asset_type_key = asset_type_map.get(asset_type)

        if asset_name == "No assets found" or not asset_type_key or not base_path:
            QMessageBox.warning(self, "Warning", "Please ensure a valid asset and base path are selected.")
            return

        # 1. Determine the required file extensions based on department
        department_map = {
            "geo": {
                "source_ext": ".usd",
                "publish_ext": ".usd"
            },
            "rig": {
                "source_ext": ".mb",
                "publish_ext": ".mb"
            },
            "tex": {
                "source_ext": ".png",
                "publish_ext": ".png"
            }
        }

        dept_info = department_map.get(department.lower())

        if not dept_info:
            QMessageBox.warning(self, "Warning", f"Publish logic not implemented for department: {department}")
            return

        source_ext = dept_info["source_ext"]
        publish_ext = dept_info["publish_ext"]

        try:
            # 2. Define source (working) path where versioned files reside
            source_dir = base_path / "prod" / "asset" / "working" / asset_type_key / asset_name / department / "export"

            # 3. Identify the highest version file using the correct extension
            highest_version_file = find_highest_version_file(source_dir, asset_name, department, source_ext)

            if not highest_version_file:
                QMessageBox.warning(self, "Warning",
                                    f"No versioned files ({source_ext}) found in: {source_dir}")
                return

            # 4. Define the destination folder (publish)
            destination_dir = base_path / "prod" / "asset" / "publish" / asset_type_key / asset_name / department

            # Define the new file name (no version, no initials: e.g., lion_geo.usd or lion_rig.mb)
            new_file_name = f"{asset_name.lower()}_{department.lower()}{publish_ext}"
            destination_file = destination_dir / new_file_name

            # Ensure the destination directory exists
            destination_dir.mkdir(parents=True, exist_ok=True)

            # 5. Copy the highest version file and rename it
            shutil.copy2(highest_version_file, destination_file)

            # 6. Success messages and GUI refresh
            self.main_window.show_message(
                f"Asset '{asset_name}' published from '{highest_version_file.name}'",
                "success"
            )
            self.main_window.show_message(
                f"Published as: {destination_file.name}",
                "info",
                delay=3000
            )
            self.main_window.directory_viewer.refresh_tree()

        except Exception as e:
            QMessageBox.critical(self, "Publish Error", f"Failed to publish asset: {str(e)}")


print("hi")

class CreateShotForm(QWidget):
    """Widget for creating a new shot."""
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setObjectName("createShotForm")
        self.setStyleSheet(".ContainerBox {background-color: #f0ffff;}") # Light cyan tint
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        header = QLabel("Create New Shot")
        header.setProperty("class", "SectionHeader")
        layout.addWidget(header)
        
        # Sequence Input
        layout.addWidget(QLabel("**Sequence #**"))
        self.sequence_input = QLineEdit()
        self.sequence_input.setPlaceholderText("Enter integer or float (e.g. 1 or 1.5)")
        layout.addWidget(self.sequence_input)

        # Shot Input
        layout.addWidget(QLabel("**Shot #**"))
        self.shot_input = QLineEdit()
        self.shot_input.setPlaceholderText("Enter integer or float (e.g. 1 or 1.5)")
        layout.addWidget(self.shot_input)

        # Create Button
        self.create_button = QPushButton("Create Shot")
        self.create_button.clicked.connect(self.handle_create_shot)
        layout.addWidget(self.create_button)
        
        layout.addStretch(1)

    def handle_create_shot(self):
        base_path = self.main_window.base_path
        if not base_path:
            QMessageBox.warning(self, "Error", "Base folder path is invalid.")
            return

        sequence_input = self.sequence_input.text().strip()
        shot_input = self.shot_input.text().strip()

        if not sequence_input or not shot_input:
            QMessageBox.critical(self, "Error", "Please enter both Sequence and Shot numbers.")
            return

        try:
            sequence_num = float(sequence_input)
            shot_num = float(shot_input)
        except ValueError:
            QMessageBox.critical(self, "Error", "Invalid numbers — please enter integer or float values (e.g. 1 or 1.5).")
            return

        try:
            # The base path for shot creation is assumed to be 'prod/sequences'
            create_new_shot(sequence_num, shot_num, base_path / "prod" / "sequences")

            # Format shot name for display
            seq_formatted = str(int(round(sequence_num * 10))).zfill(3)
            shot_formatted = str(int(round(shot_num * 10))).zfill(4)
            shot_name = f"seq_{seq_formatted}_shot_{shot_formatted}"

            self.main_window.show_message(
                f"Shot '{shot_name}' created successfully", 
                "success"
            )
            self.main_window.show_message(
                f"Location: {base_path / 'prod' / 'sequences'}", 
                "info", 
                delay=3000
            )
            self.sequence_input.clear()
            self.shot_input.clear()
            self.main_window.directory_viewer.refresh_tree()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error creating shot: {str(e)}")


class DirectoryViewer(QWidget):
    """Widget for displaying the directory tree using QTreeView and QFileSystemModel."""

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.model = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        header = QLabel("📂 Directory Structure")
        header.setProperty("class", "SectionHeader")
        layout.addWidget(header)

        # 1. Initialize the Model
        self.model = QFileSystemModel()
        self.model.setRootPath(QDir.rootPath())  # Start at the root for model initialization

        # 2. Initialize the View
        self.tree_display = QTreeView()
        self.tree_display.setModel(self.model)
        self.tree_display.setSortingEnabled(True)
        self.tree_display.setUniformRowHeights(True)
        self.tree_display.setMinimumSize(400, 300)  # Ensure it has space

        # Hide unnecessary columns (Size, Type, Date Modified)
        for i in range(1, self.model.columnCount()):
            self.tree_display.hideColumn(i)

        layout.addWidget(self.tree_display)

        # Initial refresh
        self.refresh_tree()

    def refresh_tree(self):
        base_path = self.main_window.base_path

        if not base_path or not base_path.exists():
            # Clear or show a message if the path is invalid
            self.tree_display.setRootIndex(QModelIndex())  # Clear the view
            # You might need a separate status label if you want a text warning
            return

        # Set the root of the view to the base_path
        root_index = self.model.index(str(base_path))

        if root_index.isValid():
            self.tree_display.setRootIndex(root_index)
            # Ensure the first level is expanded for visibility (optional)
            self.tree_display.expand(root_index)

            # Auto-size the Name column to fit the path name
            self.tree_display.header().resizeSection(0, 300)
        else:
            # Handle case where the path exists but isn't valid for QFileSystemModel
            # (less common, but good practice)
            self.tree_display.setRootIndex(QModelIndex())


class TextDirectoryViewer(QWidget):
    """Widget for displaying the directory tree."""
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        header = QLabel("📂 Directory Structure")
        header.setProperty("class", "SectionHeader")
        layout.addWidget(header)
        
        self.tree_display = QPlainTextEdit()
        self.tree_display.setObjectName("directoryViewer")
        self.tree_display.setReadOnly(True)
        self.tree_display.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self.tree_display)
        
        self.refresh_tree()

    def refresh_tree(self):
        base_path = self.main_window.base_path
        if not base_path or not base_path.exists():
            self.tree_display.setPlainText("Base folder not found. Please check the path.")
            return
        
        tree_text = f"📦 {base_path.name}\n"
        try:
            tree_text += build_directory_tree(base_path)
            self.tree_display.setPlainText(tree_text)
        except Exception as e:
            self.tree_display.setPlainText(f"Error reading directory: {str(e)}")


# ======================== MAIN WINDOW ========================

class JADEGui(QMainWindow):
    """Main application window, replacing the Streamlit layout."""
    def __init__(self):
        super().__init__()
        self.base_path: Optional[Path] = None
        self.default_path = Path(r"D:\SANIKA\code\jadeTEST") # Default path from original
        self.setWindowTitle("JADE - Asset Organization & Delivery Pipeline (PyQt)")
        self.setGeometry(100, 100, 1200, 800)
        self.setStyleSheet(QSS_THEME)
        self.selected_action = "publish_asset"  # "new_asset"

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        self.init_ui()

    def init_ui(self):
        # 1. Title and Messages
        title_widget = self._render_title_and_messages()
        self.main_layout.addWidget(title_widget)
        
        # 2. Base Folder Input
        self.base_path_widget = self._render_base_folder_input()
        self.main_layout.addWidget(self.base_path_widget)
        
        # 3. Main Content (Three-Column Layout: Actions | Forms | Viewer)
        self.content_container = QWidget()
        self.content_layout = QHBoxLayout(self.content_container)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        
        # LEFT COLUMN: Actions (15%)
        self.actions_panel = self._render_actions_panel()
        self.content_layout.addWidget(self.actions_panel, 15)
        
        # MIDDLE COLUMN: Forms (35%)
        self.forms_container = QVBoxLayout()
        self.forms_widget = QWidget()
        self.forms_widget.setLayout(self.forms_container)
        self.content_layout.addWidget(self.forms_widget, 35)

        self.new_asset_form = NewAssetForm(self)
        self.publish_asset_form = PublishAssetForm(self)
        self.create_shot_form = CreateShotForm(self)

        # RIGHT COLUMN: Directory Viewer (50%)
        self.directory_viewer = DirectoryViewer(self)
        self.content_layout.addWidget(self.directory_viewer, 50)

        self.main_layout.addWidget(self.content_container)
        
        # Initialize forms and update path
        self.update_path_and_ui(str(self.default_path))
        self._update_middle_column()

    def _render_title_and_messages(self):
        """Render app title, description, and message area."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(0)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Title
        title_label = QLabel("🌿JADE")
        title_label.setObjectName("titleMain")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Description
        desc_label = QLabel("An App To Streamline USD Asset Organization & Delivery Pipeline")
        desc_label.setObjectName("titleDescription")
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(desc_label)
        
        # Message Display Area (replaces st.success/st.info)
        self.message_label = QLabel("")
        self.message_label.setWordWrap(True)
        self.message_label.setMinimumHeight(20)
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.message_label)

        return container

    def show_message(self, text, type_name, delay=2000):
        """Display a temporary success/info message."""
        if type_name == "success":
            color = "#1a8449" # Darker green for success
        elif type_name == "info":
            color = "#17a2b8" # Standard info blue
        else: # error/warning if implemented later
            color = "#dc3545" 

        self.message_label.setText(text)
        self.message_label.setStyleSheet(f"background-color: {color}; color: white; padding: 5px; border-radius: 5px;")
        
        # QTimer to clear the message after a delay (in milliseconds)
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(delay, lambda: self.message_label.setStyleSheet("min-height: 20px;"))
        QTimer.singleShot(delay, lambda: self.message_label.setText(""))


    def _render_base_folder_input(self):
        """Render base folder path input and validation."""
        container = QWidget()
        container.setProperty("class", "ContainerBox")
        layout = QHBoxLayout(container)
        layout.setContentsMargins(5, 5, 5, 5)

        header = QLabel("📁 Select Base Folder")
        header.setProperty("class", "SectionHeader")
        layout.addWidget(header)
        
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("Enter path to assets folder")
        self.path_input.setText(str(self.default_path))
        self.path_input.textChanged.connect(self.update_path_and_ui)
        layout.addWidget(self.path_input)

        browse_button = QPushButton("Browse")
        browse_button.clicked.connect(self.browse_folder)
        browse_button.setStyleSheet("padding: 5px 10px; min-height: 20px;")
        layout.addWidget(browse_button)

        self.path_status_label = QLabel("")
        layout.addWidget(self.path_status_label)
        
        return container

    def browse_folder(self):
        """Open a file dialog to select the base folder."""
        folder = QFileDialog.getExistingDirectory(self, "Select Base Assets Folder")
        if folder:
            self.path_input.setText(folder) # This will trigger update_path_and_ui

    def update_path_and_ui(self, path_str: str):
        """Validate path and update dependent UI components."""
        new_path = Path(path_str)
        if new_path.exists() and new_path.is_dir():
            self.base_path = new_path
            self.path_status_label.setText("Path OK")
            self.path_status_label.setStyleSheet("color: green; font-weight: bold;")
            
            # Re-enable main content if it was disabled
            self.directory_viewer.refresh_tree()
            self.publish_asset_form.update_asset_names()
        else:
            self.base_path = None
            self.path_status_label.setText("Path Not Found")
            self.path_status_label.setStyleSheet("color: red; font-weight: bold;")
            self.directory_viewer.refresh_tree() # Display error message
    
    def _render_actions_panel(self):
        """Render left panel with action buttons."""
        container = QWidget()
        container.setProperty("class", "ContainerBox")
        layout = QVBoxLayout(container)
        
        header = QLabel("Actions")
        header.setProperty("class", "SectionHeader")
        layout.addWidget(header)
        
        self.publish_btn = QPushButton("Publish Asset")
        self.new_asset_btn = QPushButton("New Asset")
        self.create_shot_btn = QPushButton("Create New Shot")
        
        self.publish_btn.clicked.connect(lambda: self._set_action("publish_asset"))
        self.new_asset_btn.clicked.connect(lambda: self._set_action("new_asset"))
        self.create_shot_btn.clicked.connect(lambda: self._set_action("create_shot"))
        
        layout.addWidget(self.publish_btn)
        layout.addWidget(self.new_asset_btn)
        layout.addWidget(self.create_shot_btn)
        
        layout.addStretch(1) # Push content to the top
        
        # Highlight the initially selected button
        self.publish_btn.setStyleSheet("background-color: #2a7a54; border: 2px solid white;")

        return container

    def _set_action(self, action_name):
        """Set the current action and update the middle column."""
        self.selected_action = action_name
        
        # Reset button styles
        for btn in [self.publish_btn, self.new_asset_btn, self.create_shot_btn]:
            btn.setStyleSheet("")
            
        # Highlight the new active button
        if action_name == "publish_asset":
            active_btn = self.publish_btn
        elif action_name == "new_asset":
            active_btn = self.new_asset_btn
        elif action_name == "create_shot":
            active_btn = self.create_shot_btn
        else:
            raise Exception(f"Invalid action: {action_name}")

        # active_btn = getattr(self, f"{action_name.replace('_', '_')}s_btn" if action_name.endswith('asset') else f"{action_name.replace('_', '_')}s_btn")
        # if active_btn == self.publish_btn:
        #     active_btn = self.publish_btn
        # elif active_btn == self.new_asset_btn:
        #     active_btn = self.new_asset_btn
        # elif active_btn == self.create_shot_btn:
        #     active_btn = self.create_shot_btn

        active_btn.setStyleSheet("background-color: #2a7a54; border: 2px solid white;")
        
        self._update_middle_column()

    def _update_middle_column(self):
        """Switch the form displayed in the middle column."""
        # Clear existing widgets in the forms container
        for i in reversed(range(self.forms_container.count())):
            widget_to_remove = self.forms_container.itemAt(i).widget()
            if widget_to_remove:
                widget_to_remove.setParent(None)

        if self.selected_action == "new_asset":
            self.forms_container.addWidget(self.new_asset_form)
        elif self.selected_action == "publish_asset":
            self.forms_container.addWidget(self.publish_asset_form)
            self.publish_asset_form.update_asset_names() # Refresh asset list on switch
        elif self.selected_action == "create_shot":
            self.forms_container.addWidget(self.create_shot_form)


# ======================== MAIN APPLICATION ENTRY POINT ========================

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Initialize the main UI
    window = JADEGui()
    window.show()
    
    sys.exit(app.exec())