# tools/__init__.py
import importlib
import pkgutil

tool_registry = {}
# messages = []

# dynamically import all modules in tools folder
for _, module_name, _ in pkgutil.iter_modules(__path__):
    module = importlib.import_module(f"{__name__}.{module_name}")
    if hasattr(module, "TOOL_SPEC"):
        tool_spec = module.TOOL_SPEC
        # Case 1: It's a list!
        if isinstance(tool_spec, list):
            # Loop through the available specs
            for spec in tool_spec:
                # If the spec has a name,
                if hasattr(module, spec["name"]):
                    # Extract the name, register the tool
                    tool_name = spec["name"]
                    tool_registry[tool_name] = {
                        "spec": spec,
                        "func": getattr(module, tool_name)
                    }
        # Case 2: It's a dict!
        elif isinstance(tool_spec, dict):
            # If the spec has a name,
            if hasattr(module, tool_spec["name"]):
                # Extract the name, register the tool
                tool_name = tool_spec["name"]
                tool_registry[tool_name] = {
                    "spec": tool_spec,
                    "func": getattr(module, tool_name)
                }
