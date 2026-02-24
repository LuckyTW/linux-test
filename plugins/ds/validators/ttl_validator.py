"""
TTL 검증 플러그인 (20점)

subprocess.Popen + time.sleep로 TTL 만료, lazy deletion,
미존재/미설정 키의 TTL 반환값을 검증.

AI 트랩: 만료 키 lazy deletion 미구현
"""
import os
import subprocess
import sys
import time
from typing import Dict, Any, Optional, List

from core.base_validator import BaseValidator
from core.check_item import CheckItem


class TTLValidator(BaseValidator):
    """TTL 동작 검증 (EXPIRE/TTL 기본, lazy deletion, 미존재/미설정 키)"""

    def __init__(self, mission_config: Dict[str, Any]):
        super().__init__(mission_config)
        self.submission_dir = ""
        self.cli_path: Optional[str] = None
        # Phase 1: EXPIRE/TTL 기본 테스트 결과
        self._basic_responses: Optional[List[str]] = None
        # Phase 2: Lazy deletion 테스트 결과
        self._lazy_responses: Optional[List[str]] = None
        # Phase 3: 미존재/미설정 키 테스트 결과
        self._edge_responses: Optional[List[str]] = None

    def setup(self) -> None:
        self.submission_dir = self.config.get("submission_dir", "")
        cli_file = os.path.join(self.submission_dir, "cli.py")
        if os.path.isfile(cli_file):
            self.cli_path = cli_file

        # Phase 1: EXPIRE/TTL 기본
        basic_commands = (
            "SET session abc\n"
            "EXPIRE session 100\n"
            "TTL session\n"
            "exit\n"
        )
        self._basic_responses = self._run_repl(basic_commands)

        # Phase 2: Lazy deletion (Popen + sleep)
        self._lazy_responses = self._run_lazy_deletion_test()

        # Phase 3: 미존재/미설정 키
        edge_commands = (
            "TTL nonexist\n"
            "SET noexpire val\n"
            "TTL noexpire\n"
            "exit\n"
        )
        self._edge_responses = self._run_repl(edge_commands)

    def build_checklist(self) -> None:
        self.checklist.add_item(CheckItem(
            id="expire_ttl_basic",
            description="EXPIRE/TTL 기본 동작 (TTL 설정 + 남은 시간 조회)",
            points=6,
            validator=self._check_expire_ttl_basic,
            hint="EXPIRE key seconds → (integer) 1, TTL key → (integer) 남은초",
        ))

        self.checklist.add_item(CheckItem(
            id="ttl_expired_get",
            description="만료 키 GET → (nil) + DBSIZE 감소 (lazy deletion)",
            points=8,
            validator=self._check_ttl_expired_get,
            hint="GET 시 TTL 만료 확인 → 키 삭제 + (nil) 반환",
            ai_trap=True,
        ))

        self.checklist.add_item(CheckItem(
            id="ttl_nonexistent",
            description="미존재 키 TTL → (integer) -2, TTL 미설정 키 → (integer) -1",
            points=6,
            validator=self._check_ttl_nonexistent,
            hint="TTL: 키 없으면 -2, 키 있지만 TTL 미설정이면 -1",
        ))

    def teardown(self) -> None:
        pass

    # -- REPL 실행 헬퍼 --

    def _run_repl(self, commands: str, timeout: int = 10) -> Optional[List[str]]:
        """cli.py REPL을 subprocess.run으로 실행"""
        if not self.cli_path:
            return None
        try:
            result = subprocess.run(
                [sys.executable, self.cli_path],
                input=commands,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self.submission_dir,
            )
            return _parse_responses(result.stdout)
        except (subprocess.TimeoutExpired, OSError):
            return None

    def _run_lazy_deletion_test(self) -> Optional[List[str]]:
        """Popen으로 REPL 실행 → EXPIRE 1초 설정 → sleep(2) → GET 확인"""
        if not self.cli_path:
            return None

        try:
            proc = subprocess.Popen(
                [sys.executable, "-u", self.cli_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=self.submission_dir,
            )

            # Phase 1: SET + EXPIRE 1초
            proc.stdin.write("SET temp val\n")
            proc.stdin.write("EXPIRE temp 1\n")
            proc.stdin.write("DBSIZE\n")
            proc.stdin.flush()

            # 2초 대기 (TTL 만료)
            time.sleep(2)

            # Phase 2: 만료 확인
            proc.stdin.write("GET temp\n")
            proc.stdin.write("DBSIZE\n")
            proc.stdin.write("exit\n")
            proc.stdin.flush()

            stdout, _ = proc.communicate(timeout=5)
            return _parse_responses(stdout)

        except (subprocess.TimeoutExpired, OSError, BrokenPipeError):
            try:
                proc.kill()
                proc.wait(timeout=2)
            except Exception:
                pass
            return None

    # -- 검증 함수 --

    def _check_expire_ttl_basic(self) -> bool:
        """SET session abc → EXPIRE session 100 → TTL session ≈ 98~100"""
        if not self._basic_responses or len(self._basic_responses) < 3:
            return False

        # responses[0] = SET session abc → "OK"
        # responses[1] = EXPIRE session 100 → "(integer) 1"
        # responses[2] = TTL session → "(integer) 98~100"

        expire_resp = self._basic_responses[1].strip()
        if "(integer) 1" not in expire_resp:
            return False

        ttl_resp = self._basic_responses[2].strip()
        # "(integer) N" 에서 N 추출
        ttl_val = _extract_integer(ttl_resp)
        if ttl_val is None:
            return False

        # 98~100 범위 (실행 시간 오차 감안)
        return 90 <= ttl_val <= 100

    def _check_ttl_expired_get(self) -> bool:
        """만료 후 GET temp → (nil), DBSIZE → (integer) 0"""
        if not self._lazy_responses or len(self._lazy_responses) < 5:
            return False

        # responses[0] = SET temp val → "OK"
        # responses[1] = EXPIRE temp 1 → "(integer) 1"
        # responses[2] = DBSIZE → "(integer) 1" (만료 전)
        # --- sleep(2) ---
        # responses[3] = GET temp → "(nil)" (만료!)
        # responses[4] = DBSIZE → "(integer) 0" (lazy deletion)

        get_resp = self._lazy_responses[3].strip()
        dbsize_resp = self._lazy_responses[4].strip()

        get_nil = "(nil)" in get_resp
        dbsize_zero = "(integer) 0" in dbsize_resp

        return get_nil and dbsize_zero

    def _check_ttl_nonexistent(self) -> bool:
        """TTL nonexist → (integer) -2, TTL noexpire → (integer) -1"""
        if not self._edge_responses or len(self._edge_responses) < 3:
            return False

        # responses[0] = TTL nonexist → "(integer) -2"
        # responses[1] = SET noexpire val → "OK"
        # responses[2] = TTL noexpire → "(integer) -1"

        ttl_nonexist = self._edge_responses[0].strip()
        ttl_noexpire = self._edge_responses[2].strip()

        return "(integer) -2" in ttl_nonexist and "(integer) -1" in ttl_noexpire


def _parse_responses(stdout: str) -> List[str]:
    """REPL stdout에서 프롬프트를 제거하고 응답만 추출"""
    responses = []
    lines = stdout.split("\n")
    current_response_lines = []

    for line in lines:
        if "mini-redis>" in line:
            if current_response_lines:
                responses.append("\n".join(current_response_lines))
                current_response_lines = []

            after_prompt = line.split("mini-redis>", 1)[1].strip()
            if after_prompt:
                current_response_lines.append(after_prompt)
        elif line.strip():
            current_response_lines.append(line.strip())

    if current_response_lines:
        responses.append("\n".join(current_response_lines))

    return responses


def _extract_integer(response: str) -> Optional[int]:
    """'(integer) N' 형식에서 N 추출"""
    response = response.strip()
    if response.startswith("(integer)"):
        try:
            return int(response.split("(integer)")[1].strip())
        except (ValueError, IndexError):
            return None
    return None
