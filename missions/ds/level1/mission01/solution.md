## 문항 1 정답지

### 정답 코드

모범 답안은 `sample_submission_ds/` 디렉토리에 위치합니다:
- `sample_submission_ds/lru_cache.py` — Node + DoublyLinkedList + LRUCache
- `sample_submission_ds/cli.py` — REPL + 명령어 파싱 + Redis 출력

### 핵심 구현 포인트

1. **Node 클래스**: `prev`, `next`, `key`, `value` 4개 속성
2. **DoublyLinkedList**: 센티널 head/tail로 경계 조건 제거, `move_to_front()`는 `remove()` + `insert_front()`
3. **LRUCache.get()**: `move_to_front()` 호출로 LRU 순서 갱신 (트랩!)
4. **Lazy deletion**: `get()` 호출 시 `time.time()` 비교 → 만료 키 즉시 삭제
5. **Redis 출력 형식**: `"value"` (쌍따옴표), `(nil)`, `(integer) N`, `OK`

### 정답 체크리스트

| 번호 | 체크 항목 | 배점 | 검증 방법 | AI 트랩 |
|------|----------|------|----------|---------|
| 1 | Node 클래스에 prev/next/key/value 존재 | 10 | AST 분석 | - |
| 2 | OrderedDict/deque/lru_cache 미사용 | 10 | AST Import 검사 | **Yes** |
| 3 | 이중 연결 리스트 조작 메서드 존재 | 5 | AST FunctionDef 검사 | - |
| 4 | cli.py 실행 + 프롬프트 출력 | 3 | subprocess | - |
| 5 | SET/GET 기본 동작 | 8 | subprocess | - |
| 6 | DEL 후 GET → (nil) | 4 | subprocess | - |
| 7 | EXISTS/DBSIZE 정확한 카운트 | 5 | subprocess | - |
| 8 | Redis 출력 형식 준수 | 5 | subprocess | **Yes** |
| 9 | CONFIG SET maxmemory 동작 | 5 | subprocess | - |
| 10 | LRU 제거 동작 | 8 | subprocess | - |
| 11 | GET 접근 시 LRU 순서 갱신 | 10 | subprocess | **Yes** |
| 12 | INFO memory 통계 정확 | 7 | subprocess | - |
| 13 | EXPIRE/TTL 기본 동작 | 6 | Popen + sleep | - |
| 14 | 만료 키 lazy deletion | 8 | Popen + sleep | **Yes** |
| 15 | 미존재/미설정 키 TTL 반환값 | 6 | subprocess | - |

- Pass 기준: 총 100점 중 70점 이상

### AI 트랩 해설

1. **no_builtin_cache** (10점): AI가 `from collections import OrderedDict`로 LRU를 간편 구현. Node 클래스로 직접 구현해야 함.
2. **output_format** (5점): AI가 Python의 `True`/`None`을 그대로 출력하거나, GET 값에 `"` 따옴표를 빠뜨림. Redis 형식 `OK`/`(nil)`/`(integer) N`/`"value"` 준수 필요.
3. **lru_get_refresh** (10점): AI가 SET만 LRU 갱신하고 GET은 조회만 함. GET도 `move_to_front()` 호출 필수.
4. **ttl_expired_get** (8점): AI가 별도 타이머/스레드로 TTL 처리. 실제로는 GET 시 만료 확인 → 삭제 + `(nil)` 반환하는 lazy deletion 필요.
