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
            "03115 - Assessoria E Consultoria": {
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

    def validate_service_cnpj(self, row) -> bool:
        """
        Valida se o CNPJ está autorizado para o serviço específico.
        
        Args:
            row: Linha do DataFrame contendo Municipality Code e CNPJ - WEG
            
        Returns:
            bool: True se o CNPJ está autorizado para o serviço, False caso contrário
        """
        municipality_code = str(row['Municipality Code']).strip()
        cnpj = str(row['CNPJ - WEG']).strip()
        
        # Procura o serviço que corresponde ao código municipal
        service = None
        for service_name, cnpjs in self.service_cnpj_mapping.items():
            if service_name.startswith(municipality_code):
                service = service_name
                break
        
        if not service:
            return False
            
        return cnpj in self.service_cnpj_mapping[service]

    def check_divergences(self, mun_code_data: pd.DataFrame, r189_data: pd.DataFrame) -> tuple[bool, str, pd.DataFrame]:
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
        """
        try:
            # Primeiro, valida os CNPJs por serviço
            mun_code_data['CNPJ_Autorizado'] = mun_code_data.apply(self.validate_service_cnpj, axis=1)
            
            # Filtra apenas os registros com CNPJs não autorizados
            cnpj_divergences = mun_code_data[~mun_code_data['CNPJ_Autorizado']].copy()
            cnpj_divergences['Tipo_Divergencia'] = 'CNPJ não autorizado para o serviço'
            
            # Remove a coluna de validação para o próximo passo
            mun_code_data = mun_code_data[mun_code_data['CNPJ_Autorizado']].drop('CNPJ_Autorizado', axis=1)
            
            # Agrupa os dados por Municipality Code, CNPJ - WEG e Invoice number
            grouped_data = mun_code_data.groupby(
                ['Municipality Code', 'CNPJ - WEG', 'Invoice number']
            ).agg({
                'Total Geral': 'sum',
                'Site Name - WEG 2': 'first'  # Mantém o primeiro Site Name encontrado
            }).reset_index()
            
            # Verifica se há duplicatas após o agrupamento
            duplicates = grouped_data[grouped_data.duplicated(
                subset=['Municipality Code', 'CNPJ - WEG', 'Invoice number'],
                keep=False
            )].copy()
            
            if not duplicates.empty:
                duplicates['Tipo_Divergencia'] = 'Duplicata após agrupamento'
            
            # Combina as divergências de CNPJ e duplicatas
            all_divergences = pd.concat([cnpj_divergences, duplicates], ignore_index=True)
            
            has_divergences = not all_divergences.empty
            
            if has_divergences:
                message = (
                    f"Encontradas {len(cnpj_divergences)} divergências de CNPJ não autorizado e "
                    f"{len(duplicates)} duplicatas após agrupamento."
                )
                return True, message, all_divergences
            else:
                message = "Nenhuma divergência encontrada."
                return False, message, pd.DataFrame()
            
        except Exception as e:
            return True, f"Erro ao verificar divergências: {str(e)}", pd.DataFrame()

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
            mun_code_file = self.sharepoint_auth.buscar_arquivo_sharepoint(
                'Municipality_Code_consolidado.xlsx',
                '/teams/BR-TI-TIN/AutomaoFinanas/CONSOLIDADO'
            )
            
            r189_file = self.sharepoint_auth.buscar_arquivo_sharepoint(
                'R189_consolidado.xlsx',
                '/teams/BR-TI-TIN/AutomaoFinanas/CONSOLIDADO'
            )
            
            if not mun_code_file or not r189_file:
                return False, "Não foi possível encontrar os arquivos consolidados no SharePoint."
            
            # Lê os arquivos em DataFrames
            mun_code_data = pd.read_excel(BytesIO(mun_code_file.content))
            r189_data = pd.read_excel(BytesIO(r189_file.content))
            
            # Verifica divergências
            has_divergences, message, divergences = self.check_divergences(mun_code_data, r189_data)
            
            if has_divergences and not divergences.empty:
                # Gera o arquivo de relatório
                report_file = BytesIO()
                with pd.ExcelWriter(report_file, engine='xlsxwriter') as writer:
                    divergences.to_excel(writer, index=False, sheet_name='Divergencias')
                
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