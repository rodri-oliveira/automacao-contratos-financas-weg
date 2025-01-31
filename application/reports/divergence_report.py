# application/reports/divergence_report.py

import pandas as pd

def gerar_relatorio_divergencias(cnpjs_invalidos):
    """
    Gera um relatório de divergências com base nos CNPJs inválidos.
    
    :param cnpjs_invalidos: Lista de dicionários contendo os CNPJs inválidos.
    """
    try:
        # Converte os dados para um DataFrame
        df = pd.DataFrame(cnpjs_invalidos)

        # Gera o relatório em formato Excel
        caminho_arquivo = "relatorio_divergencias_r189.xlsx"
        df.to_excel(caminho_arquivo, index=False)
        print(f"Relatório gerado com sucesso: {caminho_arquivo}")
    except Exception as e:
        print(f"Erro ao gerar o relatório de divergências: {e}")
        
# {
#   "60.621.141/0005-87": ["PMAR_BRCSA"],
#   "07.175.725/0030-02": ["WEL_BRGCV"],
#   "60.621.141/0006-68": ["PMAR_BRMUA"],
#   "07.175.725/0010-50": ["WEL_BRJGS", "PENDING"],
#   "10.885.321/0001-74": ["WLI_BRLNH"],
#   "84.584.994/0007-16": ["WTB_BRSZO"],
#   "07.175.725/0042-38": ["WEL_BRBTI"],
#   "14.759.173/0001-00": ["WCES_BRMTT"],
#   "14.759.173/0002-83": ["WCES_BRBGV"],
#   "07.175.725/0024-56": ["WEL_BRRPO"],
#   "07.175.725/0014-84": ["WEL_BRBNU"],
#   "13.772.125/0007-77": ["RF_BRCOR"],
#   "07.175.725/0004-02": ["WEL_BRITJ"],
#   "60.621.141/0004-04": ["PMAR_BRGRM"],
#   "07.175.725/0021-03": ["WEL_BRSBC"],
#   "07.175.725/0026-18": ["WEL_BRSPO"]
# }
