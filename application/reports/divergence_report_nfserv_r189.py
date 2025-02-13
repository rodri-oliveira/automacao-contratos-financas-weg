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
            
            # Extrai as siglas dos IDs
            def extract_sigla(id_value):
                if pd.isna(id_value):
                    return None
                parts = str(id_value).split('-')
                return parts[0] if len(parts) > 1 else None
            
            # Adiciona coluna de sigla em ambos os DataFrames
            nfserv_data['SIGLA'] = nfserv_data['NFSERV_ID'].apply(extract_sigla)
            r189_data['SIGLA'] = r189_data['Invoice number'].apply(extract_sigla)
            
            # Obtém siglas únicas (excluindo SPB e valores nulos)
            siglas_unicas = set(nfserv_data['SIGLA'].unique()) - {'SPB', None}
            
            # Verifica se as colunas necessárias existem
            nfserv_required = ['NFSERV_ID', 'CNPJ', 'VALOR_TOTAL']
            r189_required = ['Invoice number', 'CNPJ - WEG', 'Total Geral']
            
            missing_nfserv = [col for col in nfserv_required if col not in nfserv_data.columns]
            if missing_nfserv:
                return False, f"Erro: Colunas necessárias não encontradas no NFSERV: {', '.join(missing_nfserv)}", pd.DataFrame()
                
            missing_r189 = [col for col in r189_required if col not in r189_data.columns]
            if missing_r189:
                return False, f"Erro: Colunas necessárias não encontradas no R189: {', '.join(missing_r189)}", pd.DataFrame()
            
            # Validação de tipos de dados
            try:
                nfserv_data['VALOR_TOTAL'] = pd.to_numeric(nfserv_data['VALOR_TOTAL'], errors='coerce')
                r189_data['Total Geral'] = pd.to_numeric(r189_data['Total Geral'], errors='coerce')
            except Exception as e:
                return False, f"Erro: Valores inválidos nas colunas de valor: {str(e)}", pd.DataFrame()
            
            # Para cada sigla, verifica as contagens e divergências
            for sigla in siglas_unicas:
                # Contagem no NFSERV
                nfserv_count = len(nfserv_data[nfserv_data['SIGLA'] == sigla])
                
                # Contagem no R189
                r189_count = len(r189_data[r189_data['SIGLA'] == sigla])
                
                # Adiciona contagem para todas as siglas
                divergences.append({
                    'Tipo': f'CONTAGEM_{sigla}',
                    'NFSERV_ID': 'N/A',
                    'CNPJ NFSERV': 'N/A',
                    'CNPJ R189': 'N/A',
                    'Valor NFSERV': nfserv_count,
                    'Valor R189': r189_count,
                    'Detalhes': f'Total de notas {sigla}: NFSERV={nfserv_count}, R189={r189_count}'
                })
                
                # Se houver diferença nas contagens, registra a divergência
                if nfserv_count != r189_count:
                    divergences.append({
                        'Tipo': 'CONTAGEM_NFSERV',
                        'NFSERV_ID': 'N/A',
                        'CNPJ NFSERV': 'N/A',
                        'CNPJ R189': 'N/A',
                        'Valor NFSERV': nfserv_count,
                        'Valor R189': r189_count
                    })
                
                # Verifica IDs específicos da sigla
                nfserv_ids = set(nfserv_data[nfserv_data['SIGLA'] == sigla]['NFSERV_ID'])
                r189_ids = set(r189_data[r189_data['SIGLA'] == sigla]['Invoice number'])
                
                # IDs no NFSERV mas não no R189
                for nfserv_id in nfserv_ids - r189_ids:
                    nfserv_row = nfserv_data[nfserv_data['NFSERV_ID'] == nfserv_id].iloc[0]
                    divergences.append({
                        'Tipo': 'Nota não encontrada no R189',
                        'NFSERV_ID': nfserv_id,
                        'CNPJ NFSERV': nfserv_row['CNPJ'],
                        'CNPJ R189': 'Não encontrado',
                        'Valor NFSERV': nfserv_row['VALOR_TOTAL'],
                        'Valor R189': 'N/A',
                        'Detalhes': f'Nota {nfserv_id} existe no NFSERV mas não foi encontrada no R189'
                    })
                
                # IDs no R189 mas não no NFSERV
                for r189_id in r189_ids - nfserv_ids:
                    r189_row = r189_data[r189_data['Invoice number'] == r189_id].iloc[0]
                    divergences.append({
                        'Tipo': 'Nota não encontrada no NFSERV',
                        'NFSERV_ID': r189_id,
                        'CNPJ NFSERV': 'N/A',
                        'CNPJ R189': r189_row['CNPJ - WEG'],
                        'Valor NFSERV': 'N/A',
                        'Valor R189': r189_row['Total Geral'],
                        'Detalhes': f'Nota {r189_id} existe no R189 mas não foi encontrada no NFSERV'
                    })
                
                # Verifica divergências para IDs que existem em ambos
                for nfserv_id in nfserv_ids & r189_ids:
                    nfserv_row = nfserv_data[nfserv_data['NFSERV_ID'] == nfserv_id].iloc[0]
                    r189_row = r189_data[r189_data['Invoice number'] == nfserv_id].iloc[0]
                    
                    # Verifica CNPJ - Normaliza removendo espaços e pontuação
                    nfserv_cnpj = str(nfserv_row['CNPJ']).strip().replace('.', '').replace('-', '').replace('/', '')
                    r189_cnpj = str(r189_row['CNPJ - WEG']).strip().replace('.', '').replace('-', '').replace('/', '')
                    
                    if nfserv_cnpj != r189_cnpj:
                        divergences.append({
                            'Tipo': 'CNPJ divergente',
                            'NFSERV_ID': nfserv_id,
                            'CNPJ NFSERV': nfserv_row['CNPJ'],
                            'CNPJ R189': r189_row['CNPJ - WEG'],
                            'Valor NFSERV': nfserv_row['VALOR_TOTAL'],
                            'Valor R189': r189_row['Total Geral'],
                            'Detalhes': f'CNPJ diferente para nota {nfserv_id}: NFSERV={nfserv_row["CNPJ"]}, R189={r189_row["CNPJ - WEG"]}'
                        })
                    
                    # Verifica Valor
                    try:
                        # Trata valores com vírgula ou ponto
                        nfserv_valor = str(nfserv_row['VALOR_TOTAL']).strip().replace(',', '.')
                        r189_valor = str(r189_row['Total Geral']).strip().replace(',', '.')
                        
                        # Remove caracteres não numéricos exceto ponto
                        nfserv_valor = ''.join(c for c in nfserv_valor if c.isdigit() or c == '.')
                        r189_valor = ''.join(c for c in r189_valor if c.isdigit() or c == '.')
                        
                        # Converte para float
                        nfserv_valor = float(nfserv_valor)
                        r189_valor = float(r189_valor)
                        
                        if abs(nfserv_valor - r189_valor) > 0.01:
                            divergences.append({
                                'Tipo': 'Valor divergente',
                                'NFSERV_ID': nfserv_id,
                                'CNPJ NFSERV': nfserv_row['CNPJ'],
                                'CNPJ R189': r189_row['CNPJ - WEG'],
                                'Valor NFSERV': nfserv_valor,
                                'Valor R189': r189_valor,
                                'Detalhes': f'Valor diferente para nota {nfserv_id}: NFSERV={nfserv_valor:.2f}, R189={r189_valor:.2f}'
                            })
                    except (ValueError, TypeError) as e:
                        # Se houver erro na conversão, registra como divergência
                        divergences.append({
                            'Tipo': 'Erro na validação de valor',
                            'NFSERV_ID': nfserv_id,
                            'CNPJ NFSERV': nfserv_row['CNPJ'],
                            'CNPJ R189': r189_row['CNPJ - WEG'],
                            'Valor NFSERV': str(nfserv_row['VALOR_TOTAL']),
                            'Valor R189': str(r189_row['Total Geral']),
                            'Detalhes': f'Erro ao comparar valores para nota {nfserv_id}: Formato inválido'
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
            return (
                False,
                f"Erro inesperado ao gerar relatório: {str(e)}\n"
                "Por favor, verifique:\n"
                "1. Se os arquivos consolidados existem no SharePoint\n"
                "2. Se você tem permissão de acesso\n"
                "3. Se a conexão com o SharePoint está funcionando"
            )