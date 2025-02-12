import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from presentation.styles.weg_style import WegStyle
from application.extractors.r189_extractor import R189Extractor
from application.extractors.qpe_extractor import QPEExtractor
from application.extractors.spb_extractor import SPBExtractor
from auth.auth import SharePointAuth
import os

class MainWindow:
    def __init__(self):
        print("Iniciando MainWindow...")  # Debug print
        self.root = tk.Tk()
        self.root.title("Automação de Contratos - Finanças")
        self._configure_window()
        self._apply_style()
        self._create_widgets()
        self.sharepoint_auth = SharePointAuth()

    def _configure_window(self):
        window_width = 1024
        window_height = 768
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.root.minsize(800, 600)

    def _apply_style(self):
        WegStyle.apply_style()

    def _create_widgets(self):
        print("Criando widgets...")  # Debug print
        
        # Botão de Reset direto na janela principal
        reset_button = tk.Button(
            self.root,
            text="Resetar Processo",
            command=self._reset_process,
            bg='#d9534f',  # Vermelho
            fg='white',
            font=('Arial', 10, 'bold'),
            padx=10,
            pady=5
        )
        reset_button.pack(side='top', padx=5, pady=5)
        print("Botão de reset criado e empacotado")
        
        # Frame principal que contém notebook e status
        main_container = ttk.Frame(self.root)
        main_container.pack(fill='both', expand=True)
        
        # Criar notebook (abas)
        self.notebook = ttk.Notebook(main_container)
        self.notebook.pack(fill='both', expand=True, padx=20, pady=5)
        
        # Criar abas
        self.tabs = {}
        for aba in ['R189', 'QPE', 'SPB']:
            self.tabs[aba] = ttk.Frame(self.notebook, style='TFrame')
            self.notebook.add(self.tabs[aba], text=aba)
            self.setup_tab(aba)
        
        # Frame de status no rodapé
        self.status_frame = ttk.Frame(main_container, style='TFrame')
        self.status_frame.pack(fill='x', side='bottom', padx=20, pady=10)
        
        # Configurar o grid do status frame
        self.status_frame.grid_columnconfigure(0, weight=1)
        self.status_frame.grid_columnconfigure(1, weight=1)
        self.status_frame.grid_columnconfigure(2, weight=1)
        
        # Labels de status para cada aba
        self.status_vars = {}
        for i, aba in enumerate(['R189', 'QPE', 'SPB']):
            status_var = tk.StringVar(value=f"Status {aba}: Aguardando processamento")
            setattr(self, f'status_var_{aba}', status_var)
            ttk.Label(
                self.status_frame,
                textvariable=status_var,
                style='Status.TLabel'
            ).grid(row=0, column=i, padx=10, sticky='ew')
        
        # Bind para atualizar botões quando mudar de aba
        self.notebook.bind('<<NotebookTabChanged>>', self.on_tab_change)

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
        
        self.listbox = tk.Listbox(
            lista_frame,
            selectmode='extended',
            yscrollcommand=scrollbar.set,
            height=10,
            borderwidth=1,
            relief='solid',
            bg='white',
            fg='#00579d'
        )
        self.listbox.pack(side='left', fill='both', expand=True)
        
        # Arredondando os cantos da listbox
        self.listbox.configure(relief='groove', bd=2)
        
        scrollbar.config(command=self.listbox.yview)
        
        setattr(self, f'listbox_{aba}', self.listbox)
        
        # Seção de Validação (apenas na aba R189)
        if aba == 'R189':
            # Frame de validação com cantos arredondados
            self.validation_frame = ttk.LabelFrame(main_frame, text="Validação")
            
            # Frame para os botões de validação
            buttons_frame = ttk.Frame(self.validation_frame)
            buttons_frame.pack(fill='x', padx=15, pady=10)
            
            # Botões de validação com cantos arredondados
            self.validation_buttons = {}
            
            # Validação R189
            self.validation_buttons['R189'] = ttk.Button(
                buttons_frame,
                text="1. Verificar Divergências R189",
                command=self.verificar_divergencias,
                style='Custom.TButton',
                state='disabled'
            )
            self.validation_buttons['R189'].pack(fill='x', pady=5)
            
            # Validação QPE vs R189
            self.validation_buttons['QPE'] = ttk.Button(
                buttons_frame,
                text="2. Verificar Divergências QPE vs R189",
                command=self.verificar_divergencias_qpe_r189,
                style='Custom.TButton',
                state='disabled'
            )
            self.validation_buttons['QPE'].pack(fill='x', pady=5)
            
            # Validação SPB vs R189
            self.validation_buttons['SPB'] = ttk.Button(
                buttons_frame,
                text="3. Verificar Divergências SPB vs R189",
                command=self.verificar_divergencias_spb_r189,
                style='Custom.TButton',
                state='disabled'
            )
            self.validation_buttons['SPB'].pack(fill='x', pady=5)

    def on_tab_change(self, event):
        # Atualiza o estado dos botões quando muda de aba
        pass

    def buscar_arquivos(self, aba):
        # Implementação da busca de arquivos
        pass

    def processar_arquivos(self, aba):
        # Implementação do processamento de arquivos
        pass

    def verificar_divergencias(self):
        # Implementação da verificação de divergências
        pass

    def verificar_divergencias_qpe_r189(self):
        # Implementação da verificação de divergências QPE vs R189
        pass

    def verificar_divergencias_spb_r189(self):
        # Implementação da verificação de divergências SPB vs R189
        pass

    def _reset_process(self):
        """Reseta todo o processo e seleciona a aba R189"""
        # Limpa os campos de arquivo
        for aba in self.tabs:
            if hasattr(self, f'listbox_{aba}'):
                getattr(self, f'listbox_{aba}').delete(0, tk.END)
        
        # Limpa os status
        for aba in ['R189', 'QPE', 'SPB']:
            getattr(self, f'status_var_{aba}').set(f"Status {aba}: Aguardando processamento")
        
        # Desabilita os botões de validação
        if hasattr(self, 'validation_buttons'):
            for button in self.validation_buttons.values():
                button.configure(state='disabled')
        
        # Seleciona a aba R189
        self.notebook.select(self.tabs['R189'])
        
        # Mostra mensagem de confirmação
        messagebox.showinfo("Reset", "Processo resetado com sucesso!")

    def mainloop(self):
        self.root.mainloop()
