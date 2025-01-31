import re

texto = "CNPJ: 12.345.678/0001-90"
padrao_cnpj = r"\d{2,3}[.-]?\d{3}[.-]?\d{3}[/-]?\d{4}[.-]?\d{2}"

match = re.search(padrao_cnpj, texto)
if match:
    print("CNPJ encontrado:", match.group())
else:
    print("Nenhum CNPJ encontrado.")
