"""
Mini Redis CLI - LRU 캐시 REPL 인터페이스

## 지원 명령어
- SET key value → OK
- GET key → "value" 또는 (nil)
- DEL key → (integer) N
- EXISTS key → (integer) N
- DBSIZE → (integer) N
- EXPIRE key seconds → (integer) N
- TTL key → (integer) N
- CONFIG SET maxmemory N → OK
- INFO memory → key:value 형식
- EXIT / QUIT → 종료

## 출력 형식 (Redis 호환)
- 성공: OK
- 문자열: "value" (쌍따옴표 포함)
- 정수: (integer) N
- 미존재: (nil)

## 프롬프트
- mini-redis>

TODO: REPL 루프와 명령어 파싱을 구현하세요
"""
from lru_cache import LRUCache


def main():
    cache = LRUCache()

    # TODO: REPL 루프 구현
    # 1. "mini-redis> " 프롬프트 출력
    # 2. 명령어 파싱 (따옴표 처리)
    # 3. 명령어 실행 + Redis 형식 출력
    # 4. EXIT/QUIT 시 종료
    pass


if __name__ == "__main__":
    main()
