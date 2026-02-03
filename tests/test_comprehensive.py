import os
import unittest
import tempfile
import json
import logging
import threading
import time
import pathlib
from typing import Optional, List, Tuple, Union
from envifrog import BaseConfig, Var, MissingVariableError, ValidationError, TypeCastingError, FrozenInstanceError
from envifrog.utils import setup_logging_redactor, cast_value
from envifrog.cli import generate_example, check_health
from unittest.mock import patch, MagicMock
import io

class DeepConfig(BaseConfig):
    LEAF: int = Var(default=10)

class MidConfig(BaseConfig):
    DEEP: DeepConfig = Var(prefix="DEEP_")
    MID_VAL: str = "mid"

class RootConfig(BaseConfig):
    ROOT_VAL: bool = True
    MID: MidConfig = Var(prefix="MID_")

class TestComprehensive(unittest.TestCase):
    def setUp(self):
        self.env_patcher = patch.dict(os.environ, {}, clear=True)
        self.env_patcher.start()

    def tearDown(self):
        self.env_patcher.stop()

    def test_deep_nesting_and_frozen(self):
        """Test deeply nested configs and verify all levels are frozen."""
        cfg = RootConfig()
        self.assertEqual(cfg.MID.DEEP.LEAF, 10)
        self.assertEqual(cfg.MID.MID_VAL, "mid")
        
        with self.assertRaises(FrozenInstanceError):
            cfg.ROOT_VAL = False
        with self.assertRaises(FrozenInstanceError):
            cfg.MID.MID_VAL = "changed"
        with self.assertRaises(FrozenInstanceError):
            cfg.MID.DEEP.LEAF = 20

    def test_casting_edge_cases(self):
        """Test complex casting scenarios."""
        os.environ['LIST_FLOATS'] = " 1.1, 2.2 , 3.3 "
        os.environ['TUPLE_STR'] = "a, b, c"
        os.environ['PATH_VAR'] = "./test_dir/file.txt"
        os.environ['BOOL_MIXED'] = "Yes"
        os.environ['OPT_PATH'] = "relative/path"
        
        class CastConfig(BaseConfig):
            LIST_FLOATS: List[float]
            TUPLE_STR: Tuple[str, ...]
            PATH_VAR: pathlib.Path
            BOOL_MIXED: bool
            OPT_PATH: Optional[pathlib.Path]
            
        cfg = CastConfig()
        self.assertEqual(cfg.LIST_FLOATS, [1.1, 2.2, 3.3])
        self.assertEqual(cfg.TUPLE_STR, ("a", "b", "c"))
        self.assertIsInstance(cfg.PATH_VAR, pathlib.Path)
        self.assertTrue(cfg.BOOL_MIXED)
        self.assertEqual(cfg.OPT_PATH, pathlib.Path("relative/path"))

    def test_optional_empty_string(self):
        """Test that empty string for Optional results in None."""
        os.environ['OPT_INT'] = ""
        os.environ['OPT_STR'] = ""
        
        class OptConfig(BaseConfig):
            OPT_INT: Optional[int]
            OPT_STR: Optional[str]
            
        cfg = OptConfig()
        self.assertIsNone(cfg.OPT_INT)
        # For str, empty string is technically a valid str, but our logic for Union/Optional treats "" as None
        # Let's see if that's what we want. Usually yes for env vars.
        self.assertIsNone(cfg.OPT_STR)

    def test_missing_with_prefix(self):
        """Test error message for missing var with prefix."""
        class PrefixConfig(BaseConfig):
            MISSING: str = Var(prefix="MYAPP_")
            
        with self.assertRaisesRegex(MissingVariableError, "Missing required variable: MYAPP_MISSING"):
            PrefixConfig()

    def test_validation_errors(self):
        """Test specific validation error messages."""
        class ValConfig(BaseConfig):
            SMALL: int = Var(min_val=10)
            LARGE: int = Var(max_val=100)
            CHOICE: str = Var(choices=["A", "B"])
            CUSTOM: int = Var(validator=lambda x: x > 0)

        with self.assertRaisesRegex(ValidationError, "SMALL \(5\) < min_val 10"):
            os.environ['SMALL'] = '5'
            os.environ['LARGE'] = '50'
            os.environ['CHOICE'] = 'A'
            os.environ['CUSTOM'] = '1'
            ValConfig()
        
        del os.environ['SMALL']
        with self.assertRaisesRegex(ValidationError, "LARGE \(150\) > max_val 100"):
            os.environ['SMALL'] = '20'
            os.environ['LARGE'] = '150'
            ValConfig()

    def test_hook_post_init(self):
        """Test the post-init hook for cross-field validation."""
        class HookConfig(BaseConfig):
            MIN: int
            MAX: int
            
            def hook(self):
                if self.MIN > self.MAX:
                    raise ValidationError("MIN cannot be greater than MAX")
                    
        os.environ['MIN'] = '10'
        os.environ['MAX'] = '20'
        cfg = HookConfig()
        self.assertEqual(cfg.MIN, 10)
        
        os.environ['MIN'] = '30'
        with self.assertRaisesRegex(ValidationError, "MIN cannot be greater than MAX"):
            HookConfig()

    def test_to_dict_nested_secrets(self):
        """Test that secrets are masked even in nested configs."""
        class SecretDeep(BaseConfig):
            API_KEY: str = Var(secret=True)
            
        class SecretRoot(BaseConfig):
            DB_PASS: str = Var(secret=True)
            NESTED: SecretDeep = Var(prefix="DEEP_")
            PUBLIC: str = "open"
            
        os.environ['DB_PASS'] = 'pass123'
        os.environ['DEEP_API_KEY'] = 'key456'
        
        cfg = SecretRoot()
        d = cfg.to_dict()
        
        self.assertEqual(d['DB_PASS'], '********')
        self.assertEqual(d['NESTED']['API_KEY'], '********')
        self.assertEqual(d['PUBLIC'], 'open')
        
        # Verify show_secrets=True
        full = cfg.to_dict(show_secrets=True)
        self.assertEqual(full['DB_PASS'], 'pass123')
        self.assertEqual(full['NESTED']['API_KEY'], 'key456')

    def test_dotenv_parsing_robustness(self):
        """Test .env parsing with quotes, spaces, etc."""
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, encoding='utf-8') as tmp:
            tmp.write('VAR1 = " quoted value " # comment\n')
            tmp.write("VAR2='single quoted'#comment\n")
            tmp.write("VAR3 = unquoted value with spaces # another comment\n")
            tmp.write("VAR4=#just comment\n")
            tmp.write("# Comment line\n")
            tmp.write("  # Indented comment\n")
            tmp_path = tmp.name
            
        try:
            class EnvConfig(BaseConfig):
                VAR1: str
                VAR2: str
                VAR3: str
                VAR4: str = "default"
                
            cfg = EnvConfig(env_path=tmp_path)
            self.assertEqual(cfg.VAR1, " quoted value ")
            self.assertEqual(cfg.VAR2, "single quoted")
            self.assertEqual(cfg.VAR3, "unquoted value with spaces")
            self.assertEqual(cfg.VAR4, "")
        finally:
            os.remove(tmp_path)

    def test_priority_merging(self):
        """Test merging priority: OS > File 2 > File 1."""
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, encoding='utf-8') as f1:
            f1.write("P1=file1\nP2=file1\nP3=file1")
            p1 = f1.name
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, encoding='utf-8') as f2:
            f2.write("P2=file2\nP3=file2")
            p2 = f2.name
            
        os.environ['P3'] = 'os_env'
        
        try:
            class PriorityConfig(BaseConfig):
                P1: str
                P2: str
                P3: str
                
            cfg = PriorityConfig(env_path=[p1, p2])
            self.assertEqual(cfg.P1, "file1")
            self.assertEqual(cfg.P2, "file2")
            self.assertEqual(cfg.P3, "os_env")
        finally:
            os.remove(p1)
            os.remove(p2)

    def test_cli_generate_example(self):
        """Test CLI generate-example output."""
        # We need a dummy config file to import
        dummy_code = """
from envifrog import BaseConfig, Var
class DummyConfig(BaseConfig):
    REQUIRED: int
    OPTIONAL: str = Var(default="default", choices=["a", "b"])
    NESTED: int = Var(prefix="N_", default=1)
"""
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.py', delete=False) as f:
            f.write(dummy_code)
            dummy_path = f.name
            
        try:
            args = MagicMock()
            args.file = dummy_path
            args.class_name = "DummyConfig"
            
            with patch('sys.stdout', new=io.StringIO()) as fake_out:
                generate_example(args)
                output = fake_out.getvalue()
                
            self.assertIn("REQUIRED=  # Type: int | Required", output)
            self.assertIn("OPTIONAL=default  # Type: str | Choices: ['a', 'b']", output)
            self.assertIn("NESTED=1  # Type: int", output)
        finally:
            os.remove(dummy_path)

    def test_cli_check_success(self):
        """Test CLI check command success."""
        dummy_code = """
from envifrog import BaseConfig
class DummyConfig(BaseConfig):
    VAL: int
"""
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.py', delete=False) as f:
            f.write(dummy_code)
            dummy_path = f.name
            
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.env', delete=False) as e:
            e.write("VAL=100")
            env_path = e.name

        try:
            args = MagicMock()
            args.file = dummy_path
            args.class_name = "DummyConfig"
            args.env_file = env_path
            
            with patch('sys.stdout', new=io.StringIO()) as fake_out:
                check_health(args)
                output = fake_out.getvalue()
                
            self.assertIn("Configuration loaded successfully", output)
            self.assertIn("VAL=100", output)
        finally:
            os.remove(dummy_path)
            os.remove(env_path)

    def test_unsupported_type_error(self):
        """Test that unsupported types raise TypeCastingError."""
        class BadTypeConfig(BaseConfig):
            BAD: dict # Not supported
            
        os.environ['BAD'] = '{"a": 1}'
        with self.assertRaisesRegex(TypeCastingError, "Unsupported type"):
            BadTypeConfig()

    def test_markdown_docs_complex(self):
        """Test MD generation with various types."""
        class MDConfig(BaseConfig):
            VAR_A: List[int] = Var(default=[1, 2])
            VAR_B: Optional[pathlib.Path] = Var(default=None, secret=True)
            
        cfg = MDConfig()
        md = cfg.generate_markdown_docs()
        self.assertIn("List[int]", md)
        self.assertIn("Optional[Path]", md)
        self.assertIn("Yes", md) # Secret

    def test_repr_nested(self):
        """Test repr of nested configs."""
        cfg = RootConfig()
        r = repr(cfg)
        self.assertIn("RootConfig(", r)
        self.assertIn("MID=MidConfig(", r)
        self.assertIn("DEEP=DeepConfig(", r)
        self.assertIn("LEAF=10", r)

if __name__ == '__main__':
    unittest.main()
