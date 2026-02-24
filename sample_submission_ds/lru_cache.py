"""
Mini LRU Cache - 이중 연결 리스트 + dict 기반 LRU 캐시 구현

Node 클래스로 이중 연결 리스트를 직접 구현하며,
OrderedDict/deque/functools.lru_cache를 사용하지 않는다.
"""
import time


class Node:
    """이중 연결 리스트 노드"""

    def __init__(self, key: str = "", value: str = ""):
        self.key = key
        self.value = value
        self.prev: "Node | None" = None
        self.next: "Node | None" = None


class DoublyLinkedList:
    """센티널(head/tail) 기반 이중 연결 리스트"""

    def __init__(self):
        self.head = Node()  # 센티널 head
        self.tail = Node()  # 센티널 tail
        self.head.next = self.tail
        self.tail.prev = self.head

    def insert_front(self, node: Node) -> None:
        """노드를 리스트 맨 앞(head 다음)에 삽입"""
        node.prev = self.head
        node.next = self.head.next
        self.head.next.prev = node
        self.head.next = node

    def remove(self, node: Node) -> None:
        """노드를 리스트에서 제거"""
        node.prev.next = node.next
        node.next.prev = node.prev
        node.prev = None
        node.next = None

    def remove_back(self) -> Node | None:
        """리스트 맨 뒤(tail 이전) 노드를 제거하고 반환"""
        if self.tail.prev is self.head:
            return None
        node = self.tail.prev
        self.remove(node)
        return node

    def move_to_front(self, node: Node) -> None:
        """노드를 리스트 맨 앞으로 이동 (LRU 갱신)"""
        self.remove(node)
        self.insert_front(node)

    def is_empty(self) -> bool:
        """리스트가 비어있는지 확인"""
        return self.head.next is self.tail


class LRUCache:
    """dict + DoublyLinkedList 조합 LRU 캐시"""

    def __init__(self):
        self._store: dict[str, Node] = {}
        self._lru_list = DoublyLinkedList()
        self._ttl_map: dict[str, float] = {}
        self._maxmemory: int = 0  # 0 = 무제한
        self._evicted_keys: int = 0

    def _is_expired(self, key: str) -> bool:
        """키의 TTL이 만료되었는지 확인"""
        if key not in self._ttl_map:
            return False
        return time.time() > self._ttl_map[key]

    def _lazy_delete(self, key: str) -> None:
        """만료된 키를 lazy deletion으로 제거"""
        if key in self._store:
            node = self._store.pop(key)
            self._lru_list.remove(node)
        if key in self._ttl_map:
            del self._ttl_map[key]

    def _evict_if_needed(self) -> None:
        """maxmemory 초과 시 LRU 키 제거"""
        while self._maxmemory > 0 and len(self._store) > self._maxmemory:
            evicted = self._lru_list.remove_back()
            if evicted is None:
                break
            self._store.pop(evicted.key, None)
            self._ttl_map.pop(evicted.key, None)
            self._evicted_keys += 1

    def set(self, key: str, value: str) -> str:
        """키-값 저장. 이미 존재하면 값 갱신 + LRU 순서 갱신"""
        # 만료된 키 정리
        if key in self._store and self._is_expired(key):
            self._lazy_delete(key)

        if key in self._store:
            node = self._store[key]
            node.value = value
            self._lru_list.move_to_front(node)
        else:
            node = Node(key, value)
            self._store[key] = node
            self._lru_list.insert_front(node)
            self._evict_if_needed()

        return "OK"

    def get(self, key: str) -> str | None:
        """키 조회. GET도 LRU 순서를 갱신한다."""
        # 만료 확인 → lazy deletion
        if key in self._store and self._is_expired(key):
            self._lazy_delete(key)
            return None

        if key not in self._store:
            return None

        node = self._store[key]
        self._lru_list.move_to_front(node)  # GET 접근 시 LRU 갱신!
        return node.value

    def delete(self, key: str) -> int:
        """키 삭제. 삭제된 키 수 반환 (0 또는 1)"""
        if key in self._store and self._is_expired(key):
            self._lazy_delete(key)
            return 0

        if key not in self._store:
            return 0

        node = self._store.pop(key)
        self._lru_list.remove(node)
        self._ttl_map.pop(key, None)
        return 1

    def exists(self, key: str) -> int:
        """키 존재 여부 확인. 1 또는 0 반환"""
        if key in self._store and self._is_expired(key):
            self._lazy_delete(key)
            return 0

        return 1 if key in self._store else 0

    def dbsize(self) -> int:
        """현재 저장된 키 수 반환"""
        # 만료 키는 lazy하게 처리하므로, 실제로 접근 시에만 정리
        return len(self._store)

    def expire(self, key: str, seconds: int) -> int:
        """키에 TTL 설정. 성공 시 1, 키 미존재 시 0"""
        if key in self._store and self._is_expired(key):
            self._lazy_delete(key)
            return 0

        if key not in self._store:
            return 0

        self._ttl_map[key] = time.time() + seconds
        return 1

    def ttl(self, key: str) -> int:
        """키의 남은 TTL 조회.
        -2: 키 미존재, -1: TTL 미설정, >=0: 남은 초"""
        if key in self._store and self._is_expired(key):
            self._lazy_delete(key)
            return -2

        if key not in self._store:
            return -2

        if key not in self._ttl_map:
            return -1

        remaining = self._ttl_map[key] - time.time()
        return max(0, int(remaining))

    def config_set(self, param: str, value: str) -> str:
        """CONFIG SET 명령어 처리"""
        if param == "maxmemory":
            self._maxmemory = int(value)
            self._evict_if_needed()
            return "OK"
        return "ERR unknown parameter"

    def info_memory(self) -> dict:
        """INFO memory 통계 반환"""
        return {
            "used_memory": len(self._store),
            "maxmemory": self._maxmemory,
            "evicted_keys": self._evicted_keys,
        }
