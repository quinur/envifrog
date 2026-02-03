# Secrets & Logging

Handling sensitive information like API keys, passwords, and tokens is a critical part of configuration management. `envifrog` provides several tools to help you do this safely.

## Masking in Representations

By tagging a field as a secret, you ensure it won't be leaked when printing the configuration object or logging it directly.

```python
from envifrog import BaseConfig, Var

class Config(BaseConfig):
    DATABASE_PASSWORD: str = Var(secret=True)

config = Config()
print(config) 
# <Config(DATABASE_PASSWORD='********')>
```

## Logging Redaction

Even if you don't print the config object, sensitive values might still end up in your logs if you log raw messages containing them. 

`envifrog` provides a `setup_logging_redactor` utility that attaches a filter to your loggers to automatically redact any known secrets from all log messages.

```python
import logging
from envifrog import BaseConfig, Var
from envifrog.utils import setup_logging_redactor

class Config(BaseConfig):
    API_KEY: str = Var(secret=True)

config = Config()

# Pass the secret values to the redactor
setup_logging_redactor(list(config.to_dict(show_secrets=True).values()))

# Now these will be safe:
logging.warning(f"Connection failed for key: {config.API_KEY}")
# Output: WARNING:root:Connection failed for key: [REDACTED]
```

## Accessing Raw Values

If you need to get the real values for your application logic (e.g., to pass to a database driver), you can simply access the attribute:

```python
# This IS the real value
real_pass = config.DATABASE_PASSWORD
```

Or convert the whole config to a dictionary with secrets included:

```python
full_dict = config.to_dict(show_secrets=True)
```
