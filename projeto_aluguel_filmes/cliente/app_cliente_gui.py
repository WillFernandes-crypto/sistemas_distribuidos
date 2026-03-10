import threading
import tkinter as tk
from tkinter import messagebox, ttk

from app_cliente import obter_proxy_servidor


class RpcGateway:
    def listar_filmes(self) -> list:
        proxy = obter_proxy_servidor()
        return proxy.listar_filmes()

    def alugar_filme(self, filme_id: int, cliente: str) -> dict:
        proxy = obter_proxy_servidor()
        return proxy.alugar_filme(filme_id, cliente)

    def historico_alugueis(self) -> list:
        proxy = obter_proxy_servidor()
        return proxy.historico_alugueis()


class AppClienteGUI(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("MovieRent | Distributed Client")
        self.geometry("1100x700")
        self.minsize(980, 620)

        self.palette = {
            "bg": "#F8F4EC",
            "panel": "#FFFDF8",
            "text": "#1F2937",
            "muted": "#6B7280",
            "accent": "#0F766E",
            "accent_2": "#F97316",
            "ok": "#15803D",
            "warn": "#C2410C",
            "danger": "#B91C1C",
            "border": "#E5E7EB",
        }
        self.configure(bg=self.palette["bg"])

        self.gateway = RpcGateway()
        self.filmes: list[dict] = []
        self._history_window: tk.Toplevel | None = None
        self._history_tree: ttk.Treeview | None = None
        self._toast_label: tk.Label | None = None
        self._toast_after_id: str | None = None
        self._loading = False

        self.nome_var = tk.StringVar(value="")
        self.filme_var = tk.StringVar(value="")

        self._configure_styles()
        self._build_layout()
        self.after(200, self.carregar_catalogo)

    def _configure_styles(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")

        style.configure(
            "Movie.Horizontal.TProgressbar",
            troughcolor=self.palette["panel"],
            background=self.palette["accent"],
            bordercolor=self.palette["panel"],
            lightcolor=self.palette["accent"],
            darkcolor=self.palette["accent"],
        )
        style.configure(
            "Movie.Treeview",
            background=self.palette["panel"],
            fieldbackground=self.palette["panel"],
            foreground=self.palette["text"],
            borderwidth=0,
            rowheight=30,
        )
        style.configure(
            "Movie.Treeview.Heading",
            background="#E2E8F0",
            foreground=self.palette["text"],
            relief="flat",
            font=("Segoe UI", 10, "bold"),
        )
        style.map("Movie.Treeview", background=[("selected", "#CCE8E4")])

    def _build_layout(self) -> None:
        self.header = tk.Canvas(self, height=110, bd=0, highlightthickness=0)
        self.header.pack(fill="x")
        self.header.bind("<Configure>", self._render_header)

        self.main = tk.Frame(self, bg=self.palette["bg"])
        self.main.pack(fill="both", expand=True, padx=18, pady=(10, 14))

        self.left_panel = tk.Frame(
            self.main,
            bg=self.palette["panel"],
            highlightbackground=self.palette["border"],
            highlightthickness=1,
            padx=16,
            pady=16,
        )
        self.left_panel.pack(side="left", fill="y")

        self.right_panel = tk.Frame(
            self.main,
            bg=self.palette["panel"],
            highlightbackground=self.palette["border"],
            highlightthickness=1,
            padx=12,
            pady=12,
        )
        self.right_panel.pack(side="left", fill="both", expand=True, padx=(14, 0))

        self._build_left_panel()
        self._build_right_panel()
        self._build_status_bar()

    def _render_header(self, _event=None) -> None:
        width = max(self.header.winfo_width(), 100)
        height = max(self.header.winfo_height(), 100)
        self.header.delete("all")

        c1 = (15, 118, 110)
        c2 = (249, 115, 22)
        for i in range(width):
            ratio = i / width
            r = int(c1[0] + (c2[0] - c1[0]) * ratio)
            g = int(c1[1] + (c2[1] - c1[1]) * ratio)
            b = int(c1[2] + (c2[2] - c1[2]) * ratio)
            self.header.create_line(i, 0, i, height, fill=f"#{r:02x}{g:02x}{b:02x}")

        self.header.create_oval(width - 170, -40, width + 60, 160, fill="#ffffff22", outline="")
        self.header.create_oval(width - 300, 30, width - 40, 230, fill="#ffffff1b", outline="")

        self.header.create_text(
            26,
            34,
            text="MovieRent Distributed",
            anchor="w",
            fill="white",
            font=("Bahnschrift", 23, "bold"),
        )
        self.header.create_text(
            26,
            74,
            text="Catalogo online com RPC, descoberta de servico e sincronizacao",
            anchor="w",
            fill="#F8FAFC",
            font=("Segoe UI", 11),
        )

    def _build_left_panel(self) -> None:
        tk.Label(
            self.left_panel,
            text="Painel de Aluguel",
            bg=self.palette["panel"],
            fg=self.palette["text"],
            font=("Bahnschrift", 16, "bold"),
        ).pack(anchor="w")

        tk.Label(
            self.left_panel,
            text="Preencha os campos e confirme o aluguel.",
            bg=self.palette["panel"],
            fg=self.palette["muted"],
            font=("Segoe UI", 10),
        ).pack(anchor="w", pady=(3, 14))

        tk.Label(
            self.left_panel,
            text="Nome do cliente",
            bg=self.palette["panel"],
            fg=self.palette["text"],
            font=("Segoe UI", 10, "bold"),
        ).pack(anchor="w")

        self.nome_entry = tk.Entry(
            self.left_panel,
            textvariable=self.nome_var,
            font=("Segoe UI", 11),
            relief="flat",
            bg="#F9FAFB",
            fg=self.palette["text"],
            highlightthickness=1,
            highlightbackground=self.palette["border"],
            highlightcolor=self.palette["accent"],
            width=32,
        )
        self.nome_entry.pack(anchor="w", pady=(6, 14), ipady=6)

        tk.Label(
            self.left_panel,
            text="Filme",
            bg=self.palette["panel"],
            fg=self.palette["text"],
            font=("Segoe UI", 10, "bold"),
        ).pack(anchor="w")

        self.combo_filmes = ttk.Combobox(
            self.left_panel,
            textvariable=self.filme_var,
            state="readonly",
            width=34,
            font=("Segoe UI", 10),
        )
        self.combo_filmes.pack(anchor="w", pady=(6, 18), ipady=4)

        self.btn_alugar = self._create_action_button(
            self.left_panel,
            text="Alugar Agora",
            bg=self.palette["accent"],
            command=self.alugar_filme,
        )
        self.btn_alugar.pack(fill="x", pady=(0, 10))

        self.btn_hist = self._create_action_button(
            self.left_panel,
            text="Ver Historico",
            bg=self.palette["accent_2"],
            command=self.abrir_historico,
        )
        self.btn_hist.pack(fill="x", pady=(0, 16))

        self.btn_refresh = self._create_action_button(
            self.left_panel,
            text="Atualizar Catalogo",
            bg="#334155",
            command=self.carregar_catalogo,
        )
        self.btn_refresh.pack(fill="x")

    def _build_right_panel(self) -> None:
        header = tk.Frame(self.right_panel, bg=self.palette["panel"])
        header.pack(fill="x", pady=(2, 10))

        tk.Label(
            header,
            text="Catalogo de Filmes",
            bg=self.palette["panel"],
            fg=self.palette["text"],
            font=("Bahnschrift", 18, "bold"),
        ).pack(side="left")

        tk.Label(
            header,
            text="Atualizacao em tempo real via RPC",
            bg=self.palette["panel"],
            fg=self.palette["muted"],
            font=("Segoe UI", 10),
        ).pack(side="left", padx=(14, 0), pady=(6, 0))

        self.scroll_canvas = tk.Canvas(
            self.right_panel,
            bg=self.palette["panel"],
            bd=0,
            highlightthickness=0,
        )
        self.scrollbar = tk.Scrollbar(
            self.right_panel,
            orient="vertical",
            command=self.scroll_canvas.yview,
        )
        self.cards_container = tk.Frame(self.scroll_canvas, bg=self.palette["panel"])

        self.cards_container.bind(
            "<Configure>",
            lambda _e: self.scroll_canvas.configure(scrollregion=self.scroll_canvas.bbox("all")),
        )

        self.scroll_canvas.create_window((0, 0), window=self.cards_container, anchor="nw")
        self.scroll_canvas.configure(yscrollcommand=self.scrollbar.set)

        self.scroll_canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

    def _build_status_bar(self) -> None:
        self.status_bar = tk.Frame(self, bg="#EEF2F7", height=36)
        self.status_bar.pack(fill="x", side="bottom")

        self.status_label = tk.Label(
            self.status_bar,
            text="Pronto para conectar.",
            bg="#EEF2F7",
            fg="#334155",
            font=("Segoe UI", 9),
        )
        self.status_label.pack(side="left", padx=12)

        self.loader = ttk.Progressbar(
            self.status_bar,
            mode="indeterminate",
            length=140,
            style="Movie.Horizontal.TProgressbar",
        )
        self.loader.pack(side="right", padx=12, pady=7)
        self.loader.stop()

    def _create_action_button(self, parent: tk.Widget, text: str, bg: str, command) -> tk.Button:
        btn = tk.Button(
            parent,
            text=text,
            command=command,
            font=("Segoe UI", 10, "bold"),
            bg=bg,
            fg="white",
            activebackground=self._lighten(bg, 0.15),
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            bd=0,
            padx=12,
            pady=10,
        )
        default_bg = bg
        hover_bg = self._lighten(bg, 0.08)

        btn.bind("<Enter>", lambda _e: btn.config(bg=hover_bg))
        btn.bind("<Leave>", lambda _e: btn.config(bg=default_bg))
        return btn

    def _lighten(self, hex_color: str, factor: float) -> str:
        hex_color = hex_color.lstrip("#")
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        r = min(255, int(r + (255 - r) * factor))
        g = min(255, int(g + (255 - g) * factor))
        b = min(255, int(b + (255 - b) * factor))
        return f"#{r:02x}{g:02x}{b:02x}"

    def _set_loading(self, value: bool) -> None:
        if value and not self._loading:
            self._loading = True
            self.loader.start(9)
            self.status_label.config(text="Carregando dados...")
        elif not value and self._loading:
            self._loading = False
            self.loader.stop()

    def _async_call(self, worker, on_success, error_message: str) -> None:
        self._set_loading(True)

        def _run() -> None:
            try:
                result = worker()
                self.after(0, lambda: self._on_async_success(result, on_success))
            except Exception as exc:
                self.after(0, lambda: self._on_async_error(error_message, exc))

        threading.Thread(target=_run, daemon=True).start()

    def _on_async_success(self, result, on_success) -> None:
        self._set_loading(False)
        on_success(result)

    def _on_async_error(self, error_message: str, exc: Exception) -> None:
        self._set_loading(False)
        self.status_label.config(text=error_message)
        self.show_toast(f"{error_message}: {exc}", kind="danger")

    def carregar_catalogo(self) -> None:
        self._async_call(
            worker=self.gateway.listar_filmes,
            on_success=self._on_catalogo_carregado,
            error_message="Falha ao carregar catalogo",
        )

    def _on_catalogo_carregado(self, filmes: list[dict]) -> None:
        self.filmes = filmes
        values = [f"{f['id']} - {f['titulo']} ({f['disponiveis']} disponiveis)" for f in filmes]
        self.combo_filmes["values"] = values
        if values and self.filme_var.get() not in values:
            self.filme_var.set(values[0])

        self._render_cards_animated()
        self.status_label.config(text=f"Catalogo sincronizado: {len(filmes)} filme(s).")

    def _render_cards_animated(self) -> None:
        for child in self.cards_container.winfo_children():
            child.destroy()

        if not self.filmes:
            tk.Label(
                self.cards_container,
                text="Nenhum filme cadastrado no momento.",
                bg=self.palette["panel"],
                fg=self.palette["muted"],
                font=("Segoe UI", 11),
            ).pack(anchor="w", padx=8, pady=8)
            return

        for i, filme in enumerate(self.filmes):
            self.after(i * 65, lambda f=filme: self._add_movie_card(f))

    def _add_movie_card(self, filme: dict) -> None:
        disponiveis = int(filme["disponiveis"])
        if disponiveis <= 0:
            badge_color = self.palette["danger"]
            badge_text = "Sem copias"
        elif disponiveis == 1:
            badge_color = self.palette["warn"]
            badge_text = "Ultima copia"
        else:
            badge_color = self.palette["ok"]
            badge_text = f"{disponiveis} disponiveis"

        card = tk.Frame(
            self.cards_container,
            bg="#FFFFFF",
            highlightthickness=1,
            highlightbackground=self.palette["border"],
            padx=14,
            pady=12,
        )
        card.pack(fill="x", padx=6, pady=6)

        top = tk.Frame(card, bg="#FFFFFF")
        top.pack(fill="x")

        tk.Label(
            top,
            text=f"#{filme['id']}",
            bg="#D1FAE5",
            fg="#065F46",
            font=("Segoe UI", 9, "bold"),
            padx=10,
            pady=2,
        ).pack(side="left")

        tk.Label(
            top,
            text=badge_text,
            bg=badge_color,
            fg="white",
            font=("Segoe UI", 9, "bold"),
            padx=10,
            pady=2,
        ).pack(side="right")

        tk.Label(
            card,
            text=filme["titulo"],
            bg="#FFFFFF",
            fg=self.palette["text"],
            font=("Bahnschrift", 17),
        ).pack(anchor="w", pady=(10, 0))

        subtitle = "Disponivel para aluguel imediato" if disponiveis > 0 else "Sem estoque neste momento"
        tk.Label(
            card,
            text=subtitle,
            bg="#FFFFFF",
            fg=self.palette["muted"],
            font=("Segoe UI", 10),
        ).pack(anchor="w", pady=(2, 2))

        self._apply_hover(card)

    def _apply_hover(self, card: tk.Frame) -> None:
        def enter(_event=None):
            card.config(highlightbackground=self.palette["accent"])

        def leave(_event=None):
            card.config(highlightbackground=self.palette["border"])

        widgets = [card] + card.winfo_children()
        for w in widgets:
            w.bind("<Enter>", enter)
            w.bind("<Leave>", leave)

    def alugar_filme(self) -> None:
        nome = self.nome_var.get().strip()
        item = self.filme_var.get().strip()

        if not nome:
            messagebox.showwarning("Campo obrigatorio", "Informe o nome do cliente.")
            return

        if not item:
            messagebox.showwarning("Campo obrigatorio", "Selecione um filme.")
            return

        try:
            filme_id = int(item.split(" - ", 1)[0])
        except Exception:
            messagebox.showerror("Erro", "Nao foi possivel identificar o filme selecionado.")
            return

        self._async_call(
            worker=lambda: self.gateway.alugar_filme(filme_id, nome),
            on_success=self._on_aluguel_concluido,
            error_message="Falha ao processar aluguel",
        )

    def _on_aluguel_concluido(self, resposta: dict) -> None:
        ok = bool(resposta.get("ok"))
        msg = resposta.get("mensagem", "Operacao concluida.")
        self.show_toast(msg, kind="success" if ok else "warning")
        self.status_label.config(text=msg)
        self.carregar_catalogo()

    def abrir_historico(self) -> None:
        if self._history_window and self._history_window.winfo_exists():
            self._history_window.lift()
            self._carregar_historico()
            return

        self._history_window = tk.Toplevel(self)
        self._history_window.title("Historico de Alugueis")
        self._history_window.geometry("760x420")
        self._history_window.configure(bg=self.palette["panel"])

        frame = tk.Frame(self._history_window, bg=self.palette["panel"], padx=10, pady=10)
        frame.pack(fill="both", expand=True)

        tree = ttk.Treeview(
            frame,
            columns=("id", "data", "cliente", "titulo"),
            show="headings",
            style="Movie.Treeview",
        )
        tree.heading("id", text="#")
        tree.heading("data", text="Data/Hora")
        tree.heading("cliente", text="Cliente")
        tree.heading("titulo", text="Titulo")

        tree.column("id", width=55, anchor="center")
        tree.column("data", width=180)
        tree.column("cliente", width=190)
        tree.column("titulo", width=310)

        tree.pack(fill="both", expand=True)
        self._history_tree = tree

        self._carregar_historico()

    def _carregar_historico(self) -> None:
        self._async_call(
            worker=self.gateway.historico_alugueis,
            on_success=self._on_historico_carregado,
            error_message="Falha ao carregar historico",
        )

    def _on_historico_carregado(self, itens: list[dict]) -> None:
        if not self._history_tree:
            return

        for row in self._history_tree.get_children():
            self._history_tree.delete(row)

        for item in itens:
            self._history_tree.insert(
                "",
                "end",
                values=(item["id"], item["data_hora"], item["cliente"], item["titulo"]),
            )

        self.status_label.config(text=f"Historico carregado: {len(itens)} registro(s).")

    def show_toast(self, message: str, kind: str = "info") -> None:
        colors = {
            "info": "#2563EB",
            "success": self.palette["ok"],
            "warning": self.palette["warn"],
            "danger": self.palette["danger"],
        }
        bg = colors.get(kind, "#2563EB")

        if self._toast_label is None or not self._toast_label.winfo_exists():
            self._toast_label = tk.Label(
                self,
                text="",
                bg=bg,
                fg="white",
                font=("Segoe UI", 10, "bold"),
                padx=14,
                pady=8,
            )

        self._toast_label.config(text=message, bg=bg)
        self.update_idletasks()

        target_x = max(20, self.winfo_width() - self._toast_label.winfo_reqwidth() - 24)
        start_x = self.winfo_width() + 30
        y = 20

        if self._toast_after_id:
            self.after_cancel(self._toast_after_id)
            self._toast_after_id = None

        def slide_in(step: int = 0) -> None:
            if step > 12:
                self._toast_after_id = self.after(2200, slide_out)
                return
            x = int(start_x - (start_x - target_x) * (step / 12))
            self._toast_label.place(x=x, y=y)
            self.after(14, lambda: slide_in(step + 1))

        def slide_out(step: int = 0) -> None:
            if step > 12:
                self._toast_label.place_forget()
                self._toast_after_id = None
                return
            x = int(target_x + (start_x - target_x) * (step / 12))
            self._toast_label.place(x=x, y=y)
            self.after(14, lambda: slide_out(step + 1))

        slide_in()


def main() -> None:
    app = AppClienteGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
