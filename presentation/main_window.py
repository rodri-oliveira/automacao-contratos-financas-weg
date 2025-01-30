import os
import requests
import tkinter as tk
from tkinter import messagebox
from auth import obter_token_sharepoint  # Importa a função para obter o token


# Obter as variáveis de ambiente
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
TENANT_ID = os.getenv('TENANT_ID')
RESOURCE = os.getenv('RESOURCE')
SITE_URL = os.getenv('SITE_URL')


def obter_token_sharepoint():
    """Obtém um token de autenticação do SharePoint usando credenciais de cliente."""
    url = f"https://accounts.accesscontrol.windows.net/{TENANT_ID}/tokens/OAuth/2"
    
    payload = {
        'grant_type': 'client_credentials',
        'client_id': f"{CLIENT_ID}@{TENANT_ID}",
        'client_secret': CLIENT_SECRET,
        'resource': f"{RESOURCE}@{TENANT_ID}"
    }

    try:
        response = requests.post(url, data=payload)
        response.raise_for_status()
        return response.json()['access_token']
    except requests.exceptions.RequestException as e:
        print(f"Erro ao obter token: {e}")
        raise Exception("Falha ao obter o token de autenticação.")


def buscar_arquivos_pasta(caminho_pasta, token):
    """Busca arquivos em uma pasta específica no SharePoint."""
    url = f"https://weg365.sharepoint.com/_api/web/GetFolderByServerRelativeUrl('{caminho_pasta}')/Files"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json;odata=verbose"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()  # Retorna a resposta JSON com os arquivos
    except requests.exceptions.RequestException as e:
        print(f"Erro ao buscar arquivos: {e}")
        return None


def buscar_arquivos_r189(token):
    url = "https://weg365.sharepoint.com/teams/BR-TI-TIN/_api/web/GetFolderByServerRelativeUrl('/teams/BR-TI-TIN/AutomaoFinanas/R189')/Files"
    
    headers = {
        "Accept": "application/json;odata=verbose",
        "Authorization": f"Bearer {token}"
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        dados = response.json()
        arquivos = [arquivo["Name"] for arquivo in dados["d"]["results"]]
        
        if arquivos:
            print("Arquivos encontrados na pasta R189:", arquivos)
            return arquivos
        else:
            print("Nenhum arquivo encontrado na pasta R189.")
            return None
    else:
        print(f"Erro ao buscar arquivos: {response.status_code} - {response.text}")
        return None




# Janela principal do tkinter
class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Validação de Documentos Fiscais")
        self.geometry("800x600")
        self.create_widgets()

    def create_widgets(self):
        self.tab_view = tk.Frame(self)
        self.tab_view.pack(fill="both", expand=True)

        self.r189_tab = tk.Frame(self.tab_view)
        self.r189_tab.pack(pady=10)
        self.qpe_tab = tk.Frame(self.tab_view)
        self.qpe_tab.pack(pady=10)
        self.spb_tab = tk.Frame(self.tab_view)
        self.spb_tab.pack(pady=10)

        # Remover o botão de navegação e adicionar o botão de validação
        tk.Button(self.r189_tab, text="Validar R189", command=self.validar_r189).pack(pady=10)
        tk.Button(self.qpe_tab, text="Validar QPE", command=self.validate_qpe).pack(pady=10)
        tk.Button(self.spb_tab, text="Validar SPB", command=self.validate_spb).pack(pady=10)

    def validar_r189(self):
        token = obter_token_sharepoint()  # Obtém o token de autenticação
        if token:
            buscar_arquivos_r189(token)  # Agora a função recebe o token corretamente
        else:
            print("Erro: Não foi possível obter o token.")


    def validate_qpe(self):
        print("Validação QPE em progresso...")

    def validate_spb(self):
        print("Validação SPB em progresso...")

if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()
