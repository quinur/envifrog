# Envifrog Documentation

Welcome to the **envifrog** documentation!

**envifrog** is designed to be the simplest, fastest way to handle configuration in Python without adding any external dependencies. It is perfect for microservices, scripts, and applications where you want to keep your footprint small.

## Table of Contents

1. [Introduction](#introduction)
2. [Basic Usage](basics.md)
3. [Field Configuration (Var)](fields.md)
4. [Nested Configurations](nested_configs.md)
5. [Validation & Type Casting](validation.md)
6. [Live Reloading & Watching](watching.md)
7. [Secrets & Logging](secrets.md)
8. [CLI reference](cli.md)

## Introduction

Envifrog follows the "Configuration as Code" philosophy but specifically focuses on **Environment Variables**. It uses standard Python type hints to define the structure of your configuration and automatically handles the conversion from environment strings to Python types.

### Key Philosophy
- **Zero Runtime Dependencies**: We use only the standard library.
- **Fail Fast**: We validate your config at startup. If a required variable is missing or malformed, we raise an error immediately.
- **Immutability**: Once loaded, configuration objects are frozen. They cannot be modified at runtime (except via the controlled watch/reload process).

### Project Structure
- `BaseConfig`: The core class you inherit from.
- `Var`: A helper to configure specific attributes (defaults, secrets, validation).
- `cli`: A command-line companion for developer productivity.
