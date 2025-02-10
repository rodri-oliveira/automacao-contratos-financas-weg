import unittest
from io import BytesIO
from application.extractors.nfserv_extractor import NFServExtractor

class TestNFServExtractor(unittest.TestCase):
    def setUp(self):
        """
        Configuração inicial para cada teste
        """
        self.extractor = NFServExtractor(input_file=None)
        
        # PDF válido simulado
        self.pdf_valido = BytesIO(b'''
            N. CONTROLE: QPE_SPB-120398
            CLIENTE: WEG-CESTARI
            CNPJ: 14.759.173/0002-83
            CIDADE JARAGUÁ DO SUL ESTADO
            VALOR DO DOCUMENTO 1483,36
        '''.encode('utf-8'))
        
        # PDF inválido simulado
        self.pdf_invalido = BytesIO(b'''
            Documento inválido
            Sem dados necessários
        '''.encode('utf-8'))
        
    def test_extrair_dados_pdf_valido(self):
        """
        Testa a extração de dados de um PDF válido
        """
        resultado = self.extractor.extrair_dados_pdf(self.pdf_valido)
        
        self.assertIsNotNone(resultado)
        self.assertEqual(resultado['NFSERV_ID'], 'QPE_SPB-120398')
        self.assertEqual(resultado['CNPJ'], '14.759.173/0002-83')
        self.assertEqual(resultado['CIDADE'], 'JARAGUÁ DO SUL')
        self.assertEqual(resultado['VALOR_TOTAL'], 1483.36)
    
    def test_extrair_dados_pdf_invalido(self):
        """
        Testa a extração de dados de um PDF inválido
        """
        resultado = self.extractor.extrair_dados_pdf(self.pdf_invalido)
        self.assertIsNone(resultado)
    
    def test_consolidar_nfserv(self):
        """
        Testa a consolidação de múltiplos PDFs
        """
        # Simula dois PDFs válidos
        pdf1 = BytesIO(b'''
            N. CONTROLE: QPE_SPB-120398
            CLIENTE: WEG-CESTARI
            CNPJ: 14.759.173/0002-83
            CIDADE JARAGUÁ DO SUL ESTADO
            VALOR DO DOCUMENTO 1483,36
        '''.encode('utf-8'))
        
        pdf2 = BytesIO(b'''
            N. CONTROLE: QPE_SPB-120399
            CLIENTE: WEG-CESTARI
            CNPJ: 14.759.173/0002-83
            CIDADE JARAGUÁ DO SUL ESTADO
            VALOR DO DOCUMENTO 2000,00
        '''.encode('utf-8'))
        
        pdfs_mock = [pdf1, pdf2]
        resultado = self.extractor.consolidar_nfserv(pdfs_mock)
        
        self.assertIsNotNone(resultado)

if __name__ == '__main__':
    unittest.main()
