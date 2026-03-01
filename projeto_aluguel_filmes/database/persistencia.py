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
						FOREIGN KEY(filme_id) REFERENCES filmes(id)
					)
					"""
				)
				conn.commit()

			self._seed_if_empty()

	def _seed_if_empty(self) -> None:
		with self._connect() as conn:
			total = conn.execute("SELECT COUNT(*) AS total FROM filmes").fetchone()["total"]
			if total > 0:
				return

			filmes_iniciais = [
				(1, "Interestelar", 2),
				(2, "Matrix", 1),
				(3, "Cidade de Deus", 3),
				(4, "O Senhor dos Anéis", 2),
				(5, "A Viagem de Chihiro", 1),
			]
			conn.executemany(
				"INSERT INTO filmes (id, titulo, disponiveis) VALUES (?, ?, ?)",
				filmes_iniciais,
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

	def historico_alugueis(self) -> List[Dict]:
		with self._db_lock:
			with self._connect() as conn:
				rows = conn.execute(
					"""
					SELECT a.id, a.cliente, a.data_hora, f.titulo
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
				"titulo": row["titulo"],
			}
			for row in rows
		]

