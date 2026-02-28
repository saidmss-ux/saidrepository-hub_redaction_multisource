from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")


class TaskRunner:
    def run(self, fn: Callable[[], T]) -> T:
        return fn()


def get_task_runner() -> TaskRunner:
    return TaskRunner()
