def make_query_string(params):
    if params is None:
        return ""
    if len(params.items()) == 0:
        return ""
    return "?" + "&".join(map("=".join, params.items()))
