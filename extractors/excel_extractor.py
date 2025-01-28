import pandas as pd

class ExcelExtractor:
    def extract(self, file_path, sheet_name=None):
        try:
            if sheet_name:
                return pd.read_excel(file_path, sheet_name=sheet_name)
            return pd.read_excel(file_path)
        except Exception as e:
            raise Exception(f"Erro ao extrair dados do Excel: {e}")
