"""
Mini LRU Cache - 이중 연결 리스트 + dict 기반 LRU 캐시 구현

## 요구사항
- Node 클래스로 이중 연결 리스트를 직접 구현할 것
- OrderedDict, deque, functools.lru_cache 사용 금지
- dict는 사용 가능
- time.time() 기반 TTL 관리
"""
import time


class Node:
    """이중 연결 리스트 노드

    TODO: prev, next, key, value 속성을 구현하세요
    """

    def __init__(self, key: str = "", value: str = ""):
        pass  # TODO: 구현하세요


class DoublyLinkedList:
    """센티널(head/tail) 기반 이중 연결 리스트

    TODO: 아래 메서드들을 구현하세요
    """

    def __init__(self):
        pass  # TODO: head/tail 센티널 노드 초기화

    def insert_front(self, node: Node) -> None:
        """노드를 리스트 맨 앞(head 다음)에 삽입"""
        pass  # TODO: 구현하세요

    def remove(self, node: Node) -> None:
        """노드를 리스트에서 제거"""
        pass  # TODO: 구현하세요

    def remove_back(self) -> Node | None:
        """리스트 맨 뒤(tail 이전) 노드를 제거하고 반환"""
        pass  # TODO: 구현하세요

    def move_to_front(self, node: Node) -> None:
        """노드를 리스트 맨 앞으로 이동 (LRU 갱신)"""
        pass  # TODO: 구현하세요


class LRUCache:
    """dict + DoublyLinkedList 조합 LRU 캐시

    TODO: 아래 메서드들을 구현하세요.
    주의: GET도 LRU 순서를 갱신해야 합니다!
    """

    def __init__(self):
        pass  # TODO: _store, _lru_list, _ttl_map, _maxmemory, _evicted_keys 초기화

    def set(self, key: str, value: str) -> str:
        """키-값 저장. 이미 존재하면 값 갱신. → "OK" 반환"""
        pass  # TODO: 구현하세요

    def get(self, key: str) -> str | None:
        """키 조회. 만료 시 lazy deletion → None 반환"""
        pass  # TODO: 구현하세요 (LRU 순서 갱신 필수!)

    def delete(self, key: str) -> int:
        """키 삭제. 삭제된 키 수 반환 (0 또는 1)"""
        pass  # TODO: 구현하세요

    def exists(self, key: str) -> int:
        """키 존재 여부. 1 또는 0 반환"""
        pass  # TODO: 구현하세요

    def dbsize(self) -> int:
        """현재 저장된 키 수 반환"""
        pass  # TODO: 구현하세요

    def expire(self, key: str, seconds: int) -> int:
        """키에 TTL 설정. 성공 1, 키 미존재 0"""
        pass  # TODO: 구현하세요

    def ttl(self, key: str) -> int:
        """남은 TTL 조회. -2: 미존재, -1: TTL 미설정, >=0: 남은 초"""
        pass  # TODO: 구현하세요

    def config_set(self, param: str, value: str) -> str:
        """CONFIG SET 명령어 처리 (maxmemory 설정)"""
        pass  # TODO: 구현하세요

    def info_memory(self) -> dict:
        """INFO memory 통계 반환 (used_memory, maxmemory, evicted_keys)"""
        pass  # TODO: 구현하세요
