import requests
import time

from functools import wraps
from enum import Enum

EXCEPTIONS_TO_CATCH = (ConnectionError, TimeoutError, requests.exceptions.HTTPError, requests.exceptions.Timeout)

def retry(retries=3, backoff=2, backoff_factor=2):
    def retry_decorator(f):
        @wraps(f)
        def retry_f(*args, **kwargs):
            nonlocal retries
            nonlocal backoff
            last_exc = None
            while retries > 1:
                last_exc = None
                try:
                    return f(*args, **kwargs)
                except EXCEPTIONS_TO_CATCH as e:
                    last_exc = e
                    print(f"Err: {e}, retrying {retries} more times in {backoff} seconds")
                    time.sleep(backoff)
                    retries -= 1
                    backoff *= backoff_factor

            if last_exc:
                raise last_exc
                
            return last_exc
        return retry_f
    return retry_decorator


# TODO exc carryover bug
# @retry()
def make_request(method, url, data=None, json=None, params=None, headers=None, timeout=5):
    r = requests.request(method, url, data=data, json=json, params=params, headers=headers)
    if r.status_code != 200:
        raise requests.exceptions.HTTPError(r.text)

    return r.json()
        
