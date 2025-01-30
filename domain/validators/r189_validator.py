# domain/validators/r189_validator.py
from interfaces.i_validator import IValidator

# Dados de referência
parametros = {
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

class R189Validator(IValidator):
    def validate(self, data, reference_data=parametros):
        """
        Valida os CNPJs extraídos do Excel contra os dados de referência.
        Retorna uma lista de CNPJs com o status 'Válido' ou 'Inválido'.
        """
        validated_data = []
        for row in data:
            cnpj = row.get("CNPJ")
            if cnpj not in reference_data:
                validated_data.append({"CNPJ": cnpj, "status": "Inválido"})
            else:
                validated_data.append({"CNPJ": cnpj, "status": "Válido"})
        return validated_data
