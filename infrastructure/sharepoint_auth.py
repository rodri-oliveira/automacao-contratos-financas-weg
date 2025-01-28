from office365.runtime.auth.authentication_context import AuthenticationContext
from office365.sharepoint.client_context import ClientContext
import os
from dotenv import load_dotenv

load_dotenv()

class SharePointAuth:
    def __init__(self):
        self.site_url = os.getenv("SHAREPOINT_URL")
        self.client_id = os.getenv("CLIENT_ID")
        self.client_secret = os.getenv("CLIENT_SECRET")
        self.context = None

    def authenticate(self):
        context_auth = AuthenticationContext(self.site_url)
        if context_auth.acquire_token_for_app(self.client_id, self.client_secret):
            self.context = ClientContext(self.site_url, context_auth)
        else:
            raise Exception("Erro ao autenticar no SharePoint")
