import inspect

from functools import wraps
from typing import Any


def _get_function_params_values_dict(func, args: tuple, kwargs: dict) -> dict:
    params = list(inspect.signature(func).parameters)
    result = {}
    for param in tuple(params):
        if param in kwargs:
            result[param] = kwargs[param]
            params.remove(param)
    if params:
        for i, param in enumerate(params):
            result[param] = args[i]
    return result


def cache_by_params(*kw_params: str):
    """
    cache_by_params кеширует вызов вашей функции по выбранным примитивным параметрам

    @cache_by_params('a', 'b')
    def function(a, b, c):
        ...

    function(1, 2, 3) # не кешированный вызов функции
    function(1, 2, 4) # вернёт результат из кеша

    :param kw_params: список названий параметров
    :return:
    """
    def decorator(user_function):
        cache: dict = {}

        @wraps(user_function)
        def func_wrapper(*args, **kwargs) -> Any:
            params_values = _get_function_params_values_dict(user_function, args, kwargs)
            cache_key = list()
            for kw in kw_params:
                cache_key.append(params_values[kw])
            cache_key = tuple(cache_key)
            if cached_result := cache.get(cache_key, False):
                return cached_result
            result = user_function(*args, **kwargs)
            cache[cache_key] = result
            return result

        return func_wrapper

    return decorator
