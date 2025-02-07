import unittest
import pandas as pd
from unittest.mock import patch, MagicMock
from datetime import datetime
from io import BytesIO
from application.reports.divergence_report_qpe_r189 import DivergenceReportQPER189
from application.reports.divergence_report_spb_r189 import DivergenceReportSPBR189
from auth.auth import SharePointAuth

class TestSharePointIntegration(unittest.TestCase):
    def setUp(self):
        """Configuração inicial para cada teste"""
        self.qpe_report = DivergenceReportQPER189()
        self.spb_report = DivergenceReportSPBR189()
        
        # Mock do token de autenticação
        self.mock_token = "mock_token_12345"
        
        # DataFrame de exemplo para testes
        self.divergences_df = pd.DataFrame({
            'Tipo': ['CONTAGEM_QPE', 'QPE_ID não encontrado no R189'],
            'QPE_ID': ['N/A', 'QPE-001'],
            'CNPJ QPE': ['N/A', '60.621.141/0004-04'],
            'CNPJ R189': ['N/A', 'Não encontrado'],
            'Valor QPE': [10, 100.00],
            'Valor R189': [8, 'Não encontrado']
        })

    @patch('auth.auth.SharePointAuth.acquire_token')
    def test_authentication_success(self, mock_acquire_token):
        """Testa se a autenticação com o SharePoint é bem-sucedida"""
        mock_acquire_token.return_value = self.mock_token
        auth = SharePointAuth()
        token = auth.acquire_token()
        self.assertEqual(token, self.mock_token)

    @patch('auth.auth.SharePointAuth.acquire_token')
    def test_authentication_failure(self, mock_acquire_token):
        """Testa o comportamento quando a autenticação falha"""
        mock_acquire_token.side_effect = Exception("Falha na autenticação")
        auth = SharePointAuth()
        with self.assertRaises(Exception):
            auth.acquire_token()

    @patch('auth.auth.SharePointAuth.enviar_para_sharepoint')
    def test_report_upload_success(self, mock_upload):
        """Testa se o upload do relatório é bem-sucedido"""
        mock_upload.return_value = True
        success, _ = self.qpe_report.save_report(self.divergences_df)
        self.assertTrue(success)
        mock_upload.assert_called_once()

    @patch('auth.auth.SharePointAuth.enviar_para_sharepoint')
    def test_report_upload_failure(self, mock_upload):
        """Testa o comportamento quando o upload falha"""
        mock_upload.side_effect = Exception("Erro no upload")
        success, message = self.qpe_report.save_report(self.divergences_df)
        self.assertFalse(success)
        self.assertIn("Erro", message)

    @patch('auth.auth.SharePointAuth.baixar_arquivo_sharepoint')
    def test_file_download_success(self, mock_download):
        """Testa se o download de arquivos é bem-sucedido"""
        mock_content = BytesIO(b"mock file content")
        mock_download.return_value = mock_content
        
        auth = SharePointAuth()
        content = auth.baixar_arquivo_sharepoint("file.xlsx", "/mock/path")
        self.assertEqual(content.getvalue(), b"mock file content")

    @patch('auth.auth.SharePointAuth.baixar_arquivo_sharepoint')
    def test_file_download_failure(self, mock_download):
        """Testa o comportamento quando o download falha"""
        mock_download.side_effect = Exception("Erro no download")
        auth = SharePointAuth()
        with self.assertRaises(Exception):
            auth.baixar_arquivo_sharepoint("file.xlsx", "/mock/path")

    @patch('auth.auth.SharePointAuth.excluir_arquivo_sharepoint')
    def test_file_delete_success(self, mock_delete):
        """Testa se a exclusão de arquivos é bem-sucedida"""
        mock_delete.return_value = True
        auth = SharePointAuth()
        success = auth.excluir_arquivo_sharepoint("file.xlsx", "/mock/path")
        self.assertTrue(success)

if __name__ == '__main__':
    unittest.main()
