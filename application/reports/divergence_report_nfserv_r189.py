import pandas as pd
from io import BytesIO
from datetime import datetime
from auth.auth import SharePointAuth

class DivergenceReportNFSERVR189:
    """
    Classe responsável por verificar divergências entre os arquivos consolidados NFSERV e R189.
    """
    
    def __init__(self):
        self.sharepoint_auth = SharePointAuth()

    def check_divergences(self, nfserv_data: pd.DataFrame, r189_data: pd.DataFrame) -> tuple[bool, str, pd.DataFrame]:
        """
        Verifica divergências entre os dados consolidados do NFSERV e R189.
        
        Args:
            nfserv_data: DataFrame com os dados consolidados do NFSERV
            r189_data: DataFrame com os dados consolidados do R189
            
        Returns:
            tuple: (sucesso, mensagem, DataFrame com divergências)
        """
        try:
            # Validação inicial dos DataFrames
            if nfserv_data is None or r189_data is None:
                return False, "Erro: DataFrames não podem ser None", pd.DataFrame()
                
            if nfserv_data.empty or r189_data.empty:
                return False, "Erro: DataFrames não podem estar vazios", pd.DataFrame()
            
            divergences = []
            
            # Extrai todas as siglas únicas do NFSERV_consolidado (exceto SPB)
            nfserv_ids = nfserv_data['NFSERV_ID'].unique()
            siglas_dict = {}
            
            # Conta as ocorrências de cada sigla no NFSERV
            for nfserv_id in nfserv_ids:
                if pd.isna(nfserv_id):
                    continue
                sigla = str(nfserv_id).split('-')[0]
                # Ignora IDs que começam com SPB
                if sigla == 'SPB':
                    continue
                if sigla not in siglas_dict:
                    siglas_dict[sigla] = {
                        'nfserv_count': 0,
                        'r189_count': 0,
                        'ids_nfserv': set(),
                        'ids_r189': set()
                    }
                siglas_dict[sigla]['nfserv_count'] += 1
                siglas_dict[sigla]['ids_nfserv'].add(nfserv_id)
            
            # Conta as ocorrências de cada sigla no R189
            r189_ids = r189_data['Invoice number'].unique()
            for r189_id in r189_ids:
                if pd.isna(r189_id):
                    continue
                sigla = str(r189_id).split('-')[0]
                # Ignora IDs que começam com SPB
                if sigla == 'SPB':
                    continue
                if sigla in siglas_dict:  # Só conta se a sigla existir no NFSERV
                    siglas_dict[sigla]['r189_count'] += 1
                    siglas_dict[sigla]['ids_r189'].add(r189_id)
            
            # Adiciona contagem por sigla ao relatório
            for sigla, counts in siglas_dict.items():
                if counts['nfserv_count'] != counts['r189_count']:
                    divergences.append({
                        'Tipo': f'CONTAGEM_{sigla}',
                        'NFSERV_ID': 'N/A',
                        'CNPJ NFSERV': 'N/A',
                        'CNPJ R189': 'N/A',
                        'Valor NFSERV': counts['nfserv_count'],
                        'Valor R189': counts['r189_count'],
                        'Detalhes': f'Sigla: {sigla}, NFSERV: {counts["nfserv_count"]}, R189: {counts["r189_count"]}'
                    })
                    
                    # IDs que estão no NFSERV mas não no R189
                    ids_faltando_r189 = counts['ids_nfserv'] - counts['ids_r189']
                    for nfserv_id in ids_faltando_r189:
                        nfserv_row = nfserv_data[nfserv_data['NFSERV_ID'] == nfserv_id].iloc[0]
                        divergences.append({
                            'Tipo': f'ID do {sigla} não encontrado no R189',
                            'NFSERV_ID': nfserv_id,
                            'CNPJ NFSERV': nfserv_row['CNPJ'],
                            'CNPJ R189': 'N/A',
                            'Valor NFSERV': nfserv_row['VALOR_TOTAL'],
                            'Valor R189': 'N/A'
                        })
                    
                    # IDs que estão no R189 mas não no NFSERV
                    ids_faltando_nfserv = counts['ids_r189'] - counts['ids_nfserv']
                    for r189_id in ids_faltando_nfserv:
                        r189_row = r189_data[r189_data['Invoice number'] == r189_id].iloc[0]
                        divergences.append({
                            'Tipo': f'ID encontrado apenas no R189 ({sigla})',
                            'NFSERV_ID': r189_id,
                            'CNPJ NFSERV': 'N/A',
                            'CNPJ R189': r189_row['CNPJ - WEG'],
                            'Valor NFSERV': 'N/A',
                            'Valor R189': r189_row['Total Geral']
                        })
            
            # Verifica divergências de CNPJ e valor para IDs que existem em ambos
            for sigla, counts in siglas_dict.items():
                ids_em_ambos = counts['ids_nfserv'].intersection(counts['ids_r189'])
                for nfserv_id in ids_em_ambos:
                    nfserv_row = nfserv_data[nfserv_data['NFSERV_ID'] == nfserv_id].iloc[0]
                    r189_row = r189_data[r189_data['Invoice number'] == nfserv_id].iloc[0]
                    
                    # Verifica CNPJ
                    if nfserv_row['CNPJ'] != r189_row['CNPJ - WEG']:
                        divergences.append({
                            'Tipo': f'CNPJ divergente ({sigla})',
                            'NFSERV_ID': nfserv_id,
                            'CNPJ NFSERV': nfserv_row['CNPJ'],
                            'CNPJ R189': r189_row['CNPJ - WEG'],
                            'Valor NFSERV': nfserv_row['VALOR_TOTAL'],
                            'Valor R189': r189_row['Total Geral']
                        })
                    
                    # Verifica valor
                    if float(str(nfserv_row['VALOR_TOTAL']).replace(',', '.')) != float(str(r189_row['Total Geral']).replace(',', '.')):
                        divergences.append({
                            'Tipo': f'Valor divergente ({sigla})',
                            'NFSERV_ID': nfserv_id,
                            'CNPJ NFSERV': nfserv_row['CNPJ'],
                            'CNPJ R189': r189_row['CNPJ - WEG'],
                            'Valor NFSERV': nfserv_row['VALOR_TOTAL'],
                            'Valor R189': r189_row['Total Geral']
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
            required_columns = ['Tipo', 'NFSERV_ID', 'CNPJ NFSERV', 'CNPJ R189', 'Valor NFSERV', 'Valor R189']
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
                    divergences_df.to_excel(writer, index=False, sheet_name='Divergencias_NFSERV_R189')
                    
                    # Ajusta largura das colunas
                    worksheet = writer.sheets['Divergencias_NFSERV_R189']
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
            filename = f"{now.strftime('%Y%m%d_%H%M%S')}_divergencias_nfserv_r189.xlsx"
            
            # Envia para o SharePoint
            if self.sharepoint_auth.enviar_para_sharepoint(
                excel_file,
                filename,
                '/teams/BR-TI-TIN/AutomaoFinanas/RELATÓRIOS/NFSERV_R189'
            ):
                return True, f"Relatório salvo com sucesso: {filename}"
            else:
                return False, f"Erro ao salvar relatório no SharePoint: {filename}"
                
        except Exception as e:
            return False, f"Erro inesperado ao salvar relatório: {str(e)}"

    def generate_report(self) -> tuple[bool, str]:
        """
        Gera o relatório de divergências comparando NFSERV e R189.
        
        Returns:
            tuple: (sucesso, mensagem)
        """
        try:
            # Tenta baixar os arquivos consolidados
            nfserv_consolidado = self.sharepoint_auth.baixar_arquivo_sharepoint(
                'NFSERV_consolidado.xlsx',
                '/teams/BR-TI-TIN/AutomaoFinanas/CONSOLIDADO'
            )
            
            if not nfserv_consolidado:
                return False, "Erro: Arquivo NFSERV_consolidado.xlsx não encontrado no SharePoint"
            
            r189_consolidado = self.sharepoint_auth.baixar_arquivo_sharepoint(
                'R189_consolidado.xlsx',
                '/teams/BR-TI-TIN/AutomaoFinanas/CONSOLIDADO'
            )
            
            if not r189_consolidado:
                return False, "Erro: Arquivo R189_consolidado.xlsx não encontrado no SharePoint"
            
            try:
                # Lê os arquivos consolidados
                df_nfserv = pd.read_excel(nfserv_consolidado, sheet_name='Consolidado_NFSERV')
                df_r189 = pd.read_excel(r189_consolidado, sheet_name='Consolidado_R189')
            except Exception as e:
                return False, f"Erro ao ler arquivos consolidados: {str(e)}\n" + \
                            "Verifique se os arquivos estão corrompidos ou se as abas existem."
            
            if df_nfserv.empty:
                return False, "Erro: Arquivo NFSERV_consolidado.xlsx está vazio"
                
            if df_r189.empty:
                return False, "Erro: Arquivo R189_consolidado.xlsx está vazio"
            
            # Verifica divergências
            success, message, divergences_df = self.check_divergences(df_nfserv, df_r189)
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
                    "O arquivo foi salvo na pasta RELATÓRIOS/NFSERV_R189 no SharePoint."
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
