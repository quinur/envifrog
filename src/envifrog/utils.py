import os
import logging
import pathlib
from typing import Any, Dict, List, Tuple, Type, Union, get_args, get_origin
from .exceptions import TypeCastingError

try:
    import tomllib
except ImportError:
    tomllib = None  # type: ignore

import json

class SecretFilter(logging.Filter):
    """
    logging.Filter that redacts secrets from log records.
    """
    def __init__(self, secrets: List[str], replacement: str = "[REDACTED]"):
        super().__init__()
        self.secrets = secrets
        self.replacement = replacement

    def filter(self, record: logging.LogRecord) -> bool:
        if not isinstance(record.msg, str):
            return True
            
        msg = record.msg
        for secret in self.secrets:
            if secret and secret in msg:
                msg = msg.replace(secret, self.replacement)
        record.msg = msg
        return True

def setup_logging_redactor(secrets: List[str]) -> None:
    """
    Attach the SecretFilter to the root logger to redact known secrets.
    """
    if not secrets:
        return
    
    # Avoid duplicate filters if called multiple times? 
    # For simplicity, we just add it. Users should call this once.
    f = SecretFilter(secrets)
    logging.getLogger().addFilter(f)

def load_config_file(path: str) -> Dict[str, Any]:
    """
    Load configuration from a file (.env, .json, .toml).
    """
    _, ext = os.path.splitext(path)
    ext = ext.lower()
    
    if ext == '.json':
        return _parse_json(path)
    elif ext == '.toml':
        return _parse_toml(path)
    else:
        return _parse_env(path)

def _parse_json(path: str) -> Dict[str, Any]:
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError as e:
        raise TypeCastingError(f"Error parsing JSON file {path}: {e}")

def _parse_toml(path: str) -> Dict[str, Any]:
    if tomllib is None:
        raise ImportError("TOML support requires Python 3.11+ (standard library 'tomllib')")
    
    try:
        with open(path, 'rb') as f:
            return tomllib.load(f)
    except FileNotFoundError:
        return {}
    except tomllib.TOMLDecodeError as e:
        raise TypeCastingError(f"Error parsing TOML file {path}: {e}")

def _parse_env(path: str) -> Dict[str, str]:
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
    Supports int, float, bool, list, tuple, pathlib.Path, and Optional/Union.
    """
    # 1. Handle Optional/Union types
    origin = get_origin(target_type)
    args = get_args(target_type)
    
    if origin is Union:
        # We only support Optional[T] style (Union[T, None]) efficiently
        non_none_args = [arg for arg in args if arg is not type(None)]
        if non_none_args:
            # Try the first non-None type
            target_type = non_none_args[0]
            origin = get_origin(target_type)
            args = get_args(target_type)

    # 2. String (no cast needed)
    if target_type == str:
        return value
    
    # 3. Path
    if target_type == pathlib.Path:
        return pathlib.Path(value)
    
    # 4. Primitives
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
        
    # 5. Iterables (List/Tuple)
    if origin in (list, tuple) or target_type in (list, tuple):
        items = [item.strip() for item in value.split(',')]
        
        # Determine inner type if specified (e.g. list[int])
        if args:
            item_type = args[0]
            casted_items = [cast_value(item, item_type) for item in items]
        else:
            casted_items = items
            
        if origin is tuple or target_type == tuple:
            return tuple(casted_items)
        return casted_items

    # Fallback/Fail
    raise TypeCastingError(f"Unsupported type: {target_type}")
