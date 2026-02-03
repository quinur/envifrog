# Field Configuration with `Var`

In `envifrog`, you define your configuration using class annotations. For simple fields, you can just use the type hint. For more control, use the `Var` class.

## Basic Declaration

```python
from envifrog import BaseConfig, Var

class MyConfig(BaseConfig):
    # Simple required field
    PORT: int
    
    # Simple field with default
    DEBUG: bool = False
    
    # Explicit configuration with Var
    API_KEY: str = Var(secret=True)
```

## `Var` Parameters

The `Var` class accepts the following arguments:

| Argument | Type | Description |
|---|---|---|
| `default` | `Any` | The default value. Use `...` (Ellipsis) to mark it as required. |
| `secret` | `bool` | If `True`, the value is masked in `repr(config)` and `str(config)`. |
| `min_val` | `float` | Minimum allowed value (for numeric types). |
| `max_val` | `float` | Maximum allowed value (for numeric types). |
| `prefix` | `str` | A prefix to apply to the environment variable name (useful for nesting). |
| `validator` | `Callable` | A function `(val) -> bool` that must return `True` for the value to be valid. |
| `choices` | `list` | A list of allowed values. |

## Required Fields

If a field has no default value and is not assigned a `Var` with a default, it is considered **Required**. `envifrog` will raise a `MissingVariableError` if it's not found in the environment.

```python
class Config(BaseConfig):
    REQUIRED_KEY: str # Required
    OPTIONAL_KEY: str = "default" # Optional
    ANOTHER_REQUIRED: str = Var(...) # Also Required
```

## Secrets Management

When `secret=True` is passed to `Var`, `envifrog` tracks this field. 
- It will be shown as `********` when printing the config object.
- You can use `config.to_dict(show_secrets=True)` to get the real values if needed.
- You can use `setup_logging_redactor(config._secrets_values)` (see [Secrets & Logging](secrets.md)) to prevent secrets from leaking into your logs.
