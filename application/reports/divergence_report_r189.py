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
        
        # Lista de possíveis nomes para a coluna de total
        self.colunas_total = ['Total Geral', 'Grand Total', 'Total Gera']

    def check_divergences(self, consolidated_data: pd.DataFrame) -> tuple[bool, str, pd.DataFrame]:
        """
        Verifica divergências entre os dados consolidados e o mapeamento esperado.
        
        Args:
            consolidated_data: DataFrame com os dados consolidados do R189
            
        Returns:
            tuple: (sucesso, mensagem, DataFrame com divergências)
        """
        try:
            # Validação inicial do DataFrame
            if consolidated_data is None:
                return False, "Erro: DataFrame não pode ser None", pd.DataFrame()
                
            if consolidated_data.empty:
                return False, "Erro: DataFrame está vazio", pd.DataFrame()
            
            divergences = []
            
            # Verifica qual coluna de total está presente no DataFrame
            coluna_total_encontrada = None
            for col in self.colunas_total:
                if col in consolidated_data.columns:
                    coluna_total_encontrada = col
                    break
                    
            if not coluna_total_encontrada:
                return False, f"Erro: Nenhuma das colunas de total foi encontrada. Esperado uma das seguintes: {self.colunas_total}", pd.DataFrame()
            
            # Verifica se as colunas necessárias existem
            required_columns = ['CNPJ - WEG', 'Site Name - WEG 2', 'Invoice number', coluna_total_encontrada]
            missing_columns = [col for col in required_columns if col not in consolidated_data.columns]
            if missing_columns:
                return False, f"Erro: Colunas necessárias não encontradas: {', '.join(missing_columns)}", pd.DataFrame()
            
            # Validação de tipos de dados
            try:
                consolidated_data[coluna_total_encontrada] = pd.to_numeric(consolidated_data[coluna_total_encontrada], errors='coerce')
            except Exception as e:
                return False, f"Erro: Valores inválidos na coluna '{coluna_total_encontrada}': {str(e)}", pd.DataFrame()
            
            # Verifica valores nulos
            null_cnpj = consolidated_data['CNPJ - WEG'].isnull().sum()
            null_site = consolidated_data['Site Name - WEG 2'].isnull().sum()
            null_invoice = consolidated_data['Invoice number'].isnull().sum()
            null_total = consolidated_data[coluna_total_encontrada].isnull().sum()
            
            if any([null_cnpj, null_site, null_invoice, null_total]):
                return False, (
                    "Erro: Encontrados valores nulos:\n"
                    f"CNPJ: {null_cnpj} valores nulos\n"
                    f"Site Name: {null_site} valores nulos\n"
                    f"Invoice: {null_invoice} valores nulos\n"
                    f"{coluna_total_encontrada}: {null_total} valores nulos"
                ), pd.DataFrame()
            
            # Itera sobre cada linha do DataFrame
            for idx, row in consolidated_data.iterrows():
                cnpj = str(row['CNPJ - WEG']).strip()
                site_name = str(row['Site Name - WEG 2']).strip()
                invoice = str(row['Invoice number']).strip()
                valor = float(row[coluna_total_encontrada])
                
                # Validação do CNPJ
                if not cnpj or len(cnpj) != 18:  # Formato XX.XXX.XXX/XXXX-XX
                    divergences.append({
                        'Tipo': 'CNPJ inválido',
                        'Invoice Number': invoice,
                        'CNPJ': cnpj,
                        'Site Name Encontrado': site_name,
                        'Site Name Esperado': 'CNPJ em formato inválido',
                        'Total Geral': valor
                    })
                    continue
                
                # Validação do Site Name
                if not site_name:
                    divergences.append({
                        'Tipo': 'Site Name vazio',
                        'Invoice Number': invoice,
                        'CNPJ': cnpj,
                        'Site Name Encontrado': 'VAZIO',
                        'Site Name Esperado': 'Site Name não pode ser vazio',
                        'Total Geral': valor
                    })
                    continue
                
                # Verifica se o CNPJ existe no mapeamento
                if cnpj in self.cnpj_site_mapping:
                    # Verifica se o Site Name está correto
                    if site_name not in self.cnpj_site_mapping[cnpj]:
                        divergences.append({
                            'Tipo': 'Site Name incorreto',
                            'Invoice Number': invoice,
                            'CNPJ': cnpj,
                            'Site Name Encontrado': site_name,
                            'Site Name Esperado': ', '.join(self.cnpj_site_mapping[cnpj]),
                            'Total Geral': valor
                        })
                else:
                    divergences.append({
                        'Tipo': 'CNPJ não mapeado',
                        'Invoice Number': invoice,
                        'CNPJ': cnpj,
                        'Site Name Encontrado': site_name,
                        'Site Name Esperado': 'CNPJ não cadastrado',
                        'Total Geral': valor
                    })
            
            if divergences:
                df_divergences = pd.DataFrame(divergences)
                return True, f"Encontradas {len(divergences)} divergências:\n" + \
                           f"- {df_divergences['Tipo'].value_counts().to_string()}", df_divergences
            
            return True, "Nenhuma divergência encontrada nos dados analisados", pd.DataFrame()
            
        except Exception as e:
            return False, f"Erro inesperado ao verificar divergências: {str(e)}\n" + \
                         "Por favor, verifique se o arquivo está no formato correto.", pd.DataFrame()

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
            required_columns = ['Tipo', 'Invoice Number', 'CNPJ', 'Site Name Encontrado', 'Site Name Esperado', 'Total Geral']
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
                    divergences_df.to_excel(writer, index=False, sheet_name='Divergencias_R189')
                    
                    # Ajusta a largura das colunas
                    worksheet = writer.sheets['Divergencias_R189']
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
            filename = f"{now.strftime('%Y%m%d_%H%M%S')}_divergencias_r189.xlsx"
            
            # Envia para o SharePoint
            if self.sharepoint_auth.enviar_para_sharepoint(
                excel_file,
                filename,
                '/teams/BR-TI-TIN/AutomaoFinanas/RELATÓRIOS/R189'
            ):
                return True, f"Relatório salvo com sucesso: {filename}"
            else:
                return False, f"Erro ao salvar relatório no SharePoint: {filename}"
                
        except Exception as e:
            return False, f"Erro inesperado ao salvar relatório: {str(e)}"

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
                return False, "Erro: Arquivo R189_consolidado.xlsx não encontrado no SharePoint"
            
            try:
                # Lê o arquivo consolidado
                df = pd.read_excel(consolidado, sheet_name='Consolidado_R189')
            except Exception as e:
                return False, f"Erro ao ler arquivo consolidado: {str(e)}\n" + \
                            "Verifique se o arquivo está corrompido ou se a aba 'Consolidado_R189' existe."
            
            if df.empty:
                return False, "Erro: Arquivo consolidado está vazio"
            
            # Verifica divergências
            success, message, divergences_df = self.check_divergences(df)
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
                    "O arquivo foi salvo na pasta RELATÓRIOS/R189 no SharePoint."
                )
            
            return True, message
            
        except Exception as e:
            return False, (
                f"Erro inesperado ao gerar relatório: {str(e)}\n"
                "Por favor, verifique:\n"
                "1. Se o arquivo consolidado existe no SharePoint\n"
                "2. Se você tem permissão de acesso\n"
                "3. Se a conexão com o SharePoint está funcionando"
            )