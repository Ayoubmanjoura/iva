# actions/create_automation.py

import os
import re
from datetime import datetime

AUTOMATIONS_FOLDER = "D:/Projects/iva/.iva/automations"


def run(args):
    """
    Creates a new automation script file.
    Expects args = {
        "name": "automation_name.py",
        "script": "full python script as a string"
    }
    """

    name = args.get("name")
    script = args.get("script")

    if not name or not script:
        raise ValueError("Both 'name' and 'script' arguments are required")

    # ensure folder exists
    os.makedirs(AUTOMATIONS_FOLDER, exist_ok=True)

    # validate filename (only letters, numbers, underscores, hyphens, .py)
    if not re.match(r"^[\w\-_]+\.py$", name):
        raise ValueError(
            "Invalid filename. Use letters, numbers, underscores, hyphens, ending with .py"
        )

    file_path = os.path.join(AUTOMATIONS_FOLDER, name)

    # optional: backup existing file
    if os.path.exists(file_path):
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        backup_path = file_path.replace(".py", f"_{timestamp}.bak.py")
        os.rename(file_path, backup_path)

    # write the script
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(script)

    return f"Automation '{name}' created successfully!"
