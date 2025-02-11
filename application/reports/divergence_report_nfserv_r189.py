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

    def extract_id(self, id_str: str) -> str:
        """
        Extrai o ID base de uma string, removendo prefixos como QPE_, PIO_, etc.
        
        Args:
            id_str: String contendo o ID com possível prefixo
            
        Returns:
            str: ID base sem prefixo
        """
        try:
            # Converte para string e remove espaços
            id_str = str(id_str).strip()
            
            # Procura por padrão XXX-XXXXXX (onde X são números)
            if '-' in id_str:
                # Pega a parte após o último '_' se existir, senão usa a string completa
                base_id = id_str.split('_')[-1]
                return base_id.strip()
            return id_str
        except Exception:
            return id_str

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

            # Verifica valores nulos
            null_nfserv_id = nfserv_data['NFSERV_ID'].isnull().sum()
            null_nfserv_cnpj = nfserv_data['CNPJ'].isnull().sum()
            null_nfserv_valor = nfserv_data['VALOR_TOTAL'].isnull().sum()
            
            if any([null_nfserv_id, null_nfserv_cnpj, null_nfserv_valor]):
                return False, (
                    "Erro: Encontrados valores nulos no NFSERV:\n"
                    f"NFSERV_ID: {null_nfserv_id} valores nulos\n"
                    f"CNPJ: {null_nfserv_cnpj} valores nulos\n"
                    f"VALOR_TOTAL: {null_nfserv_valor} valores nulos"
                ), pd.DataFrame()
            
            # Criar conjuntos de IDs normalizados
            nfserv_ids = set(nfserv_data['NFSERV_ID'].apply(self.extract_id).str.lower())
            r189_ids = set(r189_data['Invoice number'].apply(self.extract_id).str.lower())
            
            # Adiciona informação de quantidade ao início do relatório
            divergences.append({
                'Tipo': 'CONTAGEM_NFSERV',
                'NFSERV_ID': 'N/A',
                'CNPJ NFSERV': 'N/A',
                'CNPJ R189': 'N/A',
                'Valor NFSERV': len(nfserv_ids),
                'Valor R189': len(r189_ids)
            })

            # Se houver divergência na quantidade, identifica quais estão faltando
            if len(nfserv_ids) != len(r189_ids):
                # IDs que estão no NFSERV mas não no R189
                missing_in_r189 = nfserv_ids - r189_ids
                for nfserv_id in missing_in_r189:
                    nfserv_row = nfserv_data[nfserv_data['NFSERV_ID'].apply(self.extract_id).str.lower() == nfserv_id].iloc[0]
                    divergences.append({
                        'Tipo': 'NFSERV_ID não encontrado no R189',
                        'NFSERV_ID': nfserv_row['NFSERV_ID'],
                        'CNPJ NFSERV': nfserv_row['CNPJ'],
                        'CNPJ R189': 'N/A',
                        'Valor NFSERV': nfserv_row['VALOR_TOTAL'],
                        'Valor R189': 'N/A'
                    })
                
                # IDs que estão no R189 mas não no NFSERV
                missing_in_nfserv = r189_ids - nfserv_ids
                for r189_id in missing_in_nfserv:
                    r189_row = r189_data[r189_data['Invoice number'].apply(self.extract_id).str.lower() == r189_id].iloc[0]
                    divergences.append({
                        'Tipo': 'NFSERV_ID não encontrado no NFSERV',
                        'NFSERV_ID': r189_row['Invoice number'],
                        'CNPJ NFSERV': 'N/A',
                        'CNPJ R189': r189_row['CNPJ - WEG'],
                        'Valor NFSERV': 'N/A',
                        'Valor R189': r189_row['Total Geral']
                    })

            # Itera sobre cada linha do NFSERV
            for idx, nfserv_row in nfserv_data.iterrows():
                nfserv_id = str(nfserv_row['NFSERV_ID']).strip()
                nfserv_base_id = self.extract_id(nfserv_id).lower()
                nfserv_cnpj = str(nfserv_row['CNPJ']).strip()
                nfserv_valor = float(nfserv_row['VALOR_TOTAL'])
                
                # Validação do NFSERV_ID
                if not nfserv_id:
                    divergences.append({
                        'Tipo': 'NFSERV_ID vazio',
                        'NFSERV_ID': 'VAZIO',
                        'CNPJ NFSERV': nfserv_cnpj,
                        'CNPJ R189': 'N/A',
                        'Valor NFSERV': nfserv_valor,
                        'Valor R189': 'N/A'
                    })
                    continue
                
                # Validação do CNPJ
                if not nfserv_cnpj or len(nfserv_cnpj) != 18:  # Formato XX.XXX.XXX/XXXX-XX
                    divergences.append({
                        'Tipo': 'CNPJ inválido',
                        'NFSERV_ID': nfserv_id,
                        'CNPJ NFSERV': nfserv_cnpj,
                        'CNPJ R189': 'N/A',
                        'Valor NFSERV': nfserv_valor,
                        'Valor R189': 'N/A'
                    })
                    continue
                
                # Procura o ID no R189
                r189_match = r189_data[r189_data['Invoice number'].apply(self.extract_id).str.lower() == nfserv_base_id]
                
                if not r189_match.empty:
                    r189_row = r189_match.iloc[0]
                    r189_cnpj = str(r189_row['CNPJ - WEG']).strip()
                    r189_valor = float(r189_row['Total Geral'])
                    
                    # Verifica CNPJ
                    if nfserv_cnpj != r189_cnpj:
                        divergences.append({
                            'Tipo': 'CNPJ divergente',
                            'NFSERV_ID': nfserv_id,
                            'CNPJ NFSERV': nfserv_cnpj,
                            'CNPJ R189': r189_cnpj,
                            'Valor NFSERV': nfserv_valor,
                            'Valor R189': r189_valor
                        })
                    # Verifica Valor
                    elif abs(nfserv_valor - r189_valor) > 0.01:  # Tolerância de 1 centavo
                        divergences.append({
                            'Tipo': 'Valor divergente',
                            'NFSERV_ID': nfserv_id,
                            'CNPJ NFSERV': nfserv_cnpj,
                            'CNPJ R189': r189_cnpj,
                            'Valor NFSERV': nfserv_valor,
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
                    
                    # Ajusta a largura das colunas
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
            nfserv_file = self.sharepoint_auth.baixar_arquivo_sharepoint(
                'NFSERV_consolidado.xlsx',
                '/teams/BR-TI-TIN/AutomaoFinanas/CONSOLIDADO'
            )
            if not nfserv_file:
                return False, "Erro: Não foi possível baixar o arquivo NFSERV_consolidado.xlsx do SharePoint"
            
            r189_file = self.sharepoint_auth.baixar_arquivo_sharepoint(
                'R189_consolidado.xlsx',
                '/teams/BR-TI-TIN/AutomaoFinanas/CONSOLIDADO'
            )
            if not r189_file:
                return False, "Erro: Não foi possível baixar o arquivo R189_consolidado.xlsx do SharePoint"
            
            try:
                # Carrega os arquivos em DataFrames
                nfserv_data = pd.read_excel(nfserv_file)
                r189_data = pd.read_excel(r189_file)
            except Exception as e:
                return False, f"Erro ao ler arquivos Excel: {str(e)}"
            
            # Verifica divergências
            success, message, divergences_df = self.check_divergences(nfserv_data, r189_data)
            if not success:
                return False, f"Erro ao verificar divergências: {message}"
                
            # Se houver divergências, salva o relatório
            if not divergences_df.empty:
                save_success, save_message = self.save_report(divergences_df)
                if not save_success:
                    return False, f"Erro ao salvar relatório: {save_message}"
                return True, f"Relatório gerado e salvo com sucesso.\n{message}\n{save_message}"
            
            return True, message  # "Nenhuma divergência encontrada nos dados analisados"
            
        except Exception as e:
            return False, f"Erro inesperado ao gerar relatório: {str(e)}"