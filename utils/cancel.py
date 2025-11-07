import threading


class _CancelRegistry:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._flags: dict[str, bool] = {}

    def key(self, scope: str, identifier: int | str) -> str:
        return f"{scope}:{identifier}"

    def cancel(self, scope: str, identifier: int | str) -> None:
        with self._lock:
            self._flags[self.key(scope, identifier)] = True

    def is_cancelled(self, scope: str, identifier: int | str) -> bool:
        with self._lock:
            return self._flags.get(self.key(scope, identifier), False)

    def clear(self, scope: str, identifier: int | str) -> None:
        with self._lock:
            self._flags.pop(self.key(scope, identifier), None)


cancel_registry = _CancelRegistry()



