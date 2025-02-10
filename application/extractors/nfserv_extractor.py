import os
from io import BytesIO
import pandas as pd
import PyPDF2
from auth.auth import SharePointAuth
import re
import traceback

class NFServExtractor:
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
            
            # Extrair NFSERV_ID
            padrao_nfserv = r'N\.\s*CONTROLE:\s*(\S+)'  # Capturar qualquer coisa após CONTROLE:
            nfserv_match = re.search(padrao_nfserv, texto_combinado)
            nfserv_id = nfserv_match.group(1) if nfserv_match else "ID NÃO ENCONTRADO"
            
            # Extrair CNPJ
            padrao_cnpj = r'CNPJ:\s*(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})'
            cnpj_match = re.search(padrao_cnpj, texto_combinado, re.DOTALL)
            cnpj = cnpj_match.group(1) if cnpj_match else None
            
            # Extrair Cidade
            padrao_cidade = r'CIDADE\s+([A-ZÀ-Ú\s]+)\s+ESTADO'  # Capturar apenas CIDADE seguido do nome
            cidade_match = re.search(padrao_cidade, texto_combinado)
            cidade = cidade_match.group(1).strip() if cidade_match else None
            
            # Extrair Valor Total
            padrao_valor = r'VALOR DO DOCUMENTO\s*([\d.,]+)'
            valor_match = re.search(padrao_valor, texto_combinado)
            valor_total = float(valor_match.group(1).replace('.', '').replace(',', '.')) if valor_match else 0.00
            
            dados = {
                'CNPJ': cnpj,
                'NFSERV_ID': nfserv_id,
                'VALOR_TOTAL': valor_total,
                'CIDADE': cidade
            }
            
            # Debug prints
            print(f"CNPJ: {cnpj}")
            print(f"NFSERV_ID: {nfserv_id}")
            print(f"Valor Total: {valor_total}")
            print(f"Cidade: {cidade}")
            
            return dados
            
        except Exception as e:
            print(f"❌ Erro ao extrair dados do PDF: {str(e)}")
            print(traceback.format_exc())
            raise

    def consolidar_nfserv(self, pdf_files: list) -> BytesIO:
        """
        Consolida os dados dos PDFs selecionados em um novo arquivo Excel.
        Cada PDF selecionado gera uma nova linha no consolidado.
        """
        dados_consolidados = []
        pasta_nfserv = '/teams/BR-TI-TIN/AutomaoFinanas/NFSERV'
        pasta_consolidado = '/teams/BR-TI-TIN/AutomaoFinanas/CONSOLIDADO'
        nome_arquivo = 'NFSERV_consolidado.xlsx'
        
        # Processa cada PDF selecionado
        for pdf_file in pdf_files:
            try:
                # Se for string, é um arquivo do SharePoint
                if isinstance(pdf_file, str):
                    print(f"Baixando arquivo {pdf_file}...")
                    pdf_content = self.sharepoint_auth.baixar_arquivo_sharepoint(
                        pdf_file, 
                        pasta_nfserv
                    )
                else:
                    pdf_content = pdf_file
                
                if not pdf_content:
                    print(f"❌ Não foi possível processar o arquivo")
                    continue
                
                # Extrai os dados do PDF
                dados = self.extrair_dados_pdf(pdf_content)
                dados_consolidados.append(dados)
                print(f"✅ Arquivo processado com sucesso: {dados['NFSERV_ID']}")
                
            except Exception as e:
                print(f"❌ Erro ao processar arquivo: {str(e)}")
                continue
        
        # Se nenhum arquivo foi processado com sucesso
        if not dados_consolidados:
            print("❌ Nenhum arquivo foi processado com sucesso")
            return None
        
        try:
            print(f"Criando DataFrame com {len(dados_consolidados)} registros...")
            # Cria o DataFrame com os dados extraídos
            df = pd.DataFrame(dados_consolidados)
            df = df.sort_values('NFSERV_ID')
            
            # Prepara o arquivo Excel
            print("Preparando arquivo Excel...")
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Consolidado_NFSERV')
                
                # Ajusta largura das colunas
                worksheet = writer.sheets['Consolidado_NFSERV']
                for idx, col in enumerate(df.columns):
                    max_length = max(df[col].astype(str).apply(len).max(), len(col))
                    worksheet.set_column(idx, idx, max_length + 2)
            
            output.seek(0)
            
            # Tenta excluir o arquivo anterior
            print(f"Tentando excluir arquivo anterior: {nome_arquivo}")
            excluido = self.sharepoint_auth.excluir_arquivo_sharepoint(
                nome_arquivo,
                pasta_consolidado
            )
            if excluido:
                print("✅ Arquivo anterior excluído com sucesso")
            else:
                print("⚠️ Não foi possível excluir o arquivo anterior (pode não existir)")
            
            # Salva o novo consolidado
            print(f"Salvando novo arquivo: {nome_arquivo}")
            sucesso = self.sharepoint_auth.enviar_para_sharepoint(
                output,
                nome_arquivo,
                pasta_consolidado
            )
            
            if sucesso:
                print(f"✅ Novo consolidado criado com {len(df)} registros")
                return output
            else:
                print("❌ Erro ao salvar o consolidado")
                return None
                
        except Exception as e:
            print(f"❌ Erro ao criar consolidado: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return None