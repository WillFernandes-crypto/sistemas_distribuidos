import threading
import tkinter as tk
import unicodedata
from pathlib import Path
from tkinter import messagebox, ttk

from PIL import Image, ImageOps, ImageTk

from app_cliente import obter_proxy_servidor


POSTER_WIDTH = 150
POSTER_HEIGHT = 220


class RpcGateway:
    def listar_filmes(self) -> list:
        proxy = obter_proxy_servidor()
        return proxy.listar_filmes()

    def alugar_filme(self, filme_id: int, cliente: str) -> dict:
        proxy = obter_proxy_servidor()
        return proxy.alugar_filme(filme_id, cliente)

    def devolver_filme(self, filme_id: int, cliente: str) -> dict:
        proxy = obter_proxy_servidor()
        return proxy.devolver_filme(filme_id, cliente)

    def historico_alugueis(self) -> list:
        proxy = obter_proxy_servidor()
        return proxy.historico_alugueis()


class AppClienteGUI(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("MovieRent | Distributed Client")
        self.geometry("1220x760")
        self.minsize(980, 640)

        self.palette = {
            "bg": "#F4EFE6",
            "panel": "#FFFCF5",
            "text": "#1F2937",
            "muted": "#6B7280",
            "accent": "#0F766E",
            "accent_2": "#F97316",
            "ok": "#15803D",
            "warn": "#C2410C",
            "danger": "#B91C1C",
            "border": "#E5E7EB",
            "card": "#FFFFFF",
            "selected": "#CDECE8",
        }
        self.configure(bg=self.palette["bg"])

        self.gateway = RpcGateway()
        self.filmes: list[dict] = []
        self.filtered_filmes: list[dict] = []
        self.selected_filme_id: int | None = None

        self.nome_var = tk.StringVar(value="")
        self.search_var = tk.StringVar(value="")

        self._history_window: tk.Toplevel | None = None
        self._history_tree: ttk.Treeview | None = None
        self._toast_label: tk.Label | None = None
        self._toast_after_id: str | None = None
        self._loading = False

        self.image_dir = Path(__file__).resolve().parents[1] / "imgs"
        self.cover_cache: dict[str, ImageTk.PhotoImage] = {}
        self._image_files = [
            p
            for p in self.image_dir.glob("*")
            if p.suffix.lower() in {".jpg", ".jpeg", ".jfif", ".png"}
        ]

        self._configure_styles()
        self._build_layout()
        self.after(220, self.carregar_catalogo)

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
            rowheight=28,
        )
        style.configure(
            "Movie.Treeview.Heading",
            background="#E2E8F0",
            foreground=self.palette["text"],
            relief="flat",
            font=("Segoe UI", 10, "bold"),
        )

    def _build_layout(self) -> None:
        self.header = tk.Canvas(self, height=112, bd=0, highlightthickness=0)
        self.header.pack(fill="x")
        self.header.bind("<Configure>", self._render_header)

        self.main = tk.Frame(self, bg=self.palette["bg"])
        self.main.pack(fill="both", expand=True, padx=18, pady=(12, 14))

        self.left_panel = tk.Frame(
            self.main,
            bg=self.palette["panel"],
            highlightbackground=self.palette["border"],
            highlightthickness=1,
            padx=16,
            pady=16,
            width=300,
        )
        self.left_panel.pack(side="left", fill="y")
        self.left_panel.pack_propagate(False)

        self.right_panel = tk.Frame(
            self.main,
            bg=self.palette["panel"],
            highlightbackground=self.palette["border"],
            highlightthickness=1,
            padx=14,
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

        c1 = (17, 94, 89)
        c2 = (234, 88, 12)
        for i in range(width):
            ratio = i / width
            r = int(c1[0] + (c2[0] - c1[0]) * ratio)
            g = int(c1[1] + (c2[1] - c1[1]) * ratio)
            b = int(c1[2] + (c2[2] - c1[2]) * ratio)
            self.header.create_line(i, 0, i, height, fill=f"#{r:02x}{g:02x}{b:02x}")

        self.header.create_oval(width - 185, -44, width + 70, 164, fill="#ffffff1e", outline="")
        self.header.create_oval(width - 330, 26, width - 50, 236, fill="#ffffff16", outline="")

        self.header.create_text(
            26,
            36,
            text="MovieRent Distributed",
            anchor="w",
            fill="white",
            font=("Bahnschrift", 24, "bold"),
        )
        self.header.create_text(
            26,
            78,
            text="Catálogo visual por capas, busca instantânea e fluxo de aluguel/devolução via RPC",
            anchor="w",
            fill="#F8FAFC",
            font=("Segoe UI", 11),
        )

    def _build_left_panel(self) -> None:
        tk.Label(
            self.left_panel,
            text="Ações",
            bg=self.palette["panel"],
            fg=self.palette["text"],
            font=("Bahnschrift", 17, "bold"),
        ).pack(anchor="w")

        tk.Label(
            self.left_panel,
            text="Selecione um filme no catálogo e informe o cliente.",
            bg=self.palette["panel"],
            fg=self.palette["muted"],
            font=("Segoe UI", 10),
            wraplength=250,
            justify="left",
        ).pack(anchor="w", pady=(4, 14))

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
            width=28,
        )
        self.nome_entry.pack(anchor="w", pady=(6, 14), ipady=6)

        self.selected_label = tk.Label(
            self.left_panel,
            text="Filme selecionado: nenhum",
            bg=self.palette["panel"],
            fg=self.palette["muted"],
            font=("Segoe UI", 10, "italic"),
            wraplength=250,
            justify="left",
        )
        self.selected_label.pack(anchor="w", pady=(0, 12))

        self.btn_alugar = self._create_action_button(
            self.left_panel,
            text="Alugar Filme",
            bg=self.palette["accent"],
            command=self.alugar_filme,
        )
        self.btn_alugar.pack(fill="x", pady=(0, 10))

        self.btn_devolver = self._create_action_button(
            self.left_panel,
            text="Devolver Filme",
            bg="#1D4ED8",
            command=self.devolver_filme,
        )
        self.btn_devolver.pack(fill="x", pady=(0, 10))

        self.btn_hist = self._create_action_button(
            self.left_panel,
            text="Ver Histórico",
            bg=self.palette["accent_2"],
            command=self.abrir_historico,
        )
        self.btn_hist.pack(fill="x", pady=(0, 10))

        self.btn_refresh = self._create_action_button(
            self.left_panel,
            text="Atualizar Catálogo",
            bg="#334155",
            command=self.carregar_catalogo,
        )
        self.btn_refresh.pack(fill="x", pady=(0, 16))

        tk.Label(
            self.left_panel,
            text="Dica: use a barra de busca para filtrar por nome.",
            bg=self.palette["panel"],
            fg=self.palette["muted"],
            font=("Segoe UI", 9),
            wraplength=250,
            justify="left",
        ).pack(anchor="w")

    def _build_right_panel(self) -> None:
        header = tk.Frame(self.right_panel, bg=self.palette["panel"])
        header.pack(fill="x", pady=(2, 10))

        tk.Label(
            header,
            text="Catálogo de Filmes",
            bg=self.palette["panel"],
            fg=self.palette["text"],
            font=("Bahnschrift", 20, "bold"),
        ).pack(side="left")

        search_wrap = tk.Frame(header, bg=self.palette["panel"])
        search_wrap.pack(side="right")

        tk.Label(
            search_wrap,
            text="Buscar:",
            bg=self.palette["panel"],
            fg=self.palette["muted"],
            font=("Segoe UI", 10, "bold"),
        ).pack(side="left", padx=(0, 6))

        self.search_entry = tk.Entry(
            search_wrap,
            textvariable=self.search_var,
            width=28,
            font=("Segoe UI", 10),
            relief="flat",
            bg="#F9FAFB",
            highlightthickness=1,
            highlightbackground=self.palette["border"],
            highlightcolor=self.palette["accent"],
        )
        self.search_entry.pack(side="left", ipady=4)
        self.search_var.trace_add("write", self._on_search_change)

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
        self.scroll_canvas.bind("<Configure>", self._on_canvas_resize)

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
            error_message="Falha ao carregar catálogo",
        )

    def _on_catalogo_carregado(self, filmes: list[dict]) -> None:
        self.filmes = filmes
        self._apply_filter_and_render()
        self.status_label.config(text=f"Catálogo sincronizado: {len(filmes)} filme(s).")

    def _on_search_change(self, *_args) -> None:
        self._apply_filter_and_render()

    def _on_canvas_resize(self, _event=None) -> None:
        # Re-render to keep a responsive grid based on available width.
        self._render_grid(animated=False)

    def _apply_filter_and_render(self) -> None:
        query = self._normalize(self.search_var.get().strip())
        if not query:
            self.filtered_filmes = list(self.filmes)
        else:
            self.filtered_filmes = [f for f in self.filmes if query in self._normalize(f["titulo"])]

        if self.selected_filme_id and not any(f["id"] == self.selected_filme_id for f in self.filtered_filmes):
            self.selected_filme_id = None
            self.selected_label.config(text="Filme selecionado: nenhum")

        self._render_grid(animated=True)

    def _normalize(self, text: str) -> str:
        normalized = unicodedata.normalize("NFKD", text)
        return "".join(ch for ch in normalized if not unicodedata.combining(ch)).lower()

    def _render_grid(self, animated: bool) -> None:
        for child in self.cards_container.winfo_children():
            child.destroy()

        if not self.filtered_filmes:
            msg = "Nenhum filme encontrado para a busca." if self.search_var.get().strip() else "Nenhum filme cadastrado."
            tk.Label(
                self.cards_container,
                text=msg,
                bg=self.palette["panel"],
                fg=self.palette["muted"],
                font=("Segoe UI", 11),
            ).pack(anchor="w", padx=8, pady=8)
            return

        width = max(self.scroll_canvas.winfo_width(), 620)
        cols = max(3, width // 190)

        for idx, filme in enumerate(self.filtered_filmes):
            if animated:
                self.after(idx * 35, lambda i=idx, f=filme, c=cols: self._add_poster_card(i, f, c))
            else:
                self._add_poster_card(idx, filme, cols)

    def _add_poster_card(self, idx: int, filme: dict, cols: int) -> None:
        row = idx // cols
        col = idx % cols

        is_selected = self.selected_filme_id == filme["id"]
        border_color = self.palette["accent"] if is_selected else self.palette["border"]
        card_bg = self.palette["selected"] if is_selected else self.palette["card"]

        card = tk.Frame(
            self.cards_container,
            bg=card_bg,
            highlightthickness=2,
            highlightbackground=border_color,
            padx=8,
            pady=8,
            cursor="hand2",
        )
        card.grid(row=row, column=col, padx=8, pady=8, sticky="n")

        image = self._get_cover_image(filme["titulo"])
        poster = tk.Label(card, image=image, bg=card_bg, cursor="hand2")
        poster.image = image
        poster.pack()

        titulo = tk.Label(
            card,
            text=filme["titulo"],
            bg=card_bg,
            fg=self.palette["text"],
            font=("Segoe UI", 10, "bold"),
            wraplength=POSTER_WIDTH,
            justify="center",
            cursor="hand2",
        )
        titulo.pack(pady=(8, 2))

        disponiveis = int(filme["disponiveis"])
        estoque_cor = self.palette["ok"] if disponiveis > 1 else self.palette["warn"] if disponiveis == 1 else self.palette["danger"]
        estoque = tk.Label(
            card,
            text=f"{disponiveis} disponíveis",
            bg=card_bg,
            fg=estoque_cor,
            font=("Segoe UI", 9, "bold"),
            cursor="hand2",
        )
        estoque.pack(pady=(0, 2))

        self._bind_select(card, filme)
        self._bind_select(poster, filme)
        self._bind_select(titulo, filme)
        self._bind_select(estoque, filme)

    def _bind_select(self, widget: tk.Widget, filme: dict) -> None:
        widget.bind("<Button-1>", lambda _e: self._select_filme(filme))

    def _select_filme(self, filme: dict) -> None:
        self.selected_filme_id = int(filme["id"])
        self.selected_label.config(text=f"Filme selecionado: {filme['titulo']} (id {filme['id']})")
        self._render_grid(animated=False)

    def _get_cover_image(self, titulo: str) -> ImageTk.PhotoImage:
        key = self._normalize(titulo)
        if key in self.cover_cache:
            return self.cover_cache[key]

        image_path = self._resolve_cover_path(titulo)
        if image_path:
            img = Image.open(image_path).convert("RGB")
            img = ImageOps.fit(img, (POSTER_WIDTH, POSTER_HEIGHT), method=Image.Resampling.LANCZOS)
        else:
            img = Image.new("RGB", (POSTER_WIDTH, POSTER_HEIGHT), color="#CBD5E1")

        photo = ImageTk.PhotoImage(img)
        self.cover_cache[key] = photo
        return photo

    def _resolve_cover_path(self, titulo: str) -> Path | None:
        norm_title = self._normalize(titulo)

        manual_map = {
            "matrix": ["The Matrix.jfif", "matrix.jfif", "matrix.jpg"],
            "cidade de deus": ["cidade de deus.jfif", "cidade_de_deus.jpg"],
            "interestelar": ["interestelar.jpg", "interstellar.jpg"],
            "a viagem de chihiro": ["viagem-de-chihiro.jpg", "chihiro.jpg"],
            "o alto da compadecida": ["o_alto_da_compadecida.jpg"],
            "o poderoso chefao": ["the_godfather.jfif", "godfather.jpg"],
            "a lista de schindler": ["schindler's_list.jpg", "schindlers_list.jpg"],
        }

        for title_key, files in manual_map.items():
            if title_key == norm_title:
                for filename in files:
                    path = self.image_dir / filename
                    if path.exists():
                        return path

        for file_path in self._image_files:
            norm_name = self._normalize(file_path.stem)
            if norm_title in norm_name or norm_name in norm_title:
                return file_path

        return None

    def _selected_filme(self) -> dict | None:
        if self.selected_filme_id is None:
            return None
        for filme in self.filmes:
            if int(filme["id"]) == self.selected_filme_id:
                return filme
        return None

    def alugar_filme(self) -> None:
        nome = self.nome_var.get().strip()
        filme = self._selected_filme()

        if not nome:
            messagebox.showwarning("Campo obrigatório", "Informe o nome do cliente.")
            return

        if filme is None:
            messagebox.showwarning("Seleção obrigatória", "Selecione um filme no catálogo.")
            return

        filme_id = int(filme["id"])
        self._async_call(
            worker=lambda: self.gateway.alugar_filme(filme_id, nome),
            on_success=self._on_operacao_aluguel,
            error_message="Falha ao processar aluguel",
        )

    def devolver_filme(self) -> None:
        nome = self.nome_var.get().strip()
        filme = self._selected_filme()

        if not nome:
            messagebox.showwarning("Campo obrigatório", "Informe o nome do cliente.")
            return

        if filme is None:
            messagebox.showwarning("Seleção obrigatória", "Selecione um filme no catálogo.")
            return

        filme_id = int(filme["id"])
        self._async_call(
            worker=lambda: self.gateway.devolver_filme(filme_id, nome),
            on_success=self._on_operacao_devolucao,
            error_message="Falha ao processar devolução",
        )

    def _on_operacao_aluguel(self, resposta: dict) -> None:
        ok = bool(resposta.get("ok"))
        msg = resposta.get("mensagem", "Operação concluída.")
        self.show_toast(msg, kind="success" if ok else "warning")
        self.status_label.config(text=msg)
        self.carregar_catalogo()

    def _on_operacao_devolucao(self, resposta: dict) -> None:
        ok = bool(resposta.get("ok"))
        msg = resposta.get("mensagem", "Operação concluída.")
        self.show_toast(msg, kind="success" if ok else "warning")
        self.status_label.config(text=msg)
        self.carregar_catalogo()

    def abrir_historico(self) -> None:
        if self._history_window and self._history_window.winfo_exists():
            self._history_window.lift()
            self._carregar_historico()
            return

        self._history_window = tk.Toplevel(self)
        self._history_window.title("Histórico de Aluguéis")
        self._history_window.geometry("900x460")
        self._history_window.configure(bg=self.palette["panel"])

        frame = tk.Frame(self._history_window, bg=self.palette["panel"], padx=10, pady=10)
        frame.pack(fill="both", expand=True)

        tree = ttk.Treeview(
            frame,
            columns=("id", "data", "cliente", "titulo", "status", "devolucao"),
            show="headings",
            style="Movie.Treeview",
        )
        tree.heading("id", text="#")
        tree.heading("data", text="Data Aluguel")
        tree.heading("cliente", text="Cliente")
        tree.heading("titulo", text="Título")
        tree.heading("status", text="Status")
        tree.heading("devolucao", text="Data Devolução")

        tree.column("id", width=55, anchor="center")
        tree.column("data", width=155)
        tree.column("cliente", width=140)
        tree.column("titulo", width=240)
        tree.column("status", width=110)
        tree.column("devolucao", width=155)

        tree.pack(fill="both", expand=True)
        self._history_tree = tree

        self._carregar_historico()

    def _carregar_historico(self) -> None:
        self._async_call(
            worker=self.gateway.historico_alugueis,
            on_success=self._on_historico_carregado,
            error_message="Falha ao carregar histórico",
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
                values=(
                    item["id"],
                    item["data_hora"],
                    item["cliente"],
                    item["titulo"],
                    item.get("status", "-"),
                    item.get("devolvido_em") or "-",
                ),
            )

        self.status_label.config(text=f"Histórico carregado: {len(itens)} registro(s).")

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
