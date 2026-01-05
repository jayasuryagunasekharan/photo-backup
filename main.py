import subprocess
import tempfile
import os
import threading
import queue
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk


def copy_iphone_internal_storage(destination):
    ps_script = f"""
$shell = New-Object -ComObject Shell.Application
$thisPC = $shell.Namespace(17)

$iphone = $thisPC.Items() | Where-Object {{ $_.Name -like "*iPhone*" }} | Select-Object -First 1
if (-not $iphone) {{
    Write-Error "iPhone not detected. Please connect and unlock your iPhone."
    exit 1
}}

$folder = $iphone.GetFolder()
if (-not $folder) {{
    Write-Error "Unable to access iPhone folder object."
    exit 1
}}

$internal = $folder.Items() | Where-Object {{ $_.Name -eq "Internal Storage" }} | Select-Object -First 1
if (-not $internal) {{
    Write-Error "Internal Storage not accessible."
    exit 1
}}

$dest = "{destination}"
New-Item -ItemType Directory -Force -Path $dest | Out-Null

$destPath = (Get-Item -LiteralPath $dest).FullName
$destFolder = $shell.Namespace($destPath)
if (-not $destFolder) {{
    Write-Error "Destination namespace not found: $destPath"
    exit 1
}}

foreach ($item in $internal.GetFolder().Items()) {{
    $destFolder.CopyHere($item, 16)
}}
"""

    with tempfile.NamedTemporaryFile(delete=False, suffix=".ps1", mode="w") as f:
        f.write(ps_script)
        ps_file = f.name

    try:
        run_powershell_with_progress(ps_file)
    finally:
        os.remove(ps_file)


def run_powershell_with_progress(ps_file):
    creationflags = 0
    if os.name == 'nt':
        # Hide the child PowerShell window on Windows
        creationflags = subprocess.CREATE_NO_WINDOW

    proc = subprocess.Popen(
        ["powershell", "-ExecutionPolicy", "Bypass", "-File", ps_file],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        creationflags=creationflags
    )

    q = queue.Queue()

    def reader_thread(stream, name):
        for line in iter(stream.readline, ""):
            q.put((name, line.rstrip()))
        stream.close()

    t_out = threading.Thread(target=reader_thread, args=(proc.stdout, "out"), daemon=True)
    t_err = threading.Thread(target=reader_thread, args=(proc.stderr, "err"), daemon=True)
    t_out.start()
    t_err.start()

    # Create a transient progress window
    win = tk.Toplevel()
    win.title("Copy Progress")
    win.geometry("480x140")
    win.resizable(False, False)

    tk.Label(win, text="Copying from iPhone", font=("Segoe UI", 12, "bold")).pack(pady=(10, 5))
    progress = ttk.Progressbar(win, orient="horizontal", length=440, mode="determinate")
    progress.pack(pady=5)
    status_lbl = tk.Label(win, text="Preparing...", anchor="w")
    status_lbl.pack(fill="x", padx=10)

    total = 0
    current = 0

    def poll_queue():
        nonlocal total, current
        try:
            while True:
                kind, line = q.get_nowait()
                if kind == "out" and line.startswith("PROGRESS:"):
                    # expected format: PROGRESS:i:total:name
                    parts = line.split(":", 3)
                    if len(parts) >= 4:
                        _, i_str, total_str, name = parts
                        try:
                            current = int(i_str)
                            total = int(total_str)
                        except ValueError:
                            pass
                        if total > 0:
                            progress["maximum"] = total
                            progress["value"] = current
                            pct = int((current / total) * 100)
                            status_lbl.config(text=f"{current} of {total} — {pct}% — {name}")
                elif kind == "out":
                    # other stdout lines show as status
                    status_lbl.config(text=line)
                elif kind == "err":
                    status_lbl.config(text=f"ERROR: {line}")
        except queue.Empty:
            pass

        if proc.poll() is None:
            win.after(100, poll_queue)
        else:
            # drain remaining
            try:
                while True:
                    kind, line = q.get_nowait()
                    if kind == "out" and line.startswith("PROGRESS:"):
                        parts = line.split(":", 3)
                        if len(parts) >= 4:
                            _, i_str, total_str, name = parts
                            try:
                                current = int(i_str)
                                total = int(total_str)
                            except ValueError:
                                pass
                            if total > 0:
                                progress["maximum"] = total
                                progress["value"] = current
                                pct = int((current / total) * 100)
                                status_lbl.config(text=f"{current} of {total} — {pct}% — {name}")
                    elif kind == "out":
                        status_lbl.config(text=line)
                    elif kind == "err":
                        status_lbl.config(text=f"ERROR: {line}")
            except queue.Empty:
                pass

            win.after(500, win.destroy)

    # start polling
    win.after(100, poll_queue)

    # block until window is closed (which happens after process exit)
    win.transient()
    win.grab_set()
    win.wait_window()

    retcode = proc.wait()
    if retcode != 0:
        # collect stderr
        _, stderr = proc.communicate()
        raise subprocess.CalledProcessError(returncode=retcode, cmd=proc.args, output=None, stderr=stderr)


def start_copy():
    dest = filedialog.askdirectory(title="Select destination folder")
    if not dest:
        return

    try:
        messagebox.showinfo(
            "Instructions",
            "Please ensure:\n\n"
            "• iPhone is connected\n"
            "• iPhone is UNLOCKED\n"
            "• You tapped 'Trust This Computer'\n\n"
            "Click OK to begin."
        )
        copy_iphone_internal_storage(dest)
        messagebox.showinfo("Success", "Copy completed successfully!")
    except subprocess.CalledProcessError:
        messagebox.showerror(
            "Error",
            "Copy failed.\nMake sure your iPhone stays unlocked."
        )
    except Exception as e:
        messagebox.showerror("Error", str(e))


root = tk.Tk()
root.title("iPhone Media Copier")
root.geometry("420x240")
root.resizable(False, False)

tk.Label(root, text="iPhone Media Copier", font=("Segoe UI", 16, "bold")).pack(pady=20)
tk.Button(root, text="Start Copy", command=start_copy, height=2, width=25).pack(pady=30)

root.mainloop()
