import os
import inspect
from typing import Any, Dict, get_type_hints
from .fields import Var
from .exceptions import MissingVariableError, ValidationError, TypeCastingError
from .utils import parse_env_file, cast_value

class BaseConfig:
    """
    Base configuration class.
    
    Usage:
        class AppConfig(BaseConfig):
            PORT: int = Var(default=8000)
            
        config = AppConfig()
    """
    
    def __init__(self, env_path: str = None):
        """
        Initialize the configuration.
        
        Args:
            env_path: Optional path to a .env file.
        """
        # 1. Load variables
        self._env_vars = os.environ.copy()
        if env_path and os.path.exists(env_path):
            file_vars = parse_env_file(env_path)
            self._env_vars.update(file_vars) # os.environ normally takes precedence, but requirements said:
            # "If env_path is provided and exists, merge its values (os.environ takes priority)."
            # Wait, usually os.environ SHOULD take priority.
            # Requirement: "If env_path is provided and exists, merge its values (os.environ takes priority)."
            # So duplicate keys in os.environ overwrite keys in .env file.
            # My logic above: self._env_vars (os.environ) .update(file_vars) means file_vars would overwrite.
            # Correct logic:
            
            # Start with file vars
            combined_vars = file_vars.copy()
            # Update with os.environ (so os.environ wins)
            combined_vars.update(os.environ)
            self._env_vars = combined_vars
        
        # 2. Iterate over annotations using get_type_hints to resolve forward refs if any
        # We need to look at the class of 'self'
        cls = self.__class__
        
        # get_type_hints is generally better than __annotations__ for inheritance and forward refs
        try:
            hints = get_type_hints(cls)
        except Exception:
            # Fallback if there are issues with resolving hints (e.g. strict forward refs missing)
            hints = cls.__annotations__

        # We also need to inspect the class attributes to find Var() definitions (defaults)
        # We can iter over hints, and check if the attribute exists on the class
        
        for field_name, field_type in hints.items():
            if field_name.startswith('_'):
                continue
                
            # Get the Var definition or default value from class attribute
            field_val = getattr(cls, field_name, Var(default=...))
            
            # If it's a raw value (not a Var), treat it as a Var with that default
            if not isinstance(field_val, Var):
                field_val = Var(default=field_val)
                
            var_config: Var = field_val
            
            # 3. Find value
            value_str = self._env_vars.get(field_name)
            
            final_value = None
            
            if value_str is None:
                # Use default
                if var_config.default is ...:
                    raise MissingVariableError(f"Missing required environment variable: {field_name}")
                final_value = var_config.default
            else:
                # 4. Cast value
                try:
                    final_value = cast_value(value_str, field_type)
                except TypeCastingError as e:
                     raise TypeCastingError(f"Error validating {field_name}: {str(e)}") from e

            # 5. Validate (min/max)
            # Only if value is a number and min/max are set
            if isinstance(final_value, (int, float)):
                if var_config.min_val is not None and final_value < var_config.min_val:
                    raise ValidationError(f"{field_name} must be >= {var_config.min_val}, got {final_value}")
                if var_config.max_val is not None and final_value > var_config.max_val:
                    raise ValidationError(f"{field_name} must be <= {var_config.max_val}, got {final_value}")

            # 6. Set attribute
            # We store the value directly on the instance
            setattr(self, field_name, final_value)
            
            # We also verify 'secret' status for __repr__ and to_dict
            # We can store a metadata dict for secrets
            if not hasattr(self, '_secrets'):
                self._secrets = set()
            
            if var_config.secret:
                self._secrets.add(field_name)

    def to_dict(self, show_secrets: bool = False) -> Dict[str, Any]:
        """
        Return a dictionary representation of the configuration.
        
        Args:
            show_secrets: If True, secret values are shown. Otherwise masked.
        """
        result = {}
        # Iterate over public attributes
        for key in dir(self):
            if key.startswith('_') or key in ('to_dict',):
                continue
            
            val = getattr(self, key)
            if callable(val):
                continue
                
            # Check if secret
            is_secret = hasattr(self, '_secrets') and key in self._secrets
            
            if is_secret and not show_secrets:
                result[key] = "********"
            else:
                result[key] = val
        return result

    def __repr__(self) -> str:
        """Show the config state (masked)."""
        return f"<{self.__class__.__name__} {self.to_dict(show_secrets=False)}>"
