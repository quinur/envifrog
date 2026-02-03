# CLI Reference

`envifrog` comes with a command-line tool to help with development and CI/CD pipelines.

## Installation

The CLI is available as `envifrog` after installing the package.

```bash
pip install envifrog
```

## Commands

### `generate-example`

Generates a `.env.example` file by inspecting your configuration class.

**Usage:**
```bash
envifrog generate-example <path_to_config_file> <class_name>
```

**Example:**
```bash
envifrog generate-example src/my_app/config.py MyConfig > .env.example
```

This will output a formatted list of all variables, including their types, default values, and requirements.

### `check`

Validates a configuration file against your class definition. This is extremely useful for CI/CD checks or local testing.

**Usage:**
```bash
envifrog check <path_to_config_file> <class_name> [--env-file <path_to_env>]
```

**Example:**
```bash
# Checks the default .env
envifrog check src/my_app/config.py MyConfig

# Checks a specific production env file
envifrog check src/my_app/config.py MyConfig --env-file .env.prod
```

It will exit with code `0` on success and `1` on failure, making it easy to integrate into scripts.
