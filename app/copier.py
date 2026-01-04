import os
try:
    from win32com.client import Dispatch
except Exception:
    Dispatch = None


def copy_iphone_media(destination: str):
    """Simple copier: copy everything under iPhone -> Internal Storage to `destination`.

    Mirrors the PowerShell script: uses Shell.Application and CopyHere for each item.
    Raises RuntimeError on failure. Requires pywin32 (`pip install pywin32`).
    """
    if Dispatch is None:
        raise RuntimeError("pywin32 is required. Install with: pip install pywin32")

    shell = Dispatch("Shell.Application")
    thisPC = shell.Namespace(17)

    # helper to list connected devices (for diagnostic messages)
    def _list_device_names():
        names = []
        try:
            for d in thisPC.Items():
                try:
                    names.append(str(d.Name))
                except Exception:
                    names.append('<unknown>')
        except Exception:
            pass
        return names

    # Try to find the iPhone device with retries (device may take time to enumerate)
    iphone = None
    for attempt in range(6):
        try:
            for dev in thisPC.Items():
                try:
                    nm = str(dev.Name).lower()
                except Exception:
                    nm = ''
                if 'iphone' in nm or 'apple' in nm and 'phone' in nm:
                    iphone = dev
                    break
        except Exception:
            iphone = None

        if iphone is not None:
            break
        import time
        time.sleep(1)

    if iphone is None:
        available = _list_device_names()
        raise RuntimeError(
            "iPhone not detected. Ensure it's unlocked and trusted.\n"
            f"Available devices: {available}"
        )

    # find Internal Storage (try several heuristics and retries)
    internal = None
    for attempt in range(6):
        try:
            try:
                folder = iphone.GetFolder()
            except Exception:
                folder = None

            if folder is not None:
                for it in folder.Items():
                    try:
                        name = str(it.Name)
                    except Exception:
                        name = ''
                    if name.lower() == 'internal storage' or 'internal' in name.lower():
                        internal = it
                        break
                # if still not found, maybe DCIM is directly under folder
                if internal is None:
                    for it in folder.Items():
                        try:
                            # check if this child has a DCIM folder
                            sub = None
                            try:
                                sub = it.GetFolder()
                            except Exception:
                                sub = None
                            if sub is None:
                                continue
                            for s in sub.Items():
                                try:
                                    if str(s.Name).lower() == 'dcim':
                                        internal = it
                                        break
                                except Exception:
                                    continue
                            if internal is not None:
                                break
                        except Exception:
                            continue
        except Exception:
            internal = None

        if internal is not None:
            break
        import time
        time.sleep(1)

    if internal is None:
        # provide diagnostic children list to help debugging
        children = []
        try:
            for it in iphone.GetFolder().Items():
                try:
                    children.append(str(it.Name))
                except Exception:
                    children.append('<unknown>')
        except Exception:
            pass
        raise RuntimeError(
            "Internal Storage not accessible. Confirm the phone is unlocked and trusted.\n"
            f"Device children: {children}"
        )

    # ensure destination exists
    os.makedirs(destination, exist_ok=True)
    dest_ns = shell.Namespace(os.path.abspath(destination))
    if not dest_ns:
        raise RuntimeError(f"Destination folder not accessible via Shell Namespace: {destination}")

    # Copy EVERYTHING under Internal Storage
    for item in internal.GetFolder().Items():
        dest_ns.CopyHere(item, 16)

