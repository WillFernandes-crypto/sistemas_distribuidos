from contextlib import contextmanager
from threading import Lock


class GerenciadorLocks:
	def __init__(self) -> None:
		self._global_lock = Lock()
		self._locks_por_recurso: dict[str, Lock] = {}

	def _obter_lock(self, recurso: str) -> Lock:
		with self._global_lock:
			if recurso not in self._locks_por_recurso:
				self._locks_por_recurso[recurso] = Lock()
			return self._locks_por_recurso[recurso]

	@contextmanager
	def lock_recurso(self, recurso: str):
		lock = self._obter_lock(recurso)
		lock.acquire()
		try:
			yield
		finally:
			lock.release()

