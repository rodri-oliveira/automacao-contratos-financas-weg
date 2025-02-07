import unittest
import pandas as pd
import numpy as np
from application.reports.divergence_report_qpe_r189 import DivergenceReportQPER189
from application.reports.divergence_report_spb_r189 import DivergenceReportSPBR189

class TestEdgeCases(unittest.TestCase):
    def setUp(self):
        """Configuração inicial para cada teste"""
        self.qpe_report = DivergenceReportQPER189()
        self.spb_report = DivergenceReportSPBR189()

    def test_extremely_large_values(self):
        """Testa o comportamento com valores extremamente grandes"""
        qpe_data = pd.DataFrame({
            'QPE_ID': ['QPE-001'],
            'CNPJ': ['60.621.141/0004-04'],
            'VALOR_TOTAL': [1e15]  # Valor muito grande
        })
        
        r189_data = pd.DataFrame({
            'Invoice number': ['QPE-001'],
            'CNPJ - WEG': ['60.621.141/0004-04'],
            'Total Geral': [1e15]
        })
        
        success, message, divergences = self.qpe_report.check_divergences(qpe_data, r189_data)
        self.assertTrue(success)
        self.assertEqual(len(divergences), 1)  # Apenas CONTAGEM_QPE

    def test_special_characters(self):
        """Testa o comportamento com caracteres especiais nos IDs"""
        qpe_data = pd.DataFrame({
            'QPE_ID': ['QPE-001@#$%'],
            'CNPJ': ['60.621.141/0004-04'],
            'VALOR_TOTAL': [100.00]
        })
        
        r189_data = pd.DataFrame({
            'Invoice number': ['QPE-001@#$%'],
            'CNPJ - WEG': ['60.621.141/0004-04'],
            'Total Geral': [100.00]
        })
        
        success, message, divergences = self.qpe_report.check_divergences(qpe_data, r189_data)
        self.assertTrue(success)
        self.assertEqual(len(divergences), 1)  # Apenas CONTAGEM_QPE

    def test_unicode_characters(self):
        """Testa o comportamento com caracteres Unicode"""
        qpe_data = pd.DataFrame({
            'QPE_ID': ['QPE-001áéíóú'],
            'CNPJ': ['60.621.141/0004-04'],
            'VALOR_TOTAL': [100.00]
        })
        
        r189_data = pd.DataFrame({
            'Invoice number': ['QPE-001áéíóú'],
            'CNPJ - WEG': ['60.621.141/0004-04'],
            'Total Geral': [100.00]
        })
        
        success, message, divergences = self.qpe_report.check_divergences(qpe_data, r189_data)
        self.assertTrue(success)
        self.assertEqual(len(divergences), 1)  # Apenas CONTAGEM_QPE

    def test_very_small_values(self):
        """Testa o comportamento com valores muito pequenos"""
        qpe_data = pd.DataFrame({
            'QPE_ID': ['QPE-001'],
            'CNPJ': ['60.621.141/0004-04'],
            'VALOR_TOTAL': [0.0000001]
        })
        
        r189_data = pd.DataFrame({
            'Invoice number': ['QPE-001'],
            'CNPJ - WEG': ['60.621.141/0004-04'],
            'Total Geral': [0.0000001]
        })
        
        success, message, divergences = self.qpe_report.check_divergences(qpe_data, r189_data)
        self.assertTrue(success)
        self.assertEqual(len(divergences), 1)  # Apenas CONTAGEM_QPE

    def test_scientific_notation(self):
        """Testa o comportamento com valores em notação científica"""
        qpe_data = pd.DataFrame({
            'QPE_ID': ['QPE-001'],
            'CNPJ': ['60.621.141/0004-04'],
            'VALOR_TOTAL': [1.23e5]
        })
        
        r189_data = pd.DataFrame({
            'Invoice number': ['QPE-001'],
            'CNPJ - WEG': ['60.621.141/0004-04'],
            'Total Geral': [123000.00]
        })
        
        success, message, divergences = self.qpe_report.check_divergences(qpe_data, r189_data)
        self.assertTrue(success)
        self.assertEqual(len(divergences), 1)  # Apenas CONTAGEM_QPE

    def test_leading_trailing_spaces(self):
        """Testa o comportamento com espaços extras nos IDs"""
        qpe_data = pd.DataFrame({
            'QPE_ID': ['  QPE-001  '],
            'CNPJ': ['60.621.141/0004-04'],
            'VALOR_TOTAL': [100.00]
        })
        
        r189_data = pd.DataFrame({
            'Invoice number': ['QPE-001'],
            'CNPJ - WEG': ['60.621.141/0004-04'],
            'Total Geral': [100.00]
        })
        
        success, message, divergences = self.qpe_report.check_divergences(qpe_data, r189_data)
        self.assertTrue(success)
        self.assertEqual(len(divergences), 1)  # Apenas CONTAGEM_QPE

    def test_duplicate_ids(self):
        """Testa o comportamento com IDs duplicados"""
        qpe_data = pd.DataFrame({
            'QPE_ID': ['QPE-001', 'QPE-001'],
            'CNPJ': ['60.621.141/0004-04', '60.621.141/0004-04'],
            'VALOR_TOTAL': [100.00, 200.00]  # Valores diferentes para o mesmo ID
        })
        
        r189_data = pd.DataFrame({
            'Invoice number': ['QPE-001'],
            'CNPJ - WEG': ['60.621.141/0004-04'],
            'Total Geral': [100.00]
        })
        
        success, message, divergences = self.qpe_report.check_divergences(qpe_data, r189_data)
        self.assertTrue(success)
        # Deve ter pelo menos a contagem e uma divergência de valor
        self.assertTrue(len(divergences) >= 2)

    def test_mixed_case_sensitivity(self):
        """Testa o comportamento com diferentes casos nos IDs"""
        qpe_data = pd.DataFrame({
            'QPE_ID': ['qpe-001'],
            'CNPJ': ['60.621.141/0004-04'],
            'VALOR_TOTAL': [100.00]
        })
        
        r189_data = pd.DataFrame({
            'Invoice number': ['QPE-001'],
            'CNPJ - WEG': ['60.621.141/0004-04'],
            'Total Geral': [100.00]
        })
        
        success, message, divergences = self.qpe_report.check_divergences(qpe_data, r189_data)
        self.assertTrue(success)
        # Deve haver apenas a contagem QPE, pois a comparação é case-insensitive
        self.assertEqual(len(divergences), 1)
        self.assertEqual(divergences.iloc[0]['Tipo'], 'CONTAGEM_QPE')
        self.assertEqual(divergences.iloc[0]['Valor QPE'], 1)
        self.assertEqual(divergences.iloc[0]['Valor R189'], 1)

if __name__ == '__main__':
    unittest.main()
