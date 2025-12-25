import os
import webbrowser


def run(args):
    """
    Opens a folder in the default file explorer.
    Expects args = {"path": "C:\\Users\\Ayoub\\Desktop"} (Windows paths)
    """

    path = args.get("path")
    if not path:
        raise ValueError("No path provided")

    # Normalize and absolute path
    abs_path = os.path.abspath(path)

    # Security check: prevent access outside your user folder
    user_folder = os.path.expanduser("~")
    if not abs_path.startswith(user_folder):
        raise PermissionError("Access to this path is not allowed")

    if not os.path.exists(abs_path):
        raise FileNotFoundError(f"Path does not exist: {abs_path}")

    # Open folder in default file explorer
    webbrowser.open(f"file:///{abs_path.replace(os.sep, '/')}")
