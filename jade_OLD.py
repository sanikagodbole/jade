# JADE - A USD Centric Pipeline App

import os
import re
import tkinter as tk
from tkinter import ttk, messagebox
import shutil
import time

###### Root folders ######
ROOT_FOLDER = r"I:\Savannah\CollaborativeSpace\stonelions\prod\assets\working"
Asset_Publish_Folder = r"I:\Savannah\CollaborativeSpace\stonelions\prod\assets\publish"
DEPARTMENTS = ["geo", "rig", "tex"]

##### GEO PUBLSH #####
def publish_geo(working_path, publish_path, category, asset, dept):
    list = []
    latest_file = None
    latest_version = -1
    latest_files = {}

    # Find latest version of USD files
    for root, dirs, files in os.walk(working_path):
        for f in files:
            if f.endswith(".usd") and "_v" in f:
                version_str = f.split("_v")[-1].split(".")[0]
                version = int(version_str)
                geo_base = re.sub(r"_[A-Za-z]{2}_v\d+$", "", os.path.splitext(f)[0])

                if geo_base not in latest_files or version > latest_files[geo_base]['version']:
                    latest_files[geo_base] = {
                        'latest_file': os.path.join(working_path, dept, f),
                        'version': version
                    }
    # publish_folder = os.path.join(publish_path, "geo")
    # os.makedirs(publish_folder, exist_ok=True)
    print(latest_file)
    print("working", working_path)
    for geo_base, info in latest_files.items():
        latest_file = info['latest_file']
        latest_version = info['version']

        file_base = os.path.splitext(os.path.basename(latest_file))[0]
        publish_file_base = re.sub(r"_[A-Za-z]{2}_v\d+$", "", file_base)
        usd_geo = os.path.join(working_path, dept, f"{publish_file_base}.usd")
        export_folder = os.path.join(working_path,"export", dept)
        print(usd_geo)
        print(export_folder)
        shutil.copy2(latest_file,usd_geo)
        # shutil.copy2(usd_geo, export_folder)


##### TEXTURE PUBLISH #####
def publish_tex(working_path, publish_path, category, asset, dept):
    latest_version = -1
    latest_tex_folder = None
    for d in os.listdir(working_path):
        tex_folder_path = os.path.join(working_path, d)
        if os.path.isdir(tex_folder_path) and d.lower().startswith("v"):
            version_num = int(d[1:]) 

            if version_num > latest_version:
                latest_version = version_num
                latest_tex_folder = tex_folder_path

    publish_folder = os.path.join(publish_path, "tex")
    folder_rename = os.path.join(working_path, f"{asset}_tex")
    os.makedirs(folder_rename, exist_ok=True)
    for root, _, files in os.walk(latest_tex_folder):
        for f in files:
            texture_rename = re.sub(r"_v\d+", "", f)
            if texture_rename != f:
                old_path = os.path.join(root, f)
                new_path = os.path.join(publish_folder, texture_rename)
                shutil.copy2(old_path, new_path)
                shutil.copy2(old_path, folder_rename)


##### RIG PUBLSH #####
def publish_rig(working_path, publish_path, category, asset, dept):
    list = []
    latest_rig = None
    latest_rig_version = -1
    for (root, dirs, file) in os.walk(working_path):
        for f in file:
            if f.endswith(".mb") and "_v" in f:
                version_str = f.split("_v")[-1].split(".")[0]
                version = int(version_str)
                if version > latest_rig_version:
                    latest_rig_version = version
                    latest_rig = os.path.join(working_path, f)

    rig_index = f.find("rig")
    if rig_index != -1:
        latest_rig_copy = f[:rig_index + 3] + ".mb"
    else:
        latest_rig_copy = f 
    latest_rig_copy = os.path.join(working_path, latest_rig_copy)
    shutil.copy2(latest_rig, latest_rig_copy)
    publish_folder = os.path.join(publish_path,"rig")
    shutil.copy2(latest_rig_copy, publish_folder)

########## GUI ###########
def GUI():
    def update_assets(event=None):
        category = combo_category.get()
        path = os.path.join(ROOT_FOLDER,category)
        assets = []
        if os.path.exists(path):
            assets = [f for f in os.listdir(path) if os.path.isdir(os.path.join(path, f))]
        
        combo_asset["values"] = assets
        if assets:
            combo_asset.current(0)
        else:
            combo_asset.set('')  

    def publish():
        category = combo_category.get()
        asset = combo_asset.get()
        dept = combo_dept.get()

        working_path = os.path.join(ROOT_FOLDER, category, asset)
        publish_path = os.path.join(Asset_Publish_Folder, category)

        if dept == "geo":
            publish_geo(working_path, publish_path, category, asset, dept)
            messagebox.showinfo("Publish Complete", f"Published {dept} for {asset}")

        if dept == "tex":
            publish_tex(working_path, publish_path, category, asset, dept)
            messagebox.showinfo("Publish Complete", f"Published {dept} for {asset}")

        if dept == "rig":
            publish_rig(working_path, publish_path, category, asset, dept)
            messagebox.showinfo("Publish Complete", f"Published {dept} for {asset}")


    #### GUI UI ####
    root = tk.Tk()
    root.title("Stone Lions Pipeline")
    root.geometry("400x400")  

    tk.Label(root, text="JADE", fg="#325732", font=("Century", 36)).pack(pady=0)

    tk.Label(root, text="Select Category:", fg="#325732", font=("Arial", 12)).pack(pady=5)
    combo_category = ttk.Combobox(root, values=["char", "prop", "set"], state="readonly", font=("Arial", 11))
    combo_category.pack(pady=5)
    combo_category.bind("<<ComboboxSelected>>", update_assets)

    tk.Label(root, text="Select Asset:",fg="#325732", font=("Arial", 12)).pack(pady=5)
    combo_asset = ttk.Combobox(root, state="readonly", font=("Arial", 11))
    combo_asset.pack(pady=5)

    tk.Label(root, text="Select Department:",fg="#325732", font=("Arial", 12)).pack(pady=5)
    combo_dept = ttk.Combobox(root, values=DEPARTMENTS, state="readonly", font=("Arial", 11))
    combo_dept.pack(pady=5)
    combo_dept.current(0)

    publish_btn = tk.Button(root, text="Publish", command=publish, font=("Arial", 14), bg="#325732", fg="white")
    publish_btn.pack(pady=20)

    root.mainloop()

GUI()