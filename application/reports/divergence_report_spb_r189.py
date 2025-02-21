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
        # Lista de possíveis nomes para a coluna de total
        self.colunas_total = ['Total Geral', 'Grand Total', 'Total Gera', 'Total', 'Valor Total']

    def check_divergences(self, spb_data: pd.DataFrame, r189_data: pd.DataFrame, nfserv_data: pd.DataFrame) -> tuple[bool, str, pd.DataFrame]:
        """
        Verifica divergências entre os dados consolidados do SPB e R189.
        
        Args:
            spb_data: DataFrame com os dados consolidados do SPB
            r189_data: DataFrame com os dados consolidados do R189
            nfserv_data: DataFrame com os dados consolidados do NFSERV
            
        Returns:
            tuple: (sucesso, mensagem, DataFrame com divergências)
        """
        try:
            # Validação inicial dos DataFrames
            if spb_data is None or r189_data is None or nfserv_data is None:
                return False, "Erro: DataFrames não podem ser None", pd.DataFrame()
                
            if spb_data.empty or r189_data.empty or nfserv_data.empty:
                return False, "Erro: DataFrames não podem estar vazios", pd.DataFrame()
            
            # Verifica qual coluna de total está presente no DataFrame do R189
            coluna_total_encontrada = None
            for col in self.colunas_total:
                if col in r189_data.columns:
                    coluna_total_encontrada = col
                    break
                    
            if not coluna_total_encontrada:
                return False, f"Erro: Nenhuma das colunas de total foi encontrada no R189. Esperado uma das seguintes: {self.colunas_total}", pd.DataFrame()
            
            # Verifica se as colunas necessárias existem no R189
            r189_required = ['Invoice number', 'CNPJ - WEG', coluna_total_encontrada]
            missing_r189 = [col for col in r189_required if col not in r189_data.columns]
            if missing_r189:
                return False, f"Erro: Colunas necessárias não encontradas no R189: {', '.join(missing_r189)}", pd.DataFrame()
            
            # Validação de tipos de dados
            try:
                spb_data['VALOR_TOTAL'] = pd.to_numeric(spb_data['VALOR_TOTAL'].astype(str).str.replace(',', '.'), errors='coerce')
                nfserv_data['VALOR_TOTAL'] = pd.to_numeric(nfserv_data['VALOR_TOTAL'].astype(str).str.replace(',', '.'), errors='coerce')
                r189_data[coluna_total_encontrada] = pd.to_numeric(r189_data[coluna_total_encontrada].astype(str).str.replace(',', '.'), errors='coerce')
            except Exception as e:
                return False, f"Erro: Valores inválidos nas colunas de valor: {str(e)}", pd.DataFrame()
            
            divergences = []
            
            # Contagem de SPB_ID do SPB_consolidado
            spb_ids = set(spb_data['SPB_ID'].unique())
            qtd_spb = len(spb_ids)
            
            # Contagem de SPB no NFSERV (procurando SPB no NFSERV_ID)
            nfserv_spb_ids = set(nfserv_data[nfserv_data['NFSERV_ID'].str.contains('SPB', na=False)]['NFSERV_ID'].unique())
            qtd_nfserv_spb = len(nfserv_spb_ids)
            
            # Contagem de SPB no R189
            r189_spb_ids = set(r189_data[r189_data['Invoice number'].str.contains('SPB', na=False)]['Invoice number'].unique())
            qtd_r189_spb = len(r189_spb_ids)
            
            # Adiciona informação de quantidade ao início do relatório
            if (qtd_spb + qtd_nfserv_spb) != qtd_r189_spb:
                divergences.append({
                    'Tipo': 'CONTAGEM_SPB',
                    'SPB_ID': 'N/A',
                    'CNPJ SPB': 'N/A',
                    'CNPJ R189': 'N/A',
                    'Valor SPB': qtd_spb + qtd_nfserv_spb,
                    'Valor R189': qtd_r189_spb,
                    'Detalhes': f'SPB: {qtd_spb}, NFSERV: {qtd_nfserv_spb}, R189: {qtd_r189_spb}'
                })
            
            # IDs que estão no R189 mas não em nenhum dos consolidados
            ids_r189_nao_encontrados = r189_spb_ids - (spb_ids.union(nfserv_spb_ids))
            for spb_id in ids_r189_nao_encontrados:
                r189_row = r189_data[r189_data['Invoice number'] == spb_id].iloc[0]
                divergences.append({
                    'Tipo': 'ID encontrado apenas no R189',
                    'SPB_ID': spb_id,
                    'CNPJ SPB': 'N/A',
                    'CNPJ R189': r189_row['CNPJ - WEG'],
                    'Valor SPB': 'N/A',
                    'Valor R189': r189_row[coluna_total_encontrada]
                })
            
            # IDs que estão nos consolidados mas não no R189
            todos_spb_ids = spb_ids.union(nfserv_spb_ids)
            ids_faltando_r189 = todos_spb_ids - r189_spb_ids
            for spb_id in ids_faltando_r189:
                # Procura primeiro no SPB_consolidado
                spb_row = spb_data[spb_data['SPB_ID'] == spb_id]
                if not spb_row.empty:
                    row = spb_row.iloc[0]
                    origem = "SPB"
                    cnpj = row['CNPJ']
                    valor = row['VALOR_TOTAL']
                else:
                    # Se não encontrou, procura no NFSERV
                    nfserv_row = nfserv_data[nfserv_data['NFSERV_ID'] == spb_id].iloc[0]
                    origem = "NFSERV"
                    cnpj = nfserv_row['CNPJ']
                    valor = nfserv_row['VALOR_TOTAL']
                
                divergences.append({
                    'Tipo': f'ID do {origem} não encontrado no R189',
                    'SPB_ID': spb_id,
                    'CNPJ SPB': cnpj,
                    'CNPJ R189': 'N/A',
                    'Valor SPB': valor,
                    'Valor R189': 'N/A'
                })
            
            # Verifica divergências de CNPJ e valor para IDs que existem em ambos
            ids_em_ambos = r189_spb_ids.intersection(todos_spb_ids)
            for spb_id in ids_em_ambos:
                r189_row = r189_data[r189_data['Invoice number'] == spb_id].iloc[0]
                
                # Procura primeiro no SPB_consolidado
                spb_row = spb_data[spb_data['SPB_ID'] == spb_id]
                if not spb_row.empty:
                    row = spb_row.iloc[0]
                    origem = "SPB"
                else:
                    # Se não encontrou, procura no NFSERV
                    nfserv_row = nfserv_data[nfserv_data['NFSERV_ID'] == spb_id].iloc[0]
                    row = nfserv_row
                    origem = "NFSERV"
                
                # Verifica CNPJ
                if row['CNPJ'] != r189_row['CNPJ - WEG']:
                    divergences.append({
                        'Tipo': 'CNPJ divergente',
                        'SPB_ID': spb_id,
                        'CNPJ SPB': row['CNPJ'],
                        'CNPJ R189': r189_row['CNPJ - WEG'],
                        'Valor SPB': row['VALOR_TOTAL'],
                        'Valor R189': r189_row[coluna_total_encontrada]
                    })
                
                # Verifica valor
                if float(str(row['VALOR_TOTAL']).replace(',', '.')) != float(str(r189_row[coluna_total_encontrada]).replace(',', '.')):
                    divergences.append({
                        'Tipo': 'Valor divergente',
                        'SPB_ID': spb_id,
                        'CNPJ SPB': row['CNPJ'],
                        'CNPJ R189': r189_row['CNPJ - WEG'],
                        'Valor SPB': row['VALOR_TOTAL'],
                        'Valor R189': r189_row[coluna_total_encontrada]
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

            nfserv_consolidado = self.sharepoint_auth.baixar_arquivo_sharepoint(
                'NFSERV_consolidado.xlsx',
                '/teams/BR-TI-TIN/AutomaoFinanas/CONSOLIDADO'
            )
            
            if not nfserv_consolidado:
                return False, "Erro: Arquivo NFSERV_consolidado.xlsx não encontrado no SharePoint"
            
            try:
                # Lê os arquivos consolidados
                df_spb = pd.read_excel(spb_consolidado, sheet_name='Consolidado_SPB')
                df_r189 = pd.read_excel(r189_consolidado, sheet_name='Consolidado_R189')
                df_nfserv = pd.read_excel(nfserv_consolidado, sheet_name='Consolidado_NFSERV')
            except Exception as e:
                return False, f"Erro ao ler arquivos consolidados: {str(e)}\n" + \
                            "Verifique se os arquivos estão corrompidos ou se as abas existem."
            
            if df_spb.empty:
                return False, "Erro: Arquivo SPB_consolidado.xlsx está vazio"
                
            if df_r189.empty:
                return False, "Erro: Arquivo R189_consolidado.xlsx está vazio"

            if df_nfserv.empty:
                return False, "Erro: Arquivo NFSERV_consolidado.xlsx está vazio"
            
            # Verifica divergências
            success, message, divergences_df = self.check_divergences(df_spb, df_r189, df_nfserv)
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