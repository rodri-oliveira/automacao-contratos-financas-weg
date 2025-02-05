# application/reports/divergence_report_r189.py

import pandas as pd
from io import BytesIO
from datetime import datetime
from auth.auth import SharePointAuth

class DivergenceReportR189:
    """
    Classe responsável por verificar divergências no arquivo R189.
    """
    
    def __init__(self):
        self.sharepoint_auth = SharePointAuth()
        
        # Mapeamento de CNPJ para Site Name esperado
        self.cnpj_site_mapping = {
            "60.621.141/0005-87": ["PMAR_BRCSA"],
            "07.175.725/0030-02": ["WEL_BRGCV"],
            "60.621.141/0006-68": ["PMAR_BRMUA"],
            "07.175.725/0010-50": ["WEL_BRJGS"],
            "10.885.321/0001-74": ["WLI_BRLNH"],
            "84.584.994/0007-16": ["WTB_BRSZO"],
            "07.175.725/0042-38": ["WEL_BRBTI"],
            "14.759.173/0001-00": ["WCES_BRMTT"],
            "14.759.173/0002-83": ["WCES_BRBGV"],
            "07.175.725/0024-56": ["WEL_BRRPO"],
            "07.175.725/0014-84": ["WEL_BRBNU"],
            "13.772.125/0007-77": ["RF_BRCOR"],
            "07.175.725/0004-02": ["WEL_BRITJ"],
            "60.621.141/0004-04": ["PMAR_BRGRM"],
            "07.175.725/0021-03": ["WEL_BRSBC"],
            "07.175.725/0026-18": ["WEL_BRSPO"]
        }

    def check_divergences(self, consolidated_data: pd.DataFrame) -> tuple[bool, str, pd.DataFrame]:
        """
        Verifica divergências entre os dados consolidados e o mapeamento esperado.
        
        Args:
            consolidated_data: DataFrame com os dados consolidados do R189
            
        Returns:
            tuple: (sucesso, mensagem, DataFrame com divergências)
        """
        try:
            divergences = []
            
            # Verifica se as colunas necessárias existem
            required_columns = ['CNPJ - WEG', 'Site Name - WEG 2']
            if not all(col in consolidated_data.columns for col in required_columns):
                return False, "Colunas necessárias não encontradas no arquivo", pd.DataFrame()
            
            # Itera sobre cada linha do DataFrame
            for idx, row in consolidated_data.iterrows():
                cnpj = row['CNPJ - WEG']
                site_name = row['Site Name - WEG 2']
                
                # Verifica se o CNPJ existe no mapeamento
                if cnpj in self.cnpj_site_mapping:
                    # Verifica se o Site Name está correto
                    if site_name not in self.cnpj_site_mapping[cnpj]:
                        divergences.append({
                            'CNPJ': cnpj,
                            'Site Name Encontrado': site_name,
                            'Site Name Esperado': ', '.join(self.cnpj_site_mapping[cnpj]),
                            'Invoice Number': row.get('Invoice number', ''),
                            'Total Geral': row.get('Total Geral', '')
                        })
                else:
                    divergences.append({
                        'CNPJ': cnpj,
                        'Site Name Encontrado': site_name,
                        'Site Name Esperado': 'CNPJ não mapeado',
                        'Invoice Number': row.get('Invoice number', ''),
                        'Total Geral': row.get('Total Geral', '')
                    })
            
            if divergences:
                df_divergences = pd.DataFrame(divergences)
                return True, f"Encontradas {len(divergences)} divergências", df_divergences
            
            return True, "Nenhuma divergência encontrada", pd.DataFrame()
            
        except Exception as e:
            return False, f"Erro ao verificar divergências: {str(e)}", pd.DataFrame()

    def save_report(self, divergences_df: pd.DataFrame) -> tuple[bool, str]:
        """
        Salva o relatório de divergências no SharePoint.
        
        Args:
            divergences_df: DataFrame com as divergências encontradas
            
        Returns:
            tuple: (sucesso, mensagem)
        """
        try:
            if divergences_df.empty:
                return True, "Nenhuma divergência para salvar"
            
            # Adiciona data e hora ao DataFrame
            now = datetime.now()
            divergences_df['Data Verificação'] = now.strftime('%Y-%m-%d')
            divergences_df['Hora Verificação'] = now.strftime('%H:%M:%S')
            
            # Cria o arquivo Excel na memória
            excel_file = BytesIO()
            with pd.ExcelWriter(excel_file, engine='xlsxwriter') as writer:
                divergences_df.to_excel(writer, index=False, sheet_name='Divergencias_R189')
            
            excel_file.seek(0)
            
            # Nome do arquivo com timestamp
            filename = f"divergencias_r189_{now.strftime('%Y%m%d_%H%M%S')}.xlsx"
            
            # Envia para o SharePoint
            if self.sharepoint_auth.enviar_para_sharepoint(
                excel_file,
                filename,
                '/teams/BR-TI-TIN/AutomaoFinanas/RELATÓRIOS'
            ):
                return True, "Relatório salvo com sucesso"
            else:
                return False, "Erro ao salvar relatório no SharePoint"
                
        except Exception as e:
            return False, f"Erro ao salvar relatório: {str(e)}"

    def generate_report(self) -> tuple[bool, str]:
        """
        Gera o relatório de divergências a partir do arquivo consolidado.
        
        Returns:
            tuple: (sucesso, mensagem)
        """
        try:
            # Tenta baixar o arquivo consolidado
            consolidado = self.sharepoint_auth.baixar_arquivo_sharepoint(
                'R189_consolidado.xlsx',
                '/teams/BR-TI-TIN/AutomaoFinanas/CONSOLIDADO'
            )
            
            if not consolidado:
                return False, "Arquivo R189_consolidado.xlsx não encontrado"
            
            # Lê o arquivo consolidado
            df = pd.read_excel(consolidado, sheet_name='Consolidado_R189')
            
            if df.empty:
                return False, "Arquivo consolidado está vazio"
            
            # Verifica divergências
            success, message, divergences_df = self.check_divergences(df)
            if not success:
                return False, message
            
            # Se encontrou divergências, salva o relatório
            if not divergences_df.empty:
                save_success, save_message = self.save_report(divergences_df)
                if not save_success:
                    return False, save_message
                return True, "Relatório de divergências gerado e salvo com sucesso"
            
            return True, message
            
        except Exception as e:
            return False, f"Erro ao gerar relatório: {str(e)}"