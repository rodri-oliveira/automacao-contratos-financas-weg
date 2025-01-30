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
