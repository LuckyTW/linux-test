## 문항 1: Mini LRU 캐시 구현

### 시험 정보
- 과정: AI 올인원
- 단계: AI·SW 기초
- 난이도: 1
- 권장 시간: 15분
- Pass 기준: 정답 체크리스트 15개 중 70점 이상 충족

### 문제

여러분은 Mini Redis를 구현합니다. **이중 연결 리스트**와 **dict**를 조합하여 LRU(Least Recently Used) 캐시를 만들고, Redis 스타일의 대화형 CLI를 제공해야 합니다.

#### 핵심 요구사항

1. **LRU 캐시 (`lru_cache.py`)**
   - `Node` 클래스: `prev`, `next`, `key`, `value` 속성을 가진 이중 연결 리스트 노드
   - `DoublyLinkedList` 클래스: 센티널(head/tail) 기반 이중 연결 리스트
     - `insert_front()`, `remove()`, `remove_back()`, `move_to_front()` 메서드
   - `LRUCache` 클래스: dict + DoublyLinkedList 조합
     - `set(key, value)` → "OK"
     - `get(key)` → 값 또는 None (**GET도 LRU 순서 갱신 필수!**)
     - `delete(key)` → 삭제된 수 (0 또는 1)
     - `exists(key)` → 1 또는 0
     - `dbsize()` → 현재 키 수
     - `expire(key, seconds)` → 1 또는 0
     - `ttl(key)` → -2(미존재), -1(TTL 미설정), >=0(남은 초)
     - `config_set("maxmemory", N)` → "OK" (maxmemory 초과 시 LRU 키 제거)
     - `info_memory()` → `{"used_memory": N, "maxmemory": N, "evicted_keys": N}`

2. **CLI (`cli.py`)**
   - `mini-redis> ` 프롬프트로 대화형 REPL
   - Redis 호환 출력 형식:
     - SET 성공 → `OK`
     - GET 값 → `"value"` (쌍따옴표 포함!)
     - GET 미존재 → `(nil)`
     - 정수 결과 → `(integer) N`
   - `EXIT` 또는 `QUIT`으로 종료
   - `CONFIG SET maxmemory N`, `INFO memory` 지원

### 제약 사항
- **OrderedDict, deque, functools.lru_cache 사용 금지** (Node로 직접 구현)
- **dict는 사용 가능** (키→노드 매핑용)
- TTL은 `time.time()` 기반 lazy deletion (GET 시 만료 확인 → 삭제 + `(nil)` 반환)
- 외부 패키지 설치 금지 (표준 라이브러리만 사용)

### 입력 형식

대화형 REPL에서 한 줄씩 명령어를 입력받습니다:

```
SET name Alice
GET name
DEL name
EXISTS name
DBSIZE
EXPIRE session 60
TTL session
CONFIG SET maxmemory 100
INFO memory
EXIT
```

### 출력 형식

Redis 호환 형식으로 출력합니다:

```
mini-redis> SET name Alice
OK
mini-redis> GET name
"Alice"
mini-redis> DEL name
(integer) 1
mini-redis> GET name
(nil)
mini-redis> DBSIZE
(integer) 0
```

### 제출 방식

`lru_cache.py`와 `cli.py` 2개 파일을 제출합니다.
- 템플릿 파일의 TODO 부분을 구현하세요.
- `cli.py`는 `from lru_cache import LRUCache`로 임포트합니다.
