import os
import tempfile
from io import BytesIO
import pandas as pd
from pyxlsb import open_workbook
from auth.auth import SharePointAuth
import uuid

class MunicipalityCodeExtractor:
    def __init__(self, input_file: str, output_dir: str = None):
        self.input_file = input_file
        # Se o output_dir não for fornecido, usa o diretório do arquivo de entrada
        self.output_dir = output_dir or os.path.dirname(input_file)
        # Instancia a classe SharePointAuth uma vez
        self.sharepoint_auth = SharePointAuth()
        # Lista de possíveis nomes para a coluna de total
        self.colunas_total = ['Total Geral', 'Grand Total', 'Total Gera', 'Total', 'Valor Total']

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

    def consolidar_municipality_code(self, conteudo: BytesIO) -> BytesIO:
        """
        Consolida o arquivo Municipality Code com colunas específicas e trata valores vazios.
        
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

            # Verifica qual coluna de total está presente no DataFrame
            coluna_total_encontrada = None
            for col in self.colunas_total:
                if col in df_brasil.columns:
                    coluna_total_encontrada = col
                    break
                    
            if not coluna_total_encontrada:
                raise ValueError(f"Nenhuma das colunas de total foi encontrada. Esperado uma das seguintes: {self.colunas_total}")

            # Seleciona apenas as colunas necessárias
            colunas_base = [
                'CNPJ - WEG',
                'Invoice number',
                'Municipality Code',
                'Invoice Type',
                'Site Name - WEG 2'
            ]
            
            colunas_necessarias = colunas_base + [coluna_total_encontrada]
            
            # Verifica se todas as colunas necessárias existem
            colunas_faltantes = [col for col in colunas_necessarias if col not in df_brasil.columns]
            if colunas_faltantes:
                raise ValueError(f"Colunas faltantes no arquivo Excel: {colunas_faltantes}")
            
            # Seleciona apenas as colunas necessárias
            df_consolidado = df_brasil[colunas_necessarias].copy()

            # Preenche valores vazios com o valor mais próximo acima para todas as colunas exceto Municipality Code
            df_consolidado[['CNPJ - WEG', 'Invoice number', 'Site Name - WEG 2']] = df_consolidado[['CNPJ - WEG', 'Invoice number', 'Site Name - WEG 2']].ffill()

            # Filtra apenas as linhas onde Invoice Type é 'SRV'
            df_resultado = df_consolidado[df_consolidado['Invoice Type'] == 'SRV'].copy()
            
            # Remove linhas que ainda possuem valores NaN nas colunas principais
            df_resultado = df_resultado.dropna(subset=['CNPJ - WEG', 'Invoice number', 'Municipality Code', coluna_total_encontrada])

            # Remove a coluna Invoice Type pois já filtramos por SRV
            df_resultado = df_resultado.drop('Invoice Type', axis=1)

            # Gera o arquivo consolidado em formato BytesIO
            arquivo_consolidado = BytesIO()
            with pd.ExcelWriter(arquivo_consolidado, engine='xlsxwriter') as writer:
                df_resultado.to_excel(writer, index=False, sheet_name='Municipality_Code_consolidado')
            
            arquivo_consolidado.seek(0)

            # Define o nome do arquivo e o caminho da pasta CONSOLIDADO
            nome_arquivo_excel = "Municipality_Code_consolidado.xlsx"
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
            print(f"❌ Erro ao consolidar arquivo Municipality Code: {str(e)}")
            raise

    def _convert_xlsb_to_xlsx(self, xlsb_file: str) -> str:
        """
        Converte um arquivo .xlsb para .xlsx.
        
        Args:
            xlsb_file: Caminho do arquivo .xlsb
            
        Returns:
            Caminho do arquivo .xlsx convertido
        """
        try:
            # Cria um arquivo temporário para o .xlsx
            temp_dir = tempfile.gettempdir()
            temp_file = os.path.join(temp_dir, f"{uuid.uuid4()}.xlsx")
            
            # Abre o arquivo .xlsb
            with open_workbook(xlsb_file) as wb:
                # Cria um novo arquivo .xlsx
                with pd.ExcelWriter(temp_file, engine='xlsxwriter') as writer:
                    # Para cada aba no arquivo .xlsb
                    for sheet in wb.sheets:
                        # Lê os dados da aba
                        data = []
                        for row in sheet.rows():
                            data.append([item.v for item in row])
                        
                        # Converte para DataFrame
                        df = pd.DataFrame(data)
                        
                        # Salva a aba no arquivo .xlsx
                        df.to_excel(writer, sheet_name=sheet.name, index=False, header=False)
            
            return temp_file
            
        except Exception as e:
            raise Exception(f"Erro ao converter arquivo .xlsb para .xlsx: {str(e)}")

    def extract(self, file_content: BytesIO = None) -> pd.DataFrame:
        """
        Extrai os dados do arquivo R189.
        
        Args:
            file_content: Conteúdo do arquivo em formato BytesIO
            
        Returns:
            DataFrame com os dados extraídos
        """
        try:
            if file_content:
                # Se recebeu o conteúdo do arquivo, processa diretamente
                arquivo_consolidado = self.consolidar_municipality_code(file_content)
                return pd.read_excel(arquivo_consolidado)
            else:
                # Se não recebeu o conteúdo, processa o arquivo do input_file
                xlsx_file = self.processar_arquivo()
                with open(xlsx_file, 'rb') as f:
                    arquivo_consolidado = self.consolidar_municipality_code(BytesIO(f.read()))
                return pd.read_excel(arquivo_consolidado)
                
        except Exception as e:
            raise Exception(f"Erro ao extrair dados do arquivo Municipality Code: {str(e)}")
