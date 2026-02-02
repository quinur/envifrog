import os
from typing import Any, Dict, List, Type, Union, get_args, get_origin
from .exceptions import TypeCastingError

def parse_env_file(path: str) -> Dict[str, str]:
    """
    Parse a .env file into a dictionary.
    Ignores comments (lines starting with #) and empty lines.
    """
    env_vars = {}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Remove surrounding quotes if present
                    if (value.startswith('"') and value.endswith('"')) or \
                       (value.startswith("'") and value.endswith("'")):
                        value = value[1:-1]
                    
                    env_vars[key] = value
    except FileNotFoundError:
        pass # It is acceptable if the file is not found
    
    return env_vars

def cast_value(value: str, target_type: Type[Any]) -> Any:
    """
    Cast a string value to the target type.
    Supports int, float, bool, and list.
    """
    # Handle Optional types (e.g., Optional[int] is Union[int, NoneType])
    origin = get_origin(target_type)
    if origin is Union:
        args = get_args(target_type)
        # We only support Optional[T], so if NoneType is present, try casting to the other type
        non_none_args = [arg for arg in args if arg is not type(None)]
        if non_none_args:
             # Just try the first one for now (simplification)
            target_type = non_none_args[0]
            origin = get_origin(target_type) # Update origin in case it's a List inside Optional

    if target_type == str:
        return value
    
    if target_type == int:
        try:
            return int(value)
        except ValueError:
            raise TypeCastingError(f"Cannot cast '{value}' to int")
            
    if target_type == float:
        try:
            return float(value)
        except ValueError:
            raise TypeCastingError(f"Cannot cast '{value}' to float")
            
    if target_type == bool:
        lower_val = value.lower()
        if lower_val in ('true', '1', 'yes', 'on'):
            return True
        if lower_val in ('false', '0', 'no', 'off'):
            return False
        raise TypeCastingError(f"Cannot cast '{value}' to bool")
        
    if origin is list or target_type == list:
        # Handle simple comma-separated list
        # If parameterized list[int], we need to cast elements
        items = [item.strip() for item in value.split(',')]
        
        args = get_args(target_type)
        if args:
            item_type = args[0]
            return [cast_value(item, item_type) for item in items]
        else:
            return items

    # Fallback/Fail
    raise TypeCastingError(f"Unsupported type: {target_type}")
