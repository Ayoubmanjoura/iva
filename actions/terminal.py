import os
import subprocess

def run(args):
    """
    Runs a PowerShell command in the terminal.
    Expects args = {"command": "Get-Process"}
    """

    command = args.get("command")
    if not command:
        raise ValueError("No command provided")

    # Security check: prevent execution of dangerous commands
    forbidden_keywords = ["Remove-Item", "Stop-Process", "Set-ExecutionPolicy"]
    if any(keyword in command for keyword in forbidden_keywords):
        raise PermissionError("Execution of this command is not allowed")

    # Execute the PowerShell command
    process = subprocess.Popen(
        ["powershell", "-Command", command],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    stdout, stderr = process.communicate()

    if process.returncode != 0:
        raise RuntimeError(f"Command failed with error: {stderr.strip()}")

    return stdout.strip()