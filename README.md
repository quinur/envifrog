# envifrog 🐸

**envifrog** is a lightweight, high-performance, zero-dependency library for managing environment variables in Python with type safety. It provides a "Pydantic-like" developer experience using standard Python type hints.

## Features

- **Zero Dependencies**: Pure Python standard library. No `pydantic` or `python-dotenv`.
- **Type Safety**: Automatically casts environment variables to your specified types (`int`, `bool`, `list`, etc.).
- **Fail-Fast**: Validates configuration on initialization.
- **Secrets Management**: Built-in support for masking secret values.

## Installation

```bash
pip install envifrog
```

## Quickstart

Create a `.env` file:

```env
DATABASE_URL=postgres://user:pass@localhost:5432/db
PORT=8000
DEBUG=true
API_KEY=supersecretkey
ALLOWED_HOSTS=localhost,127.0.0.1
```

Define your configuration class:

```python
from envifrog import BaseConfig, Var

class AppConfig(BaseConfig):
    DATABASE_URL: str
    PORT: int = Var(default=8080, min_val=1, max_val=65535)
    DEBUG: bool = Var(default=False)
    API_KEY: str = Var(secret=True)
    ALLOWED_HOSTS: list[str] = Var(default=["localhost"])

# Load configuration
config = AppConfig(env_path=".env")

print(f"Starting server on port {config.PORT}")
print(f"Debug mode: {config.DEBUG}")
print(config)  # Secrets are masked!
# <AppConfig {'DATABASE_URL': '...', 'PORT': 8000, 'DEBUG': True, 'API_KEY': '********', ...}>
```

## Why Envifrog?

Most projects pull in heavy dependencies just to read a few environment variables. `envifrog` solves this by being:
1.  **Small**: It's just a few files of pure Python.
2.  **Fast**: No complex validation schemas overhead.
3.  **Modern**: Leverages Python 3.10+ features.
