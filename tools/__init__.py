# tools/__init__.py
import importlib
import pkgutil

tool_registry = {}

# dynamically import all modules in tools folder
for _, module_name, _ in pkgutil.iter_modules(__path__):
    module = importlib.import_module(f"{__name__}.{module_name}")
    if hasattr(module, "TOOL_SPEC") and hasattr(module, module.TOOL_SPEC["name"]):
        tool_name = module.TOOL_SPEC["name"]
        tool_registry[tool_name] = {
            "spec": module.TOOL_SPEC,
            "func": getattr(module, tool_name)
        }
