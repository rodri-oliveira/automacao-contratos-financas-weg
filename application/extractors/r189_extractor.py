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

    def consolidar_r189(self, conteudo: BytesIO) -> BytesIO:
        """
        Consolida o arquivo R189 com colunas específicas e trata valores vazios de CNPJ.
        
        Args:
            conteudo: BytesIO contendo o arquivo Excel
            
        Returns:
            BytesIO contendo o arquivo consolidado
        """
        try:
            # Lê o arquivo diretamente do BytesIO
            df = pd.read_excel(
                conteudo,
                sheet_name=None,  # Lê todas as abas
                na_values=['', ' '],
                keep_default_na=True,
                header=12  # Linha 13 como cabeçalho
            )

            # Verifica se a aba 'BRASIL' existe
            if 'BRASIL' not in df:
                raise ValueError("A aba 'BRASIL' não foi encontrada no arquivo Excel.")
            
            # Obtém os dados apenas da aba 'BRASIL'
            df_brasil = df['BRASIL']

            # Combina todas as abas em um único DataFrame
            df_consolidado = df_brasil.copy()

            # Seleciona apenas as colunas necessárias
            colunas_base = [
                'CNPJ - WEG',
                'Invoice number',
                'Site Name - WEG 2',
                'Account number'
            ]
            
            # Verifica qual coluna de total está presente no DataFrame
            colunas_total = ['Total Geral', 'Grand Total', 'Total Gera']
            coluna_total_encontrada = None
            for col in colunas_total:
                if col in df_consolidado.columns:
                    coluna_total_encontrada = col
                    break
            
            if not coluna_total_encontrada:
                raise ValueError(f"Nenhuma das colunas de total foi encontrada no arquivo Excel. Esperado uma das seguintes: {colunas_total}")
            
            colunas_necessarias = colunas_base + [coluna_total_encontrada]
            
            # Verifica se todas as colunas necessárias existem
            colunas_faltantes = [col for col in colunas_necessarias if col not in df_consolidado.columns]
            if colunas_faltantes:
                raise ValueError(f"Colunas faltantes no arquivo Excel: {colunas_faltantes}")
            
            # Seleciona apenas as colunas necessárias
            df_resultado = df_consolidado[colunas_necessarias].copy()
            
            # Identifica linhas onde Account number NÃO contém a string 'Total'
            linhas_sem_total = ~df_resultado['Account number'].astype(str).str.contains('Total', na=True)
            
            # Aplica o ffill apenas nas linhas onde Account number NÃO contém 'Total'
            df_resultado.loc[linhas_sem_total, 'Invoice number'] = df_resultado.loc[linhas_sem_total, 'Invoice number'].ffill()
            
            # Preenche outros valores vazios
            df_resultado[['CNPJ - WEG', 'Site Name - WEG 2']] = df_resultado[['CNPJ - WEG', 'Site Name - WEG 2']].ffill()
            
            # Remove linhas que ainda possuem valores NaN nas colunas principais
            df_resultado = df_resultado.dropna(subset=['CNPJ - WEG', 'Invoice number', 'Site Name - WEG 2', coluna_total_encontrada])

            # Remove a coluna Account number antes do agrupamento
            df_resultado = df_resultado.drop('Account number', axis=1)

            # Agrupa por todas as colunas exceto a coluna de total e soma os valores
            df_resultado = df_resultado.groupby(['CNPJ - WEG', 'Invoice number', 'Site Name - WEG 2'], as_index=False)[coluna_total_encontrada].sum()

            # Gera o arquivo consolidado em formato BytesIO
            arquivo_consolidado = BytesIO()
            with pd.ExcelWriter(arquivo_consolidado, engine='xlsxwriter') as writer:
                df_resultado.to_excel(writer, index=False, sheet_name='Consolidado_R189')
            
            arquivo_consolidado.seek(0)

            # Define o nome do arquivo e o caminho da pasta CONSOLIDADO
            nome_arquivo_excel = "R189_consolidado.xlsx"
            pasta_consolidado = '/teams/BR-TI-TIN/AutomaoFinanas/CONSOLIDADO'
            
            # Envia apenas para a pasta CONSOLIDADO
            self.sharepoint_auth.enviar_para_sharepoint(
                arquivo_consolidado, 
                nome_arquivo_excel, 
                pasta_consolidado
            )

            # Retorna ao início do BytesIO para que possa ser lido novamente
            arquivo_consolidado.seek(0)
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