import os
from io import BytesIO
import pandas as pd
import PyPDF2
from auth.auth import SharePointAuth
import re
import traceback

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
            
            # Extrair texto da segunda página (se existir)
            texto_pagina2 = pdf_reader.pages[1].extract_text() if len(pdf_reader.pages) > 1 else ""
            
            # Texto combinado para busca
            texto_combinado = texto_pagina1 + "\n" + texto_pagina2
            
            # Extrair CNPJ do Tomador de Serviços
            padrao_cnpj = r'TOMADOR DE SERVIÇOS.*?\n.*?(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})'
            cnpj_match = re.search(padrao_cnpj, texto_combinado, re.DOTALL)
            cnpj = cnpj_match.group(1) if cnpj_match else None
            
            # Extrair Cidade
            padrao_cidade = r'.*,\s*([A-Z\s]+)\s*-'
            cidade_match = re.search(padrao_cidade, texto_combinado)
            cidade = cidade_match.group(1).strip() if cidade_match else None
            
            # Extrair QPE_ID 
            padrao_qpe = r'(QPE-\d+)'
            qpe_match = re.search(padrao_qpe, texto_combinado)
            qpe_id = qpe_match.group(1) if qpe_match else None
            
            # Extrair Valor Total
            padrao_valor = r'VALOR DO DOCUMENTO\s*([\d.,]+)'
            valor_match = re.search(padrao_valor, texto_combinado)
            valor_total = valor_match.group(1).replace('.', '').replace(',', '.') if valor_match else 0.00
            
            dados = {
                'CNPJ': cnpj,
                'QPE_ID': qpe_id,
                'VALOR_TOTAL': float(valor_total),
                'CIDADE': cidade
            }
            
            # Debug prints
            print(f"CNPJ: {cnpj}")
            print(f"Cidade: {cidade}")
            print(f"QPE_ID: {qpe_id}")
            print(f"Valor Total: {valor_total}")
            
            return dados
            
        except Exception as e:
            print(f"❌ Erro ao extrair dados do PDF: {str(e)}")
            print(traceback.format_exc())
            raise

    def consolidar_qpe(self, pdf_files: list) -> BytesIO:
        """
        Consolida os dados de múltiplos PDFs em um único arquivo Excel.
        """
        try:
            dados_consolidados = []
            
            # Pasta padrão para arquivos QPE
            pasta_qpe = '/teams/BR-TI-TIN/AutomaoFinanas/QPE'
            
            # Tentar carregar consolidado existente
            try:
                arquivo_existente = self.sharepoint_auth.baixar_arquivo_sharepoint(
                    'QPE_consolidado.xlsx', 
                    '/teams/BR-TI-TIN/AutomaoFinanas/CONSOLIDADO'
                )
                if arquivo_existente:
                    df_existente = pd.read_excel(arquivo_existente)
                    dados_consolidados = df_existente.to_dict('records')
                    print("✅ Consolidado existente carregado com sucesso")
            except Exception as e:
                print("⚠️ Não foi possível carregar consolidado existente")
            
            for pdf_file in pdf_files:
                # Baixa o PDF do SharePoint
                if isinstance(pdf_file, str):
                    pdf_content = self.sharepoint_auth.baixar_arquivo_sharepoint(pdf_file, pasta_qpe)
                else:
                    pdf_content = pdf_file
                
                if pdf_content:
                    try:
                        dados = self.extrair_dados_pdf(pdf_content)
                        
                        # Verificar se já existe entrada com mesmo QPE_ID
                        existe = any(d['QPE_ID'] == dados['QPE_ID'] for d in dados_consolidados)
                        if not existe:
                            dados_consolidados.append(dados)
                            print(f"✅ Adicionado novo registro: {dados['QPE_ID']}")
                        else:
                            print(f"⚠️ Registro {dados['QPE_ID']} já existe")
                    except Exception as e:
                        print(f"❌ Erro ao processar arquivo: {str(e)}")
                else:
                    print(f"❌ Não foi possível baixar o arquivo")
            
            if not dados_consolidados:
                print("⚠️ Nenhum dado foi extraído dos PDFs")
                return None
            
            # Criar DataFrame com os dados extraídos
            df_consolidado = pd.DataFrame(dados_consolidados)
            
            # Ordenar por QPE_ID
            df_consolidado = df_consolidado.sort_values('QPE_ID')
            
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
            sucesso = self.sharepoint_auth.enviar_para_sharepoint(
                arquivo_consolidado, 
                nome_arquivo_excel, 
                pasta_consolidado
            )
            
            if sucesso:
                print(f"✅ Arquivo QPE_consolidado.xlsx salvo com sucesso na pasta CONSOLIDADO")
                print(f"Total de registros no consolidado: {len(df_consolidado)}")
            
            return arquivo_consolidado
            
        except Exception as e:
            print(f"❌ Erro ao consolidar arquivos QPE: {str(e)}")
            print(traceback.format_exc())  # Mostra o traceback completo
            raise