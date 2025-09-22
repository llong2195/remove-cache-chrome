import os
import shutil
import tkinter as tk
from tkinter import filedialog, ttk, messagebox

# ✅ Chỉ giữ cache folder có thể xóa an toàn
CACHE_FOLDERS = [
    "Cache",
    "Code Cache",
    "GPUCache",
    "Media Cache",
    "IndexedDB",
    "blob_storage",
    os.path.join("Service Worker", "CacheStorage"),
]

def get_folder_size(path):
    """Tính dung lượng folder (MB)"""
    total_size = 0
    for dirpath, _, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if os.path.isfile(fp):
                try:
                    total_size += os.path.getsize(fp)
                except PermissionError:
                    pass
    return round(total_size / (1024 * 1024), 2)  # MB

def scan_profiles(base_path):
    """Trả về cấu trúc {instance: {profile: {cache_folder: size}}}"""
    data = {}
    for instance in os.listdir(base_path):
        inst_path = os.path.join(base_path, instance)
        if not os.path.isdir(inst_path):
            continue
        profiles_data = {}
        for profile in os.listdir(inst_path):
            profile_path = os.path.join(inst_path, profile)
            if not os.path.isdir(profile_path):
                continue
            caches_data = {}
            for cf in CACHE_FOLDERS:
                cf_path = os.path.join(profile_path, cf)
                if os.path.exists(cf_path):
                    size = get_folder_size(cf_path)
                    caches_data[cf] = size
            if caches_data:  # chỉ thêm profile nếu có folder cache
                profiles_data[profile] = caches_data
        if profiles_data:  # chỉ thêm instance nếu có profile hợp lệ
            data[instance] = profiles_data
    return data

def clear_cache_folder(base_path, instance, profile, folder):
    """Xóa 1 folder cache"""
    target = os.path.join(base_path, instance, profile, folder)
    if os.path.exists(target):
        shutil.rmtree(target, ignore_errors=True)
        return True
    return False

def clear_profile(base_path, instance, profile):
    """Xóa toàn bộ cache trong 1 profile"""
    count = 0
    for cf in CACHE_FOLDERS:
        if clear_cache_folder(base_path, instance, profile, cf):
            count += 1
    return count

def clear_instance(base_path, instance):
    """Xóa toàn bộ cache trong 1 instance"""
    count = 0
    profiles = data.get(instance, {})
    for profile in profiles.keys():
        count += clear_profile(base_path, instance, profile)
    return count

def select_root_folder():
    folder = filedialog.askdirectory(title="Select Chrome root folder")
    if folder:
        load_tree(folder)

def load_tree(folder):
    global root_path, data
    root_path = folder
    tree.delete(*tree.get_children())

    data = scan_profiles(folder)

    for inst, profiles in data.items():
        inst_id = tree.insert("", "end", text=f"{inst}", values=("",))
        for prof, caches in profiles.items():
            prof_id = tree.insert(inst_id, "end", text=prof, values=("",))
            for cf, size in caches.items():
                tree.insert(prof_id, "end", text=cf, values=(f"{size} MB",))

def clear_selected():
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("Warning", "Please select something to clear.")
        return

    total = 0
    for sel in selected:
        parent1 = tree.parent(sel)
        parent2 = tree.parent(parent1)

        if parent2:  # inst -> prof -> folder
            inst = tree.item(parent2)["text"]
            prof = tree.item(parent1)["text"]
            folder = tree.item(sel)["text"]
            if clear_cache_folder(root_path, inst, prof, folder):
                total += 1
                tree.item(sel, values=("0 MB",))

        elif parent1:  # inst -> prof
            inst = tree.item(parent1)["text"]
            prof = tree.item(sel)["text"]
            cleared = clear_profile(root_path, inst, prof)
            total += cleared
            # cập nhật tree view
            for child in tree.get_children(sel):
                tree.item(child, values=("0 MB",))

        else:  # instance
            inst = tree.item(sel)["text"]
            cleared = clear_instance(root_path, inst)
            total += cleared
            # cập nhật tree view
            for prof in tree.get_children(sel):
                for child in tree.get_children(prof):
                    tree.item(child, values=("0 MB",))

    messagebox.showinfo("Done", f"Cleared {total} cache folders.")

# --- GUI ---
root = tk.Tk()
root.title("Chrome Cache Cleaner")

tk.Button(root, text="Select Root Folder", command=select_root_folder).pack(pady=5, fill="x")

tree = ttk.Treeview(root, columns=("Size",), show="tree headings")
tree.heading("#0", text="Folder")
tree.heading("Size", text="Size")
tree.pack(fill="both", expand=True, padx=10, pady=5)

tk.Button(root, text="Clear Selected", command=clear_selected, bg="lightcoral").pack(pady=5, fill="x")

root_path = ""
data = {}

root.mainloop()
