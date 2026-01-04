import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox

# Simple GUI that mirrors the PowerShell script behavior
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    from app.copier import copy_iphone_media
except Exception:
    try:
        from .copier import copy_iphone_media
    except Exception:
        from copier import copy_iphone_media

DEFAULT_DEST = r"C:\IphoneBackUp"


def select_folder():
    path = filedialog.askdirectory(title="Select destination folder")
    if path:
        dest_var.set(path)


def start_copy():
    dest = dest_var.get().strip() or DEFAULT_DEST
    if not dest:
        messagebox.showerror("Error", "No destination selected")
        return

    try:
        messagebox.showinfo(
            "Instructions",
            "Please ensure:\n\n"
            "• iPhone is connected via cable\n"
            "• iPhone is unlocked\n"
            "• You tapped 'Trust This Computer'\n\n"
            "Click OK to start copying."
        )

        # perform copy (blocking, simple)
        copy_iphone_media(dest)
        messagebox.showinfo("Success", f"Photos and videos copied to {dest}")
    except Exception as e:
        messagebox.showerror("Error", str(e))


root = tk.Tk()
root.title("iPhone Media Copier")
root.geometry("480x150")
root.resizable(False, False)

tk.Label(root, text="iPhone Media Copier", font=("Segoe UI", 14, "bold")).pack(pady=8)

tk.Label(root, text="Copy everything from iPhone Internal Storage to destination").pack()

# Destination row
frame = tk.Frame(root)
frame.pack(pady=8, fill="x", padx=12)
tk.Label(frame, text="Destination:").pack(side="left")
dest_var = tk.StringVar(value=DEFAULT_DEST)
entry = tk.Entry(frame, textvariable=dest_var, width=40)
entry.pack(side="left", padx=6)
tk.Button(frame, text="Browse...", command=select_folder).pack(side="left")

tk.Button(root, text="Start Copy", command=start_copy, height=2, width=20).pack(pady=8)

root.mainloop()
