import os
import unittest
import tempfile
import logging
import threading
import time
from pathlib import Path
from typing import Optional, Tuple, List, Union

from envifrog import BaseConfig, Var, FrozenInstanceError
from envifrog.utils import setup_logging_redactor

class TestFeatures(unittest.TestCase):
    
    def test_immutability(self):
        class Config(BaseConfig):
             FROZEN_VAR: str = "initial"
             
        cfg = Config()
        self.assertEqual(cfg.FROZEN_VAR, "initial")
        
        with self.assertRaises(FrozenInstanceError):
            cfg.FROZEN_VAR = "modified"
            
        # Allowed internal changes if any? (Not in public API)

    def test_logging_redaction(self):
        # Create a logger capture
        logger = logging.getLogger("test_redaction")
        logger.setLevel(logging.INFO)
        
        # Add filter
        setup_logging_redactor(['SECRET_PASSWORD'])
        
        with self.assertLogs() as cm:
             logging.info("User login with SECRET_PASSWORD and more.")
             logging.info("Safe log message.")
             
        # Check logs
        self.assertTrue(any("[REDACTED]" in log for log in cm.output))
        self.assertFalse(any("SECRET_PASSWORD" in log for log in cm.output))
        
    def test_profiles_and_merging(self):
        # Create two files
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, encoding='utf-8') as f1:
            f1.write("COMMON=val1\nSPECIFIC_1=one")
            path1 = f1.name
            
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, encoding='utf-8') as f2:
            f2.write("COMMON=val2\nSPECIFIC_2=two")
            path2 = f2.name
            
        try:
             class Config(BaseConfig):
                 COMMON: str
                 SPECIFIC_1: str
                 SPECIFIC_2: str
                 
             # f2 should override f1
             cfg = Config(env_path=[path1, path2])
             
             self.assertEqual(cfg.COMMON, "val2")
             self.assertEqual(cfg.SPECIFIC_1, "one")
             self.assertEqual(cfg.SPECIFIC_2, "two")
             
        finally:
             os.remove(path1)
             os.remove(path2)

    def test_auto_detection(self):
        os.environ['ENVIFROG_MODE'] = 'testmode'
        path = '.env.testmode'
        with open(path, 'w') as f:
            f.write("AUTO_VAR=detected")
            
        try:
            class Config(BaseConfig):
                AUTO_VAR: str
            
            cfg = Config() # Should detect .env.testmode
            self.assertEqual(cfg.AUTO_VAR, "detected")
        finally:
            if os.path.exists(path):
                os.remove(path)
            del os.environ['ENVIFROG_MODE']

    def test_type_casting_extended(self):
        os.environ['MY_TUPLE'] = '1,2,3'
        os.environ['MY_PATH'] = '/tmp/path'
        os.environ['MY_OPT'] = '100'
        
        class Config(BaseConfig):
            MY_TUPLE: Tuple[int, ...]
            MY_PATH: Path
            MY_OPT: Optional[int]
            
        cfg = Config()
        self.assertEqual(cfg.MY_TUPLE, (1, 2, 3))
        self.assertIsInstance(cfg.MY_PATH, Path)
        self.assertEqual(str(cfg.MY_PATH).replace('\\', '/'), '/tmp/path')
        self.assertEqual(cfg.MY_OPT, 100)
        
        del os.environ['MY_TUPLE']
        del os.environ['MY_PATH']
        del os.environ['MY_OPT']

    def test_docs_generation(self):
        class DocConfig(BaseConfig):
            DOC_VAR: int = Var(default=10, secret=True)
            
        cfg = DocConfig()
        md = cfg.generate_markdown_docs()
        
        self.assertIn("| `DOC_VAR` |", md)
        self.assertIn("| `int` |", md)
        self.assertIn("| `10` |", md)
        self.assertIn("| Yes |", md)

    def test_live_reload(self):
         # Create a file
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, encoding='utf-8') as f:
            f.write("RELOAD_VAR=initial")
            path = f.name
            
        try:
            class ReloadConfig(BaseConfig):
                RELOAD_VAR: str
                
            cfg = ReloadConfig(env_path=path)
            self.assertEqual(cfg.RELOAD_VAR, "initial")
            
            event = threading.Event()
            def callback(c):
                event.set()
                
            cfg.watch(callback)
            
            # Wait a bit to ensure watcher started
            time.sleep(1.1)
            
            # Modify file
            # Update mtime significantly
            with open(path, 'w') as f:
                f.write("RELOAD_VAR=changed")
            
            # Windows filesystem time resolution can be coarse?
            # sleep
            
            # Wait for callback
            event.wait(timeout=5.0)
            
            self.assertEqual(cfg.RELOAD_VAR, "changed")
            
            # Stop watcher
            cfg._stop_watching.set()
            if cfg._watcher_thread:
                cfg._watcher_thread.join()
                
        finally:
            os.remove(path)

if __name__ == '__main__':
    unittest.main()
