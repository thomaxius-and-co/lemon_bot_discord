def parse(input, prefix="!"):
    if not input.startswith(prefix):
        return None, None
    cmd, *arg = input.strip(prefix).split(' ', 1)
    return cmd.lower(), arg[0] if arg else None
