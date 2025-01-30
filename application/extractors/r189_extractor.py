import os
import tempfile
from io import BytesIO
import pandas as pd
from pyxlsb import open_workbook
from auth.auth import SharePointAuth  # Importa a classe SharePointAuth
import uuid

class R189Extractor:
    def __init__(self, input_file: str, output_dir: str = None):
        self.input_file = input_file
        # Se o output_dir não for fornecido, usa o diretório do arquivo de entrada
        self.output_dir = output_dir or os.path.dirname(input_file)
        # Instancia a classe SharePointAuth uma vez
        self.sharepoint_auth = SharePointAuth()

    def processar_arquivo(self) -> str:
        """
        Processa o arquivo .xlsb e o converte para .xlsx.
        
        Returns:
            Caminho do arquivo .xlsx convertido.
        """
        if self.input_file.lower().endswith('.xlsb'):
            xlsx_file = self._convert_xlsb_to_xlsx(self.input_file)
            return xlsx_file
        else:
            raise ValueError("O arquivo de entrada não é um arquivo .xlsb")

    def consolidar_r189(self, xlsx_file: str) -> BytesIO:
        """
        Consolida o arquivo R189 com colunas específicas e trata valores vazios de CNPJ.
        
        Args:
            xlsx_file: Caminho do arquivo .xlsx já convertido
            
        Returns:
            BytesIO contendo o arquivo consolidado
        """
        try:
            df = self._ler_arquivo(xlsx_file)

            # Verifica se a aba 'BRASIL' existe
            if 'BRASIL' not in df:
                raise ValueError("A aba 'BRASIL' não foi encontrada no arquivo Excel.")
            
            # Obtém os dados apenas da aba 'BRASIL'
            df_brasil = df['BRASIL']

            # Combina todas as abas em um único DataFrame
            df_consolidado = df_brasil.copy()

            # Seleciona apenas as colunas necessárias
            colunas_necessarias = [
                'CNPJ - WEG',
                'Invoice number',
                'Site Name - WEG 2',
                'Total Geral'
            ]
            
            # Verifica se todas as colunas necessárias existem
            colunas_faltantes = [col for col in colunas_necessarias if col not in df_consolidado.columns]
            if colunas_faltantes:
                raise ValueError(f"Colunas faltantes no arquivo Excel: {colunas_faltantes}")
            
            # Seleciona apenas as colunas necessárias
            df_resultado = df_consolidado[colunas_necessarias].copy()
            
            # Preenche valores vazios com o valor anterior
            df_resultado = df_resultado.ffill()
            
            # Remove linhas que ainda possuem valores NaN
            df_resultado = df_resultado.dropna()

            # Gera o arquivo consolidado em formato BytesIO
            arquivo_consolidado = BytesIO()
            with pd.ExcelWriter(arquivo_consolidado, engine='xlsxwriter') as writer:
                df_resultado.to_excel(writer, index=False, sheet_name='Consolidado_R189')
            
            arquivo_consolidado.seek(0)

            # Define o nome do arquivo com extensão .xlsx
            nome_arquivo_excel = "r189_consolidado.xlsx"
            
            # Envia para o SharePoint com a extensão .xlsx
            sucesso = self.sharepoint_auth.enviar_para_sharepoint(arquivo_consolidado, nome_arquivo_excel, 'R189')

            # Remove as mensagens de log redundantes
            if not sucesso:
                print("❌ Falha ao enviar o arquivo consolidado para o SharePoint.")

            return arquivo_consolidado
            
        except Exception as e:
            print(f"❌ Erro ao consolidar arquivo R189: {str(e)}")
            raise

    def _convert_xlsb_to_xlsx(self, input_file: str) -> str:
        """
        Converte um arquivo .xlsb para .xlsx e remove o arquivo .xlsb original.
        """
        print("Convertendo arquivo .xlsb para .xlsx...")
        dfs = self._ler_arquivo_xlsb(input_file)

        # Cria um nome de arquivo com extensão .xlsx
        base_name = os.path.splitext(os.path.basename(input_file))[0]
        xlsx_path = os.path.join(self.output_dir, f'{base_name}.xlsx')

        # Salva como .xlsx
        with pd.ExcelWriter(xlsx_path, engine='openpyxl') as writer:
            for sheet_name, df in dfs.items():
                df.to_excel(writer, sheet_name=sheet_name, index=False)

        # Remove o arquivo .xlsb original após a conversão
        try:
            if os.path.exists(input_file):
                os.remove(input_file)
                print(f"✅ Arquivo original .xlsb removido: {input_file}")
        except Exception as e:
            print(f"⚠️ Não foi possível remover o arquivo .xlsb: {str(e)}")

        return xlsx_path

    def _ler_arquivo(self, caminho_arquivo):
        """
        Lê um arquivo .xlsx diretamente.
        """
        try:
            return pd.read_excel(
                caminho_arquivo,
                sheet_name=None,
                na_values=['', ' '],
                keep_default_na=True,
                header=12  # Linha 13 como cabeçalho
            )
        except Exception as e:
            print(f"❌ Erro ao ler arquivo: {str(e)}")
            raise

    def _ler_arquivo_xlsb(self, input_file: str):
        """
        Lê um arquivo .xlsb a partir de um caminho de arquivo
        """
        try:
            dfs = {}
            with open_workbook(input_file) as wb:
                for sheet_name in wb.sheets:
                    data = []
                    with wb.get_sheet(sheet_name) as sheet:
                        for row in sheet.rows():
                            row_data = [cell.v if cell else None for cell in row]
                            data.append(row_data)
                    
                    if data:
                        headers = data[12]  # Linha 13 como cabeçalho
                        data = data[13:]  # Dados a partir da linha 14
                        df = pd.DataFrame(data, columns=headers).drop_duplicates()
                        dfs[sheet_name] = df
                        
            return dfs
        except Exception as e:
            print(f"❌ Erro ao ler arquivo XLSB: {str(e)}")
            raise