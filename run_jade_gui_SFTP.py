import sys
from pathlib import Path
from typing import List, Optional
import shutil
import re
from jade_api.activity import log_action
from jade_api.remoteSetup import sftp_connect


from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QComboBox, QPlainTextEdit,
    QFileDialog, QSizePolicy, QMessageBox, QTreeView
)
from PyQt6.QtCore import Qt, QSize, QDir, QModelIndex
from PyQt6.QtGui import QFont, QColor, QPalette
from PyQt6.QtGui import QFileSystemModel


from jade_api.create import create_new_asset, create_new_shot, find_highest_version_file


# ======================== UTILITY FUNCTIONS ========================
def get_asset_types() -> List[str]:
    """Return available asset types"""
    return ["Character", "Prop", "Set"]


def get_asset_names(base_path: Path, asset_type: str, sftp_client=None) -> List[str]:
    """Get unique asset names for a given asset type from both publish and working dirs"""
    if not base_path.exists():
        return []

    if sftp_client:
        base_path = sftp_client.remote_default

    asset_names = set()
    # (base_path / "prod" / "asset" / mode / asset_type_key / asset_name)
    asset_type_key_map = {"Character": "char", "Prop": "prop", "Set": "set"}
    asset_type_key = asset_type_key_map.get(asset_type)

    if not asset_type_key:
        return []

    for mode in ["publish", "working"]:
        asset_dir = base_path / "prod" / "asset" / mode / asset_type_key

        if sftp_client:
            # --- REMOTE SFTP LOGIC ---
            try:
                # 1. Convert Path to POSIX string for the server
                remote_path_str = asset_dir.as_posix()

                # 2. Get the list of strings from the server
                items = sftp_client.listdir(remote_path_str)

                # 3. Update the set directly with the returned list of names
                asset_names.update(items)
                print(f"SFTP found in {mode}: {items}")
            except Exception as e:
                # If directory doesn't exist on server yet, skip it
                print(f"SFTP skipping {mode} (likely folder doesn't exist): {e}")
                continue

        else:
            # --- LOCAL LOGIC ---
            if asset_dir.exists():
                # Locally we filter for directories only
                names = [item.name for item in asset_dir.iterdir() if item.is_dir()]
                asset_names.update(names)
                print(f"Local found in {mode}: {names}")


    print(asset_dir)
    print(asset_names)
    return sorted(list(asset_names))



def get_shot_names(base_path: Path) -> List[str]:
    """Get unique shot folder names from the sequences directory"""
    sequences_dir = base_path / "prod" / "sequences"
    if not sequences_dir.exists():
        return []

    # Looks for folders starting with 'seq_' (e.g., seq_010_shot_0010)
    shot_names = [item.name for item in sequences_dir.iterdir() if item.is_dir() and item.name.startswith("seq_")]
    return sorted(shot_names)


def get_shot_departments(base_path: Path, shot_name: str) -> List[str]:
    """Get all department folder names from a specific shot's working directory."""
    # Construct the path to the working directory for the specific shot
    working_dir = base_path / "prod" / "sequences" / shot_name / "working"

    if not working_dir.exists():
        return []

    # Return names of all sub-directories inside 'working', ignoring hidden folders
    depts = [item.name for item in working_dir.iterdir() if item.is_dir() and not item.name.startswith('.')]
    return sorted(depts)


def build_directory_tree(path: Path, prefix: str = "") -> str:
    #  build tree visualization
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


# ======================== UI WIDGET CLASSES ========================

class NewAssetForm(QWidget):
    """Widget for creating a new asset."""

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setObjectName("newAssetForm")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        header = QLabel("Create New Asset")
        header.setProperty("class", "SectionHeader")
        header.setStyleSheet("color: #339664; font-weight: bold;")
        header.setFont(QFont('Consolas', 15))
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
        self.create_button.setFont(QFont('Consolas', 10))
        self.create_button.setStyleSheet("""
            QPushButton {
                background-color: #85d5ad; 
                padding: 5px 10px;
                min-height: 10px;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: #339664;
            }
        """)
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
                delay=60000
            )
            self.asset_name_input.clear()  # Clear input after success
            self.main_window.directory_viewer.refresh_tree()

            log_action(
                base_path=base_path,
                action="Create_Asset",
                details=f"{asset_type_key.upper()} / {asset_name}"
            )

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error creating asset: {str(e)}")


class PublishAssetForm(QWidget):
    """Widget for publishing an asset."""

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setObjectName("publishAssetForm")
        # self.setStyleSheet(".ContainerBox {background-color: #fffff0;}") # Light yellow tint
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        header = QLabel("Publish Asset")
        header.setProperty("class", "SectionHeader")
        header.setStyleSheet("color: #339664; font-weight: bold;")
        header.setFont(QFont('Consolas', 15))
        layout.addWidget(header)

        # Asset Type Select
        layout.addWidget(QLabel("Asset Type"))
        self.asset_type_combo = QComboBox()
        self.asset_type_combo.addItems(get_asset_types())
        self.asset_type_combo.currentIndexChanged.connect(self.update_asset_names)
        layout.addWidget(self.asset_type_combo)

        # Department Select (Now the primary filter)
        layout.addWidget(QLabel("Department"))
        self.department_combo = QComboBox()
        # Unified list of asset and shot departments
        self.department_combo.addItems(["geo", "rig", "tex", "assembly"])
        self.department_combo.currentIndexChanged.connect(self.update_asset_names)
        layout.addWidget(self.department_combo)

        # Asset Name Select
        layout.addWidget(QLabel("Asset Name"))
        self.asset_name_combo = QComboBox()
        layout.addWidget(self.asset_name_combo)

        # Publish Button
        self.publish_button = QPushButton("Publish Asset")
        self.publish_button.setFont(QFont('Consolas', 10))
        self.publish_button.setStyleSheet("""
            QPushButton {
                background-color: #85d5ad; 
                padding: 5px 10px;
                min-height: 10px;   
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: #339664;
            }
        """)

        self.publish_button.clicked.connect(self.handle_publish_asset)

        layout.addWidget(self.publish_button)

        layout.addStretch(1)
        self.update_asset_names()  # Initial population

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
        """Handle publish asset button click: focused strictly on Assets."""
        base_path = self.main_window.base_path
        asset_name = self.asset_name_combo.currentText()
        asset_type = self.asset_type_combo.currentText()
        department = self.department_combo.currentText().lower()

        # Validation
        if asset_name == "No assets found" or not base_path:
            QMessageBox.warning(self, "Warning", "Please ensure a valid selection and base path.")
            return

        department_map = {
            "geo": [(".usd", ".usd", "file")],
            "rig": [(".ma", ".ma", "file")],
            "assembly": [
                (".geo.usdc", ".geo.usdc", "file"),
                (".mtl.usdc", ".mtl.usdc", "file"),
                (".payload.usdc", ".payload.usdc", "file"),
                (".usd", ".usd", "file"),
                (None, ".textures", "folder")
            ],
            "tex": [
                (".png", ".png", "file"),
                (None, ".textures", "folder")
            ]
        }

        target_extensions = department_map.get(department)
        if not target_extensions:
            QMessageBox.warning(self, "Warning", f"Publish logic not implemented for: {department}")
            return

        try:
            # Simplified Asset-Only Path Logic
            asset_type_map = {"Character": "char", "Prop": "prop", "Set": "set"}
            asset_type_key = asset_type_map.get(asset_type)

            source_dir = base_path / "prod" / "asset" / "working" / asset_type_key / asset_name / department / "export"
            destination_dir = base_path / "prod" / "asset" / "publish" / asset_type_key / asset_name / department
            identifier_name = asset_name

            destination_dir.mkdir(parents=True, exist_ok=True)
            files_published = []
            source_file_details = []

            # 3. Special Case: TEX Department
            if department == "tex":
                highest_source_folder = find_highest_version_file(
                    source_dir, identifier_name, department, None, is_folder_search=True
                )
                if highest_source_folder:
                    source_file_details.append(highest_source_folder.name)
                    # Clear destination
                    for item in destination_dir.iterdir():
                        if item.is_dir():
                            shutil.rmtree(item)
                        else:
                            item.unlink()

                    version_and_initials_pattern = re.compile(r'_v\d+_[a-zA-Z]+')
                    items_copied_count = 0
                    for source_item_path in highest_source_folder.iterdir():
                        item_name = source_item_path.name
                        if source_item_path.is_file() and version_and_initials_pattern.search(item_name):
                            new_item_name = version_and_initials_pattern.sub('', item_name)
                            shutil.copy2(source_item_path, destination_dir / new_item_name)
                            items_copied_count += 1
                        else:
                            dest_item_path = destination_dir / item_name
                            if source_item_path.is_dir():
                                shutil.copytree(source_item_path, dest_item_path)
                            else:
                                shutil.copy2(source_item_path, dest_item_path)
                            items_copied_count += 1
                    files_published.append(f"TEX Folder: {items_copied_count} items")

            # 4. Special Case: ASSEMBLY Department (Folder Logic)
            elif department == "assembly":
                highest_source_folder = find_highest_version_file(
                    source_dir, identifier_name, department, None, is_folder_search=True
                )
                if highest_source_folder:
                    source_file_details.append(highest_source_folder.name)
                    dest_textures_path = destination_dir / ".textures"

                    if dest_textures_path.exists():
                        shutil.rmtree(dest_textures_path)

                    shutil.copytree(highest_source_folder, dest_textures_path)
                    files_published.append(f"Assembly Folder: .textures")

            # 5. Standard Publishing Loop (Files)
            for source_ext, publish_ext, item_type in target_extensions:
                if item_type == "folder":
                    continue

                highest_source_file = find_highest_version_file(source_dir, identifier_name, department, source_ext)
                if not highest_source_file:
                    continue

                source_file_details.append(highest_source_file.name)
                new_file_name = f"{identifier_name}_{department}{publish_ext}"
                destination_file = destination_dir / new_file_name

                if destination_file.exists():
                    destination_file.unlink()

                shutil.copy2(highest_source_file, destination_file)
                files_published.append(new_file_name)

            # 6. Success and Logging
            if files_published:
                self.main_window.show_message(f"Published items for {identifier_name}", "success")
                self.main_window.directory_viewer.refresh_tree()
                log_action(
                    base_path=base_path,
                    action="Publish_Asset",
                    details=f"{department.upper()} / {identifier_name} | Sources: {', '.join(source_file_details)}"
                )
            else:
                QMessageBox.information(self, "Not Found", f"No versioned items found for {department}.")

        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Publish Error", f"Failed to publish: {str(e)}")


class PublishShotForm(QWidget):
    """Widget for publishing a shot."""

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setObjectName("publishShotForm")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        header = QLabel("Publish Shot")
        header.setProperty("class", "SectionHeader")
        header.setStyleSheet("color: #339664; font-weight: bold;")
        header.setFont(QFont('Consolas', 15))
        layout.addWidget(header)

        # Shot Name Dropdown
        layout.addWidget(QLabel("Shot #"))
        self.shot_name_combo = QComboBox()
        # Trigger department refresh when shot selection changes
        self.shot_name_combo.currentIndexChanged.connect(self.update_departments)
        layout.addWidget(self.shot_name_combo)

        # Department Dropdown (Now Dynamic)
        layout.addWidget(QLabel("Department"))
        self.department_combo = QComboBox()
        layout.addWidget(self.department_combo)

        # Publish Button
        self.publish_button = QPushButton("Publish Shot")
        self.publish_button.setFont(QFont('Consolas', 10))
        self.publish_button.setStyleSheet("""
            QPushButton { background-color: #85d5ad; padding: 5px 10px; min-height: 10px; border-radius: 10px; }
            QPushButton:hover { background-color: #339664; }
        """)
        self.publish_button.clicked.connect(self.handle_publish_shot)
        layout.addWidget(self.publish_button)

        layout.addStretch(1)
        self.refresh_shots()

    def update_departments(self):
        """Dynamic refresh: gets departments based on the currently selected shot."""
        base_path = self.main_window.base_path
        shot_name = self.shot_name_combo.currentText()

        if not base_path or shot_name == "No shots found":
            self.department_combo.clear()
            return

        # Fetch folders directly from the filesystem
        depts = get_shot_departments(base_path, shot_name)

        self.department_combo.clear()
        if depts:
            self.department_combo.addItems(depts)
            self.publish_button.setEnabled(True)
        else:
            self.department_combo.addItem("No departments found")
            self.publish_button.setEnabled(False)

    def refresh_shots(self):
        base_path = self.main_window.base_path
        names = get_shot_names(base_path) if base_path else []
        self.shot_name_combo.clear()
        if names:
            self.shot_name_combo.addItems(names)
            self.publish_button.setEnabled(True)
        else:
            self.shot_name_combo.addItem("No shots found")
            self.publish_button.setEnabled(False)

    def handle_publish_shot(self):
        base_path = self.main_window.base_path
        shot_name = self.shot_name_combo.currentText()
        department = self.department_combo.currentText().lower()

        try:
            # SHOT PATHS: prod/sequences/<shot_name>/working/<dept>/export
            source_dir = base_path / "prod" / "sequences" / shot_name / "working" / department / "export"
            destination_dir = base_path / "prod" / "sequences" / shot_name / "publish" / department

            # Identify highest version using your find_highest_version_file in create.py
            # Extension is set to .usd as per your requirement
            highest_file = find_highest_version_file(source_dir, shot_name, department, ".usd")

            if not highest_file:
                QMessageBox.warning(self, "Not Found", f"No versioned .usd files found in {source_dir}")
                return

            # Final name: seq_010_shot_0010_light.usd
            dest_file = destination_dir / f"{shot_name}_{department}.usd"

            destination_dir.mkdir(parents=True, exist_ok=True)
            if dest_file.exists():
                dest_file.unlink()

            shutil.copy2(highest_file, dest_file)

            self.main_window.show_message(f"Shot '{shot_name}' {department} published successfully!", "success")
            self.main_window.directory_viewer.refresh_tree()

            log_action(
                base_path=base_path,
                action="Publish_Shot",
                details=f"{department.upper()} / {shot_name} | Source: {highest_file.name}"
            )

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to publish shot: {str(e)}")


class CreateShotForm(QWidget):
    """Widget for creating a new shot."""

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setObjectName("createShotForm")
        # self.setStyleSheet(".ContainerBox {background-color: #f0ffff;}") # Light cyan tint
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        header = QLabel("Create New Shot")
        header.setProperty("class", "SectionHeader")
        header.setStyleSheet("color: #339664; font-weight: bold;")
        header.setFont(QFont('Consolas', 15))
        layout.addWidget(header)

        # Sequence Input
        layout.addWidget(QLabel("Sequence #"))
        self.sequence_input = QLineEdit()
        self.sequence_input.setPlaceholderText("Enter Sequence #")
        layout.addWidget(self.sequence_input)

        # Shot Input
        layout.addWidget(QLabel("Shot #"))
        self.shot_input = QLineEdit()
        self.shot_input.setPlaceholderText("Enter Shot #)")
        layout.addWidget(self.shot_input)

        # Create Button
        self.create_button = QPushButton("Create Shot")
        self.create_button.setFont(QFont('Consolas', 10))
        self.create_button.setStyleSheet("""
            QPushButton {
                background-color: #85d5ad; 
                padding: 5px 10px;
                min-height: 10px;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: #339664;
            }
        """)
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
            QMessageBox.critical(self, "Error",
                                 "Invalid numbers — please enter integer or float values (e.g. 1 or 1.5).")
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
                delay=60000
            )
            self.sequence_input.clear()
            self.shot_input.clear()
            self.main_window.directory_viewer.refresh_tree()

            log_action(
                base_path=base_path,
                action="Create_Shot",
                details=shot_name
            )

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
        header.setStyleSheet("color: #339664; font-weight: bold;")
        header.setFont(QFont('Consolas', 15))
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
        header.setStyleSheet("color: #339664; font-weight: bold;")
        header.setFont(QFont('Consolas', 15))
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

class SftpToggle(QWidget):
    """Widget to toggle between Local and Remote SFTP publishing modes."""
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.init_ui()

    def init_ui(self):
        self.main_v_layout = QVBoxLayout(self)

        # --- BUTTONS SECTION ---
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Common styling for the toggle buttons
        btn_style = """
            QPushButton {
                background-color: #e0e0e0; 
                padding: 10px 20px;
                border-radius: 10px;
                font-weight: bold;
                min-width: 50px;
            }
            QPushButton:checked {
                background-color: #339664;
                color: white;
            }
        """

        self.local_btn = QPushButton("Local")
        self.local_btn.setCheckable(True)
        self.local_btn.setChecked(True)
        self.local_btn.setStyleSheet(btn_style)
        self.local_btn.clicked.connect(self.handle_local_click)

        self.remote_btn = QPushButton("Remote")
        self.remote_btn.setCheckable(True)
        self.remote_btn.setStyleSheet(btn_style)
        self.remote_btn.clicked.connect(self.handle_remote_click)

        button_layout.addWidget(self.local_btn)
        button_layout.addWidget(self.remote_btn)
        self.main_v_layout.addWidget(button_container)

        # --- CREDENTIALS SECTION ---
        self.credentials_widget = QWidget()
        self.cred_layout = QHBoxLayout(self.credentials_widget)

        self.host_input = QLineEdit()
        self.host_input.setPlaceholderText("Host")

        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("User")

        self.pass_input = QLineEdit()
        self.pass_input.setPlaceholderText("Pass")
        self.pass_input.setEchoMode(QLineEdit.EchoMode.Password)

        # Connect Button to trigger your remoteSetup function
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.setStyleSheet("background-color: #85d5ad; font-weight: bold;")
        self.connect_btn.clicked.connect(self.run_sftp_connection)

        self.cred_layout.addWidget(QLabel("Host:"))
        self.cred_layout.addWidget(self.host_input)
        self.cred_layout.addWidget(QLabel("Username:"))
        self.cred_layout.addWidget(self.user_input)
        self.cred_layout.addWidget(QLabel("Password:"))
        self.cred_layout.addWidget(self.pass_input)
        self.cred_layout.addWidget(self.connect_btn)

        self.credentials_widget.setVisible(False)
        self.main_v_layout.addWidget(self.credentials_widget)

    def handle_local_click(self):
        """Handler for Local mode selection."""
        self.local_btn.setChecked(True)
        self.remote_btn.setChecked(False)
        # Main Window variable to track state
        self.main_window.publish_mode = "local"
        self.credentials_widget.setVisible(False)

    def handle_remote_click(self):
        """Handler for Remote SFTP mode selection."""
        self.remote_btn.setChecked(True)
        self.local_btn.setChecked(False)
        # Main Window variable to track state
        self.main_window.publish_mode = "remote"
        self.credentials_widget.setVisible(True)


    def run_sftp_connection(self):
        """Calls the updated sftp_connect from remoteSetup.py"""
        host = self.host_input.text()
        user = self.user_input.text()
        pwd = self.pass_input.text()

        if not host or not user or not pwd:
            QMessageBox.warning(self, "Input Error", "Please fill in all SFTP fields.")
            return

        # Call your external function
        sftp_client, ssh_client = sftp_connect(host, user, pwd, 22)

        if sftp_client:
            self.main_window.show_message(f"Connected to {host}", "success")
            # Store the client in the main window for use during publishing
            self.main_window.current_sftp = sftp_client

            remote_default = "/I-Drive/Savannah/CollaborativeSpace/stonelions"
            self.main_window.path_input.setText(remote_default)
        else:
            QMessageBox.critical(self, "Connection Failed", "Could not connect to SFTP server.")


# ======================== MAIN WINDOW ========================

class JADEGui(QMainWindow):
    """Main application window, replacing the Streamlit layout."""

    def __init__(self):
        super().__init__()
        self.publish_mode = "local"
        self.base_path: Optional[Path] = None
        # set default path to I-Drive
        self.default_path = Path(r"D:\SANIKA\code\jadeTEST")
        self.setWindowTitle("JADE - Asset Organization & Delivery Pipeline")
        self.setFont(QFont('Consolas', 10))
        self.setGeometry(100, 100, 1200, 800)
        # self.setStyleSheet(QSS_THEME)
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
        self.publish_shot_form = PublishShotForm(self)

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
        title_label = QLabel("⟢JADE")
        title_label.setObjectName("titleMain")
        title_label.setStyleSheet("color: #339664; font-size: 50px;")
        title_label.setFont(QFont('Consolas'))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Description
        desc_label = QLabel("An App To Streamline USD Asset Organization & Delivery Pipeline")
        desc_label.setObjectName("titleDescription")
        desc_label.setStyleSheet("color: #2d5a3d;")
        desc_label.setFont(QFont('Consolas', 12))
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(desc_label)

        # ⭐ NEW SFTP TOGGLE SECTION ⭐
        self.sftp_toggle = SftpToggle(self)
        layout.addWidget(self.sftp_toggle)

        # Message Display Area (replaces st.success/st.info)
        self.message_label = QLabel("")
        self.message_label.setWordWrap(True)
        self.message_label.setMinimumHeight(20)
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.message_label)

        return container

    def show_message(self, text, type_name, delay=60000):
        """Display a temporary success/info message."""
        if type_name == "success":
            color = "#1a8449"  # Darker green for success
        elif type_name == "info":
            color = "#17a2b8"  # Standard info blue
        else:  # error/warning if implemented later
            color = "#dc3545"

        self.message_label.setText(text)
        # QTimer to clear the message after a delay (in milliseconds)
        from PyQt6.QtCore import QTimer
        # QTimer.singleShot(delay, lambda: self.message_label.setStyleSheet("min-height: 20px;"))
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
        browse_button.setFont(QFont('Consolas', 10))
        browse_button.setStyleSheet("""
            QPushButton {
                background-color: #85d5ad; 
                padding: 5px 10px;
                min-height: 10px;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: #339664;
            }
        """)
        layout.addWidget(browse_button)

        self.path_status_label = QLabel("")
        layout.addWidget(self.path_status_label)

        return container

    def browse_folder(self):
        """Open a file dialog to select the folder."""
        if self.publish_mode == "remote":
            if not hasattr(self, 'current_sftp') or self.current_sftp is None:
                QMessageBox.warning(self, "Not Connected", "Please connect to SFTP first to browse remote folders.")
                return

            # Since QFileDialog can't browse SFTP, you would manually input
            # or use a custom remote browser widget here.
            self.show_message("Remote mode active: Please enter the remote path manually.", "info")
        else:
            folder = QFileDialog.getExistingDirectory(self, "Select Base Assets Folder")
            if folder:
                self.path_input.setText(folder)

    def update_path_and_ui(self, path_str: str):
        """Validate path and update components for both Local and Remote modes."""
        if self.publish_mode == "remote":
            # --- REMOTE SFTP VALIDATION ---
            if not hasattr(self, 'current_sftp') or self.current_sftp is None:
                self.path_status_label.setText("Not Connected to SFTP")
                self.path_status_label.setStyleSheet("color: orange; font-weight: bold;")
                return

            try:
                # Use sftp.stat() to check if the remote directory exists
                # as_posix() ensures we use '/' which is required for SFTP/Linux paths
                self.current_sftp.stat(Path(path_str).as_posix())
                self.base_path = Path(path_str)
                self.path_status_label.setText("Remote Path OK")
                self.path_status_label.setStyleSheet("color: green; font-weight: bold;")

                # Update UI components using remote data
                self.publish_asset_form.update_asset_names()
                # Note: DirectoryViewer (QFileSystemModel) does not support SFTP
                # You may want to hide it or use a text-based view in remote mode
            except FileNotFoundError:
                self.base_path = None
                self.path_status_label.setText("Remote Path Not Found")
                self.path_status_label.setStyleSheet("color: red; font-weight: bold;")
        else:
            # --- LOCAL VALIDATION ---
            new_path = Path(path_str)
            if new_path.exists() and new_path.is_dir():
                self.base_path = new_path
                self.path_status_label.setText("Local Path OK")
                self.path_status_label.setStyleSheet("color: green; font-weight: bold;")

                self.directory_viewer.refresh_tree()
                self.publish_asset_form.update_asset_names()
            else:
                self.base_path = None
                self.path_status_label.setText("Local Path Not Found")
                self.path_status_label.setStyleSheet("color: red; font-weight: bold;")
                self.directory_viewer.refresh_tree()

    def _render_actions_panel(self):
        """Render left panel with action buttons."""
        container = QWidget()
        container.setProperty("class", "ContainerBox")
        layout = QVBoxLayout(container)

        header = QLabel("Actions")
        header.setProperty("class", "SectionHeader")

        header.setStyleSheet("color: #339664; font-weight: bold;")
        header.setFont(QFont('Consolas', 15))
        # header.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(header)

        self.publish_btn = QPushButton("Publish Asset")
        self.publish_btn.setFont(QFont('Consolas', 10))
        self.publish_btn.setStyleSheet("""
            QPushButton {
                background-color: #85d5ad; 
                padding: 5px 10px;
                min-height: 10px;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: #339664;
            }
        """)

        self.publish_shot_btn = QPushButton("Publish Shot")
        self.publish_shot_btn.setFont(QFont('Consolas', 10))
        self.publish_shot_btn.setStyleSheet("""
                    QPushButton { background-color: #85d5ad; padding: 5px 10px; min-height: 10px; border-radius: 10px; }
                    QPushButton:hover { background-color: #339664; }
                """)
        self.publish_shot_btn.clicked.connect(lambda: self._set_action("publish_shot"))
        layout.addWidget(self.publish_shot_btn)

        self.new_asset_btn = QPushButton("Create New Asset")
        self.new_asset_btn.setFont(QFont('Consolas', 10))
        self.new_asset_btn.setStyleSheet("""
            QPushButton {
                background-color: #85d5ad; 
                padding: 5px 10px;
                min-height: 10px;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: #339664;
            }
        """)

        self.create_shot_btn = QPushButton("Create New Shot")
        self.create_shot_btn.setFont(QFont('Consolas', 10))
        self.create_shot_btn.setStyleSheet("""
            QPushButton {
                background-color: #85d5ad; 
                padding: 5px 10px;
                min-height: 10px;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: #339664;
            }
        """)

        self.publish_btn.clicked.connect(lambda: self._set_action("publish_asset"))
        self.new_asset_btn.clicked.connect(lambda: self._set_action("new_asset"))
        self.create_shot_btn.clicked.connect(lambda: self._set_action("create_shot"))

        layout.addWidget(self.publish_btn)
        layout.addSpacing(15)
        layout.addWidget(self.publish_shot_btn)
        layout.addSpacing(15)
        layout.addWidget(self.new_asset_btn)
        layout.addSpacing(15)
        layout.addWidget(self.create_shot_btn)
        layout.addSpacing(15)

        layout.addStretch(1)  # Push content to the top

        return container

    def _set_action(self, action_name):
        """Set the current action and update the middle column."""
        self.selected_action = action_name

        # Determine the active button to potentially highlight it
        if action_name == "publish_asset":
            active_btn = self.publish_btn
        elif action_name == "publish_shot":
            active_btn = self.publish_shot_btn
        elif action_name == "new_asset":
            active_btn = self.new_asset_btn
        elif action_name == "create_shot":
            active_btn = self.create_shot_btn
        else:
            # This safety check ensures we don't try to run an undefined action
            raise Exception(f"Invalid action: {action_name}")

        # Refresh the UI to show the correct form in the middle column
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
        elif self.selected_action == "publish_shot":  # New Action
            self.forms_container.addWidget(self.publish_shot_form)
            self.publish_shot_form.refresh_shots()
        elif self.selected_action == "create_shot":
            self.forms_container.addWidget(self.create_shot_form)


# ======================== MAIN APPLICATION ENTRY POINT ========================

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Initialize the main UI
    window = JADEGui()
    window.show()

    sys.exit(app.exec())