import os
import requests
import tkinter as tk
from tkinter import ttk, messagebox
from auth.auth import SharePointAuth
from application.extractors.r189_extractor import R189Extractor
from application.extractors.qpe_extractor import QPEExtractor  # Nova importação
from application.extractors.spb_extractor import SPBExtractor  # Nova importação
import tempfile

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

        # Adiciona os botões de verificação apenas na aba R189
        if aba == 'R189':
            ttk.Button(
                button_frame,
                text="Verificar Divergências R189",
                command=self.verificar_divergencias,
                style='Custom.TButton'
            ).pack(pady=5)
            
            ttk.Button(
                button_frame,
                text="Verificar Divergências QPE vs R189",
                command=self.verificar_divergencias_qpe_r189,
                style='Custom.TButton'
            ).pack(pady=5)

            ttk.Button(
                button_frame,
                text="Verificar Divergências SPB vs R189",
                command=self.verificar_divergencias_spb_r189,
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
            arquivos_selecionados = [listbox.get(idx) for idx in selecionados]
            processadores = {
                'R189': self.processar_r189,
                'QPE': self.processar_qpe,
                'SPB': self.processar_spb
            }
            
            if aba in processadores:
                processadores[aba](arquivos_selecionados)

            status_var.set("Processamento concluído")
            messagebox.showinfo("Sucesso", "Processamento dos arquivos concluído")
        except Exception as e:
            status_var.set("Erro no processamento")
            messagebox.showerror("Erro", f"Erro durante o processamento: {str(e)}")

    def processar_r189(self, arquivos_selecionados: list) -> None:
        """
        Processa os arquivos R189 selecionados.
        
        Args:
            arquivos_selecionados: Lista de arquivos selecionados
        """
        try:
            if not arquivos_selecionados:
                print("❌ Nenhum arquivo selecionado")
                return

            for arquivo in arquivos_selecionados:
                try:
                    print(f"Baixando arquivo: {arquivo}")
                    conteudo = self.auth.baixar_arquivo_sharepoint(
                        arquivo,
                        '/teams/BR-TI-TIN/AutomaoFinanas/R189'
                    )
                    
                    if not conteudo:
                        print(f"❌ Erro ao baixar arquivo: {arquivo}")
                        continue
                    
                    # Cria uma instância do R189Extractor
                    extractor = R189Extractor("", "")
                    
                    # Processa o arquivo
                    resultado = extractor.consolidar_r189(conteudo)
                    
                    if resultado:
                        print(f"✅ Arquivo {arquivo} processado com sucesso")
                    else:
                        print(f"❌ Erro ao processar arquivo: {arquivo}")
                    
                except Exception as e:
                    print(f"❌ Erro ao processar arquivo {arquivo}: {str(e)}")
                    continue
                
        except Exception as e:
            print(f"❌ Erro ao processar arquivos R189: {str(e)}")
            raise

    def processar_qpe(self, arquivos_selecionados: list) -> None:
        """Processa arquivos QPE selecionados"""
        try:
            # Obtém todos os arquivos selecionados
            listbox = getattr(self, f'listbox_QPE')
            selecionados = listbox.curselection()
            
            # Lista para armazenar o conteúdo de todos os PDFs selecionados
            pdfs_selecionados = []
            
            # Coleta o conteúdo de todos os PDFs selecionados
            for idx in selecionados:
                arquivo_nome = listbox.get(idx)
                pdf_content = self.auth.baixar_arquivo_sharepoint(arquivo_nome, PASTAS['QPE'])
                if pdf_content:
                    pdfs_selecionados.append(pdf_content)
                    print(f"✅ Arquivo {arquivo_nome} carregado com sucesso")
                else:
                    print(f"❌ Erro ao carregar arquivo: {arquivo_nome}")
            
            if pdfs_selecionados:
                # Processa todos os PDFs de uma vez
                extractor = QPEExtractor("", "")
                extractor.consolidar_qpe(pdfs_selecionados)
                print(f"✅ Todos os arquivos foram processados e consolidados com sucesso")
            else:
                print("❌ Nenhum arquivo foi carregado com sucesso")
                
        except Exception as e:
            print(f"❌ Erro ao processar arquivos QPE: {str(e)}")

    def processar_spb(self, arquivos_selecionados: list) -> None:
        """Processa arquivos SPB selecionados"""
        try:
            # Obtém todos os arquivos selecionados
            listbox = getattr(self, f'listbox_SPB')
            selecionados = listbox.curselection()
            
            # Lista para armazenar o conteúdo de todos os PDFs selecionados
            pdfs_selecionados = []
            
            # Coleta o conteúdo de todos os PDFs selecionados
            for idx in selecionados:
                arquivo_nome = listbox.get(idx)
                pdf_content = self.auth.baixar_arquivo_sharepoint(arquivo_nome, PASTAS['SPB'])
                if pdf_content:
                    pdfs_selecionados.append(pdf_content)
                    print(f"✅ Arquivo {arquivo_nome} carregado com sucesso")
                else:
                    print(f"❌ Erro ao carregar arquivo: {arquivo_nome}")
            
            if pdfs_selecionados:
                # Processa todos os PDFs de uma vez
                extractor = SPBExtractor("", "")
                extractor.consolidar_spb(pdfs_selecionados)
                print(f"✅ Todos os arquivos foram processados e consolidados com sucesso")
            else:
                print("❌ Nenhum arquivo foi carregado com sucesso")
                
        except Exception as e:
            print(f"❌ Erro ao processar arquivos SPB: {str(e)}")
        print(f"✅ Arquivo {arquivos_selecionados[0]} processado com sucesso")

    def verificar_divergencias(self):
        """
        Verifica divergências no arquivo consolidado do R189.
        """
        try:
            status_var = getattr(self, f'status_var_R189')
            status_var.set("Verificando divergências...")
            self.update_idletasks()
            
            # Cria uma instância do DivergenceReportR189
            from application.reports.divergence_report_r189 import DivergenceReportR189
            report = DivergenceReportR189()
            
            # Gera o relatório
            success, message = report.generate_report()
            
            if success:
                if "Nenhuma divergência encontrada" in message:
                    messagebox.showinfo("Sucesso", message)
                else:
                    messagebox.showinfo(
                        "Sucesso",
                        "Relatório de divergências gerado com sucesso!\n"
                        "O arquivo foi salvo na pasta RELATORIOS no SharePoint."
                    )
            else:
                messagebox.showerror("Erro", message)
            
            status_var.set(message)
            
        except Exception as e:
            status_var.set("Erro ao verificar divergências")
            messagebox.showerror("Erro", f"Erro ao verificar divergências: {str(e)}")

    def verificar_divergencias_qpe_r189(self):
        """
        Verifica divergências entre os arquivos consolidados QPE e R189.
        """
        try:
            status_var = getattr(self, f'status_var_R189')
            status_var.set("Verificando divergências entre QPE e R189...")
            self.update_idletasks()
            
            # Cria uma instância do DivergenceReportQPER189
            from application.reports.divergence_report_qpe_r189 import DivergenceReportQPER189
            report = DivergenceReportQPER189()
            
            # Gera o relatório
            success, message = report.generate_report()
            
            if success:
                if "Nenhuma divergência encontrada" in message:
                    messagebox.showinfo("Sucesso", message)
                else:
                    messagebox.showinfo(
                        "Sucesso",
                        "Relatório de divergências QPE vs R189 gerado com sucesso!\n"
                        "O arquivo foi salvo na pasta RELATÓRIOS/QPE_R189 no SharePoint."
                    )
            else:
                messagebox.showerror("Erro", message)
            
            status_var.set(message)
            
        except Exception as e:
            status_var.set("Erro ao verificar divergências")
            messagebox.showerror("Erro", f"Erro ao verificar divergências QPE vs R189: {str(e)}")

    def verificar_divergencias_spb_r189(self):
        """
        Verifica divergências entre os arquivos consolidados SPB e R189.
        """
        try:
            status_var = getattr(self, f'status_var_R189')
            status_var.set("Verificando divergências entre SPB e R189...")
            self.update_idletasks()
            
            # Cria uma instância do DivergenceReportSPBR189
            from application.reports.divergence_report_spb_r189 import DivergenceReportSPBR189
            report = DivergenceReportSPBR189()
            
            # Gera o relatório
            success, message = report.generate_report()
            
            if success:
                if "Nenhuma divergência encontrada" in message:
                    messagebox.showinfo("Sucesso", message)
                else:
                    messagebox.showinfo(
                        "Sucesso",
                        "Relatório de divergências SPB vs R189 gerado com sucesso!\n"
                        "O arquivo foi salvo na pasta RELATÓRIOS/SPB_R189 no SharePoint."
                    )
            else:
                messagebox.showerror("Erro", message)
            
            status_var.set(message)
            
        except Exception as e:
            status_var.set("Erro ao verificar divergências")
            messagebox.showerror("Erro", f"Erro ao verificar divergências SPB vs R189: {str(e)}")

if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()