from tkinter import ttk

class WegStyle:
    # Cores WEG
    WEG_BLUE = "#00579d"
    WEG_WHITE = "#ffffff"
    WEG_LIGHT_BLUE = "#0068b8"

    @staticmethod
    def apply_style():
        style = ttk.Style()
        
        # Configuração geral - Fundo azul WEG
        style.configure('TFrame', background=WegStyle.WEG_LIGHT_BLUE)
        style.configure('TLabelframe', 
            background=WegStyle.WEG_BLUE,
            borderwidth=0,
            relief='groove'
        )
        style.configure('TLabelframe.Label', 
            background=WegStyle.WEG_BLUE,
            foreground=WegStyle.WEG_WHITE,
            font=('Arial', 10, 'bold')
        )
        
        # Botões - Branco com texto azul e cantos arredondados
        style.configure('Custom.TButton',
            padding=8,
            background=WegStyle.WEG_WHITE,
            foreground=WegStyle.WEG_BLUE,
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
            background=WegStyle.WEG_BLUE,
            foreground=WegStyle.WEG_WHITE,
            font=('Arial', 10)
        )
        
        # Notebook (Abas)
        style.configure('TNotebook',
            background=WegStyle.WEG_LIGHT_BLUE,
            borderwidth=0,
            tabmargins=[2, 5, 0, 0]
        )
        style.configure('TNotebook.Tab',
            padding=[40, 8],
            background=WegStyle.WEG_WHITE,
            foreground=WegStyle.WEG_BLUE
        )
