# actions/<action_name>.py


def run(args):
    """
    Description of what this action does.
    Expects args = { "param": "type" }
    """

    # 1. Validate args
    value = args.get("param")
    if not value:
        raise ValueError("Missing required argument: param")

    # 2. Optional security checks
    forbidden = ["bad", "dangerous", "nope"]
    if any(x in value for x in forbidden):
        raise PermissionError("This operation is not allowed")

    # 3. Do the thing
    result = f"Did something with {value}"

    # 4. Return plain text
    return result
