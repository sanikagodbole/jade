# new asset folder script

import os
import tkinter as tk
from tkinter import ttk, messagebox

ROOT_FOLDER = r"I:\Savannah\CollaborativeSpace\stonelions\prod"
Publish_Folder = r"I:\Savannah\CollaborativeSpace\stonelions\prod\asset_publish"

# GUI setup
root = tk.Tk()
root.title("New Asset Folder")
root.geometry("300x250")

tk.Label(root, text="New Asset Folder", fg="#325732", font=("Century", 20)).pack(pady=0)

tk.Label(root, text="Select Category:", fg="#325732", font=("Arial", 12)).pack(pady=5)
category_op = ttk.Combobox(root, values=["char", "prop", "set"], state="readonly", font=("Arial", 11))
category_op.current(0)
category_op.pack(pady=5)

tk.Label(root, text="Enter New Asset Name (camelCase):" , fg="#325732", font=("Arial", 12)).pack(pady=5)
entry_widget = tk.Entry(root, font=("Arial", 11))
entry_widget.pack(pady=5)

def create_folder_structure():
    user_input = entry_widget.get().strip()
    category = category_op.get().strip()

    # Build path
    new_folder = os.path.join(ROOT_FOLDER, category, user_input)
    publish = os.path.join(Publish_Folder, category, user_input)

    if os.path.exists(new_folder):
        messagebox.showinfo("Exists", f"Folder already exists:\n{new_folder}")
        return
    
    if category == "char":
        os.makedirs(os.path.join(new_folder), exist_ok=True)
        for dept in ["model_dev", "tex_dev", "rig_dev"]:
            os.makedirs(os.path.join(new_folder,dept), exist_ok=True)

        for pub in ["model", "tex", "rig"]:
            os.makedirs(os.path.join(publish, pub), exist_ok=True)
    
    else:
        os.makedirs(os.path.join(new_folder), exist_ok=True)
        for dept in ["model_dev", "tex_dev"]:
            os.makedirs(os.path.join(new_folder,dept), exist_ok=True)

        for pub in ["model", "tex"]:
            os.makedirs(os.path.join(publish, pub), exist_ok=True)      

    messagebox.showinfo("Success", f"Created Folder Structure for:\n{user_input}")
    print(f"Created structure under {new_folder}")

submit_button = tk.Button(root, text="Create Folder Structure", command=create_folder_structure)
submit_button.pack(pady=10)

root.mainloop()
