def make_query_string(params):
    return "?" + "&".join(map("=".join, params.items()))
