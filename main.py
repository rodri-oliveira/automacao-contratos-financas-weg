import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import requests
from datetime import datetime
from auth.auth import SharePointAuth
from application.extractors.r189_extractor import R189Extractor
from application.extractors.qpe_extractor import QPEExtractor
from application.extractors.spb_extractor import SPBExtractor
from application.extractors.nfserv_extractor import NFServExtractor
from application.extractors.municipality_code_extractor import MunicipalityCodeExtractor
from application.reports.divergence_report_r189 import DivergenceReportR189
from application.reports.divergence_report_qpe_r189 import DivergenceReportQPER189
from application.reports.divergence_report_spb_r189 import DivergenceReportSPBR189
from application.reports.divergence_report_nfserv_r189 import DivergenceReportNFSERVR189
from application.reports.report_mun_code_r189 import DivergenceReportMUNCODER189
from presentation.views.main_window import MainWindow

# Constantes
SITE_URL = os.getenv('SITE_URL')
PASTAS = {
    'R189': "/teams/BR-TI-TIN/AutomaoFinanas/R189",
    'QPE': "/teams/BR-TI-TIN/AutomaoFinanas/QPE",
    'SPB': "/teams/BR-TI-TIN/AutomaoFinanas/SPB",
    'NFSERV': "/teams/BR-TI-TIN/AutomaoFinanas/NFSERV",
    'MUN_CODE': "/teams/BR-TI-TIN/AutomaoFinanas/R189"  # Usa a mesma pasta do R189
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

class MainWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Automação de Contratos - Finanças")
        
        # Configuração da janela principal
        window_width = 1024
        window_height = 768
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.root.minsize(800, 600)
        
        # Cores WEG
        self.WEG_BLUE = "#00579d"
        self.WEG_WHITE = "#ffffff"
        self.WEG_LIGHT_BLUE = "#0068b8"
        
        # Configurar estilos
        self._configure_styles()
        
        # Criar widgets
        self._create_widgets()
        
        # Inicializa o SharePoint Auth
        self.auth = SharePointAuth()
        
        # Dicionário para controlar o estado dos processamentos e validações
        self.processed_files = {
            'R189': False,
            'QPE': False,
            'SPB': False,
            'NFSERV': False,
            'MUN_CODE': False
        }
        
        self.validation_status = {
            'R189': False,
            'QPE': False,
            'SPB': False,
            'NFSERV': False,
            'MUN_CODE': False
        }
        
        # Inicialmente, desabilitar todas as abas exceto R189
        self._update_tab_states()
    
    def _configure_styles(self):
        # Estilo personalizado
        style = ttk.Style()
        
        # Configuração geral - Fundo azul WEG
        style.configure('TFrame', background=self.WEG_LIGHT_BLUE)
        style.configure('TLabelframe', 
            background=self.WEG_BLUE,
            borderwidth=0,
            relief='groove'
        )
        style.configure('TLabelframe.Label', 
            background=self.WEG_BLUE,
            foreground=self.WEG_WHITE,
            font=('Arial', 10, 'bold')
        )
        
        # Botão de Reset - Azul WEG com texto branco
        style.configure('Reset.TButton',
            padding=8,
            background=self.WEG_BLUE,
            foreground=self.WEG_WHITE,
            font=('Arial', 10, 'bold'),
            relief='flat'
        )
        style.map('Reset.TButton',
            background=[('active', self.WEG_LIGHT_BLUE), ('pressed', self.WEG_LIGHT_BLUE)],
            foreground=[('active', self.WEG_WHITE), ('pressed', self.WEG_WHITE)]
        )
        
        # Botões - Branco com texto azul e cantos arredondados
        style.configure('Custom.TButton',
            padding=8,
            background=self.WEG_WHITE,
            foreground=self.WEG_BLUE,
            font=('Arial', 10, 'bold'),
            borderwidth=0,
            relief='flat',
            borderradius=15
        )
        style.map('Custom.TButton',
            background=[('active', '#f0f0f0'), ('disabled', '#cccccc')],
            foreground=[('disabled', '#666666')]
        )
        
        # Status - Texto branco
        style.configure('Status.TLabel',
            padding=8,
            background=self.WEG_BLUE,
            foreground=self.WEG_WHITE,
            font=('Arial', 9)
        )
        
        # Notebook (Abas) - Mais largas e arredondadas
        style.configure('TNotebook',
            background=self.WEG_LIGHT_BLUE,
            borderwidth=0,
            tabmargins=[2, 5, 0, 0]
            # borderradius=15
        )
        style.configure('TNotebook.Tab',
            padding=[40, 8],  # Aumentado padding horizontal
            background=self.WEG_LIGHT_BLUE,
            foreground=self.WEG_WHITE,
            font=('Arial', 11, 'bold'),
            borderwidth=0,
            borderradius=15  # Cantos arredondados
        )
        style.map('TNotebook.Tab',
            background=[('selected', self.WEG_WHITE)],
            foreground=[('selected', self.WEG_BLUE)],
            expand=[('selected', [1, 1, 1, 0])]
        )
        
        # Listbox - Fundo branco com seleção azul e cantos arredondados
        self.root.option_add('*TListbox*Background', self.WEG_WHITE)
        self.root.option_add('*TListbox*selectBackground', self.WEG_BLUE)
        self.root.option_add('*TListbox*selectForeground', self.WEG_WHITE)
        self.root.option_add('*TListbox*Font', ('Arial', 10))
        
        # Configurar cor de fundo da janela principal
        self.root.configure(bg=self.WEG_BLUE)
    
    def _create_widgets(self):
        # Frame principal que contém notebook e status
        main_container = ttk.Frame(self.root)
        main_container.pack(fill='both', expand=True)
        
        # Frame para botões globais
        global_buttons_frame = ttk.Frame(main_container)
        global_buttons_frame.pack(fill='x', padx=20, pady=5)
        
        # Botão de Reset
        reset_button = tk.Button(
            global_buttons_frame,
            text="Resetar Processo",
            command=self._reset_process,
            bg=self.WEG_BLUE,
            fg=self.WEG_WHITE,
            font=('Arial', 10, 'bold'),
            relief='flat',
            activebackground=self.WEG_LIGHT_BLUE,
            activeforeground=self.WEG_WHITE,
            cursor='hand2'  # Muda o cursor para mãozinha ao passar por cima
        )
        reset_button.pack(side='left', padx=5, pady=5)
        
        # Criar notebook (abas) - Reduzindo padding vertical
        self.notebook = ttk.Notebook(main_container)
        self.notebook.pack(fill='both', expand=True, padx=20, pady=5)
        
        # Criar abas - Distribuídas igualmente
        self.tabs = {}
        for aba in ['R189', 'QPE', 'SPB', 'NFSERV', 'MUN_CODE']:
            self.tabs[aba] = ttk.Frame(self.notebook, style='TFrame')
            self.notebook.add(self.tabs[aba], text=aba)
            self.setup_tab(aba)
        
        # Configurar largura igual para todas as abas
        self.notebook.pack_configure(expand=True)
        
        # Frame de status no rodapé
        self.status_frame = ttk.Frame(main_container, style='TFrame')
        self.status_frame.pack(fill='x', side='bottom', padx=20, pady=10)
        
        # Configurar o grid do status frame
        self.status_frame.grid_columnconfigure(0, weight=1)
        self.status_frame.grid_columnconfigure(1, weight=1)
        self.status_frame.grid_columnconfigure(2, weight=1)
        self.status_frame.grid_columnconfigure(3, weight=1)
        self.status_frame.grid_columnconfigure(4, weight=1)
        
        # Labels de status para cada aba
        self.status_vars = {}
        for i, aba in enumerate(['R189', 'QPE', 'SPB', 'NFSERV', 'MUN_CODE']):
            status_var = tk.StringVar(value=f"Status {aba}: Aguardando processamento")
            setattr(self, f'status_var_{aba}', status_var)
            ttk.Label(
                self.status_frame,
                textvariable=status_var,
                style='Status.TLabel'
            ).grid(row=0, column=i, padx=10, sticky='ew')
    
    def _update_tab_states(self):
        # Inicialmente, desabilitar todas as abas exceto R189
        for aba in ['QPE', 'SPB', 'NFSERV', 'MUN_CODE']:
            self.notebook.tab(self.notebook.index(self.tabs[aba]), state='disabled')
    
    def setup_tab(self, aba):
        frame = self.tabs[aba]
        
        # Frame principal com cantos arredondados
        main_frame = ttk.Frame(frame)
        main_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Seção de Arquivos com cantos arredondados
        files_frame = ttk.LabelFrame(main_frame, text="Arquivos")
        files_frame.pack(fill='x', padx=5, pady=5)
        
        # Frame para os botões
        button_frame = ttk.Frame(files_frame)
        button_frame.pack(fill='x', padx=15, pady=10)
        
        # Botões com espaçamento adequado e cantos arredondados
        ttk.Button(
            button_frame,
            text="Buscar Arquivos",
            command=lambda a=aba: self.buscar_arquivos(a),
            style='Custom.TButton'
        ).pack(pady=5)
        
        self.process_buttons = {}
        self.process_buttons[aba] = ttk.Button(
            button_frame,
            text="Processar Arquivos",
            command=lambda a=aba: self.processar_arquivos(a),
            style='Custom.TButton'
        )
        self.process_buttons[aba].pack(pady=5)
        
        # Lista de arquivos com margens e cantos arredondados
        lista_frame = ttk.Frame(files_frame)
        lista_frame.pack(fill='both', expand=True, padx=15, pady=(5,15))
        
        # Scrollbar personalizada
        scrollbar = ttk.Scrollbar(lista_frame)
        scrollbar.pack(side='right', fill='y')
        
        listbox = tk.Listbox(
            lista_frame,
            selectmode='extended',
            yscrollcommand=scrollbar.set,
            height=10,
            borderwidth=1,
            relief='solid',
            bg='white',
            fg='#00579d'
        )
        listbox.pack(side='left', fill='both', expand=True)
        setattr(self, f'listbox_{aba}', listbox)
        
        # Configurar scrollbar
        scrollbar.config(command=listbox.yview)
        
        # Se for a aba R189, adiciona o container de validação
        if aba == 'R189':
            validation_frame = ttk.LabelFrame(main_frame, text="Validações")
            validation_frame.pack(fill='x', padx=5, pady=5)
            
            # Frame para os botões de validação
            buttons_frame = ttk.Frame(validation_frame)
            buttons_frame.pack(fill='x', padx=15, pady=10)
            
            # Cria dicionário para armazenar os botões de validação se ainda não existir
            if not hasattr(self, 'validation_buttons'):
                self.validation_buttons = {}
            
            # Botão de validação R189
            self.validation_buttons['R189'] = ttk.Button(
                buttons_frame,
                text="1. Verificar Divergências R189",
                command=self.verificar_divergencias,
                style='Custom.TButton',
                state='disabled'
            )
            
            # Botão de validação QPE
            self.validation_buttons['QPE'] = ttk.Button(
                buttons_frame,
                text="2. Verificar Divergências QPE vs R189",
                command=self.verificar_divergencias_qpe_r189,
                style='Custom.TButton',
                state='disabled'
            )
            
            # Botão de validação SPB
            self.validation_buttons['SPB'] = ttk.Button(
                buttons_frame,
                text="3. Verificar Divergências SPB vs R189",
                command=self.verificar_divergencias_spb_r189,
                style='Custom.TButton',
                state='disabled'
            )
            
            # Botão de validação NFSERV
            self.validation_buttons['NFSERV'] = ttk.Button(
                buttons_frame,
                text="4. Verificar Divergências NFSERV vs R189",
                command=self.verificar_divergencias_nfserv_r189,
                style='Custom.TButton',
                state='disabled'
            )
            
            # Botão de validação MUN_CODE
            self.validation_buttons['MUN_CODE'] = ttk.Button(
                buttons_frame,
                text="5. Verificar Códigos de Município",
                command=self.verificar_divergencias_mun_code_r189,
                style='Custom.TButton',
                state='disabled'
            )
            
            # Esconde os botões de validação inicialmente
            for button in self.validation_buttons.values():
                button.pack_forget()

    def check_all_processed(self):
        """Verifica se todos os arquivos foram processados"""
        return all(self.processed_files.values())

    def update_validation_buttons(self):
        """Atualiza o estado dos botões de validação baseado na sequência correta"""
        if not hasattr(self, 'validation_buttons'):
            return
            
        # Primeiro verifica se todos os arquivos foram processados
        if self.check_all_processed():
            self.show_validation_container()
        
        # Atualiza botões baseado no status das validações
        if self.validation_status['R189']:
            self.validation_buttons['QPE']['state'] = 'normal'
        else:
            self.validation_buttons['QPE']['state'] = 'disabled'
            self.validation_buttons['SPB']['state'] = 'disabled'
            self.validation_buttons['NFSERV']['state'] = 'disabled'
            self.validation_buttons['MUN_CODE']['state'] = 'disabled'
            
        if self.validation_status['QPE']:
            self.validation_buttons['SPB']['state'] = 'normal'
        else:
            self.validation_buttons['SPB']['state'] = 'disabled'
            self.validation_buttons['NFSERV']['state'] = 'disabled'
            self.validation_buttons['MUN_CODE']['state'] = 'disabled'
            
        if self.validation_status['SPB']:
            self.validation_buttons['NFSERV']['state'] = 'normal'
        else:
            self.validation_buttons['NFSERV']['state'] = 'disabled'
            self.validation_buttons['MUN_CODE']['state'] = 'disabled'
            
        if self.validation_status['NFSERV']:
            self.validation_buttons['MUN_CODE']['state'] = 'normal'
        else:
            self.validation_buttons['MUN_CODE']['state'] = 'disabled'
    
    def show_validation_container(self):
        """Mostra o container de validação quando todos os arquivos forem processados"""
        if hasattr(self, 'validation_buttons'):
            # Mostra todos os botões de validação
            for button in self.validation_buttons.values():
                button.pack(fill='x', pady=5)
            
            # Habilita apenas o primeiro botão de validação (R189)
            self.validation_buttons['R189']['state'] = 'normal'
            
            # Seleciona a aba R189
            self.notebook.select(0)  # 0 é o índice da aba R189

    def on_tab_change(self, event):
        """Atualiza o estado dos botões quando muda de aba"""
        current_tab = self.notebook.select()
        tab_name = self.notebook.tab(current_tab, "text")
        self.update_validation_buttons()
    
    def buscar_arquivos(self, aba):
        """Busca arquivos no SharePoint"""
        status_var = getattr(self, f'status_var_{aba}')
        listbox = getattr(self, f'listbox_{aba}')
        
        status_var.set("Buscando arquivos...")
        self.root.update_idletasks()
        
        try:
            arquivos = buscar_arquivos(self.auth, PASTAS[aba])
            if arquivos:
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
        """Processa os arquivos selecionados"""
        listbox = getattr(self, f'listbox_{aba}')
        status_var = getattr(self, f'status_var_{aba}')
        
        selecionados = listbox.curselection()
        if not selecionados:
            messagebox.showwarning("Aviso", "Selecione pelo menos um arquivo para processar")
            return
        
        try:
            arquivos_selecionados = [listbox.get(idx) for idx in selecionados]
            status_var.set(f"Processando arquivos {aba}...")
            self.root.update_idletasks()
            
            # Processa os arquivos conforme o tipo
            if aba == 'R189':
                self.processar_r189(arquivos_selecionados)
            elif aba == 'QPE':
                self.processar_qpe(arquivos_selecionados)
            elif aba == 'SPB':
                self.processar_spb(arquivos_selecionados)
            elif aba == 'NFSERV':
                self.processar_nfserv(arquivos_selecionados)
            elif aba == 'MUN_CODE':
                self.processar_MUN_CODE(arquivos_selecionados)

            # Marca como processado
            self.processed_files[aba] = True

            # Se acabou de processar o NFSERV e todos estão processados
            if aba == 'MUN_CODE' and self.check_all_processed():
                # Muda para a aba R189 e mostra o container de validação
                self.notebook.select(0)  # 0 é o índice da aba R189
                self.show_validation_container()
                self.update_validation_buttons()
            
            # Atualiza o status e libera próxima aba
            status_var.set(f"Arquivos {aba} processados com sucesso")
            
            # Libera a próxima aba após processamento bem sucedido
            if aba == 'R189':
                self.notebook.tab(self.notebook.index(self.tabs['QPE']), state='normal')
            elif aba == 'QPE':
                self.notebook.tab(self.notebook.index(self.tabs['SPB']), state='normal')
            elif aba == 'SPB':
                self.notebook.tab(self.notebook.index(self.tabs['NFSERV']), state='normal')
            elif aba == 'NFSERV':
                self.notebook.tab(self.notebook.index(self.tabs['MUN_CODE']), state='normal')
            
            messagebox.showinfo("Sucesso", f"Processamento dos arquivos {aba} concluído")
            
        except Exception as e:
            status_var.set(f"Erro no processamento {aba}")
            messagebox.showerror("Erro", f"Erro durante o processamento: {str(e)}")
            self.processed_files[aba] = False
            self.update_validation_buttons()
    
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

    def processar_MUN_CODE(self, arquivos_selecionados: list):
        """
        Processa os arquivos Municipality Code selecionados.
        
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
                    
                    # Cria uma instância do MunicipalityCodeExtractor
                    extractor = MunicipalityCodeExtractor("", "")
                    
                    # Processa o arquivo
                    resultado = extractor.consolidar_municipality_code(conteudo)
                    
                    if resultado:
                        print(f"✅ Arquivo {arquivo} processado com sucesso")
                    else:
                        print(f"❌ Erro ao processar arquivo: {arquivo}")
                    
                except Exception as e:
                    print(f"❌ Erro ao processar arquivo {arquivo}: {str(e)}")
                    continue
                
        except Exception as e:
            print(f"❌ Erro ao processar arquivos Municipality Code: {str(e)}")
            raise

    def processar_qpe(self, arquivos_selecionados: list) -> None:
        """Processa arquivos QPE selecionados"""
        try:
            # Lista para armazenar o conteúdo de todos os PDFs selecionados
            pdfs_selecionados = []
            
            # Coleta o conteúdo de todos os PDFs selecionados
            for arquivo in arquivos_selecionados:
                pdf_content = self.auth.baixar_arquivo_sharepoint(arquivo, PASTAS['QPE'])
                if pdf_content:
                    pdfs_selecionados.append(pdf_content)
                    print(f"✅ Arquivo {arquivo} carregado com sucesso")
                else:
                    print(f"❌ Erro ao carregar arquivo: {arquivo}")
            
            if pdfs_selecionados:
                # Processa todos os PDFs de uma vez
                extractor = QPEExtractor("", "")
                extractor.consolidar_qpe(pdfs_selecionados)
                print(f"✅ Todos os arquivos foram processados e consolidados com sucesso")
            else:
                print("❌ Nenhum arquivo foi carregado com sucesso")
                
        except Exception as e:
            print(f"❌ Erro ao processar arquivos QPE: {str(e)}")
            raise

    def processar_spb(self, arquivos_selecionados: list) -> None:
        """Processa arquivos SPB selecionados"""
        try:
            # Lista para armazenar o conteúdo de todos os PDFs selecionados
            pdfs_selecionados = []
            
            # Coleta o conteúdo de todos os PDFs selecionados
            for arquivo in arquivos_selecionados:
                pdf_content = self.auth.baixar_arquivo_sharepoint(arquivo, PASTAS['SPB'])
                if pdf_content:
                    pdfs_selecionados.append(pdf_content)
                    print(f"✅ Arquivo {arquivo} carregado com sucesso")
                else:
                    print(f"❌ Erro ao carregar arquivo: {arquivo}")
            
            if pdfs_selecionados:
                # Processa todos os PDFs de uma vez
                extractor = SPBExtractor("", "")
                extractor.consolidar_spb(pdfs_selecionados)
                print(f"✅ Todos os arquivos foram processados e consolidados com sucesso")
            else:
                print("❌ Nenhum arquivo foi carregado com sucesso")
                
        except Exception as e:
            print(f"❌ Erro ao processar arquivos SPB: {str(e)}")
            raise

    def processar_nfserv(self, arquivos_selecionados: list) -> None:
        """Processa arquivos NFSERV selecionados"""
        try:
            # Lista para armazenar o conteúdo de todos os PDFs selecionados
            pdfs_selecionados = []
            
            # Coleta o conteúdo de todos os PDFs selecionados
            for arquivo in arquivos_selecionados:
                pdf_content = self.auth.baixar_arquivo_sharepoint(arquivo, PASTAS['NFSERV'])
                if pdf_content:
                    pdfs_selecionados.append(pdf_content)
                    print(f"✅ Arquivo {arquivo} carregado com sucesso")
                else:
                    print(f"❌ Erro ao carregar arquivo: {arquivo}")
            
            if pdfs_selecionados:
                # Processa todos os PDFs de uma vez
                extractor = NFServExtractor("", "")
                extractor.consolidar_nfserv(pdfs_selecionados)
                print(f"✅ Todos os arquivos foram processados e consolidados com sucesso")
            else:
                print("❌ Nenhum arquivo foi carregado com sucesso")
                
        except Exception as e:
            print(f"❌ Erro ao processar arquivos NFSERV: {str(e)}")
            raise
    
    def verificar_divergencias(self):
        """Verifica divergências no R189"""
        status_var = getattr(self, f'status_var_R189')
        try:
            status_var.set("Verificando divergências no R189...")
            self.root.update_idletasks()
            
            from application.reports.divergence_report_r189 import DivergenceReportR189
            report = DivergenceReportR189()
            
            success, message = report.generate_report()
            
            if success:
                self.validation_status['R189'] = True
                self.update_validation_buttons()
                
                if "Nenhuma divergência encontrada" in message:
                    messagebox.showinfo("Sucesso", message)
                else:
                    messagebox.showinfo(
                        "Divergências Encontradas",
                        message
                    )
            else:
                messagebox.showerror("Erro", message)
            
            status_var.set(message)
            
        except Exception as e:
            status_var.set("Erro ao verificar divergências")
            messagebox.showerror("Erro", str(e))
    
    def verificar_divergencias_qpe_r189(self):
        """Verifica divergências entre QPE e R189"""
        status_var = getattr(self, f'status_var_R189')
        try:
            status_var.set("Verificando divergências entre QPE e R189...")
            self.root.update_idletasks()
            
            from application.reports.divergence_report_qpe_r189 import DivergenceReportQPER189
            report = DivergenceReportQPER189()
            
            success, message = report.generate_report()
            
            if success:
                self.validation_status['QPE'] = True
                self.update_validation_buttons()
                
                if "Nenhuma divergência encontrada" in message:
                    messagebox.showinfo("Sucesso", message)
                else:
                    messagebox.showinfo(
                        "Divergências Encontradas",
                        message
                    )
            else:
                messagebox.showerror("Erro", message)
            
            status_var.set(message)
            
        except Exception as e:
            status_var.set("Erro ao verificar divergências")
            messagebox.showerror("Erro", str(e))
    
    def verificar_divergencias_spb_r189(self):
        """Verifica divergências entre SPB e R189"""
        status_var = getattr(self, f'status_var_R189')
        try:
            status_var.set("Verificando divergências entre SPB e R189...")
            self.root.update_idletasks()
            
            from application.reports.divergence_report_spb_r189 import DivergenceReportSPBR189
            report = DivergenceReportSPBR189()
            
            success, message = report.generate_report()
            
            if success:
                self.validation_status['SPB'] = True
                self.update_validation_buttons()
                
                if "Nenhuma divergência encontrada" in message:
                    messagebox.showinfo("Sucesso", message)
                else:
                    messagebox.showinfo(
                        "Divergências Encontradas",
                        message
                    )
            else:
                messagebox.showerror("Erro", message)
            
            status_var.set(message)
            
        except Exception as e:
            status_var.set("Erro ao verificar divergências")
            messagebox.showerror("Erro", str(e))
    
    def verificar_divergencias_nfserv_r189(self):
        """Verifica divergências entre NFSERV e R189"""
        status_var = getattr(self, f'status_var_R189')
        try:
            status_var.set("Verificando divergências entre NFSERV e R189...")
            self.root.update_idletasks()
            
            from application.reports.divergence_report_nfserv_r189 import DivergenceReportNFSERVR189
            report = DivergenceReportNFSERVR189()
            
            success, message = report.generate_report()
            
            if success:
                self.validation_status['NFSERV'] = True
                self.update_validation_buttons()
                
                if "Nenhuma divergência encontrada" in message:
                    messagebox.showinfo("Sucesso", message)
                else:
                    messagebox.showinfo(
                        "Divergências Encontradas",
                        message
                    )
            else:
                messagebox.showerror("Erro", message)
            
            status_var.set(message)
            
        except Exception as e:
            status_var.set("Erro ao verificar divergências")
            messagebox.showerror("Erro", str(e))
    
    def verificar_divergencias_mun_code_r189(self):
        """Verifica divergências entre MUN_CODE e R189"""
        status_var = getattr(self, f'status_var_R189')
        try:
            status_var.set("Verificando divergências entre MUN_CODE e R189...")
            self.root.update_idletasks()
            
            from application.reports.report_mun_code_r189 import DivergenceReportMUNCODER189
            report = DivergenceReportMUNCODER189()
            
            success, message = report.generate_report()
            
            if success:
                self.validation_status['MUN_CODE'] = True
                self.update_validation_buttons()
                
                if "Nenhuma divergência encontrada" in message:
                    messagebox.showinfo("Sucesso", message)
                else:
                    messagebox.showinfo(
                        "Divergências Encontradas",
                        message
                    )
            else:
                messagebox.showerror("Erro", message)
            
            status_var.set(message)
            
        except Exception as e:
            status_var.set("Erro ao verificar divergências")
            messagebox.showerror("Erro", str(e))
    
    def _reset_process(self):
        """Reseta o processo"""
        # Reseta os estados
        self.processed_files = {
            'R189': False,
            'QPE': False,
            'SPB': False,
            'NFSERV': False,
            'MUN_CODE': False
        }
        
        self.validation_status = {
            'R189': False,
            'QPE': False,
            'SPB': False,
            'NFSERV': False,
            'MUN_CODE': False
        }
        
        # Reseta os status e limpa as listboxes
        for aba in ['R189', 'QPE', 'SPB', 'NFSERV', 'MUN_CODE']:
            # Reseta o status
            if hasattr(self, f'status_var_{aba}'):
                status_var = getattr(self, f'status_var_{aba}')
                status_var.set(f"Status {aba}: Aguardando processamento")
            
            # Limpa a listbox
            if hasattr(self, f'listbox_{aba}'):
                listbox = getattr(self, f'listbox_{aba}')
                listbox.delete(0, tk.END)
            
            # Reseta os botões de validação se for a aba R189
            if aba == 'R189' and hasattr(self, 'validation_buttons'):
                for button in self.validation_buttons.values():
                    button['state'] = 'disabled'
        
        # Desabilita todas as abas exceto R189
        for aba in ['QPE', 'SPB', 'NFSERV', 'MUN_CODE']:
            self.notebook.tab(self.notebook.index(self.tabs[aba]), state='disabled')
        
        # Seleciona a aba R189
        self.notebook.select(self.tabs['R189'])
        
        # Mostra mensagem de confirmação
        messagebox.showinfo("Reset", "Processo resetado com sucesso!")
    
    def mainloop(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()