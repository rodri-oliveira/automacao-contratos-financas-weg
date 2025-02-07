import unittest
import pandas as pd
from application.reports.divergence_report_qpe_r189 import DivergenceReportQPER189

class TestDivergenceReportQPER189(unittest.TestCase):
    def setUp(self):
        """Configuração inicial para cada teste"""
        self.report = DivergenceReportQPER189()
        
        # Dados de exemplo para QPE
        self.qpe_data = pd.DataFrame({
            'QPE_ID': ['QPE-001', 'QPE-002', 'QPE-003', 'QPE-004'],
            'CNPJ': ['60.621.141/0004-04', '07.175.725/0021-03', '07.175.725/0021-03', '60.621.141/0004-04'],
            'VALOR_TOTAL': [100.00, 200.00, 300.00, 400.00]
        })
        
        # Dados de exemplo para R189
        self.r189_data = pd.DataFrame({
            'Invoice number': ['QPE-001', 'QPE-002', 'QPE-005'],
            'CNPJ - WEG': ['60.621.141/0004-04', '07.175.725/0021-03', '60.621.141/0004-04'],
            'Total Geral': [100.00, 250.00, 500.00]
        })

    def test_check_divergences_empty_dataframes(self):
        """Testa se o relatório trata corretamente DataFrames vazios"""
        empty_df = pd.DataFrame()
        success, message, divergences = self.report.check_divergences(empty_df, self.r189_data)
        self.assertFalse(success)
        self.assertIn("Erro: DataFrames não podem estar vazios", message)

    def test_check_divergences_missing_columns(self):
        """Testa se o relatório identifica colunas ausentes"""
        invalid_qpe = pd.DataFrame({'Invalid': [1, 2, 3]})
        success, message, divergences = self.report.check_divergences(invalid_qpe, self.r189_data)
        self.assertFalse(success)
        self.assertIn("Erro inesperado ao verificar divergências", message)

    def test_check_divergences_missing_qpe_id(self):
        """Testa se o relatório identifica QPE_IDs ausentes no R189"""
        success, message, divergences = self.report.check_divergences(self.qpe_data, self.r189_data)
        self.assertTrue(success)
        
        # Verifica se QPE-003 e QPE-004 foram identificados como ausentes no R189
        missing_qpes = divergences[divergences['Tipo'] == 'QPE_ID não encontrado no R189']
        self.assertEqual(len(missing_qpes), 2)
        self.assertTrue('QPE-003' in missing_qpes['QPE_ID'].values)
        self.assertTrue('QPE-004' in missing_qpes['QPE_ID'].values)

    def test_check_divergences_missing_r189_id(self):
        """Testa se o relatório identifica QPE_IDs presentes no R189 mas ausentes no QPE"""
        success, message, divergences = self.report.check_divergences(self.qpe_data, self.r189_data)
        self.assertTrue(success)
        
        # Verifica se QPE-005 foi identificado como ausente no QPE
        missing_in_qpe = divergences[divergences['Tipo'] == 'QPE_ID não encontrado no QPE']
        self.assertEqual(len(missing_in_qpe), 1)
        self.assertTrue('QPE-005' in missing_in_qpe['QPE_ID'].values)

    def test_check_divergences_value_mismatch(self):
        """Testa se o relatório identifica divergências de valor"""
        success, message, divergences = self.report.check_divergences(self.qpe_data, self.r189_data)
        self.assertTrue(success)
        
        # Verifica se QPE-002 foi identificado com valor divergente
        value_mismatch = divergences[divergences['Tipo'] == 'Valor divergente']
        self.assertEqual(len(value_mismatch), 1)
        self.assertTrue('QPE-002' in value_mismatch['QPE_ID'].values)

    def test_check_divergences_invalid_cnpj(self):
        """Testa se o relatório identifica CNPJs inválidos"""
        invalid_qpe = self.qpe_data.copy()
        invalid_qpe.loc[0, 'CNPJ'] = '123456'  # CNPJ inválido
        
        success, message, divergences = self.report.check_divergences(invalid_qpe, self.r189_data)
        self.assertTrue(success)
        
        # Verifica se o CNPJ inválido foi identificado
        invalid_cnpj = divergences[divergences['Tipo'] == 'CNPJ inválido']
        self.assertEqual(len(invalid_cnpj), 1)
        self.assertEqual(invalid_cnpj.iloc[0]['CNPJ QPE'], '123456')

    def test_check_divergences_null_values(self):
        """Testa se o relatório trata corretamente valores nulos"""
        null_qpe = self.qpe_data.copy()
        null_qpe.loc[0, 'VALOR_TOTAL'] = None
        
        success, message, divergences = self.report.check_divergences(null_qpe, self.r189_data)
        self.assertFalse(success)
        self.assertIn("valores nulos", message.lower())

if __name__ == '__main__':
    unittest.main()
