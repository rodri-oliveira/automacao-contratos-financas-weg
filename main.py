from auth import auth

def main():
    print("Iniciando o sistema de autenticação com o SharePoint...")

    # Inicializa a classe de autenticação
    sp_auth = auth.SharePointAuth()

    # Tenta autenticar e obter o contexto do SharePoint
    try:
        context = sp_auth.authenticate()
        print("Conexão com o SharePoint foi estabelecida com sucesso!")
        
        # Exemplo: Listar o título do site para verificar a conexão
        site = context.web.get().execute_query()
        print(f"Título do site: {site.properties['Title']}")

    except Exception as e:
        print(f"Erro durante a autenticação ou conexão: {e}")

if __name__ == "__main__":
    main()
