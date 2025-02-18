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
        try:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            texto_pagina1 = pdf_reader.pages[0].extract_text()
            texto_pagina2 = pdf_reader.pages[1].extract_text() if len(pdf_reader.pages) > 1 else ""
            texto_combinado = texto_pagina1 + "\n" + texto_pagina2
            
            print("=== TEXTO EXTRAÍDO DO PDF ===")
            print(texto_combinado)
            print("============================")
            
            # Extrair CNPJ
            padrao_cnpj = r'TOMADOR DE SERVIÇOS.*?\n.*?CPF/CNPJ:\s*(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})'
            cnpj_match = re.search(padrao_cnpj, texto_combinado, re.DOTALL)
            cnpj = cnpj_match.group(1) if cnpj_match else None
            
            # Extrair SPB_ID
            padrao_spb = r'(SPB-\d+)'
            spb_match = re.search(padrao_spb, texto_combinado)
            spb_id = spb_match.group(1) if spb_match else None
            
            # Extrair Número da Nota
            padrao_num_nota = r'Código de Verificação(0000\d{5})'
            num_nota_match = re.search(padrao_num_nota, texto_combinado)
            print(f"Testando padrão: {padrao_num_nota}")
            if num_nota_match:
                print(f"Match encontrado: {num_nota_match.group(1)}")
                num_nota = num_nota_match.group(1)  
            else:
                print("Nenhum match encontrado para o número da nota")
                num_nota = None
            
            # Extrair Valor Total
            padrao_valor = r'VALOR DO DOCUMENTO\s*([\d.,]+)'
            valor_match = re.search(padrao_valor, texto_combinado)
            valor_total = float(valor_match.group(1).replace('.', '').replace(',', '.')) if valor_match else 0.00
            
            # Extrair Cidade
            padrao_cidade = r"CEP:\s*\d{5}-\d{3}\s*(.*?)\s*INTERMEDIÁRIO DE SERVIÇOS"
            cidade_match = re.search(padrao_cidade, texto_combinado)
            # Remover o '----' e espaços extras no final
            cidade = re.sub(r'----$', '', cidade_match.group(1)).strip() if cidade_match else None
            
            dados = {
                'CNPJ': cnpj,
                'SPB_ID': spb_id,
                'Num_Nota': num_nota,  
                'VALOR_TOTAL': valor_total,
                'CIDADE': cidade
            }
            
            print(f"\nResultados finais:")
            print(f"CNPJ: {cnpj}")
            print(f"SPB_ID: {spb_id}")
            print(f"Número da Nota: {num_nota}")
            print(f"Valor Total: {valor_total}")
            print(f"Cidade: {cidade}")
            
            return dados
            
        except Exception as e:
            print(f"\u274c Erro ao extrair dados do PDF: {str(e)}")
            print(traceback.format_exc())
            raise
    
    def consolidar_spb(self, pdf_files: list) -> BytesIO:
        """
        Consolida os dados dos PDFs selecionados em um novo arquivo Excel.
        Cada PDF selecionado gera uma nova linha no consolidado.
        """
        dados_consolidados = []
        
        # Processa cada PDF selecionado
        for pdf_file in pdf_files:
            try:
                # Se for string, é um arquivo do SharePoint
                if isinstance(pdf_file, str):
                    pdf_content = self.sharepoint_auth.baixar_arquivo_sharepoint(
                        pdf_file, 
                        '/teams/BR-TI-TIN/AutomaoFinanas/SPB'
                    )
                else:
                    # Se não for string, já é o conteúdo do arquivo
                    pdf_content = pdf_file
                
                if not pdf_content:
                    print(f"❌ Não foi possível processar o arquivo")
                    continue
                
                # Extrai os dados do PDF
                dados = self.extrair_dados_pdf(pdf_content)
                dados_consolidados.append(dados)
                print(f"✅ Arquivo processado com sucesso: {dados['SPB_ID']}")
                
            except Exception as e:
                print(f"❌ Erro ao processar arquivo: {str(e)}")
                continue
        
        # Se nenhum arquivo foi processado com sucesso
        if not dados_consolidados:
            print("❌ Nenhum arquivo foi processado com sucesso")
            return None
        
        try:
            # Cria o DataFrame com os dados extraídos
            df = pd.DataFrame(dados_consolidados)
            df = df.sort_values('SPB_ID')
            
            # Prepara o arquivo Excel
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Consolidado_SPB')
                
                # Ajusta largura das colunas
                worksheet = writer.sheets['Consolidado_SPB']
                for idx, col in enumerate(df.columns):
                    max_length = max(df[col].astype(str).apply(len).max(), len(col))
                    worksheet.set_column(idx, idx, max_length + 2)
            
            output.seek(0)
            
            # Exclui o consolidado anterior se existir
            self.sharepoint_auth.excluir_arquivo_sharepoint(
                'SPB_consolidado.xlsx',
                '/teams/BR-TI-TIN/AutomaoFinanas/CONSOLIDADO'
            )
            
            # Salva o novo consolidado
            sucesso = self.sharepoint_auth.enviar_para_sharepoint(
                output,
                'SPB_consolidado.xlsx',
                '/teams/BR-TI-TIN/AutomaoFinanas/CONSOLIDADO'
            )
            
            if sucesso:
                print(f"✅ Novo consolidado criado com {len(df)} registros")
                return output
            else:
                print("❌ Erro ao salvar o consolidado")
                return None
                
        except Exception as e:
            print(f"❌ Erro ao criar consolidado: {str(e)}")
            return None