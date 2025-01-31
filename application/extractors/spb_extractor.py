import os
from io import BytesIO
import pandas as pd
import PyPDF2
from auth.auth import SharePointAuth
import re
import traceback

class SPBExtractor:
    def __init__(self, input_file: str, output_dir: str = None):
        self.input_file = input_file
        self.output_dir = output_dir or os.path.dirname(input_file)
        self.sharepoint_auth = SharePointAuth()

    def extrair_dados_pdf(self, pdf_file: BytesIO) -> dict:
        """Extrai os dados necessários do arquivo PDF."""
        try:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            texto_pagina1 = pdf_reader.pages[0].extract_text()
            texto_pagina2 = pdf_reader.pages[1].extract_text() if len(pdf_reader.pages) > 1 else ""
            texto_combinado = texto_pagina1 + "\n" + texto_pagina2
            
            # Extrair CNPJ
            padrao_cnpj = r'TOMADOR DE SERVIÇOS.*?\n.*?(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})'
            cnpj_match = re.search(padrao_cnpj, texto_combinado, re.DOTALL)
            cnpj = cnpj_match.group(1) if cnpj_match else None
            
            # Extrair SPB_ID
            padrao_spb = r'(SPB-\d+)'
            spb_match = re.search(padrao_spb, texto_combinado)
            spb_id = spb_match.group(1) if spb_match else None
            
            # Extrair Valor Total
            padrao_valor = r'VALOR DO DOCUMENTO\s*([\d.,]+)'
            valor_match = re.search(padrao_valor, texto_combinado)
            valor_total = valor_match.group(1).replace('.', '').replace(',', '.') if valor_match else 0.00
            
            dados = {
                'CNPJ': cnpj,
                'SPB_ID': spb_id,
                'VALOR_TOTAL': float(valor_total)
            }
            
            print(f"CNPJ: {cnpj}")
            print(f"SPB_ID: {spb_id}")
            print(f"Valor Total: {valor_total}")
            
            return dados
            
        except Exception as e:
            print(f"❌ Erro ao extrair dados do PDF: {str(e)}")
            print(traceback.format_exc())
            raise

    def consolidar_spb(self, pdf_files: list) -> BytesIO:
        """Consolida os dados de múltiplos PDFs em um único arquivo Excel."""
        try:
            dados_consolidados = []
            
            # Tentar carregar consolidado existente
            try:
                arquivo_existente = self.sharepoint_auth.baixar_arquivo_sharepoint(
                    'SPB_consolidado.xlsx', 
                    '/teams/BR-TI-TIN/AutomaoFinanas/CONSOLIDADO'
                )
                if arquivo_existente:
                    df_existente = pd.read_excel(arquivo_existente)
                    dados_consolidados = df_existente.to_dict('records')
                    print("✅ Consolidado existente carregado com sucesso")
            except Exception as e:
                print("⚠️ Não foi possível carregar consolidado existente")
            
            pasta_spb = '/teams/BR-TI-TIN/AutomaoFinanas/SPB'
            
            for pdf_file in pdf_files:
                if isinstance(pdf_file, str):
                    pdf_content = self.sharepoint_auth.baixar_arquivo_sharepoint(pdf_file, pasta_spb)
                else:
                    pdf_content = pdf_file
                
                if pdf_content:
                    try:
                        dados = self.extrair_dados_pdf(pdf_content)
                        
                        # Verificar duplicidade
                        existe = any(d['SPB_ID'] == dados['SPB_ID'] for d in dados_consolidados)
                        if not existe:
                            dados_consolidados.append(dados)
                            print(f"✅ Adicionado novo registro: {dados['SPB_ID']}")
                        else:
                            print(f"⚠️ Registro {dados['SPB_ID']} já existe")
                    except Exception as e:
                        print(f"❌ Erro ao processar arquivo: {str(e)}")
                        continue
                else:
                    print(f"❌ Não foi possível baixar o arquivo")
            
            if not dados_consolidados:
                print("⚠️ Nenhum dado foi extraído dos PDFs")
                return None
            
            df_consolidado = pd.DataFrame(dados_consolidados)
            df_consolidado = df_consolidado.sort_values('SPB_ID')
            
            arquivo_consolidado = BytesIO()
            with pd.ExcelWriter(arquivo_consolidado, engine='xlsxwriter') as writer:
                df_consolidado.to_excel(writer, index=False, sheet_name='Consolidado_SPB')
                
                worksheet = writer.sheets['Consolidado_SPB']
                for idx, col in enumerate(df_consolidado.columns):
                    max_length = max(
                        df_consolidado[col].astype(str).apply(len).max(),
                        len(col)
                    )
                    worksheet.set_column(idx, idx, max_length + 2)
            
            arquivo_consolidado.seek(0)
            
            nome_arquivo_excel = "SPB_consolidado.xlsx"
            pasta_consolidado = '/teams/BR-TI-TIN/AutomaoFinanas/CONSOLIDADO'
            
            sucesso = self.sharepoint_auth.enviar_para_sharepoint(
                arquivo_consolidado, 
                nome_arquivo_excel, 
                pasta_consolidado
            )
            
            if sucesso:
                print(f"✅ Arquivo SPB_consolidado.xlsx salvo com sucesso na pasta CONSOLIDADO")
                print(f"Total de registros no consolidado: {len(df_consolidado)}")
            
            return arquivo_consolidado
            
        except Exception as e:
            print(f"❌ Erro ao consolidar arquivos SPB: {str(e)}")
            print(traceback.format_exc())
            raise