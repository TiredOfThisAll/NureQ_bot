import unittest
import pkgutil

import tests

for submodule in pkgutil.iter_modules(tests.__path__):
    submodule_full_name = f"{tests.__name__}.{submodule.name}"
    exec(f"from {submodule_full_name} import *")

unittest.main()
