from functools import wraps
from typing import Callable

_api_key_middlewares: list[Callable[str,str]] = []


def api_key_middleware(func: Callable[str,str]) -> Callable[str,str]:
    _api_key_middlewares.append(func)
    return func


def apply_api_key_middleware(api_key: str) -> str:
    result: str = api_key 
    
    for akm in _api_key_middlewares:
        result = akm(result)

    return result