"""
기본 명령어 검증 플러그인 (25점)

subprocess.run + stdin pipe로 학습자의 cli.py REPL을 실행하여
SET/GET/DEL/EXISTS/DBSIZE 기본 동작과 Redis 출력 형식을 검증.

AI 트랩: Redis 출력 형식 미준수
"""
import os
import subprocess
import sys
from typing import Dict, Any, Optional, List

from core.base_validator import BaseValidator
from core.check_item import CheckItem


class BasicCommandValidator(BaseValidator):
    """기본 명령어 동작 검증 (SET/GET/DEL/EXISTS/DBSIZE + 출력 형식)"""

    def __init__(self, mission_config: Dict[str, Any]):
        super().__init__(mission_config)
        self.submission_dir = ""
        self.cli_path: Optional[str] = None
        self._responses: Optional[List[str]] = None

    def setup(self) -> None:
        self.submission_dir = self.config.get("submission_dir", "")
        cli_file = os.path.join(self.submission_dir, "cli.py")
        if os.path.isfile(cli_file):
            self.cli_path = cli_file

        # 기본 테스트 시나리오 실행
        commands = (
            "SET name Alice\n"
            "GET name\n"
            "SET count 42\n"
            "GET count\n"
            "DEL name\n"
            "GET name\n"
            "EXISTS name\n"
            "EXISTS count\n"
            "DBSIZE\n"
            "exit\n"
        )
        self._responses = self._run_repl(commands)

    def build_checklist(self) -> None:
        self.checklist.add_item(CheckItem(
            id="cli_runnable",
            description="cli.py 실행 + mini-redis> 프롬프트 출력 확인",
            points=3,
            validator=self._check_runnable,
            hint="cli.py에서 'mini-redis> ' 프롬프트를 출력하세요",
        ))

        self.checklist.add_item(CheckItem(
            id="set_get",
            description="SET/GET 기본 동작이 정확한지 확인",
            points=8,
            validator=self._check_set_get,
            hint="SET key value → OK, GET key → \"value\" 형식으로 구현하세요",
        ))

        self.checklist.add_item(CheckItem(
            id="del_command",
            description="DEL 후 GET → (nil) 확인",
            points=4,
            validator=self._check_del,
            hint="DEL key → (integer) 1, 이후 GET key → (nil)",
        ))

        self.checklist.add_item(CheckItem(
            id="exists_dbsize",
            description="EXISTS/DBSIZE 정확한 카운트 확인",
            points=5,
            validator=self._check_exists_dbsize,
            hint="EXISTS → (integer) 0/1, DBSIZE → (integer) N 형식",
        ))

        self.checklist.add_item(CheckItem(
            id="output_format",
            description="Redis 출력 형식 준수 (OK/(nil)/(integer) N/\"value\")",
            points=5,
            validator=self._check_output_format,
            hint="GET 값은 \"value\" (쌍따옴표), 미존재는 (nil), 정수는 (integer) N 형식",
            ai_trap=True,
        ))

    def teardown(self) -> None:
        pass

    # -- REPL 실행 헬퍼 --

    def _run_repl(self, commands: str, timeout: int = 10) -> Optional[List[str]]:
        """cli.py REPL을 실행하고 응답 리스트를 반환"""
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

    # -- 검증 함수 --

    def _check_runnable(self) -> bool:
        """cli.py 실행 가능 + 프롬프트 출력 확인"""
        if not self.cli_path:
            return False
        try:
            result = subprocess.run(
                [sys.executable, self.cli_path],
                input="exit\n",
                capture_output=True,
                text=True,
                timeout=5,
                cwd=self.submission_dir,
            )
            return "mini-redis>" in result.stdout
        except (subprocess.TimeoutExpired, OSError):
            return False

    def _check_set_get(self) -> bool:
        """SET name Alice → OK, GET name → "Alice"
           SET count 42 → OK, GET count → "42"
        """
        if not self._responses or len(self._responses) < 4:
            return False

        # responses[0] = SET name Alice → "OK"
        # responses[1] = GET name → '"Alice"'
        # responses[2] = SET count 42 → "OK"
        # responses[3] = GET count → '"42"'
        return (
            self._responses[0].strip() == "OK"
            and "Alice" in self._responses[1]
            and self._responses[2].strip() == "OK"
            and "42" in self._responses[3]
        )

    def _check_del(self) -> bool:
        """DEL name → (integer) 1, GET name → (nil)"""
        if not self._responses or len(self._responses) < 6:
            return False

        # responses[4] = DEL name → "(integer) 1"
        # responses[5] = GET name → "(nil)"
        del_resp = self._responses[4].strip()
        get_resp = self._responses[5].strip()

        return "(integer) 1" in del_resp and "(nil)" in get_resp

    def _check_exists_dbsize(self) -> bool:
        """EXISTS name → (integer) 0, EXISTS count → (integer) 1, DBSIZE → (integer) 1"""
        if not self._responses or len(self._responses) < 9:
            return False

        # responses[6] = EXISTS name → "(integer) 0"
        # responses[7] = EXISTS count → "(integer) 1"
        # responses[8] = DBSIZE → "(integer) 1"
        exists_name = self._responses[6].strip()
        exists_count = self._responses[7].strip()
        dbsize = self._responses[8].strip()

        return (
            "(integer) 0" in exists_name
            and "(integer) 1" in exists_count
            and "(integer) 1" in dbsize
        )

    def _check_output_format(self) -> bool:
        """Redis 출력 형식 검증:
        - GET 값: "value" (쌍따옴표 포함)
        - GET 미존재: (nil)
        - 정수: (integer) N
        - SET: OK
        """
        if not self._responses or len(self._responses) < 9:
            return False

        # SET → "OK" (True/1이 아님)
        if self._responses[0].strip() != "OK":
            return False

        # GET 값 → 쌍따옴표로 감싸야 함
        get_alice = self._responses[1].strip()
        if not (get_alice.startswith('"') and get_alice.endswith('"')):
            return False

        # GET 미존재 → "(nil)" (None이 아님)
        get_nil = self._responses[5].strip()
        if get_nil != "(nil)":
            return False

        # DEL → "(integer) 1"
        del_resp = self._responses[4].strip()
        if not del_resp.startswith("(integer)"):
            return False

        return True


def _parse_responses(stdout: str) -> List[str]:
    """REPL stdout에서 프롬프트를 제거하고 응답만 추출

    "mini-redis> OK" → "OK"
    "mini-redis> \"Alice\"" → "\"Alice\""
    여러 줄 응답(INFO memory 등)은 하나로 합침
    """
    responses = []
    lines = stdout.split("\n")
    current_response_lines = []

    for line in lines:
        if "mini-redis>" in line:
            # 이전 멀티라인 응답이 있으면 저장
            if current_response_lines:
                responses.append("\n".join(current_response_lines))
                current_response_lines = []

            # 프롬프트 이후 텍스트 추출
            after_prompt = line.split("mini-redis>", 1)[1].strip()
            if after_prompt:
                current_response_lines.append(after_prompt)
        elif line.strip():
            # 프롬프트 없는 줄 (멀티라인 응답의 일부)
            current_response_lines.append(line.strip())

    # 마지막 응답 저장
    if current_response_lines:
        responses.append("\n".join(current_response_lines))

    return responses
