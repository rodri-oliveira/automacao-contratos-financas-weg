from domain.r189_validator import IValidator

class R189Validator(IValidator):
    def validate(self, data, reference_data):
        validated_data = []
        for row in data:
            if row["CNPJ"] not in reference_data:
                validated_data.append({"CNPJ": row["CNPJ"], "status": "Inválido"})
            else:
                validated_data.append({"CNPJ": row["CNPJ"], "status": "Válido"})
        return validated_data
