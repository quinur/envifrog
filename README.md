# envifrog 🐸

**envifrog** is a lightweight, zero-dependency, type-safe environment configuration library for Python. It leverages modern Python type hints to provide a robust and intuitive developer experience.

## ✨ Key Features

- **Zero Dependencies**: Powered entirely by the Python Standard Library.
- **Type Safety**: Automatic casting to `int`, `bool`, `list`, `tuple`, `pathlib.Path`, and more.
- **Nested Configurations**: Organize complex settings into nested classes.
- **Live Reloading**: Watch and reload configuration files at runtime without restarting.
- **Secrets Management**: Mask sensitive data in logs and string representations.
- **Validation**: Built-in validators for ranges, choices, and custom logic.
- **CLI Utility**: Tools to generate `.env.example` and verify configuration health.
- **Multiple Formats**: Support for `.env`, `.json`, and `.toml` files.

## 🚀 Installation

```bash
pip install envifrog
```

## 📖 Quickstart

Create a `.env` file:
```env
# Server settings
PORT=8000
DEBUG=true

# Security
API_KEY=supersecretkey

# Lists
ALLOWED_HOSTS=localhost,127.0.0.1
```

Define and use your configuration:
```python
from envifrog import BaseConfig, Var

class AppConfig(BaseConfig):
    PORT: int = Var(default=8080, min_val=1, max_val=65535)
    DEBUG: bool = False
    API_KEY: str = Var(secret=True)
    ALLOWED_HOSTS: list[str] = ["localhost"]

# Load configuration (supports .env, .json, .toml)
config = AppConfig(env_path=".env")

print(config.PORT)      # 8000
print(config.DEBUG)     # True
print(config.API_KEY)   # Masked in repr/str
```

## 🛠️ Advanced Usage

### Nested Configs
```python
class DBConfig(BaseConfig):
    HOST: str = "localhost"
    PORT: int = 5432

class Config(BaseConfig):
    DB: DBConfig = Var(prefix="DATABASE_") # Loads DATABASE_HOST, DATABASE_PORT
```

### Live Reloading
```python
config = AppConfig(env_path=".env")
config.watch(lambda c: print(f"Config reloaded! New port: {c.PORT}"))
```

### CLI Support
```bash
# Generate an example .env file
envifrog generate-example config.py MyConfig > .env.example

# Check if configuration is valid
envifrog check config.py MyConfig --env-file .env
```

## 📄 Documentation

For detailed documentation on all features, please see the [docs/](docs/) directory.

## ⚖️ License

MIT License. See [LICENSE](LICENSE) for details.

