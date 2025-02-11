import unittest
import pandas as pd
from application.reports.divergence_report_nfserv_r189 import DivergenceReportNFSERVR189

class TestDivergenceReportNFSERVR189(unittest.TestCase):
    def setUp(self):
        # Dados do NFSERV
        self.nfserv_data = pd.DataFrame({
            'CNPJ': [
                '07.175.725/0042-38', '07.175.725/0042-38', '60.621.141/0004-04',
                '13.772.125/0007-77', '07.175.725/0014-84', '07.175.725/0004-02',
                '07.175.725/0010-50', '07.175.725/0010-50', '07.175.725/0010-50',
                '60.621.141/0004-04', '13.772.125/0007-77', '07.175.725/0004-02',
                '07.175.725/0014-84', '07.175.725/0030-02', '14.759.173/0002-83'
            ],
            'NFSERV_ID': [
                'BHO-001607', 'BHO-001617', 'BLU-001685', 'BLU-001686', 'BLU-001687',
                'BLU-001688', 'BLU-001690', 'BLU-001691', 'BLU-001699', 'BLU-001700',
                'BLU-001701', 'BLU-001702', 'BLU-001703', 'POA-002351', 'POA-002352'
            ],
            'VALOR_TOTAL': [
                6374.79, 768.46, 92.31, 10.79, 317.69, 239.74, 1886.56, 45372.36,
                14092.66, 608.98, 71.18, 1581.68, 2095.71, 3665.75, 4433.34
            ]
        })

        # Dados do R189
        self.r189_data = pd.DataFrame({
            'CNPJ - WEG': [
                '07.175.725/0004-02', '07.175.725/0004-02', '07.175.725/0004-02',
                '07.175.725/0010-50', '07.175.725/0010-50', '07.175.725/0010-50',
                '07.175.725/0014-84', '07.175.725/0014-84', '07.175.725/0021-03',
                '07.175.725/0024-56', '07.175.725/0026-18', '07.175.725/0030-02'
            ],
            'Invoice number': [
                'BLU-001688', 'BLU-001702', 'SPB-120353', 'BLU-001690', 'BLU-001691',
                'BLU-001699', 'BLU-001687', 'BLU-001703', 'SPB-120351', 'SPB-120355',
                'SPB-120359', 'POA-002351'
            ],
            'Total Geral': [
                239.74, 1581.68, 244.13, 1886.56, 45372.36, 14092.66, 317.69,
                2095.71, 3563.35, 4142.26, 3854.57, 3665.75
            ]
        })

        self.report = DivergenceReportNFSERVR189()

    def test_check_divergences(self):
        # Executa a verificação de divergências
        success, message, divergences = self.report.check_divergences(self.nfserv_data, self.r189_data)

        # Verifica se a execução foi bem sucedida
        self.assertTrue(success)
        self.assertEqual(message, "Divergências verificadas com sucesso")

        # Converte o DataFrame de divergências para um dicionário para facilitar os testes
        divergences_dict = divergences.to_dict('records')

        # Verifica se encontrou as divergências esperadas
        expected_missing_in_r189 = [
            'BHO-001607', 'BHO-001617', 'BLU-001685', 'BLU-001686',
            'BLU-001700', 'BLU-001701', 'POA-002352'
        ]

        # Verifica IDs que estão no NFSERV mas não no R189
        missing_in_r189 = [d['NFSERV_ID'] for d in divergences_dict 
                          if d['Tipo'] == 'NFSERV_ID não encontrado no R189']
        self.assertEqual(set(missing_in_r189), set(expected_missing_in_r189))

        # Verifica IDs que estão no R189 mas não no NFSERV
        expected_missing_in_nfserv = ['SPB-120353', 'SPB-120351', 'SPB-120355', 'SPB-120359']
        missing_in_nfserv = [d['NFSERV_ID'] for d in divergences_dict 
                            if d['Tipo'] == 'NFSERV_ID não encontrado no NFSERV']
        self.assertEqual(set(missing_in_nfserv), set(expected_missing_in_nfserv))

        # Verifica se não há divergências de CNPJ ou valor para os registros que existem em ambos
        matching_ids = ['BLU-001688', 'BLU-001702', 'BLU-001690', 'BLU-001691',
                       'BLU-001699', 'BLU-001687', 'BLU-001703', 'POA-002351']
        
        cnpj_divergences = [d['NFSERV_ID'] for d in divergences_dict 
                           if d['Tipo'] == 'CNPJ diferente' and d['NFSERV_ID'] in matching_ids]
        self.assertEqual(len(cnpj_divergences), 0)

        value_divergences = [d['NFSERV_ID'] for d in divergences_dict 
                           if d['Tipo'] == 'Valor diferente' and d['NFSERV_ID'] in matching_ids]
        self.assertEqual(len(value_divergences), 0)

if __name__ == '__main__':
    unittest.main()
