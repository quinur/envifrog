import os
import unittest
import tempfile
from typing import Optional, List
from envifrog import BaseConfig, Var, MissingVariableError, ValidationError, TypeCastingError

class TestCore(unittest.TestCase):
    
    def test_basic_loading_environ(self):
        """Test loading variables from os.environ."""
        os.environ['TEST_STR'] = 'hello'
        os.environ['TEST_INT'] = '42'
        
        class Config(BaseConfig):
            TEST_STR: str
            TEST_INT: int
            
        cfg = Config()
        self.assertEqual(cfg.TEST_STR, 'hello')
        self.assertEqual(cfg.TEST_INT, 42)
        
        del os.environ['TEST_STR']
        del os.environ['TEST_INT']

    def test_loading_from_file(self):
        """Test loading variables from a .env file."""
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, encoding='utf-8') as tmp:
            tmp.write("FILE_VAL=loaded\n# This is a comment\nFILE_NUM=100")
            tmp_path = tmp.name
            
        try:
            class Config(BaseConfig):
                FILE_VAL: str
                FILE_NUM: int
                
            cfg = Config(env_path=tmp_path)
            self.assertEqual(cfg.FILE_VAL, 'loaded')
            self.assertEqual(cfg.FILE_NUM, 100)
        finally:
            os.remove(tmp_path)

    def test_missing_variable(self):
        """Test that missing required variables raise MissingVariableError."""
        # Ensure var is not in env
        if 'MISSING_VAR' in os.environ:
            del os.environ['MISSING_VAR']
            
        class Config(BaseConfig):
            MISSING_VAR: str
            
        with self.assertRaises(MissingVariableError):
            Config()

    def test_defaults(self):
        """Test that default values are used when env var is missing."""
        class Config(BaseConfig):
            DEFAULT_VAR: int = Var(default=123)
            SIMPLE_DEFAULT: str = "foo"
            
        cfg = Config()
        self.assertEqual(cfg.DEFAULT_VAR, 123)
        self.assertEqual(cfg.SIMPLE_DEFAULT, "foo")

    def test_type_casting(self):
        """Test casting of int, bool, float, list."""
        os.environ['BOOL_TRUE'] = 'true'
        os.environ['BOOL_FALSE'] = '0'
        os.environ['FLOAT_VAL'] = '3.14'
        os.environ['LIST_VAL'] = 'a,b,c'
        os.environ['INT_LIST'] = '1, 2, 3'
        
        class Config(BaseConfig):
            BOOL_TRUE: bool
            BOOL_FALSE: bool
            FLOAT_VAL: float
            LIST_VAL: list
            INT_LIST: List[int]
            
        cfg = Config()
        self.assertTrue(cfg.BOOL_TRUE)
        self.assertFalse(cfg.BOOL_FALSE)
        self.assertEqual(cfg.FLOAT_VAL, 3.14)
        self.assertEqual(cfg.LIST_VAL, ['a', 'b', 'c'])
        self.assertEqual(cfg.INT_LIST, [1, 2, 3])
        
        # Cleanup
        for k in ['BOOL_TRUE', 'BOOL_FALSE', 'FLOAT_VAL', 'LIST_VAL', 'INT_LIST']:
            del os.environ[k]

    def test_casting_error(self):
        """Test that invalid values raise TypeCastingError."""
        os.environ['BAD_INT'] = 'not an int'
        
        class Config(BaseConfig):
            BAD_INT: int
            
        with self.assertRaises(TypeCastingError):
            Config()
            
        del os.environ['BAD_INT']

    def test_validation_min_max(self):
        """Test min_val and max_val validation."""
        os.environ['VAL_TOO_LOW'] = '5'
        os.environ['VAL_TOO_HIGH'] = '100'
        
        class Config(BaseConfig):
            VAL_TOO_LOW: int = Var(min_val=10)
            
        with self.assertRaises(ValidationError):
            Config()
            
        class Config2(BaseConfig):
             VAL_TOO_HIGH: int = Var(max_val=50)

        with self.assertRaises(ValidationError):
            Config2()
            
        del os.environ['VAL_TOO_LOW']
        del os.environ['VAL_TOO_HIGH']

    def test_secrets_masking(self):
        """Test that secrets are masked in to_dict and repr."""
        os.environ['SECRET_KEY'] = 'my_secret'
        os.environ['PUBLIC_KEY'] = 'public'
        
        class Config(BaseConfig):
            SECRET_KEY: str = Var(secret=True)
            PUBLIC_KEY: str
            
        cfg = Config()
        
        # Verify raw access works
        self.assertEqual(cfg.SECRET_KEY, 'my_secret')
        
        # Verify to_dict masking
        d = cfg.to_dict()
        self.assertEqual(d['SECRET_KEY'], '********')
        self.assertEqual(d['PUBLIC_KEY'], 'public')
        
        # Verify to_dict(show_secrets=True)
        d_full = cfg.to_dict(show_secrets=True)
        self.assertEqual(d_full['SECRET_KEY'], 'my_secret')
        
        # Verify repr contains stars
        self.assertIn('********', repr(cfg))
        
        del os.environ['SECRET_KEY']
        del os.environ['PUBLIC_KEY']

if __name__ == '__main__':
    unittest.main()
