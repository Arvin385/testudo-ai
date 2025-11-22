from typing import Callable
import inspect
from add_numbers import add_numbers

if __name__ == "__main__":
    source_code = inspect.getsource(add_numbers)
    print(source_code)
    print(add_numbers.__doc__)
    
    signature = inspect.signature(add_numbers)
    print(signature)

    for param in signature.parameters.values():
        print(f"Parameter: {param.name}, Default: {param.default}, Kind: {param.kind}")
        print(f"Has default: {param.default != inspect._empty}")