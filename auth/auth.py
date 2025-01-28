import os
from dotenv import load_dotenv
from office365.runtime.auth.client_credential import ClientCredential
from office365.sharepoint.client_context import ClientContext

class SharePointAuth:
    def __init__(self):
        # Carrega as variáveis de ambiente do arquivo .env
        load_dotenv()
        self.client_id = os.getenv("CLIENT_ID")
        self.client_secret = os.getenv("CLIENT_SECRET")
        self.tenant_id = os.getenv("TENANT_ID")
        self.resource = os.getenv("RESOURCE")
        self.site_url = os.getenv("SITE_URL")

        # Valida se todas as credenciais estão presentes
        self._validate_credentials()

    def _validate_credentials(self):
        """Verifica se as credenciais estão disponíveis."""
        missing_vars = [
            var_name
            for var_name in ["CLIENT_ID", "CLIENT_SECRET", "TENANT_ID", "RESOURCE", "SITE_URL"]
            if not os.getenv(var_name)
        ]
        if missing_vars:
            raise ValueError(f"As seguintes variáveis de ambiente estão ausentes no .env: {', '.join(missing_vars)}")

    def authenticate(self):
        """
        Autentica no SharePoint usando OAuth2 e retorna o contexto do site.
        """
        try:
            # Configura as credenciais do cliente
            credentials = ClientCredential(self.client_id, self.client_secret)

            # Conecta ao site SharePoint
            context = ClientContext(self.site_url).with_credentials(credentials)
            return context
        except Exception as e:
            raise ConnectionError(f"Erro ao autenticar com o SharePoint: {e}")
