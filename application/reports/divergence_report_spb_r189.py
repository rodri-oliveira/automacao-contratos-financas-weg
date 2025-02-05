import pandas as pd
from io import BytesIO
from datetime import datetime
from auth.auth import SharePointAuth

class DivergenceReportSPBR189:
    """
    Classe responsável por verificar divergências entre os arquivos consolidados SPB e R189.
    """
    
    def __init__(self):
        self.sharepoint_auth = SharePointAuth()

    def check_divergences(self, spb_data: pd.DataFrame, r189_data: pd.DataFrame) -> tuple[bool, str, pd.DataFrame]:
        """
        Verifica divergências entre os dados consolidados do SPB e R189.
        
        Args:
            spb_data: DataFrame com os dados consolidados do SPB
            r189_data: DataFrame com os dados consolidados do R189
            
        Returns:
            tuple: (sucesso, mensagem, DataFrame com divergências)
        """
        try:
            divergences = []
            
            # Verifica se as colunas necessárias existem
            spb_required = ['SPB_ID', 'CNPJ', 'VALOR_TOTAL']
            r189_required = ['Invoice number', 'CNPJ - WEG', 'Total Geral']
            
            if not all(col in spb_data.columns for col in spb_required):
                return False, "Colunas necessárias não encontradas no arquivo SPB", pd.DataFrame()
                
            if not all(col in r189_data.columns for col in r189_required):
                return False, "Colunas necessárias não encontradas no arquivo R189", pd.DataFrame()
            
            # Itera sobre cada linha do SPB
            for idx, spb_row in spb_data.iterrows():
                spb_id = spb_row['SPB_ID']
                spb_cnpj = spb_row['CNPJ']
                spb_valor = float(spb_row['VALOR_TOTAL'])
                
                # Procura o SPB_ID no R189
                r189_match = r189_data[r189_data['Invoice number'] == spb_id]
                
                if r189_match.empty:
                    # SPB_ID não encontrado no R189
                    divergences.append({
                        'Tipo': 'SPB_ID não encontrado no R189',
                        'SPB_ID': spb_id,
                        'CNPJ SPB': spb_cnpj,
                        'CNPJ R189': 'Não encontrado',
                        'Valor SPB': spb_valor,
                        'Valor R189': 'Não encontrado'
                    })
                else:
                    r189_row = r189_match.iloc[0]
                    r189_cnpj = r189_row['CNPJ - WEG']
                    r189_valor = float(r189_row['Total Geral'])
                    
                    # Verifica CNPJ
                    if spb_cnpj != r189_cnpj:
                        divergences.append({
                            'Tipo': 'CNPJ divergente',
                            'SPB_ID': spb_id,
                            'CNPJ SPB': spb_cnpj,
                            'CNPJ R189': r189_cnpj,
                            'Valor SPB': spb_valor,
                            'Valor R189': r189_valor
                        })
                    # Verifica Valor
                    elif abs(spb_valor - r189_valor) > 0.01:  # Tolerância de 1 centavo
                        divergences.append({
                            'Tipo': 'Valor divergente',
                            'SPB_ID': spb_id,
                            'CNPJ SPB': spb_cnpj,
                            'CNPJ R189': r189_cnpj,
                            'Valor SPB': spb_valor,
                            'Valor R189': r189_valor
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
                divergences_df.to_excel(writer, index=False, sheet_name='Divergencias_SPB_R189')
            
            excel_file.seek(0)
            
            # Nome do arquivo com timestamp no início
            filename = f"{now.strftime('%Y%m%d_%H%M%S')}_divergencias_spb_r189.xlsx"
            
            # Envia para o SharePoint
            if self.sharepoint_auth.enviar_para_sharepoint(
                excel_file,
                filename,
                '/teams/BR-TI-TIN/AutomaoFinanas/RELATÓRIOS/SPO_R189'
            ):
                return True, "Relatório salvo com sucesso"
            else:
                return False, "Erro ao salvar relatório no SharePoint"
                
        except Exception as e:
            return False, f"Erro ao salvar relatório: {str(e)}"

    def generate_report(self) -> tuple[bool, str]:
        """
        Gera o relatório de divergências comparando SPB e R189.
        
        Returns:
            tuple: (sucesso, mensagem)
        """
        try:
            # Tenta baixar os arquivos consolidados
            spb_consolidado = self.sharepoint_auth.baixar_arquivo_sharepoint(
                'SPB_consolidado.xlsx',
                '/teams/BR-TI-TIN/AutomaoFinanas/CONSOLIDADO'
            )
            
            if not spb_consolidado:
                return False, "Arquivo SPB_consolidado.xlsx não encontrado"
            
            r189_consolidado = self.sharepoint_auth.baixar_arquivo_sharepoint(
                'R189_consolidado.xlsx',
                '/teams/BR-TI-TIN/AutomaoFinanas/CONSOLIDADO'
            )
            
            if not r189_consolidado:
                return False, "Arquivo R189_consolidado.xlsx não encontrado"
            
            # Lê os arquivos consolidados
            df_spb = pd.read_excel(spb_consolidado, sheet_name='Consolidado_SPB')
            df_r189 = pd.read_excel(r189_consolidado, sheet_name='Consolidado_R189')
            
            if df_spb.empty:
                return False, "Arquivo SPB_consolidado.xlsx está vazio"
                
            if df_r189.empty:
                return False, "Arquivo R189_consolidado.xlsx está vazio"
            
            # Verifica divergências
            success, message, divergences_df = self.check_divergences(df_spb, df_r189)
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
