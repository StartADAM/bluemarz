from functools import wraps

_api_key_middlewares: list[function] = []


@wraps
def api_key_middleware(func: function) -> function:
    _api_key_middlewares.append(func)
    return func

def apply_api_key_middleware(api_key: str) -> str:
    result: str = api_key 
    
    for akm in _api_key_middlewares:
        result = akm(result)

    return result