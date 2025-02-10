import unittest
from unittest.mock import Mock, patch
from io import BytesIO
import pandas as pd
from application.extractors.nfserve_extractor import NFServeExtractor

class TestNFServeExtractor(unittest.TestCase):
    def setUp(self):
        """Configuração inicial para cada teste"""
        self.extractor = NFServeExtractor("", "")
        
    def test_extrair_dados_pdf_valido(self):
        """Testa a extração de dados de um PDF válido"""
        # Mock do conteúdo do PDF
        mock_pdf_content = """
        N. CONTROLE: QPE_SPB-120398
        CLIENTE: WEG-CESTARI REDUTORES E MOTORREDUTORES S
        CNPJ: 14.759.173/0002-83
        CIDADE BENTO GONCALVES ESTADO RS
        VALOR DO DOCUMENTO 1.483,36
        """
        
        # Mock do PyPDF2.PdfReader
        mock_page = Mock()
        mock_page.extract_text.return_value = mock_pdf_content
        
        with patch('PyPDF2.PdfReader') as mock_pdf_reader:
            mock_pdf_reader.return_value.pages = [mock_page]
            
            # Testa a extração
            resultado = self.extractor.extrair_dados_pdf(BytesIO())
            
            self.assertIsNotNone(resultado)
            self.assertEqual(resultado['NFSERVE_ID'], 'QPE_SPB-120398')
            self.assertEqual(resultado['CNPJ'], '14.759.173/0002-83')
            self.assertEqual(resultado['CIDADE'], 'BENTO GONCALVES')
            self.assertEqual(resultado['VALOR_TOTAL'], 1483.36)
    
    def test_extrair_dados_pdf_invalido(self):
        """Testa a extração de dados de um PDF inválido"""
        # Mock do conteúdo do PDF inválido
        mock_pdf_content = "Conteúdo inválido sem os campos necessários"
        
        # Mock do PyPDF2.PdfReader
        mock_page = Mock()
        mock_page.extract_text.return_value = mock_pdf_content
        
        with patch('PyPDF2.PdfReader') as mock_pdf_reader:
            mock_pdf_reader.return_value.pages = [mock_page]
            
            # Testa a extração
            resultado = self.extractor.extrair_dados_pdf(BytesIO())
            
            self.assertIsNone(resultado)
    
    def test_consolidar_nfserve(self):
        """Testa a consolidação de múltiplos PDFs"""
        # Mock dos dados extraídos
        dados_mock = [
            {
                'NFSERVE_ID': 'QPE_SPB-120398',
                'CNPJ': '14.759.173/0002-83',
                'CIDADE': 'BENTO GONCALVES',
                'VALOR_TOTAL': 1483.36
            },
            {
                'NFSERVE_ID': 'QPE_SPB-120399',
                'CNPJ': '14.759.173/0002-83',
                'CIDADE': 'BENTO GONCALVES',
                'VALOR_TOTAL': 2000.00
            }
        ]
        
        # Mock do método extrair_dados_pdf
        with patch.object(NFServeExtractor, 'extrair_dados_pdf') as mock_extrair:
            mock_extrair.side_effect = dados_mock
            
            # Lista de PDFs mock
            pdfs_mock = [BytesIO(), BytesIO()]
            
            # Testa a consolidação
            resultado = self.extractor.consolidar_nfserve(pdfs_mock)
            
            self.assertIsNotNone(resultado)
            # Verifica se o método foi chamado para cada PDF
            self.assertEqual(mock_extrair.call_count, 2)

if __name__ == '__main__':
    unittest.main()
