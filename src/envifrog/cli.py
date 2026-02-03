import sys
import os
import argparse
import inspect
import importlib.util
from typing import Type
from .base import BaseConfig
from .fields import Var

def import_config_class(file_path: str, class_name: str) -> Type[BaseConfig]:
    """Dynamically import a class from a python file."""
    # Add file directory to sys.path to allow relative imports inside that file
    file_dir = os.path.dirname(os.path.abspath(file_path))
    if file_dir not in sys.path:
        sys.path.insert(0, file_dir)
        
    spec = importlib.util.spec_from_file_location("config_module", file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load file: {file_path}")
    
    module = importlib.util.module_from_spec(spec)
    sys.modules["config_module"] = module
    spec.loader.exec_module(module)
    
    if not hasattr(module, class_name):
        raise AttributeError(f"Class {class_name} not found in {file_path}")
        
    cls = getattr(module, class_name)
    if not issubclass(cls, BaseConfig):
        raise TypeError(f"{class_name} must be a subclass of BaseConfig")
        
    return cls

def generate_example(args):
    """Generate .env.example file."""
    try:
        cls = import_config_class(args.file, args.class_name)
    except Exception as e:
        print(f"Error importing class: {e}")
        sys.exit(1)
    
    output_lines = []
    
    # Simple introspection of Var fields
    # We need to handle nested configs too?
    # For now, flat listing might be enough or we recurse?
    # .env files are flat, so nested config variables (like DB_HOST) should be listed flattened.
    
    # We need to instantiate it? No, we inspect annotations and Var defaults.
    # But nested config logic is in __init__.
    # To get full list of expected keys with prefixes, we might need to instantiate or simulate it.
    # Simulating is better.
    
    def _recurse_vars(cls: Type[BaseConfig], prefix: str = "") -> list[str]:
        lines = []
        
        # Get hints
        hints = {}
        try:
            hints = inspect.get_type_hints(cls)
        except Exception:
            hints = cls.__annotations__
            
        for name, _type in hints.items():
            if name.startswith('_'): continue
            
            field_val = getattr(cls, name, Var(default=...))
            if not isinstance(field_val, Var):
                field_val = Var(default=field_val)
                
            effective_prefix = prefix
            if field_val.prefix:
                effective_prefix += field_val.prefix
            
            # Check for Nested
            origin = getattr(_type, '__origin__', None)
            args_type = getattr(_type, '__args__', [])
            target_cls = _type
            if origin:
               non_none = [a for a in args_type if a is not type(None)]
               if non_none: target_cls = non_none[0]
               
            if isinstance(target_cls, type) and issubclass(target_cls, BaseConfig):
                # Recurse
                lines.append(f"\n# --- {name} Configuration ---")
                lines.extend(_recurse_vars(target_cls, effective_prefix))
                continue
            
            # Regular field
            full_name = effective_prefix + name
            default_val = field_val.default
            
            comment = ""
            if field_val.default is ...:
                comment = "  # Required"
                val_str = ""
            else:
                val_str = str(default_val)
            
            if field_val.choices:
                comment += f"  # Choices: {field_val.choices}"
                
            lines.append(f"{full_name}={val_str}{comment}")
            
        return lines

    output_lines.extend(_recurse_vars(cls))
    
    print("\n".join(output_lines))


def check_health(args):
    """Check configuration health."""
    try:
        cls = import_config_class(args.file, args.class_name)
    except Exception as e:
        print(f"Error importing class: {e}")
        sys.exit(1)
        
    print(f"Checking configuration health for {args.class_name}...")
    try:
        # Instantiate
        config = cls(env_path=args.env_file)
        print("✅ Configuration loaded successfully!")
        print("\nLoaded Values:")
        print(config)
        
    except Exception as e:
        print(f"❌ Configuration check failed: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Envifrog CLI Tool")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # generate-example
    gen_parser = subparsers.add_parser("generate-example", help="Generate .env.example")
    gen_parser.add_argument("file", help="Path to python file containing the config class")
    gen_parser.add_argument("class_name", help="Name of the config class")
    gen_parser.set_defaults(func=generate_example)
    
    # check
    check_parser = subparsers.add_parser("check", help="Check configuration health")
    check_parser.add_argument("file", help="Path to python file containing the config class")
    check_parser.add_argument("class_name", help="Name of the config class")
    check_parser.add_argument("--env-file", help="Path to .env file to test against", default=None)
    check_parser.set_defaults(func=check_health)
    
    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
