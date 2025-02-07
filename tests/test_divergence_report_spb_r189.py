import unittest
import pandas as pd
from application.reports.divergence_report_spb_r189 import DivergenceReportSPBR189

class TestDivergenceReportSPBR189(unittest.TestCase):
    def setUp(self):
        """Configuração inicial para cada teste"""
        self.report = DivergenceReportSPBR189()
        
        # Dados de exemplo para SPB
        self.spb_data = pd.DataFrame({
            'SPB_ID': ['SPB-001', 'SPB-002', 'SPB-003', 'SPB-004'],
            'CNPJ': ['60.621.141/0004-04', '07.175.725/0021-03', '07.175.725/0021-03', '60.621.141/0004-04'],
            'VALOR_TOTAL': [100.00, 200.00, 300.00, 400.00]
        })
        
        # Dados de exemplo para R189
        self.r189_data = pd.DataFrame({
            'Invoice number': ['SPB-001', 'SPB-002', 'SPB-005'],
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
        invalid_spb = pd.DataFrame({'Invalid': [1, 2, 3]})
        success, message, divergences = self.report.check_divergences(invalid_spb, self.r189_data)
        self.assertFalse(success)
        self.assertIn("Erro inesperado ao verificar divergências", message)

    def test_check_divergences_missing_spb_id(self):
        """Testa se o relatório identifica SPB_IDs ausentes no R189"""
        success, message, divergences = self.report.check_divergences(self.spb_data, self.r189_data)
        self.assertTrue(success)
        
        # Verifica se SPB-003 e SPB-004 foram identificados como ausentes no R189
        missing_spbs = divergences[divergences['Tipo'] == 'SPB_ID não encontrado no R189']
        self.assertEqual(len(missing_spbs), 2)
        self.assertTrue('SPB-003' in missing_spbs['SPB_ID'].values)
        self.assertTrue('SPB-004' in missing_spbs['SPB_ID'].values)

    def test_check_divergences_missing_r189_id(self):
        """Testa se o relatório identifica SPB_IDs presentes no R189 mas ausentes no SPB"""
        success, message, divergences = self.report.check_divergences(self.spb_data, self.r189_data)
        self.assertTrue(success)
        
        # Verifica se SPB-005 foi identificado como ausente no SPB
        missing_in_spb = divergences[divergences['Tipo'] == 'SPB_ID não encontrado no SPB']
        self.assertEqual(len(missing_in_spb), 1)
        self.assertTrue('SPB-005' in missing_in_spb['SPB_ID'].values)

    def test_check_divergences_value_mismatch(self):
        """Testa se o relatório identifica divergências de valor"""
        success, message, divergences = self.report.check_divergences(self.spb_data, self.r189_data)
        self.assertTrue(success)
        
        # Verifica se SPB-002 foi identificado com valor divergente
        value_mismatch = divergences[divergences['Tipo'] == 'Valor divergente']
        self.assertEqual(len(value_mismatch), 1)
        self.assertTrue('SPB-002' in value_mismatch['SPB_ID'].values)

    def test_check_divergences_invalid_cnpj(self):
        """Testa se o relatório identifica CNPJs inválidos"""
        invalid_spb = self.spb_data.copy()
        invalid_spb.loc[0, 'CNPJ'] = '123456'  # CNPJ inválido
        
        success, message, divergences = self.report.check_divergences(invalid_spb, self.r189_data)
        self.assertTrue(success)
        
        # Verifica se o CNPJ inválido foi identificado
        invalid_cnpj = divergences[divergences['Tipo'] == 'CNPJ inválido']
        self.assertEqual(len(invalid_cnpj), 1)
        self.assertEqual(invalid_cnpj.iloc[0]['CNPJ SPB'], '123456')

    def test_check_divergences_null_values(self):
        """Testa se o relatório trata corretamente valores nulos"""
        null_spb = self.spb_data.copy()
        null_spb.loc[0, 'VALOR_TOTAL'] = None
        
        success, message, divergences = self.report.check_divergences(null_spb, self.r189_data)
        self.assertFalse(success)
        self.assertIn("valores nulos", message.lower())

if __name__ == '__main__':
    unittest.main()
