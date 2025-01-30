import os
from io import BytesIO
import pandas as pd
import PyPDF2
from auth.auth import SharePointAuth
import re

class QPEExtractor:
    def __init__(self, input_file: str, output_dir: str = None):
        self.input_file = input_file
        self.output_dir = output_dir or os.path.dirname(input_file)
        self.sharepoint_auth = SharePointAuth()

    def extrair_dados_pdf(self, pdf_file: BytesIO) -> dict:
        """
        Extrai os dados necessários do arquivo PDF.
        """
        try:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            # Extrair texto da primeira página
            texto_pagina1 = pdf_reader.pages[0].extract_text()
            
            # Extrair CNPJ do Tomador de Serviços
            padrao_cnpj = r'TOMADOR DE SERVIÇOS.*?\n.*?(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})'
            cnpj_match = re.search(padrao_cnpj, texto_pagina1, re.DOTALL)
            cnpj = cnpj_match.group(1) if cnpj_match else None

            # Extrair QPE_ID das Observações
            padrao_qpe = r'OBSERVAÇÕES.*?(\d+)'
            qpe_match = re.search(padrao_qpe, texto_pagina1, re.DOTALL)
            qpe_id = qpe_match.group(1) if qpe_match else None

            # Extrair Valor Total
            padrao_valor = r'VALOR LÍQUIDO.*?R\$\s*([\d.,]+)'
            valor_match = re.search(padrao_valor, texto_pagina1, re.DOTALL)
            valor_total = valor_match.group(1).replace('.', '').replace(',', '.') if valor_match else None
            
            dados = {
                'CNPJ': cnpj,
                'QPE_ID': qpe_id,
                'VALOR_TOTAL': float(valor_total) if valor_total else None
            }
            
            # Validar dados extraídos
            if not all(dados.values()):
                campos_faltantes = [campo for campo, valor in dados.items() if not valor]
                raise ValueError(f"Campos não encontrados no PDF: {campos_faltantes}")
            
            return dados
            
        except Exception as e:
            print(f"❌ Erro ao extrair dados do PDF: {str(e)}")
            raise

    def consolidar_qpe(self, pdf_files: list) -> BytesIO:
        """
        Consolida os dados de múltiplos PDFs em um único arquivo Excel.
        """
        try:
            dados_consolidados = []
            
            for pdf_file in pdf_files:
                dados = self.extrair_dados_pdf(pdf_file)
                dados_consolidados.append(dados)
            
            # Criar DataFrame com os dados extraídos
            df_consolidado = pd.DataFrame(dados_consolidados)
            
            # Ordenar por QPE_ID
            df_consolidado = df_consolidado.sort_values('QPE_ID')
            
            # Formatar as colunas
            df_consolidado['VALOR_TOTAL'] = df_consolidado['VALOR_TOTAL'].map('R$ {:,.2f}'.format)
            
            # Gerar arquivo Excel
            arquivo_consolidado = BytesIO()
            with pd.ExcelWriter(arquivo_consolidado, engine='xlsxwriter') as writer:
                df_consolidado.to_excel(writer, index=False, sheet_name='Consolidado_QPE')
                
                # Ajustar largura das colunas
                worksheet = writer.sheets['Consolidado_QPE']
                for idx, col in enumerate(df_consolidado.columns):
                    max_length = max(
                        df_consolidado[col].astype(str).apply(len).max(),
                        len(col)
                    )
                    worksheet.set_column(idx, idx, max_length + 2)
            
            arquivo_consolidado.seek(0)
            
            # Define o nome do arquivo e o caminho da pasta CONSOLIDADO
            nome_arquivo_excel = "QPE_consolidado.xlsx"
            pasta_consolidado = '/teams/BR-TI-TIN/AutomaoFinanas/CONSOLIDADO'
            
            # Envia apenas para a pasta CONSOLIDADO
            self.sharepoint_auth.enviar_para_sharepoint(
                arquivo_consolidado, 
                nome_arquivo_excel, 
                pasta_consolidado
            )
            
            return arquivo_consolidado
            
        except Exception as e:
            print(f"❌ Erro ao consolidar arquivos QPE: {str(e)}")
            raise 