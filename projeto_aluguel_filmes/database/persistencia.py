import sqlite3
from pathlib import Path
from threading import Lock
from typing import Dict, List


class RepositorioFilmes:
	def __init__(self, db_path: str | None = None) -> None:
		base_dir = Path(__file__).resolve().parent
		self.db_path = db_path or str(base_dir / "catalogo_filmes.db")
		self._db_lock = Lock()
		self._init_db()

	def _connect(self) -> sqlite3.Connection:
		conn = sqlite3.connect(self.db_path, check_same_thread=False)
		conn.row_factory = sqlite3.Row
		return conn

	def _init_db(self) -> None:
		with self._db_lock:
			with self._connect() as conn:
				conn.execute(
					"""
					CREATE TABLE IF NOT EXISTS filmes (
						id INTEGER PRIMARY KEY,
						titulo TEXT NOT NULL,
						disponiveis INTEGER NOT NULL CHECK(disponiveis >= 0)
					)
					"""
				)
				conn.execute(
					"""
					CREATE TABLE IF NOT EXISTS alugueis (
						id INTEGER PRIMARY KEY AUTOINCREMENT,
						filme_id INTEGER NOT NULL,
						cliente TEXT NOT NULL,
						data_hora TEXT DEFAULT CURRENT_TIMESTAMP,
						devolvido_em TEXT,
						FOREIGN KEY(filme_id) REFERENCES filmes(id)
					)
					"""
				)
				self._garantir_coluna_devolucao(conn)
				conn.commit()

			self._seed_if_empty()
			self._sincronizar_catalogo_base()

	def _catalogo_base(self) -> list[tuple[int, str, int]]:
		return [
			(1, "Interestelar", 2),
			(2, "Matrix", 1),
			(3, "Cidade de Deus", 3),
			(4, "O Alto da Compadecida", 2),
			(5, "A Viagem de Chihiro", 1),
			(6, "O Poderoso Chefão", 2),
			(7, "A Lista de Schindler", 2),
		]

	def _garantir_coluna_devolucao(self, conn: sqlite3.Connection) -> None:
		colunas = {row["name"] for row in conn.execute("PRAGMA table_info(alugueis)").fetchall()}
		if "devolvido_em" not in colunas:
			conn.execute("ALTER TABLE alugueis ADD COLUMN devolvido_em TEXT")

	def _seed_if_empty(self) -> None:
		with self._connect() as conn:
			total = conn.execute("SELECT COUNT(*) AS total FROM filmes").fetchone()["total"]
			if total > 0:
				return

			conn.executemany(
				"INSERT INTO filmes (id, titulo, disponiveis) VALUES (?, ?, ?)",
				self._catalogo_base(),
			)
			conn.commit()

	def _sincronizar_catalogo_base(self) -> None:
		with self._connect() as conn:
			for filme_id, titulo, disponiveis_default in self._catalogo_base():
				row = conn.execute(
					"SELECT id, titulo FROM filmes WHERE id = ?",
					(filme_id,),
				).fetchone()

				if row is None:
					conn.execute(
						"INSERT INTO filmes (id, titulo, disponiveis) VALUES (?, ?, ?)",
						(filme_id, titulo, disponiveis_default),
					)
				elif row["titulo"] != titulo:
					conn.execute(
						"UPDATE filmes SET titulo = ? WHERE id = ?",
						(titulo, filme_id),
					)

			# Remove item antigo caso esteja fora do catalogo padrao.
			conn.execute(
				"DELETE FROM filmes WHERE titulo IN (?, ?)",
				("O Senhor dos Anéis", "O Senhor dos Aneis"),
			)
			conn.commit()

	def listar_filmes(self) -> List[Dict]:
		with self._db_lock:
			with self._connect() as conn:
				rows = conn.execute(
					"SELECT id, titulo, disponiveis FROM filmes ORDER BY id"
				).fetchall()

		return [
			{"id": row["id"], "titulo": row["titulo"], "disponiveis": row["disponiveis"]}
			for row in rows
		]

	def alugar_filme(self, filme_id: int, cliente: str) -> Dict:
		with self._db_lock:
			with self._connect() as conn:
				row = conn.execute(
					"SELECT id, titulo, disponiveis FROM filmes WHERE id = ?",
					(filme_id,),
				).fetchone()

				if row is None:
					return {
						"ok": False,
						"mensagem": f"Filme com id {filme_id} não encontrado.",
					}

				if row["disponiveis"] <= 0:
					return {
						"ok": False,
						"mensagem": f"Sem cópias disponíveis para '{row['titulo']}'.",
					}

				conn.execute(
					"UPDATE filmes SET disponiveis = disponiveis - 1 WHERE id = ?",
					(filme_id,),
				)
				conn.execute(
					"INSERT INTO alugueis (filme_id, cliente) VALUES (?, ?)",
					(filme_id, cliente),
				)
				conn.commit()

				disponiveis = row["disponiveis"] - 1
				return {
					"ok": True,
					"mensagem": (
						f"Aluguel confirmado para '{row['titulo']}' por {cliente}. "
						f"Cópias restantes: {disponiveis}."
					),
				}

	def devolver_filme(self, filme_id: int, cliente: str) -> Dict:
		with self._db_lock:
			with self._connect() as conn:
				filme = conn.execute(
					"SELECT id, titulo FROM filmes WHERE id = ?",
					(filme_id,),
				).fetchone()

				if filme is None:
					return {
						"ok": False,
						"mensagem": f"Filme com id {filme_id} não encontrado.",
					}

				aluguel = conn.execute(
					"""
					SELECT id
					FROM alugueis
					WHERE filme_id = ? AND cliente = ? AND devolvido_em IS NULL
					ORDER BY id DESC
					LIMIT 1
					""",
					(filme_id, cliente),
				).fetchone()

				if aluguel is None:
					return {
						"ok": False,
						"mensagem": (
							f"Nenhum aluguel ativo de '{filme['titulo']}' encontrado para {cliente}."
						),
					}

				conn.execute(
					"UPDATE filmes SET disponiveis = disponiveis + 1 WHERE id = ?",
					(filme_id,),
				)
				conn.execute(
					"UPDATE alugueis SET devolvido_em = CURRENT_TIMESTAMP WHERE id = ?",
					(aluguel["id"],),
				)
				conn.commit()

				return {
					"ok": True,
					"mensagem": f"Devolução registrada para '{filme['titulo']}' por {cliente}.",
				}

	def historico_alugueis(self) -> List[Dict]:
		with self._db_lock:
			with self._connect() as conn:
				rows = conn.execute(
					"""
					SELECT
						a.id,
						a.cliente,
						a.data_hora,
						a.devolvido_em,
						f.titulo,
						CASE WHEN a.devolvido_em IS NULL THEN 'ativo' ELSE 'devolvido' END AS status
					FROM alugueis a
					JOIN filmes f ON f.id = a.filme_id
					ORDER BY a.id DESC
					"""
				).fetchall()

		return [
			{
				"id": row["id"],
				"cliente": row["cliente"],
				"data_hora": row["data_hora"],
				"devolvido_em": row["devolvido_em"],
				"status": row["status"],
				"titulo": row["titulo"],
			}
			for row in rows
		]

