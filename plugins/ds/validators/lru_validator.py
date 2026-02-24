"""
LRU 동작 검증 플러그인 (30점)

subprocess.run + stdin pipe로 LRU 제거, GET 접근 시 LRU 갱신,
INFO memory 통계를 검증.

AI 트랩: GET 시 LRU 순서 미갱신
"""
import os
import subprocess
import sys
from typing import Dict, Any, Optional, List

from core.base_validator import BaseValidator
from core.check_item import CheckItem


class LRUValidator(BaseValidator):
    """LRU 동작 검증 (maxmemory, 제거, GET 갱신, INFO memory)"""

    def __init__(self, mission_config: Dict[str, Any]):
        super().__init__(mission_config)
        self.submission_dir = ""
        self.cli_path: Optional[str] = None
        self._lru_responses: Optional[List[str]] = None

    def setup(self) -> None:
        self.submission_dir = self.config.get("submission_dir", "")
        cli_file = os.path.join(self.submission_dir, "cli.py")
        if os.path.isfile(cli_file):
            self.cli_path = cli_file

        # LRU GET 갱신 핵심 테스트 시나리오
        commands = (
            "CONFIG SET maxmemory 3\n"
            "SET k1 v1\n"
            "SET k2 v2\n"
            "SET k3 v3\n"
            "GET k1\n"
            "SET k4 v4\n"
            "GET k2\n"
            "GET k1\n"
            "GET k4\n"
            "INFO memory\n"
            "DBSIZE\n"
            "exit\n"
        )
        self._lru_responses = self._run_repl(commands)

    def build_checklist(self) -> None:
        self.checklist.add_item(CheckItem(
            id="config_maxmemory",
            description="CONFIG SET maxmemory 설정이 동작하는지 확인",
            points=5,
            validator=self._check_config_maxmemory,
            hint="CONFIG SET maxmemory N → OK 반환하고, 최대 N개의 키만 유지",
        ))

        self.checklist.add_item(CheckItem(
            id="lru_eviction",
            description="메모리 초과 시 LRU 키가 제거되는지 확인",
            points=8,
            validator=self._check_lru_eviction,
            hint="maxmemory 초과 시 가장 오래 접근하지 않은 키부터 제거",
        ))

        self.checklist.add_item(CheckItem(
            id="lru_get_refresh",
            description="GET 접근 시 LRU 순서가 갱신되는지 확인",
            points=10,
            validator=self._check_lru_get_refresh,
            hint="GET도 접근으로 간주하여 LRU 순서를 갱신해야 합니다 (move_to_front)",
            ai_trap=True,
        ))

        self.checklist.add_item(CheckItem(
            id="info_memory",
            description="INFO memory 통계 (used_memory/maxmemory/evicted_keys) 정확성 확인",
            points=7,
            validator=self._check_info_memory,
            hint="INFO memory 출력에 used_memory:N, maxmemory:N, evicted_keys:N 포함",
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

    def _check_config_maxmemory(self) -> bool:
        """CONFIG SET maxmemory 3 → OK"""
        if not self._lru_responses or len(self._lru_responses) < 1:
            return False
        return self._lru_responses[0].strip() == "OK"

    def _check_lru_eviction(self) -> bool:
        """maxmemory=3, SET 4개 후 가장 오래된 키가 제거되었는지 확인

        시나리오: k1,k2,k3 SET → GET k1(갱신) → SET k4(초과 → 제거)
        k2가 제거되어야 함 (GET k1으로 k1이 갱신되었으므로)
        DBSIZE가 3이어야 함
        """
        if not self._lru_responses or len(self._lru_responses) < 11:
            return False

        # responses[10] = DBSIZE → "(integer) 3"
        dbsize_resp = self._lru_responses[10].strip()
        return "(integer) 3" in dbsize_resp

    def _check_lru_get_refresh(self) -> bool:
        """GET k1 후 SET k4 → k2가 제거되어야 함 (k1이 아님)

        핵심 트랩: GET k1으로 k1의 LRU 순서가 갱신됨
        → SET k4 시 k2가 제거됨 (가장 오래 접근 안 한 키)
        → GET k2 = (nil), GET k1 = "v1"
        """
        if not self._lru_responses or len(self._lru_responses) < 9:
            return False

        # responses[4] = GET k1 → '"v1"' (LRU 갱신!)
        # responses[5] = SET k4 → "OK" (초과 → k2 제거)
        # responses[6] = GET k2 → "(nil)" (제거됨)
        # responses[7] = GET k1 → '"v1"' (생존!)
        # responses[8] = GET k4 → '"v4"'

        get_k2 = self._lru_responses[6].strip()
        get_k1 = self._lru_responses[7].strip()

        k2_removed = "(nil)" in get_k2
        k1_alive = "v1" in get_k1

        return k2_removed and k1_alive

    def _check_info_memory(self) -> bool:
        """INFO memory → used_memory:3, maxmemory:3, evicted_keys:1"""
        if not self._lru_responses or len(self._lru_responses) < 10:
            return False

        info_resp = self._lru_responses[9]

        has_used = "used_memory:3" in info_resp
        has_max = "maxmemory:3" in info_resp
        has_evicted = "evicted_keys:1" in info_resp

        return has_used and has_max and has_evicted


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
