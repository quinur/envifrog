# Nested Configurations

`envifrog` supports grouping configuration into nested classes. This is useful for large applications with many subsystems (e.g., Database, Redis, Auth).

## Defining Nested Configs

To nest a configuration, simply use another `BaseConfig` subclass as the type hint.

```python
from envifrog import BaseConfig, Var

class DatabaseConfig(BaseConfig):
    HOST: str = "localhost"
    PORT: int = 5432

class AppConfig(BaseConfig):
    DB: DatabaseConfig
    DEBUG: bool = False
```

## Variable Names and Prefixes

By default, nested configs will look for variables using the attribute name as a prefix.

Example:
- `DB.HOST` will look for `DB_HOST`.
- `DB.PORT` will look for `DB_PORT`.

You can override this behavior using the `prefix` argument in `Var`:

```python
class AppConfig(BaseConfig):
    # This will look for DATABASE_HOST and DATABASE_PORT
    DB: DatabaseConfig = Var(prefix="DATABASE_")
```

If you want **no prefix** (flattened variables), pass an empty string:

```python
class AppConfig(BaseConfig):
    # This will look for HOST and PORT directly
    DB: DatabaseConfig = Var(prefix="")
```

## Depth

Nesting can be as deep as you need. Each level will append its prefix to the previous one.

```python
class Inner(BaseConfig):
    VAL: str

class Mid(BaseConfig):
    INNER: Inner = Var(prefix="I_")

class Outer(BaseConfig):
    MID: Mid = Var(prefix="M_")

# Loads M_I_VAL
```
