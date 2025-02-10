import unittest
import pandas as pd
from application.reports.divergence_report_nfserve_r189 import DivergenceReportNFServeR189

class TestDivergenceReportNFServeR189(unittest.TestCase):
    def setUp(self):
        """Configuração inicial para cada teste"""
        self.report = DivergenceReportNFServeR189()
        
        # Dados de exemplo do NFSERVE
        self.nfserve_data = pd.DataFrame({
            'NFSERVE_ID': ['QPE_SPB-120398', 'QPE_SPB-120399'],
            'CNPJ': ['14.759.173/0002-83', '14.759.173/0002-83'],
            'VALOR_TOTAL': [1483.36, 2000.00]
        })
        
        # Dados de exemplo do R189
        self.r189_data = pd.DataFrame({
            'Invoice number': ['QPE_SPB-120398', 'QPE_SPB-120399'],
            'CNPJ - WEG': ['14.759.173/0002-83', '14.759.173/0002-83'],
            'Total Geral': [1483.36, 2000.00]
        })
    
    def test_check_divergences_sem_divergencias(self):
        """Testa verificação quando não há divergências"""
        success, message, divergences = self.report.check_divergences(
            self.nfserve_data, 
            self.r189_data
        )
        
        self.assertTrue(success)
        self.assertEqual(len(divergences), 0)
    
    def test_check_divergences_id_nao_encontrado(self):
        """Testa verificação quando há ID não encontrado no R189"""
        # Altera um ID no R189
        self.r189_data.loc[0, 'Invoice number'] = 'QPE_SPB-999999'
        
        success, message, divergences = self.report.check_divergences(
            self.nfserve_data, 
            self.r189_data
        )
        
        self.assertTrue(success)
        self.assertEqual(len(divergences), 1)
        self.assertEqual(divergences[0]['Tipo'], 'ID não encontrado no R189')
    
    def test_check_divergences_cnpj_divergente(self):
        """Testa verificação quando há CNPJ divergente"""
        # Altera um CNPJ no R189
        self.r189_data.loc[0, 'CNPJ - WEG'] = '99.999.999/9999-99'
        
        success, message, divergences = self.report.check_divergences(
            self.nfserve_data, 
            self.r189_data
        )
        
        self.assertTrue(success)
        self.assertEqual(len(divergences), 1)
        self.assertEqual(divergences[0]['Tipo'], 'CNPJ divergente')
    
    def test_check_divergences_valor_divergente(self):
        """Testa verificação quando há valor divergente"""
        # Altera um valor no R189
        self.r189_data.loc[0, 'Total Geral'] = 9999.99
        
        success, message, divergences = self.report.check_divergences(
            self.nfserve_data, 
            self.r189_data
        )
        
        self.assertTrue(success)
        self.assertEqual(len(divergences), 1)
        self.assertEqual(divergences[0]['Tipo'], 'Valor divergente')
    
    def test_check_divergences_dados_vazios(self):
        """Testa verificação com dados vazios"""
        nfserve_vazio = pd.DataFrame()
        r189_vazio = pd.DataFrame()
        
        success, message, divergences = self.report.check_divergences(
            nfserve_vazio, 
            r189_vazio
        )
        
        self.assertFalse(success)
        self.assertEqual(message, "Dados vazios")
        self.assertEqual(len(divergences), 0)

if __name__ == '__main__':
    unittest.main()
