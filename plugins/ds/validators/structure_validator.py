"""
LRU 캐시 구조 검증 플러그인 (25점)

AST 분석으로 학습자가 Node 클래스로 이중 연결 리스트를 직접 구현했는지,
OrderedDict/deque/functools.lru_cache를 사용하지 않았는지 검증.

AI 트랩: OrderedDict/deque 사용
"""
import ast
from typing import Dict, Any, List, Tuple

from core.base_validator import BaseValidator
from core.check_item import CheckItem
from plugins.python.validators._helpers import (
    collect_py_files,
    parse_all_files,
)


class StructureValidator(BaseValidator):
    """LRU 캐시 코드 구조 검증 (Node 클래스, 금지 import, 연결 리스트 메서드)"""

    def __init__(self, mission_config: Dict[str, Any]):
        super().__init__(mission_config)
        self.submission_dir = ""
        self.parsed: List[Tuple[str, ast.Module]] = []

    def setup(self) -> None:
        self.submission_dir = self.config.get("submission_dir", "")
        py_files = collect_py_files(self.submission_dir)
        self.parsed = parse_all_files(py_files)

    def build_checklist(self) -> None:
        self.checklist.add_item(CheckItem(
            id="node_class",
            description="Node 클래스에 prev/next/key/value 속성이 존재하는지 확인",
            points=10,
            validator=self._check_node_class,
            hint="Node 클래스에 prev, next, key, value 속성을 정의하세요",
        ))

        self.checklist.add_item(CheckItem(
            id="no_builtin_cache",
            description="OrderedDict/deque/functools.lru_cache를 사용하지 않는지 확인",
            points=10,
            validator=self._check_no_builtin_cache,
            hint="OrderedDict, deque, functools.lru_cache 대신 Node 클래스로 직접 구현하세요",
            ai_trap=True,
        ))

        self.checklist.add_item(CheckItem(
            id="linked_list_ops",
            description="이중 연결 리스트 조작 메서드(move_to_front 등)가 존재하는지 확인",
            points=5,
            validator=self._check_linked_list_ops,
            hint="DoublyLinkedList에 move_to_front, insert_front, remove 등의 메서드를 구현하세요",
        ))

    def teardown(self) -> None:
        pass

    # -- 검증 함수 --

    def _check_node_class(self) -> bool:
        """AST에서 Node 클래스의 __init__에 prev/next/key/value 할당 확인"""
        required_attrs = {"prev", "next", "key", "value"}

        for _, tree in self.parsed:
            for node in ast.walk(tree):
                if not (isinstance(node, ast.ClassDef) and node.name == "Node"):
                    continue

                # __init__ 메서드 찾기
                found_attrs = set()
                for item in node.body:
                    if isinstance(item, ast.FunctionDef) and item.name == "__init__":
                        for stmt in ast.walk(item):
                            # self.attr = ... 패턴 탐색
                            if isinstance(stmt, ast.Assign):
                                for target in stmt.targets:
                                    if (isinstance(target, ast.Attribute)
                                            and isinstance(target.value, ast.Name)
                                            and target.value.id == "self"):
                                        found_attrs.add(target.attr)
                            # self.attr: type = ... (AnnAssign)
                            if isinstance(stmt, ast.AnnAssign):
                                if (isinstance(stmt.target, ast.Attribute)
                                        and isinstance(stmt.target.value, ast.Name)
                                        and stmt.target.value.id == "self"):
                                    found_attrs.add(stmt.target.attr)

                if required_attrs.issubset(found_attrs):
                    return True

        return False

    def _check_no_builtin_cache(self) -> bool:
        """AST에서 OrderedDict/deque/functools.lru_cache import 탐지"""
        forbidden_names = {"OrderedDict", "deque", "lru_cache"}
        forbidden_modules = {"collections", "functools"}

        for _, tree in self.parsed:
            for node in ast.walk(tree):
                # import collections / import functools
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name in forbidden_modules:
                            return False

                # from collections import OrderedDict / from collections import deque
                if isinstance(node, ast.ImportFrom):
                    if node.module in forbidden_modules:
                        for alias in node.names:
                            if alias.name in forbidden_names:
                                return False
                    # from functools import lru_cache
                    if node.module == "functools":
                        for alias in node.names:
                            if alias.name == "lru_cache":
                                return False

        return True

    def _check_linked_list_ops(self) -> bool:
        """이중 연결 리스트 관련 메서드 존재 확인

        아래 메서드 이름 중 2개 이상이 존재하면 통과:
        move_to_front, insert_front, remove, remove_back, add_to_head, add_to_front,
        move_to_head, remove_tail, remove_last, push_front, pop_back
        """
        linked_list_methods = {
            "move_to_front", "insert_front", "remove", "remove_back",
            "add_to_head", "add_to_front", "move_to_head",
            "remove_tail", "remove_last", "push_front", "pop_back",
        }

        found_methods = set()

        for _, tree in self.parsed:
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if node.name in linked_list_methods:
                        found_methods.add(node.name)

        # 최소 2개 이상의 연결 리스트 메서드가 있어야 함
        return len(found_methods) >= 2
