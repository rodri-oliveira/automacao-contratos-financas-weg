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
            # Validação inicial dos DataFrames
            if spb_data is None or r189_data is None:
                return False, "Erro: DataFrames não podem ser None", pd.DataFrame()
                
            if spb_data.empty or r189_data.empty:
                return False, "Erro: DataFrames não podem estar vazios", pd.DataFrame()
            
            divergences = []
            
            # Contagem de SPB_ID
            spb_ids = set(spb_data['SPB_ID'].unique())
            # Contagem de SPB no R189 (filtrando por 'spb-')
            r189_spb_ids = set(r189_data[r189_data['Invoice number'].str.lower().str.startswith('spb-', na=False)]['Invoice number'].unique())
            
            # Adiciona informação de quantidade ao início do relatório
            divergences.append({
                'Tipo': 'CONTAGEM_SPB',
                'SPB_ID': 'N/A',
                'CNPJ SPB': 'N/A',
                'CNPJ R189': 'N/A',
                'Valor SPB': len(spb_ids),
                'Valor R189': len(r189_spb_ids)
            })

            # Se houver divergência na quantidade, identifica quais estão faltando
            if len(spb_ids) != len(r189_spb_ids):
                # IDs que estão no SPB mas não no R189
                missing_in_r189 = spb_ids - r189_spb_ids
                for spb_id in missing_in_r189:
                    spb_row = spb_data[spb_data['SPB_ID'] == spb_id].iloc[0]
                    divergences.append({
                        'Tipo': 'SPB_ID não encontrado no R189',
                        'SPB_ID': spb_id,
                        'CNPJ SPB': spb_row['CNPJ'],
                        'CNPJ R189': 'N/A',
                        'Valor SPB': spb_row['VALOR_TOTAL'],
                        'Valor R189': 'N/A'
                    })
                
                # IDs que estão no R189 mas não no SPB
                missing_in_spb = r189_spb_ids - spb_ids
                for r189_id in missing_in_spb:
                    r189_row = r189_data[r189_data['Invoice number'] == r189_id].iloc[0]
                    divergences.append({
                        'Tipo': 'SPB_ID não encontrado no SPB',
                        'SPB_ID': r189_id,
                        'CNPJ SPB': 'N/A',
                        'CNPJ R189': r189_row['CNPJ - WEG'],
                        'Valor SPB': 'N/A',
                        'Valor R189': r189_row['Total Geral']
                    })
            
            # Verifica se as colunas necessárias existem
            spb_required = ['SPB_ID', 'CNPJ', 'VALOR_TOTAL']
            r189_required = ['Invoice number', 'CNPJ - WEG', 'Total Geral']
            
            missing_spb = [col for col in spb_required if col not in spb_data.columns]
            if missing_spb:
                return False, f"Erro: Colunas necessárias não encontradas no SPB: {', '.join(missing_spb)}", pd.DataFrame()
                
            missing_r189 = [col for col in r189_required if col not in r189_data.columns]
            if missing_r189:
                return False, f"Erro: Colunas necessárias não encontradas no R189: {', '.join(missing_r189)}", pd.DataFrame()
            
            # Validação de tipos de dados
            try:
                spb_data['VALOR_TOTAL'] = pd.to_numeric(spb_data['VALOR_TOTAL'], errors='coerce')
                r189_data['Total Geral'] = pd.to_numeric(r189_data['Total Geral'], errors='coerce')
            except Exception as e:
                return False, f"Erro: Valores inválidos nas colunas de valor: {str(e)}", pd.DataFrame()
            
            # Verifica valores nulos
            null_spb_id = spb_data['SPB_ID'].isnull().sum()
            null_spb_cnpj = spb_data['CNPJ'].isnull().sum()
            null_spb_valor = spb_data['VALOR_TOTAL'].isnull().sum()
            
            if any([null_spb_id, null_spb_cnpj, null_spb_valor]):
                return False, (
                    "Erro: Encontrados valores nulos no SPB:\n"
                    f"SPB_ID: {null_spb_id} valores nulos\n"
                    f"CNPJ: {null_spb_cnpj} valores nulos\n"
                    f"VALOR_TOTAL: {null_spb_valor} valores nulos"
                ), pd.DataFrame()
            
            # Itera sobre cada linha do SPB
            for idx, spb_row in spb_data.iterrows():
                spb_id = str(spb_row['SPB_ID']).strip()
                spb_cnpj = str(spb_row['CNPJ']).strip()
                spb_valor = float(spb_row['VALOR_TOTAL'])
                
                # Validação do SPB_ID
                if not spb_id:
                    divergences.append({
                        'Tipo': 'SPB_ID vazio',
                        'SPB_ID': 'VAZIO',
                        'CNPJ SPB': spb_cnpj,
                        'CNPJ R189': 'N/A',
                        'Valor SPB': spb_valor,
                        'Valor R189': 'N/A'
                    })
                    continue
                
                # Validação do CNPJ
                if not spb_cnpj or len(spb_cnpj) != 18:  # Formato XX.XXX.XXX/XXXX-XX
                    divergences.append({
                        'Tipo': 'CNPJ inválido',
                        'SPB_ID': spb_id,
                        'CNPJ SPB': spb_cnpj,
                        'CNPJ R189': 'N/A',
                        'Valor SPB': spb_valor,
                        'Valor R189': 'N/A'
                    })
                    continue
                
                # Procura o SPB_ID no R189
                r189_match = r189_data[r189_data['Invoice number'] == spb_id]
                
                if r189_match.empty:
                    # Não adiciona novamente se já foi registrado como ausente
                    if spb_id not in missing_in_r189:
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
                    r189_cnpj = str(r189_row['CNPJ - WEG']).strip()
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
                return True, f"Encontradas {len(divergences)} divergências:\n" + \
                           f"- {df_divergences['Tipo'].value_counts().to_string()}", df_divergences
            
            return True, "Nenhuma divergência encontrada nos dados analisados", pd.DataFrame()
            
        except Exception as e:
            return False, f"Erro inesperado ao verificar divergências: {str(e)}\n" + \
                         "Por favor, verifique se os arquivos estão no formato correto.", pd.DataFrame()

    def save_report(self, divergences_df: pd.DataFrame) -> tuple[bool, str]:
        """
        Salva o relatório de divergências no SharePoint.
        
        Args:
            divergences_df: DataFrame com as divergências encontradas
            
        Returns:
            tuple: (sucesso, mensagem)
        """
        try:
            if divergences_df is None:
                return False, "Erro: DataFrame de divergências é None"
                
            if divergences_df.empty:
                return True, "Nenhuma divergência para salvar"
            
            # Validação das colunas necessárias
            required_columns = ['Tipo', 'SPB_ID', 'CNPJ SPB', 'CNPJ R189', 'Valor SPB', 'Valor R189']
            missing_columns = [col for col in required_columns if col not in divergences_df.columns]
            if missing_columns:
                return False, f"Erro: Colunas necessárias não encontradas no DataFrame de divergências: {', '.join(missing_columns)}"
            
            # Adiciona data e hora ao DataFrame
            now = datetime.now()
            divergences_df['Data Verificação'] = now.strftime('%Y-%m-%d')
            divergences_df['Hora Verificação'] = now.strftime('%H:%M:%S')
            
            try:
                # Cria o arquivo Excel na memória
                excel_file = BytesIO()
                with pd.ExcelWriter(excel_file, engine='xlsxwriter') as writer:
                    divergences_df.to_excel(writer, index=False, sheet_name='Divergencias_SPB_R189')
                    
                    # Ajusta a largura das colunas
                    worksheet = writer.sheets['Divergencias_SPB_R189']
                    for i, col in enumerate(divergences_df.columns):
                        max_length = max(
                            divergences_df[col].astype(str).apply(len).max(),
                            len(str(col))
                        )
                        worksheet.set_column(i, i, max_length + 2)
                
                excel_file.seek(0)
            except Exception as e:
                return False, f"Erro ao criar arquivo Excel: {str(e)}"
            
            # Nome do arquivo com timestamp no início
            filename = f"{now.strftime('%Y%m%d_%H%M%S')}_divergencias_spb_r189.xlsx"
            
            # Envia para o SharePoint
            if self.sharepoint_auth.enviar_para_sharepoint(
                excel_file,
                filename,
                '/teams/BR-TI-TIN/AutomaoFinanas/RELATÓRIOS/SPO_R189'
            ):
                return True, f"Relatório salvo com sucesso: {filename}"
            else:
                return False, f"Erro ao salvar relatório no SharePoint: {filename}"
                
        except Exception as e:
            return False, f"Erro inesperado ao salvar relatório: {str(e)}"

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
                return False, "Erro: Arquivo SPB_consolidado.xlsx não encontrado no SharePoint"
            
            r189_consolidado = self.sharepoint_auth.baixar_arquivo_sharepoint(
                'R189_consolidado.xlsx',
                '/teams/BR-TI-TIN/AutomaoFinanas/CONSOLIDADO'
            )
            
            if not r189_consolidado:
                return False, "Erro: Arquivo R189_consolidado.xlsx não encontrado no SharePoint"
            
            try:
                # Lê os arquivos consolidados
                df_spb = pd.read_excel(spb_consolidado, sheet_name='Consolidado_SPB')
                df_r189 = pd.read_excel(r189_consolidado, sheet_name='Consolidado_R189')
            except Exception as e:
                return False, f"Erro ao ler arquivos consolidados: {str(e)}\n" + \
                            "Verifique se os arquivos estão corrompidos ou se as abas existem."
            
            if df_spb.empty:
                return False, "Erro: Arquivo SPB_consolidado.xlsx está vazio"
                
            if df_r189.empty:
                return False, "Erro: Arquivo R189_consolidado.xlsx está vazio"
            
            # Verifica divergências
            success, message, divergences_df = self.check_divergences(df_spb, df_r189)
            if not success:
                return False, message
            
            # Se encontrou divergências, salva o relatório
            if not divergences_df.empty:
                save_success, save_message = self.save_report(divergences_df)
                if not save_success:
                    return False, save_message
                    
                # Retorna mensagem detalhada
                return True, (
                    "Relatório de divergências gerado e salvo com sucesso!\n\n"
                    f"Resumo das divergências encontradas:\n{message}\n\n"
                    "O arquivo foi salvo na pasta RELATÓRIOS/SPO_R189 no SharePoint."
                )
            
            return True, message
            
        except Exception as e:
            return False, (
                f"Erro inesperado ao gerar relatório: {str(e)}\n"
                "Por favor, verifique:\n"
                "1. Se os arquivos consolidados existem no SharePoint\n"
                "2. Se você tem permissão de acesso\n"
                "3. Se a conexão com o SharePoint está funcionando"
            )
