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
        Consolida os dados dos PDFs selecionados em um novo arquivo Excel.
        Cada PDF selecionado gera uma nova linha no consolidado.
        """
        dados_consolidados = []
        pasta_qpe = '/teams/BR-TI-TIN/AutomaoFinanas/QPE'
        pasta_consolidado = '/teams/BR-TI-TIN/AutomaoFinanas/CONSOLIDADO'
        nome_arquivo = 'QPE_consolidado.xlsx'
        
        # Processa cada PDF selecionado
        for pdf_file in pdf_files:
            try:
                # Se for string, é um arquivo do SharePoint
                if isinstance(pdf_file, str):
                    print(f"Baixando arquivo {pdf_file}...")
                    pdf_content = self.sharepoint_auth.baixar_arquivo_sharepoint(
                        pdf_file, 
                        pasta_qpe
                    )
                else:
                    pdf_content = pdf_file
                
                if not pdf_content:
                    print(f"❌ Não foi possível processar o arquivo")
                    continue
                
                # Extrai os dados do PDF
                dados = self.extrair_dados_pdf(pdf_content)
                dados_consolidados.append(dados)
                print(f"✅ Arquivo processado com sucesso: {dados['QPE_ID']}")
                
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
            df = df.sort_values('QPE_ID')
            
            # Prepara o arquivo Excel
            print("Preparando arquivo Excel...")
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Consolidado_QPE')
                
                # Ajusta largura das colunas
                worksheet = writer.sheets['Consolidado_QPE']
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