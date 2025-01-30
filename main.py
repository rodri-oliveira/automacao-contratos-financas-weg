import os
import requests
import tkinter as tk
from tkinter import ttk, messagebox
from auth.auth import SharePointAuth
from application.extractors.r189_extractor import R189Extractor

# Constantes
SITE_URL = os.getenv('SITE_URL')
PASTAS = {
    'R189': "/teams/BR-TI-TIN/AutomaoFinanas/R189",
    'QPE': "/teams/BR-TI-TIN/AutomaoFinanas/QPE",
    'SPB': "/teams/BR-TI-TIN/AutomaoFinanas/SPB"
}

def buscar_arquivos(auth, pasta):
    """Busca arquivos na pasta especificada do SharePoint."""
    token = auth.acquire_token()
    if not token:
        return None

    url = f"{SITE_URL}/_api/web/GetFolderByServerRelativeUrl('{pasta}')/Files"
    headers = {
        "Accept": "application/json;odata=verbose",
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            dados = response.json()
            arquivos = [arquivo["Name"] for arquivo in dados["d"]["results"]]
            print("✅ Arquivos encontrados:", arquivos)
            return arquivos
        else:
            print(f"❌ Erro ao buscar arquivos: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Erro durante a busca: {str(e)}")
        return None

class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Validação de Documentos Fiscais")
        self.geometry("1024x768")
        self.configure(bg='#f0f0f0')
        
        self.auth = SharePointAuth()
        self.arquivos_encontrados = []
        
        self.create_widgets()
        self.setup_styles()

    def setup_styles(self):
        style = ttk.Style()
        style.configure('TNotebook', background='#f0f0f0')
        style.configure('TFrame', background='#f0f0f0')
        style.configure('Custom.TButton', padding=10, font=('Helvetica', 10))

    def create_widgets(self):
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)

        self.tabs = {}
        for aba in PASTAS.keys():
            self.tabs[aba] = ttk.Frame(self.notebook)
            self.notebook.add(self.tabs[aba], text=aba)
            self.setup_tab(aba)

    def setup_tab(self, aba):
        frame = self.tabs[aba]
        
        button_frame = ttk.Frame(frame)
        button_frame.pack(pady=20)
        
        ttk.Button(
            button_frame,
            text="Buscar Arquivos",
            command=lambda a=aba: self.buscar_arquivos(a),
            style='Custom.TButton'
        ).pack(pady=5)

        ttk.Button(
            button_frame,
            text="Processar Arquivos Selecionados",
            command=lambda a=aba: self.processar_arquivos(a),
            style='Custom.TButton'
        ).pack(pady=5)

        lista_frame = ttk.Frame(frame)
        lista_frame.pack(fill='both', expand=True, padx=20)

        ttk.Label(
            lista_frame,
            text="Arquivos Encontrados:",
            font=('Helvetica', 10, 'bold')
        ).pack(anchor='w', pady=(0, 5))

        list_frame = ttk.Frame(lista_frame)
        list_frame.pack(fill='both', expand=True)

        listbox = tk.Listbox(list_frame, selectmode='multiple', font=('Helvetica', 10))
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=listbox.yview)
        listbox.configure(yscrollcommand=scrollbar.set)

        listbox.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        setattr(self, f'listbox_{aba}', listbox)

        status_var = tk.StringVar()
        status_bar = ttk.Label(frame, textvariable=status_var, font=('Helvetica', 9))
        status_bar.pack(side='bottom', fill='x', pady=5)
        
        setattr(self, f'status_var_{aba}', status_var)

    def buscar_arquivos(self, aba):
        status_var = getattr(self, f'status_var_{aba}')
        listbox = getattr(self, f'listbox_{aba}')
        
        status_var.set("Buscando arquivos...")
        self.update_idletasks()

        try:
            arquivos = buscar_arquivos(self.auth, PASTAS[aba])
            if arquivos:
                self.arquivos_encontrados = arquivos
                listbox.delete(0, tk.END)
                for arquivo in arquivos:
                    listbox.insert(tk.END, arquivo)
                status_var.set(f"Encontrados {len(arquivos)} arquivos")
            else:
                status_var.set("Nenhum arquivo encontrado")
                messagebox.showinfo("Informação", f"Nenhum arquivo encontrado na pasta {aba}")
        except Exception as e:
            status_var.set("Erro ao buscar arquivos")
            messagebox.showerror("Erro", f"Erro ao buscar arquivos: {str(e)}")

    def processar_arquivos(self, aba):
        listbox = getattr(self, f'listbox_{aba}')
        status_var = getattr(self, f'status_var_{aba}')
        
        selecionados = listbox.curselection()
        if not selecionados:
            messagebox.showwarning("Aviso", "Selecione pelo menos um arquivo para processar")
            return

        status_var.set("Processando arquivos...")
        self.update_idletasks()
        
        try:
            for idx in selecionados:
                arquivo = listbox.get(idx)
                status_var.set(f"Processando {arquivo}...")
                self.update_idletasks()
                
                conteudo = self.auth.baixar_arquivo_sharepoint(arquivo, PASTAS[aba])
                if conteudo:
                    if aba == 'R189':
                        self.processar_r189(arquivo, conteudo)
                    
            status_var.set("Processamento concluído")
            messagebox.showinfo("Sucesso", "Processamento dos arquivos concluído")
        except Exception as e:
            status_var.set("Erro no processamento")
            messagebox.showerror("Erro", f"Erro durante o processamento: {str(e)}")

    def processar_r189(self, arquivo, conteudo):
        extractor = R189Extractor("", "")
        resultado = extractor.consolidar_r189(conteudo)
        
        if resultado:
            # Força a extensão .xlsx no nome do arquivo
            nome_base = os.path.splitext(arquivo)[0]  # Remove a extensão atual
            nome_destino = f"consolidado_{nome_base}.xlsx"  # Adiciona .xlsx
            
            if self.auth.enviar_para_sharepoint(resultado, nome_destino, PASTAS['R189']):
                print(f"✅ Arquivo {arquivo} processado e enviado com sucesso")
            else:
                print(f"❌ Erro ao enviar arquivo processado: {arquivo}")

if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()