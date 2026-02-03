import os
import sys
import json
import unittest
import tempfile
from typing import Optional
from envifrog.base import BaseConfig
from envifrog.fields import Var
from envifrog.exceptions import ValidationError, MissingVariableError

# Mock tomllib for older python versions if needed
try:
    import tomllib
    HAS_TOML = True
except ImportError:
    HAS_TOML = False

class DbConfig(BaseConfig):
    HOST: str = Var(default="localhost")
    PORT: int = Var(default=5432)

class ValidatorConfig(BaseConfig):
    # Choices
    ENV: str = Var(choices=["dev", "prod"], default="dev")
    # Custom Validator: must be even
    EVEN: int = Var(validator=lambda x: x % 2 == 0, default=2)

class AppConfig(BaseConfig):
    APP_NAME: str = Var(default="TestApp")
    DB: DbConfig = Var(prefix="DB_")
    VALID: ValidatorConfig = Var(prefix="VAL_")
    
    @property
    def connection_string(self) -> str:
        return f"{self.DB.HOST}:{self.DB.PORT}"

from unittest.mock import patch

class TestAdvancedFeatures(unittest.TestCase):
    def setUp(self):
        self.env_patcher = patch.dict(os.environ, {}, clear=True)
        self.env_patcher.start()

    def tearDown(self):
        self.env_patcher.stop()

    def test_nested_defaults(self):
        config = AppConfig()
        self.assertEqual(config.DB.HOST, "localhost")
        self.assertEqual(config.DB.PORT, 5432)
        self.assertEqual(config.VALID.ENV, "dev")

    def test_nested_overrides(self):
        os.environ["DB_HOST"] = "192.168.1.1"
        os.environ["DB_PORT"] = "9999"
        config = AppConfig()
        self.assertEqual(config.DB.HOST, "192.168.1.1")
        self.assertEqual(config.DB.PORT, 9999)

    def test_choices_validation(self):
        os.environ["VAL_ENV"] = "staging" # Not in ["dev", "prod"]
        with self.assertRaises(ValidationError) as cm:
            AppConfig()
        self.assertIn("not in", str(cm.exception))

    def test_custom_validator(self):
        os.environ["VAL_EVEN"] = "3"
        with self.assertRaises(ValidationError) as cm:
            AppConfig()
        self.assertIn("Custom validation failed", str(cm.exception))

    def test_computed_properties(self):
        config = AppConfig()
        d = config.to_dict(show_computed=True)
        self.assertIn("connection_string", d)
        self.assertEqual(d["connection_string"], "localhost:5432")

    def test_json_loading(self):
        data = {
            "APP_NAME": "JsonApp",
            "DB_HOST": "json-host",
            "VAL_EVEN": 4
        }
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            fname = f.name
        
        try:
            config = AppConfig(env_path=fname)
            self.assertEqual(config.APP_NAME, "JsonApp")
            self.assertEqual(config.DB.HOST, "json-host")
            self.assertEqual(config.VALID.EVEN, 4)
        finally:
            os.remove(fname)

    def test_toml_loading(self):
        if not HAS_TOML:
            print("Skipping TOML test (tomllib not available)")
            return

        data = """
        APP_NAME = "TomlApp"
        DB_HOST = "toml-host"
        VAL_EVEN = 8
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False, encoding='utf-8') as f:
            f.write(data)
            fname = f.name
            
        try:
            config = AppConfig(env_path=fname)
            self.assertEqual(config.APP_NAME, "TomlApp")
            self.assertEqual(config.DB.HOST, "toml-host")
            self.assertEqual(config.VALID.EVEN, 8)
        finally:
            os.remove(fname)

if __name__ == '__main__':
    unittest.main()
