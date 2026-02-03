# Live Reloading and Watching

`envifrog` includes a built-in mechanism to watch for changes in your configuration files and update your config instance at runtime.

## Enabling Watcher

You can start the background watcher by calling the `.watch()` method. It takes a callback function that is executed whenever a change is detected.

```python
from envifrog import BaseConfig

class Config(BaseConfig):
    PORT: int = 8000

def on_reload(new_config):
    print(f"Reloaded! New port: {new_config.PORT}")

config = Config(env_path=".env")
config.watch(on_reload)
```

## How it Works

1. **Polling**: The watcher runs in a background daemon thread and checks the modification time (`mtime`) of all loaded files every second.
2. **Atomic Update**: When a change is detected, `envifrog` re-loads the files, re-casts the types, and re-validates the new values.
3. **Immutability Bypass**: During the reload process, `envifrog` temporarily unfreezes the instance to apply the new values, then freezes it again.
4. **Failure Handling**: If the new configuration fails validation (e.g., a required variable was deleted or a type is invalid), the error is caught, printed to standard output, and the **old configuration remains intact**.

## Important Considerations

- **Thread Safety**: While `envifrog` updates the values atomically, your application code needs to be prepared for the fact that `config.PORT` might return a different value from one second to the next if you are using it in a long-running loop.
- **Environment Variables**: The watcher only monitors physical files (like `.env`, `.json`, `.toml`). It **cannot** detect changes to actual OS environment variables (e.g., if you run `export PORT=9000` in your terminal while the app is running).
