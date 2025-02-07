import pandas as pd
from io import BytesIO
from datetime import datetime
from auth.auth import SharePointAuth

class DivergenceReportQPER189:
    """
    Classe responsável por verificar divergências entre os arquivos consolidados QPE e R189.
    """
    
    def __init__(self):
        self.sharepoint_auth = SharePointAuth()

    def check_divergences(self, qpe_data: pd.DataFrame, r189_data: pd.DataFrame) -> tuple[bool, str, pd.DataFrame]:
        """
        Verifica divergências entre os dados consolidados do QPE e R189.
        
        Args:
            qpe_data: DataFrame com os dados consolidados do QPE
            r189_data: DataFrame com os dados consolidados do R189
            
        Returns:
            tuple: (sucesso, mensagem, DataFrame com divergências)
        """
        try:
            # Validação inicial dos DataFrames
            if qpe_data is None or r189_data is None:
                return False, "Erro: DataFrames não podem ser None", pd.DataFrame()
                
            if qpe_data.empty or r189_data.empty:
                return False, "Erro: DataFrames não podem estar vazios", pd.DataFrame()
            
            divergences = []
            
            # Contagem de QPE_ID
            qpe_ids = set(qpe_data['QPE_ID'].unique())
            r189_qpe_ids = set(r189_data[r189_data['Invoice number'].str.lower().str.startswith('qpe-', na=False)]['Invoice number'].unique())
            
            # Adiciona informação de quantidade ao início do relatório
            divergences.append({
                'Tipo': 'CONTAGEM_QPE',
                'QPE_ID': 'N/A',
                'CNPJ QPE': 'N/A',
                'CNPJ R189': 'N/A',
                'Valor QPE': len(qpe_ids),
                'Valor R189': len(r189_qpe_ids)
            })
            
            # Se houver divergência na quantidade, identifica quais estão faltando
            if len(qpe_ids) != len(r189_qpe_ids):
                # IDs que estão no QPE mas não no R189
                missing_in_r189 = qpe_ids - r189_qpe_ids
                for qpe_id in missing_in_r189:
                    qpe_row = qpe_data[qpe_data['QPE_ID'] == qpe_id].iloc[0]
                    divergences.append({
                        'Tipo': 'QPE_ID_AUSENTE_R189',
                        'QPE_ID': qpe_id,
                        'CNPJ QPE': qpe_row['CNPJ'],
                        'CNPJ R189': 'N/A',
                        'Valor QPE': qpe_row['VALOR_TOTAL'],
                        'Valor R189': 'N/A'
                    })
                
                # IDs que estão no R189 mas não no QPE
                missing_in_qpe = r189_qpe_ids - qpe_ids
                for r189_id in missing_in_qpe:
                    r189_row = r189_data[r189_data['Invoice number'] == r189_id].iloc[0]
                    divergences.append({
                        'Tipo': 'QPE_ID_AUSENTE_QPE',
                        'QPE_ID': r189_id,
                        'CNPJ QPE': 'N/A',
                        'CNPJ R189': r189_row['CNPJ - WEG'],
                        'Valor QPE': 'N/A',
                        'Valor R189': r189_row['Total Geral']
                    })
            
            # Verifica se as colunas necessárias existem
            qpe_required = ['QPE_ID', 'CNPJ', 'VALOR_TOTAL']
            r189_required = ['Invoice number', 'CNPJ - WEG', 'Total Geral']
            
            missing_qpe = [col for col in qpe_required if col not in qpe_data.columns]
            if missing_qpe:
                return False, f"Erro: Colunas necessárias não encontradas no QPE: {', '.join(missing_qpe)}", pd.DataFrame()
                
            missing_r189 = [col for col in r189_required if col not in r189_data.columns]
            if missing_r189:
                return False, f"Erro: Colunas necessárias não encontradas no R189: {', '.join(missing_r189)}", pd.DataFrame()
            
            # Validação de tipos de dados
            try:
                qpe_data['VALOR_TOTAL'] = pd.to_numeric(qpe_data['VALOR_TOTAL'], errors='coerce')
                r189_data['Total Geral'] = pd.to_numeric(r189_data['Total Geral'], errors='coerce')
            except Exception as e:
                return False, f"Erro: Valores inválidos nas colunas de valor: {str(e)}", pd.DataFrame()
            
            # Verifica valores nulos
            null_qpe_id = qpe_data['QPE_ID'].isnull().sum()
            null_qpe_cnpj = qpe_data['CNPJ'].isnull().sum()
            null_qpe_valor = qpe_data['VALOR_TOTAL'].isnull().sum()
            
            if any([null_qpe_id, null_qpe_cnpj, null_qpe_valor]):
                return False, (
                    "Erro: Encontrados valores nulos no QPE:\n"
                    f"QPE_ID: {null_qpe_id} valores nulos\n"
                    f"CNPJ: {null_qpe_cnpj} valores nulos\n"
                    f"VALOR_TOTAL: {null_qpe_valor} valores nulos"
                ), pd.DataFrame()
            
            # Itera sobre cada linha do QPE
            for idx, qpe_row in qpe_data.iterrows():
                qpe_id = str(qpe_row['QPE_ID']).strip()
                qpe_cnpj = str(qpe_row['CNPJ']).strip()
                qpe_valor = float(qpe_row['VALOR_TOTAL'])
                
                # Validação do QPE_ID
                if not qpe_id:
                    divergences.append({
                        'Tipo': 'QPE_ID vazio',
                        'QPE_ID': 'VAZIO',
                        'CNPJ QPE': qpe_cnpj,
                        'CNPJ R189': 'N/A',
                        'Valor QPE': qpe_valor,
                        'Valor R189': 'N/A'
                    })
                    continue
                
                # Validação do CNPJ
                if not qpe_cnpj or len(qpe_cnpj) != 18:  # Formato XX.XXX.XXX/XXXX-XX
                    divergences.append({
                        'Tipo': 'CNPJ inválido',
                        'QPE_ID': qpe_id,
                        'CNPJ QPE': qpe_cnpj,
                        'CNPJ R189': 'N/A',
                        'Valor QPE': qpe_valor,
                        'Valor R189': 'N/A'
                    })
                    continue
                
                # Procura o QPE_ID no R189
                r189_match = r189_data[r189_data['Invoice number'] == qpe_id]
                
                if r189_match.empty:
                    # QPE_ID não encontrado no R189
                    divergences.append({
                        'Tipo': 'QPE_ID não encontrado no R189',
                        'QPE_ID': qpe_id,
                        'CNPJ QPE': qpe_cnpj,
                        'CNPJ R189': 'Não encontrado',
                        'Valor QPE': qpe_valor,
                        'Valor R189': 'Não encontrado'
                    })
                else:
                    r189_row = r189_match.iloc[0]
                    r189_cnpj = str(r189_row['CNPJ - WEG']).strip()
                    r189_valor = float(r189_row['Total Geral'])
                    
                    # Verifica CNPJ
                    if qpe_cnpj != r189_cnpj:
                        divergences.append({
                            'Tipo': 'CNPJ divergente',
                            'QPE_ID': qpe_id,
                            'CNPJ QPE': qpe_cnpj,
                            'CNPJ R189': r189_cnpj,
                            'Valor QPE': qpe_valor,
                            'Valor R189': r189_valor
                        })
                    # Verifica Valor
                    elif abs(qpe_valor - r189_valor) > 0.01:  # Tolerância de 1 centavo
                        divergences.append({
                            'Tipo': 'Valor divergente',
                            'QPE_ID': qpe_id,
                            'CNPJ QPE': qpe_cnpj,
                            'CNPJ R189': r189_cnpj,
                            'Valor QPE': qpe_valor,
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
            required_columns = ['Tipo', 'QPE_ID', 'CNPJ QPE', 'CNPJ R189', 'Valor QPE', 'Valor R189']
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
                    divergences_df.to_excel(writer, index=False, sheet_name='Divergencias_QPE_R189')
                    
                    # Ajusta a largura das colunas
                    worksheet = writer.sheets['Divergencias_QPE_R189']
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
            filename = f"{now.strftime('%Y%m%d_%H%M%S')}_divergencias_qpe_r189.xlsx"
            
            # Envia para o SharePoint
            if self.sharepoint_auth.enviar_para_sharepoint(
                excel_file,
                filename,
                '/teams/BR-TI-TIN/AutomaoFinanas/RELATÓRIOS/QPE_R189'
            ):
                return True, f"Relatório salvo com sucesso: {filename}"
            else:
                return False, f"Erro ao salvar relatório no SharePoint: {filename}"
                
        except Exception as e:
            return False, f"Erro inesperado ao salvar relatório: {str(e)}"

    def generate_report(self) -> tuple[bool, str]:
        """
        Gera o relatório de divergências comparando QPE e R189.
        
        Returns:
            tuple: (sucesso, mensagem)
        """
        try:
            # Tenta baixar os arquivos consolidados
            qpe_consolidado = self.sharepoint_auth.baixar_arquivo_sharepoint(
                'QPE_consolidado.xlsx',
                '/teams/BR-TI-TIN/AutomaoFinanas/CONSOLIDADO'
            )
            
            if not qpe_consolidado:
                return False, "Erro: Arquivo QPE_consolidado.xlsx não encontrado no SharePoint"
            
            r189_consolidado = self.sharepoint_auth.baixar_arquivo_sharepoint(
                'R189_consolidado.xlsx',
                '/teams/BR-TI-TIN/AutomaoFinanas/CONSOLIDADO'
            )
            
            if not r189_consolidado:
                return False, "Erro: Arquivo R189_consolidado.xlsx não encontrado no SharePoint"
            
            try:
                # Lê os arquivos consolidados
                df_qpe = pd.read_excel(qpe_consolidado, sheet_name='Consolidado_QPE')
                df_r189 = pd.read_excel(r189_consolidado, sheet_name='Consolidado_R189')
            except Exception as e:
                return False, f"Erro ao ler arquivos consolidados: {str(e)}\n" + \
                            "Verifique se os arquivos estão corrompidos ou se as abas existem."
            
            if df_qpe.empty:
                return False, "Erro: Arquivo QPE_consolidado.xlsx está vazio"
                
            if df_r189.empty:
                return False, "Erro: Arquivo R189_consolidado.xlsx está vazio"
            
            # Verifica divergências
            success, message, divergences_df = self.check_divergences(df_qpe, df_r189)
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
                    "O arquivo foi salvo na pasta RELATÓRIOS/QPE_R189 no SharePoint."
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