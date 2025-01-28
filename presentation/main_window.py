import customtkinter as ctk

class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Validação de Documentos Fiscais")
        self.geometry("800x600")
        self.create_widgets()

    def create_widgets(self):
        self.tab_view = ctk.CTkTabview(self)
        self.tab_view.pack(fill="both", expand=True)

        self.r189_tab = self.tab_view.add("R189")
        self.qpe_tab = self.tab_view.add("QPE")
        self.spb_tab = self.tab_view.add("SPB")

        ctk.CTkButton(self.r189_tab, text="Validar R189", command=self.validate_r189).pack(pady=10)
        ctk.CTkButton(self.qpe_tab, text="Validar QPE", command=self.validate_qpe).pack(pady=10)
        ctk.CTkButton(self.spb_tab, text="Validar SPB", command=self.validate_spb).pack(pady=10)

    def validate_r189(self):
        print("Validação R189 em progresso...")

    def validate_qpe(self):
        print("Validação QPE em progresso...")

    def validate_spb(self):
        print("Validação SPB em progresso...")

if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()
