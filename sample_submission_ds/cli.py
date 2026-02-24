"""
Mini Redis CLI - LRU 캐시 REPL 인터페이스

Redis 스타일 출력 형식:
- SET → OK
- GET → "value" 또는 (nil)
- DEL → (integer) N
- EXISTS → (integer) N
- DBSIZE → (integer) N
- EXPIRE → (integer) N
- TTL → (integer) N
- CONFIG SET param value → OK
- INFO memory → key:value 형식
"""
import shlex
import sys

from lru_cache import LRUCache


def format_string(value: str | None) -> str:
    """Redis 문자열 형식으로 포맷"""
    if value is None:
        return "(nil)"
    return f'"{value}"'


def format_integer(value: int) -> str:
    """Redis 정수 형식으로 포맷"""
    return f"(integer) {value}"


def parse_command(line: str) -> list[str]:
    """명령어 파싱 (따옴표 처리 포함)"""
    try:
        return shlex.split(line)
    except ValueError:
        return line.split()


def main():
    cache = LRUCache()

    while True:
        try:
            line = input("mini-redis> ")
        except EOFError:
            break

        line = line.strip()
        if not line:
            continue

        tokens = parse_command(line)
        if not tokens:
            continue

        cmd = tokens[0].upper()

        if cmd == "EXIT" or cmd == "QUIT":
            break
        elif cmd == "SET" and len(tokens) >= 3:
            result = cache.set(tokens[1], tokens[2])
            print(result)
        elif cmd == "GET" and len(tokens) >= 2:
            result = cache.get(tokens[1])
            print(format_string(result))
        elif cmd == "DEL" and len(tokens) >= 2:
            result = cache.delete(tokens[1])
            print(format_integer(result))
        elif cmd == "EXISTS" and len(tokens) >= 2:
            result = cache.exists(tokens[1])
            print(format_integer(result))
        elif cmd == "DBSIZE":
            result = cache.dbsize()
            print(format_integer(result))
        elif cmd == "EXPIRE" and len(tokens) >= 3:
            try:
                seconds = int(tokens[2])
                result = cache.expire(tokens[1], seconds)
                print(format_integer(result))
            except ValueError:
                print("(error) ERR value is not an integer")
        elif cmd == "TTL" and len(tokens) >= 2:
            result = cache.ttl(tokens[1])
            print(format_integer(result))
        elif cmd == "CONFIG" and len(tokens) >= 4 and tokens[1].upper() == "SET":
            result = cache.config_set(tokens[2], tokens[3])
            print(result)
        elif cmd == "INFO" and len(tokens) >= 2 and tokens[1].lower() == "memory":
            info = cache.info_memory()
            for k, v in info.items():
                print(f"{k}:{v}")
        else:
            print(f"(error) ERR unknown command '{tokens[0]}'")


if __name__ == "__main__":
    main()
