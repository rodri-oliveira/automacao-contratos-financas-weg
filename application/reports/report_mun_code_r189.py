import pandas as pd
from io import BytesIO
from datetime import datetime
from auth.auth import SharePointAuth

class DivergenceReportMUNCODER189:
    """
    Classe responsável por verificar divergências entre os arquivos consolidados de códigos municipais e R189.
    """
    
    def __init__(self):
        self.sharepoint_auth = SharePointAuth()
        self.service_cnpj_mapping = {
            "14.02 - Assistência Técnica": {
                "14.759.173/0002-83", "07.175.725/0042-38", "07.175.725/0014-84",
                "60.621.141/0005-87", "13.772.125/0007-77", "07.175.725/0030-02",
                "60.621.141/0004-04", "07.175.725/0004-02", "07.175.725/0010-50",
                "10.885.321/0001-74", "60.621.141/0006-68", "14.759.173/0001-00",
                "07.175.725/0024-56", "07.175.725/0021-03", "07.175.725/0026-18",
                "84.584.994/0007-16"
            },
            "17.01 - Acessoria ou Consultoria": {
                "14.759.173/0002-83", "07.175.725/0042-38", "07.175.725/0014-84",
                "60.621.141/0005-87", "13.772.125/0007-77", "07.175.725/0030-02",
                "60.621.141/0004-04", "07.175.725/0004-02", "07.175.725/0010-50",
                "10.885.321/0001-74", "60.621.141/0006-68", "14.759.173/0001-00",
                "07.175.725/0024-56", "07.175.725/0021-03", "07.175.725/0026-18",
                "84.584.994/0007-16"
            },
            "14.01 - LUBRIFICACAO, LIMPEZA": {
                "14.759.173/0002-83", "07.175.725/0042-38", "07.175.725/0014-84",
                "60.621.141/0005-87", "13.772.125/0007-77", "07.175.725/0030-02",
                "60.621.141/0004-04", "07.175.725/0004-02", "07.175.725/0010-50",
                "10.885.321/0001-74", "60.621.141/0006-68", "14.759.173/0001-00",
                "07.175.725/0024-56", "07.175.725/0021-03", "07.175.725/0026-18",
                "84.584.994/0007-16"
            },
            "1.07 - SUPORTE TECNICO EM INFORMATICA": {
                "14.759.173/0002-83", "07.175.725/0042-38", "07.175.725/0014-84",
                "60.621.141/0005-87", "13.772.125/0007-77", "07.175.725/0030-02",
                "60.621.141/0004-04", "07.175.725/0004-02", "07.175.725/0010-50",
                "10.885.321/0001-74", "60.621.141/0006-68", "14.759.173/0001-00",
                "07.175.725/0024-56", "07.175.725/0021-03", "07.175.725/0026-18",
                "84.584.994/0007-16"
            },
            "3115 - Assessoria E Consultoria": {
                "14.759.173/0002-83", "07.175.725/0042-38", "07.175.725/0014-84",
                "60.621.141/0005-87", "13.772.125/0007-77", "07.175.725/0030-02",
                "60.621.141/0004-04", "07.175.725/0004-02", "07.175.725/0010-50",
                "10.885.321/0001-74", "60.621.141/0006-68", "14.759.173/0001-00",
                "07.175.725/0024-56", "07.175.725/0021-03", "07.175.725/0026-18",
                "84.584.994/0007-16"
            },
            "1880 - Assistência Técnica - Instalação": {
                "14.759.173/0002-83", "07.175.725/0042-38", "07.175.725/0014-84",
                "60.621.141/0005-87", "13.772.125/0007-77", "07.175.725/0030-02",
                "60.621.141/0004-04", "07.175.725/0004-02", "07.175.725/0010-50",
                "10.885.321/0001-74", "60.621.141/0006-68", "14.759.173/0001-00",
                "07.175.725/0024-56", "07.175.725/0021-03", "07.175.725/0026-18",
                "84.584.994/0007-16"
            },
            "1.03 - Processamento e Armazenamento": {
                "14.759.173/0002-83", "07.175.725/0042-38", "07.175.725/0014-84",
                "60.621.141/0005-87", "13.772.125/0007-77", "07.175.725/0030-02",
                "60.621.141/0004-04", "07.175.725/0004-02", "07.175.725/0010-50",
                "10.885.321/0001-74", "60.621.141/0006-68", "14.759.173/0001-00",
                "07.175.725/0024-56", "07.175.725/0021-03", "07.175.725/0026-18",
                "84.584.994/0007-16"
            }
        }
        
        # Lista de possíveis nomes para a coluna de total
        self.colunas_total = ['Total Geral', 'Grand Total', 'Total Gera', 'Total', 'Valor Total']

    def validate_service_cnpj(self, row) -> bool:
        """
        Valida se o CNPJ está autorizado para o serviço específico.
        
        Args:
            row: Linha do DataFrame contendo Municipality Code e CNPJ - WEG
            
        Returns:
            bool: True se o CNPJ está autorizado para o serviço, False caso contrário
        """
        # Converte o código do município para inteiro
        try:
            municipality_code = str(int(float(str(row['Municipality Code']).strip())))
        except (ValueError, TypeError):
            municipality_code = str(row['Municipality Code']).strip()
            
        cnpj = str(row['CNPJ - WEG']).strip()
        
        # Debug: imprime os valores para verificação
        print(f"Validando: Municipality Code={municipality_code}, CNPJ={cnpj}")
        
        # Procura o serviço que corresponde ao código municipal
        service = None
        for service_name in self.service_cnpj_mapping:
            # Extrai apenas o código numérico do nome do serviço e converte para inteiro
            try:
                service_code = str(int(float(service_name.split(' - ')[0].strip())))
            except (ValueError, TypeError):
                service_code = service_name.split(' - ')[0].strip()
                
            print(f"Comparando: {service_code} == {municipality_code}")
            if service_code == municipality_code:
                service = service_name
                print(f"Serviço encontrado: {service}")
                break
        
        if not service:
            print(f"Nenhum serviço encontrado para o código {municipality_code}")
            return False
        
        is_authorized = cnpj in self.service_cnpj_mapping[service]
        print(f"CNPJ {cnpj} {'está' if is_authorized else 'não está'} autorizado para o serviço {service}")
        return is_authorized

    def check_divergences(self, mun_code_data: pd.DataFrame, r189_data: pd.DataFrame) -> tuple[bool, str, pd.DataFrame, pd.DataFrame]:
        """
        Verifica divergências entre os dados consolidados dos códigos municipais e R189.
        
        Args:
            mun_code_data: DataFrame com os dados consolidados dos códigos municipais
            r189_data: DataFrame com os dados consolidados do R189
            
        Returns:
            tuple contendo:
            - bool: True se houver divergências, False caso contrário
            - str: Mensagem descritiva do resultado
            - DataFrame: DataFrame com as divergências encontradas
            - DataFrame: DataFrame com os dados agrupados
        """
        try:
            # Verifica qual coluna de total está presente no DataFrame
            coluna_total = None
            for col in self.colunas_total:
                if col in mun_code_data.columns:
                    coluna_total = col
                    break
                    
            if not coluna_total:
                raise ValueError(f"Nenhuma coluna de total encontrada. Colunas disponíveis: {', '.join(self.colunas_total)}")

            # Primeiro, valida os CNPJs por serviço
            mun_code_data['CNPJ_Autorizado'] = mun_code_data.apply(self.validate_service_cnpj, axis=1)
            
            # Filtra apenas os registros com CNPJs não autorizados
            cnpj_divergences = mun_code_data[~mun_code_data['CNPJ_Autorizado']].copy()
            cnpj_divergences['Tipo_Divergencia'] = 'CNPJ não autorizado para o serviço'
            
            # Filtra apenas os registros com CNPJs autorizados para o agrupamento
            valid_data = mun_code_data[mun_code_data['CNPJ_Autorizado']].drop('CNPJ_Autorizado', axis=1)
            
            # Agrupa os dados por Municipality Code, CNPJ - WEG e Invoice number
            grouped_data = valid_data.groupby(
                ['Municipality Code', 'CNPJ - WEG', 'Invoice number']
            ).agg({
                coluna_total: 'sum',
                'Site Name - WEG 2': 'first'  # Mantém o primeiro Site Name encontrado
            }).reset_index()
            
            # Ordena o DataFrame agrupado para melhor visualização
            grouped_data = grouped_data.sort_values(
                by=['Municipality Code', 'CNPJ - WEG', 'Invoice number']
            )
            
            has_divergences = not cnpj_divergences.empty
            
            if has_divergences:
                message = f"Encontradas {len(cnpj_divergences)} divergências de CNPJ não autorizado."
            else:
                message = "Nenhuma divergência encontrada."
                
            message += f"\nForam geradas {len(grouped_data)} linhas após o agrupamento."
            
            return True, message, cnpj_divergences, grouped_data
            
        except Exception as e:
            return True, f"Erro ao verificar divergências: {str(e)}", pd.DataFrame(), pd.DataFrame()

    def generate_report(self) -> tuple[bool, str]:
        """
        Gera o relatório de divergências entre códigos municipais e R189.
        
        Returns:
            tuple contendo:
            - bool: True se o relatório foi gerado com sucesso, False caso contrário
            - str: Mensagem descritiva do resultado
        """
        try:
            # Busca os arquivos consolidados no SharePoint
            mun_code_file = self.sharepoint_auth.baixar_arquivo_sharepoint(
                'Municipality_Code_consolidado.xlsx',
                '/teams/BR-TI-TIN/AutomaoFinanas/CONSOLIDADO'
            )
            
            r189_file = self.sharepoint_auth.baixar_arquivo_sharepoint(
                'R189_consolidado.xlsx',
                '/teams/BR-TI-TIN/AutomaoFinanas/CONSOLIDADO'
            )
            
            if not mun_code_file or not r189_file:
                return False, "Não foi possível encontrar os arquivos consolidados no SharePoint."
            
            # Lê os arquivos em DataFrames
            mun_code_data = pd.read_excel(mun_code_file)
            r189_data = pd.read_excel(r189_file)
            
            # Verifica divergências e obtém dados agrupados
            has_data, message, divergences, grouped_data = self.check_divergences(mun_code_data, r189_data)
            
            if has_data:
                # Gera o arquivo de relatório
                report_file = BytesIO()
                with pd.ExcelWriter(report_file, engine='xlsxwriter') as writer:
                    # Aba de divergências (se houver)
                    if not divergences.empty:
                        divergences.to_excel(
                            writer, 
                            index=False, 
                            sheet_name='Divergencias_CNPJs'
                        )
                    
                    # Aba de dados agrupados
                    grouped_data.to_excel(
                        writer, 
                        index=False, 
                        sheet_name='Dados_Agrupados'
                    )
                    
                    # Ajusta o formato das colunas
                    workbook = writer.book
                    
                    # Formato para valores monetários
                    money_format = workbook.add_format({'num_format': '#,##0.00'})
                    
                    # Aplica formato nas abas
                    for sheet_name in writer.sheets:
                        worksheet = writer.sheets[sheet_name]
                        # Ajusta largura das colunas
                        for idx, col in enumerate(grouped_data.columns):
                            max_length = max(
                                grouped_data[col].astype(str).apply(len).max(),
                                len(col)
                            )
                            worksheet.set_column(idx, idx, max_length + 2)
                        
                        # Aplica formato monetário na coluna de total
                        for col in self.colunas_total:
                            if col in grouped_data.columns:
                                total_col = grouped_data.columns.get_loc(col)
                                worksheet.set_column(total_col, total_col, None, money_format)
                                break
                report_file.seek(0)
                
                # Define o nome do arquivo com timestamp
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                report_name = f'report_mun_code_r189_{timestamp}.xlsx'
                
                # Envia o relatório para o SharePoint
                self.sharepoint_auth.enviar_para_sharepoint(
                    report_file,
                    report_name,
                    '/teams/BR-TI-TIN/AutomaoFinanas/RELATÓRIOS/MUN_CODE'
                )
                
                message += f"\nRelatório gerado com sucesso: {report_name}"
            
            return True, message
            
        except Exception as e:
            return False, f"Erro ao gerar relatório: {str(e)}"