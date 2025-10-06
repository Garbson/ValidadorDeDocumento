#!/usr/bin/env python3
"""
Script para executar todos os testes
"""

import unittest
import sys
from pathlib import Path

# Adicionar o diretório src ao path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

if __name__ == '__main__':
    # Descobrir e executar todos os testes
    loader = unittest.TestLoader()
    suite = loader.discover('tests', pattern='test_*.py')

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Sair com código de erro se testes falharam
    sys.exit(0 if result.wasSuccessful() else 1)