from presentation.views.main_window import MainWindow
import requests
import tkinter as tk
from tkinter import messagebox
from application.extractors.r189_extractor import R189Extractor
import os
from domain.validators.r189_validator import R189Validator  # Adicionar o validador
from application.reports.divergence_report import DivergenceReport  # Gerar relatórios de divergência

# URL base do SharePoint
BASE_URL = "https://weg365.sharepoint.com/sites/BR-TI-TIN/AutomaoFinanas/_api/web"

# Token de acesso - você já tem uma forma de obtê-lo em seu projeto, então só usaremos o token aqui
ACCESS_TOKEN = "SEU_TOKEN_AQUI"

# Cabeçalhos para a requisição (incluindo o token)
HEADERS = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Accept": "application/json",
}

# Função para listar pastas e arquivos em uma URL do SharePoint
def listar_itens(url):
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json()['d']['results']
    else:
        messagebox.showerror("Erro", f"Erro ao acessar o SharePoint: {response.status_code}")
        return []

# Função para atualizar a lista de pastas/arquivos no GUI
def atualizar_lista(itens, listbox):
    listbox.delete(0, tk.END)  # Limpa a lista
    for item in itens:
        listbox.insert(tk.END, item['Name'])  # Adiciona o item na lista

# Função para navegar e exibir os itens da pasta selecionada
def item_selecionado(event, listbox, pasta_atual, label_info):
    selecionado = listbox.get(listbox.curselection())
    label_info.config(text=f"Você selecionou: {selecionado}")
    
    # Verifica se o item selecionado é uma pasta ou arquivo
    if 'Folder' in selecionado:
        url = f"{BASE_URL}/GetFolderByServerRelativeUrl('{pasta_atual}/{selecionado}')/Files"
        itens = listar_itens(url)
        atualizar_lista(itens, listbox)
    else:
        messagebox.showinfo("Arquivo Selecionado", f"Arquivo: {selecionado} foi selecionado!")
        
    # Função para iniciar a navegação no SharePoint
def inicializar_navegacao_sharepoint():
    # Janela principal para navegação
    janela = tk.Tk()
    janela.title("Seleção de Arquivos no SharePoint")

    # Label com informações
    label_info = tk.Label(janela, text="Escolha uma pasta ou arquivo")
    label_info.pack()

    # Listbox para exibir arquivos e pastas
    listbox = tk.Listbox(janela, width=50, height=20)
    listbox.pack()

    # Inicializando a pasta inicial
    pasta_inicial = "/sites/BR-TI-TIN/AutomaoFinanas"
    url_inicial = f"{BASE_URL}/GetFolderByServerRelativeUrl('{pasta_inicial}')/Files"
    itens_iniciais = listar_itens(url_inicial)
    atualizar_lista(itens_iniciais, listbox)

    # Bind do evento de seleção de item
    listbox.bind('<<ListboxSelect>>', lambda event: item_selecionado(event, listbox, pasta_inicial, label_info))

    # Botão para sair
    btn_sair = tk.Button(janela, text="Sair", command=janela.quit)
    btn_sair.pack()

    # Iniciar a interface gráfica
    janela.mainloop()

# Função para consolidar os arquivos do SharePoint
def consolidar_arquivos(r189_extracted_data):
    # Agora, você pode criar um novo arquivo consolidado
    try:
        # Chama o extrator para consolidar os dados
        consolidado_data = R189Extractor.consolidar_dados(r189_extracted_data)
        
        # Validação de dados (opcional)
        if R189Validator.validar(consolidado_data):
            # Cria o arquivo consolidado
            path_consolidado = "consolidado-r189.xlsx"
            consolidado_data.to_excel(path_consolidado, index=False)
            messagebox.showinfo("Sucesso", f"Arquivo consolidado gerado: {path_consolidado}")
        else:
            messagebox.showerror("Erro de Validação", "Os dados não passaram na validação.")

    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao consolidar os arquivos: {str(e)}")

# Função principal para rodar o aplicativo
if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()  # Adicionando mainloop() para iniciar o loop de eventos