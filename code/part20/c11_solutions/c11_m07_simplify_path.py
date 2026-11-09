"""M7: canonical absolute path."""


def simplify_path(path):
    """'/a//b/./c/../d/' -> '/a/b/d'. '..' at the root stays at the root."""
    stack = []
    for part in path.split("/"):
        if part in ("", "."):
            continue
        if part == "..":
            if stack:
                stack.pop()
        else:
            stack.append(part)
    return "/" + "/".join(stack)
