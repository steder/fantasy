import functools
import json
import os


def memoize_to_disk(func):
    @functools.wraps(func)
    def wrapper(*args):
        data_path = "_".join([str(a) for a in args]) + ".data"

        if os.path.exists(data_path):
            with open(data_path, "r") as f:
                data = json.load(f)
        else:
            data = func(*args)
            with open(data_path, "w") as f:
                json.dump(data, f)

        return data

    return wrapper
