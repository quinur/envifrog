# Basic Usage

## Creating a Configuration Class

Inherit from `BaseConfig` and use standard Python type hints.

```python
from envifrog import BaseConfig

class AppConfig(BaseConfig):
    DATABASE_URL: str
    PORT: int = 8080
    DEBUG: bool = False
```

## Loading Configuration

When you instantiate your class, `envifrog` performs the following steps:
1.  **Detects Files**: Looks for `.env` or files specified in `env_path`.
2.  **Loads Variables**: Reads variables from files and merges them with `os.environ`.
3.  **Casts Types**: Converts strings to the types specified in hints.
4.  **Validates**: Ensures all required variables are present and valid.
5.  **Freezes**: Makes the instance immutable.

### Loading from specific files

```python
# From a single file
config = AppConfig(env_path=".env.prod")

# From multiple files (later files override earlier ones)
config = AppConfig(env_path=[".env", ".env.local"])
```

### Supported Formats

- **.env**: Standard `KEY=VALUE` format.
- **.json**: Valid JSON objects.
- **.toml**: Valid TOML files (requires Python 3.11+).

### Auto-detection (Profiles)

If `env_path` is not provided, `envifrog` looks for the `ENVIFROG_MODE` environment variable.
- If `ENVIFROG_MODE=dev`, it load `.env` and `.env.dev`.
- If `ENVIFROG_MODE=prod`, it loads `.env` and `.env.prod`.

## Type Support

Envifrog supports many types out of the box:
- `str`, `int`, `float`, `bool`
- `list`, `tuple` (comma-separated strings)
- `list[int]`, `tuple[str, ...]` (generic types)
- `pathlib.Path`
- `Optional[T]` (returns `None` if value is empty/missing)

## Programmatic Documentation

You can generate a Markdown table describing your configuration classes programmatically:

```python
config = AppConfig()
markdown_string = config.generate_markdown_docs()
print(markdown_string)
```

This is useful for automatically updating your project's documentation via scripts.
