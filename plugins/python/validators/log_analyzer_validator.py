"""
서버 접근 로그 분석기 검증 플러그인 (100점)

학습자가 CSV 로그를 파싱하여 IP별 접근 횟수, 상태코드 비율,
느린 엔드포인트를 분석하는 report.txt를 생성하는지 검증.

AI 트랩: 빈 IP 행, 1xx 상태코드, 소수점 response_time, 동점 내림차순 정렬
"""
import os
import re
import subprocess
import sys
import tempfile
from typing import Dict, Any, Optional, List, Tuple

from core.base_validator import BaseValidator
from core.check_item import CheckItem

# 함정 포함 CSV 데이터 (24행)
# 함정 1: 빈 IP 행 (행 2)
# 함정 2: 1xx 상태코드 (행 3)
# 함정 3: 소수점 응답시간 (행 14)
# 함정 4: 동점 IP/엔드포인트 내림차순 정렬
TRAP_CSV_HEADER = "timestamp,ip,method,endpoint,status_code,response_time_ms"
TRAP_CSV_ROWS = [
    ("2025-03-15T09:00:00", "192.168.1.1", "GET", "/api/users", "200", "45"),
    ("2025-03-15T09:01:30", "", "GET", "/api/health", "200", "10"),
    ("2025-03-15T09:01:35", "10.0.0.5", "GET", "/api/health", "100", "2"),
    ("2025-03-15T09:02:00", "192.168.1.1", "POST", "/api/users", "201", "38"),
    ("2025-03-15T09:02:10", "10.0.0.5", "GET", "/api/products", "200", "52"),
    ("2025-03-15T09:02:20", "172.16.0.10", "GET", "/api/users", "200", "41"),
    ("2025-03-15T09:02:30", "172.16.0.10", "GET", "/api/products", "200", "33.7"),
    ("2025-03-15T09:03:00", "192.168.1.1", "DELETE", "/api/users", "403", "12"),
    ("2025-03-15T09:03:30", "192.168.2.20", "GET", "/api/orders", "500", "5120"),
    ("2025-03-15T09:04:00", "10.0.0.5", "PUT", "/api/products", "200", "67"),
    ("2025-03-15T09:04:30", "192.168.1.1", "GET", "/api/health", "200", "3"),
    ("2025-03-15T09:05:00", "172.16.0.10", "GET", "/api/orders", "301", "25"),
    ("2025-03-15T09:05:30", "10.0.0.99", "GET", "/api/users", "404", "8"),
    ("2025-03-15T09:06:00", "192.168.1.1", "GET", "/api/products", "200", "55"),
    ("2025-03-15T09:06:30", "10.0.0.5", "POST", "/api/orders", "201", "310"),
    ("2025-03-15T09:07:00", "172.16.0.10", "GET", "/api/health", "200", "4"),
    ("2025-03-15T09:07:30", "192.168.2.20", "GET", "/api/products", "500", "3200"),
    ("2025-03-15T09:08:00", "10.0.0.5", "GET", "/api/users", "200", "29"),
    ("2025-03-15T09:08:30", "192.168.1.1", "GET", "/api/orders", "500", "4500"),
    ("2025-03-15T09:09:00", "10.0.0.99", "POST", "/api/users", "201", "42"),
    ("2025-03-15T09:09:30", "172.16.0.10", "GET", "/api/products", "200", "61"),
    ("2025-03-15T09:10:00", "10.0.0.5", "GET", "/api/health", "200", "5"),
    ("2025-03-15T09:10:30", "192.168.2.20", "GET", "/api/users", "200", "37"),
    ("2025-03-15T09:11:00", "10.0.0.99", "GET", "/api/products", "200", "48"),
]

# 기대 정답값 (수동 검증 완료)
# IP TOP 5 (내림차순, 동점 시 IP도 내림차순)
EXPECTED_TOP_IPS = [
    ("192.168.1.1", 6),
    ("10.0.0.5", 6),
    ("172.16.0.10", 5),
    ("192.168.2.20", 3),
    ("10.0.0.99", 3),
]

# 상태코드 비율 (총 24행 기준, 빈 IP 행도 포함)
EXPECTED_STATUS = {
    "2xx": 70.8,
    "3xx": 4.2,
    "4xx": 8.3,
    "5xx": 12.5,
}

# 느린 엔드포인트 TOP 3 (평균 응답시간 내림차순)
EXPECTED_SLOW_ENDPOINTS = [
    ("/api/orders", 2488.8),
    ("/api/products", 502.4),
    ("/api/users", 31.5),
]


class LogAnalyzerValidator(BaseValidator):
    """서버 접근 로그 분석기 검증 (CSV 파싱, IP 집계, 상태코드, 엔드포인트)"""

    def __init__(self, mission_config: Dict[str, Any]):
        super().__init__(mission_config)
        self.submission_dir = ""
        self.report_content: Optional[str] = None
        self._tmpdir: Optional[tempfile.TemporaryDirectory] = None

    def setup(self) -> None:
        self.submission_dir = self.config.get("submission_dir", "")

        # 학생 제출 파일 확인
        script_path = os.path.join(self.submission_dir, "log_analyzer.py")
        if not os.path.isfile(script_path):
            return

        # 임시 디렉토리에 함정 CSV 생성 및 학생 코드 실행
        self._tmpdir = tempfile.TemporaryDirectory()
        tmp_path = self._tmpdir.name

        csv_path = os.path.join(tmp_path, "access_log.csv")
        report_path = os.path.join(tmp_path, "report.txt")

        # 함정 포함 CSV 쓰기
        self._write_trap_csv(csv_path)

        # subprocess로 학생 코드 실행
        try:
            subprocess.run(
                [sys.executable, script_path,
                 "--log", csv_path,
                 "--output", report_path],
                capture_output=True,
                text=True,
                timeout=10,
                cwd=self.submission_dir,
            )
        except (subprocess.TimeoutExpired, OSError):
            pass

        # report.txt 읽기
        if os.path.isfile(report_path):
            try:
                with open(report_path, "r", encoding="utf-8") as f:
                    self.report_content = f.read()
            except (OSError, UnicodeDecodeError):
                pass

    def build_checklist(self) -> None:
        self.checklist.add_item(CheckItem(
            id="csv_parse",
            description="CSV 정상 파싱 + report.txt 생성 확인",
            points=10,
            validator=self._check_csv_parse,
            hint="argparse로 --log, --output 인자를 받아 CSV를 파싱하고 report.txt를 생성하세요",
        ))

        self.checklist.add_item(CheckItem(
            id="top_ips",
            description="IP별 접근 횟수 TOP 5가 정확한지 확인",
            points=15,
            validator=self._check_top_ips,
            hint="빈 IP 행은 제외하고 IP별 접근 횟수를 집계하세요",
            ai_trap=True,
        ))

        self.checklist.add_item(CheckItem(
            id="ip_order",
            description="동점 IP 정렬 순서 (접근 횟수 내림차순, 동점 시 IP 내림차순)",
            points=15,
            validator=self._check_ip_order,
            hint="접근 횟수가 같으면 IP 주소도 내림차순으로 정렬하세요",
            ai_trap=True,
        ))

        self.checklist.add_item(CheckItem(
            id="status_ratio",
            description="HTTP 상태코드 그룹별 비율이 정확한지 확인",
            points=20,
            validator=self._check_status_ratio,
            hint="1xx 상태코드도 올바르게 분류하고, 전체 행 수 기준으로 비율을 계산하세요",
            ai_trap=True,
        ))

        self.checklist.add_item(CheckItem(
            id="slow_order",
            description="느린 엔드포인트 TOP 3 순서가 정확한지 확인",
            points=15,
            validator=self._check_slow_order,
            hint="엔드포인트별 평균 응답시간을 계산하여 내림차순으로 정렬하세요",
        ))

        self.checklist.add_item(CheckItem(
            id="report_sections",
            description="리포트에 3개 섹션 (IP 분석, 상태코드, 엔드포인트)이 모두 포함되어 있는지 확인",
            points=15,
            validator=self._check_report_sections,
            hint="리포트에 IP 접근 횟수, 상태코드 비율, 느린 엔드포인트 섹션을 모두 포함하세요",
        ))

        self.checklist.add_item(CheckItem(
            id="slow_values",
            description="엔드포인트 평균 응답시간 수치가 정확한지 확인",
            points=10,
            validator=self._check_slow_values,
            hint="소수점 response_time(예: 33.7)도 정확히 처리하여 평균을 계산하세요",
            ai_trap=True,
        ))

    def teardown(self) -> None:
        if self._tmpdir:
            self._tmpdir.cleanup()

    # -- 헬퍼 --

    @staticmethod
    def _write_trap_csv(csv_path: str) -> None:
        """함정 포함 CSV 파일 쓰기"""
        with open(csv_path, "w", encoding="utf-8") as f:
            f.write(TRAP_CSV_HEADER + "\n")
            for row in TRAP_CSV_ROWS:
                f.write(",".join(row) + "\n")

    @staticmethod
    def _extract_numbers(text: str) -> List[float]:
        """텍스트에서 숫자(정수/소수) 추출"""
        return [float(x) for x in re.findall(r"\d+\.?\d*", text)]

    # -- 검증 함수 --

    def _check_csv_parse(self) -> bool:
        """report.txt가 생성되었고 내용이 있는지 확인"""
        return self.report_content is not None and len(self.report_content.strip()) > 0

    def _check_top_ips(self) -> bool:
        """IP별 접근 횟수 TOP 5 값 확인 (순서 무관, 값만 확인)"""
        if not self.report_content:
            return False

        report = self.report_content
        # 상위 5개 IP와 횟수가 모두 리포트에 존재하는지 확인
        for ip, count in EXPECTED_TOP_IPS:
            if ip not in report:
                return False
            if str(count) not in report:
                return False
        return True

    def _check_ip_order(self) -> bool:
        """IP TOP 5 순서 확인 (접근 횟수 내림차순, 동점 시 IP 내림차순)"""
        if not self.report_content:
            return False

        report = self.report_content
        # 동점 쌍의 순서 확인: 192.168.1.1(6) > 10.0.0.5(6), 192.168.2.20(3) > 10.0.0.99(3)
        pos_192_1 = report.find("192.168.1.1")
        pos_10_5 = report.find("10.0.0.5")
        pos_192_20 = report.find("192.168.2.20")
        pos_10_99 = report.find("10.0.0.99")

        if any(p == -1 for p in [pos_192_1, pos_10_5, pos_192_20, pos_10_99]):
            return False

        # 192.168.1.1이 10.0.0.5보다 먼저, 192.168.2.20이 10.0.0.99보다 먼저
        return pos_192_1 < pos_10_5 and pos_192_20 < pos_10_99

    def _check_status_ratio(self) -> bool:
        """HTTP 상태코드 그룹별 비율 확인"""
        if not self.report_content:
            return False

        report = self.report_content

        # 각 비율이 리포트에 포함되어 있는지 확인 (소수점 1자리)
        for group, ratio in EXPECTED_STATUS.items():
            ratio_str = f"{ratio:.1f}"
            if ratio_str not in report:
                return False
        return True

    def _check_slow_order(self) -> bool:
        """느린 엔드포인트 TOP 3 순서 확인"""
        if not self.report_content:
            return False

        report = self.report_content
        positions = []
        for endpoint, _ in EXPECTED_SLOW_ENDPOINTS:
            pos = report.find(endpoint)
            if pos == -1:
                return False
            positions.append(pos)

        # 순서 확인: /api/orders > /api/products > /api/users
        return positions[0] < positions[1] < positions[2]

    def _check_report_sections(self) -> bool:
        """리포트 3개 섹션 존재 확인"""
        if not self.report_content:
            return False

        report = self.report_content.lower()

        # 각 섹션 관련 키워드 확인
        has_ip_section = "ip" in report and ("top" in report or "접근" in report)
        has_status_section = ("status" in report or "상태" in report) and "%" in report
        has_endpoint_section = ("endpoint" in report or "엔드포인트" in report) and "ms" in report.lower()

        return has_ip_section and has_status_section and has_endpoint_section

    def _check_slow_values(self) -> bool:
        """엔드포인트 평균 응답시간 수치 정확성 확인 (강화: 3개 수치 모두 확인)"""
        if not self.report_content:
            return False

        report = self.report_content
        # 3개 핵심 수치가 모두 존재하는지 확인
        expected_values = ["2488.8", "502.4", "31.5"]
        for value in expected_values:
            if value not in report:
                return False
        return True
