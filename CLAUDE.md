# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 프로젝트 개요

PBL(Problem-Based Learning) 교육 후 학습자의 학습 성취도를 자동 채점하는 **플러그인 기반 검증 프레임워크**.
리눅스 시스템 관리, Python 코딩 시험을 지원하며, 알고리즘/자료구조/데이터베이스 등으로 확장 가능한 구조.

- **외부 의존성**: PyYAML 1개만 사용, 나머지는 Python 표준 라이브러리
- **합격 기준**: 70점 이상 Pass
- **결과 형식**: JSON + Markdown 리포트 자동 생성

---

## 실행 명령어

```bash
# 의존성 설치
pip3 install -r requirements.txt

# 리눅스 미션 채점 (실제 리눅스 환경 필요)
python3 scripts/run_grading.py --student-id <학생ID> --mission-id linux_level1_mission01 --output-dir results

# 리눅스 보안 감사 미션 채점 (macOS/Linux 가능, --submission-dir 필수)
python3 scripts/run_grading.py --student-id <학생ID> --mission-id linux_level2_mission01 --submission-dir /path/to/submission

# Python 미션 채점 (--submission-dir 필수)
python3 scripts/run_grading.py --student-id <학생ID> --mission-id python_level1_mission01 --submission-dir /path/to/submission
python3 scripts/run_grading.py --student-id <학생ID> --mission-id python_level1_mission02 --submission-dir /path/to/submission

# 자료구조 미션 채점 (--submission-dir 필수)
python3 scripts/run_grading.py --student-id <학생ID> --mission-id ds_level1_mission01 --submission-dir /path/to/submission

# 샘플 정답 코드로 Python mission01 채점 (테스트용)
python3 scripts/run_grading.py --student-id sample --mission-id python_level1_mission01 --submission-dir sample_submission

# 샘플 정답 코드로 DS mission01 채점 (테스트용)
python3 scripts/run_grading.py --student-id sample --mission-id ds_level1_mission01 --submission-dir sample_submission_ds
```

테스트 디렉토리(`tests/`)는 존재하나 아직 구현된 테스트 없음.

---

## 디렉토리 구조

```
linux-test/
├── CLAUDE.md                           # 프로젝트 지침서
├── README.md
├── requirements.txt                    # PyYAML>=6.0
│
├── core/                               # 채점 엔진 핵심 모듈
│   ├── base_validator.py               #   BaseValidator(ABC) - 추상 기반 클래스
│   ├── check_item.py                   #   CheckItem(dataclass) + CheckStatus(Enum)
│   ├── checklist.py                    #   Checklist - CheckItem 컬렉션
│   ├── grader.py                       #   Grader - 메인 채점 엔진 (동적 Validator 로딩)
│   └── validation_result.py            #   ValidationResult - 결과 집계/리포트 생성
│
├── scripts/
│   └── run_grading.py                  # CLI 진입점 (argparse)
│
├── utils/
│   └── config_loader.py                # YAML 설정 로더
│
├── plugins/                            # Validator 플러그인 (미션 유형별)
│   ├── linux/validators/               #   리눅스 미션용 (5개)
│   │   ├── ssh_validator.py
│   │   ├── firewall_validator.py
│   │   ├── account_validator.py
│   │   ├── script_validator.py
│   │   └── linux_auditor_validator.py  #   보안 감사 도구 (subprocess+tmpdir 기반)
│   ├── python/validators/              #   Python 미션용 (5개 + 헬퍼)
│   │   ├── _helpers.py                 #     공통 유틸 (import_student_module 등)
│   │   ├── model_validator.py
│   │   ├── pattern_validator.py
│   │   ├── cli_validator.py
│   │   ├── persistence_validator.py
│   │   └── log_analyzer_validator.py
│   └── ds/validators/                  #   자료구조 미션용 (4개)
│       ├── structure_validator.py      #     AST 분석형 (Node 클래스, 금지 import)
│       ├── basic_command_validator.py  #     subprocess형 (SET/GET/DEL/EXISTS/DBSIZE)
│       ├── lru_validator.py            #     subprocess형 (LRU 제거, GET 갱신, INFO)
│       └── ttl_validator.py            #     Popen형 (EXPIRE/TTL, lazy deletion)
│
├── missions/                           # 미션 정의 (config.yaml + problem.md + solution.md)
│   ├── linux/
│   │   ├── level1/mission01/           #   리눅스 시스템 보안 및 관제 기초 설정
│   │   └── level2/mission01/           #   리눅스 서버 보안 감사 도구 (Python 제출)
│   ├── python/
│   │   ├── level1/mission01/           #   Python 도서 관리 시스템 코딩 시험
│   │   │   └── template/              #     cli.py, filters.py, models.py, storage.py
│   │   └── level1/mission02/           #   서버 접근 로그 분석기
│   │       └── template/
│   │           └── access_log_sample.csv
│   └── ds/
│       └── level1/mission01/           #   Mini LRU 캐시 구현 시험
│           └── template/              #     lru_cache.py, cli.py
│
├── sample_submission/                  # python_level1_mission01 정답 예시 코드
│   ├── models.py                       #   @dataclass Book
│   ├── filters.py                      #   yield 제너레이터 + validate_args 데코레이터
│   ├── storage.py                      #   JSONL 직렬화/역직렬화
│   └── cli.py                          #   argparse CLI (add/list/search)
│
├── sample_submission_ds/               # ds_level1_mission01 정답 예시 코드
│   ├── lru_cache.py                    #   Node + DoublyLinkedList + LRUCache
│   └── cli.py                          #   Redis 스타일 REPL CLI
│
├── results/                            # 채점 결과 출력 디렉토리
├── submissions/                        # 학생 제출물 보관 (빈 디렉토리)
└── tests/                              # 테스트 (구조만 존재, 미구현)
    ├── test_core/
    └── test_plugins/
```

---

## 아키텍처

### 핵심 채점 흐름

```
CLI (run_grading.py)
 └→ Grader.execute()
     ├→ config.yaml 로드 (utils/config_loader.py)
     ├→ importlib로 Validator 동적 로딩
     └→ 각 Validator.validate() 실행
         ├→ setup()          — 환경 준비 (tmpdir 생성 등)
         ├→ build_checklist() — CheckItem 목록 구성
         ├→ checklist.execute_all() — 각 항목 pass/fail 판정
         └→ teardown()       — 정리 (finally 보장)
              └→ ValidationResult → JSON/Markdown 리포트
```

### core/ 모듈 상세

| 파일 | 클래스 | 핵심 메서드 |
|------|--------|------------|
| `base_validator.py` | `BaseValidator(ABC)` | `setup()`, `build_checklist()`, `teardown()`, `validate()` |
| `check_item.py` | `CheckItem(dataclass)` | `execute()` — `validator: Callable[[], bool]` 호출로 pass/fail |
| `check_item.py` | `CheckStatus(Enum)` | `PASS`, `FAIL`, `ERROR`, `SKIP` |
| `checklist.py` | `Checklist` | `add_item()`, `execute_all()`, `get_total_points()` |
| `grader.py` | `Grader` | `load_validators()` (importlib), `execute()` |
| `validation_result.py` | `ValidationResult` | `add_result()`, `finalize()`, `to_json()`, `to_markdown()` |

### plugins/ 헬퍼

`plugins/python/validators/_helpers.py`:
- `import_student_module(path, name)` — 학생 모듈 동적 임포트
- `collect_py_files(dir)` — .py 파일 수집
- `parse_all_files(dir)` — AST 파싱

---

## 미션 목록

### linux_level1_mission01 — 리눅스 시스템 보안 및 관제 기초 설정

- **제한시간**: 900초 (15분) | **합격**: 70점
- **실행 환경**: 실제 리눅스 환경 필수 (macOS 불가)

| Validator | 가중치 | CheckItem (총 12개) | 배점 |
|-----------|--------|---------------------|------|
| `SSHValidator` | 30 | ssh_port_20022 | 15점 |
| | | ssh_root_login_no | 15점 (**AI 트랩**) |
| `FirewallValidator` | 20 | ufw_enabled | 5점 |
| | | ufw_port_20022 | 5점 |
| | | ufw_port_80 | 5점 |
| | | ufw_port_443 | 5점 |
| `AccountValidator` | 20 | user_agent_admin_exists | 7점 |
| | | user_agent_dev_exists | 7점 |
| | | user_admin_in_common_group | 3점 |
| | | user_dev_in_common_group | 3점 |
| `ScriptValidator` | 30 | script_exists | 15점 |
| | | script_executable | 15점 (**AI 트랩**) |

**AI 트랩 포인트**:
- `ssh_root_login_no`: AI가 `PermitRootLogin prohibit-password`로 설정 → 정답은 `no`
- `script_executable`: AI가 `chmod 644`로 설정 → 정답은 `chmod 755`

---

### python_level1_mission01 — Python 도서 관리 시스템 코딩 시험

- **제한시간**: 900초 (15분) | **합격**: 70점
- **실행 환경**: macOS/Linux 모두 가능 (subprocess + tmpdir 기반)
- **정답 예시**: `sample_submission/` 디렉토리

| Validator | 가중치 | CheckItem (총 17개) | 배점 |
|-----------|--------|---------------------|------|
| `ModelValidator` | 25 | model_dataclass | 7점 |
| | | model_fields | 6점 |
| | | model_type_hints | 5점 |
| | | model_post_init | 7점 |
| `PatternValidator` | 25 | pattern_yield | 8점 (**AI 트랩**) |
| | | pattern_decorator | 7점 |
| | | pattern_type_hints | 5점 |
| | | pattern_no_any | 5점 (**AI 트랩**) |
| `CLIValidator` | 30 | cli_runnable | 5점 |
| | | cli_help | 5점 (**AI 트랩**) |
| | | cli_add | 8점 |
| | | cli_list | 7점 |
| | | cli_no_crash | 5점 |
| `PersistenceValidator` | 20 | persist_roundtrip | 7점 |
| | | persist_format | 3점 |
| | | persist_no_pickle | 5점 (**AI 트랩**) |
| | | persist_integrity | 5점 |

**AI 트랩 포인트**:
- `pattern_yield`: yield 없이 리스트 반환하는 실수
- `pattern_no_any`: `Any` 타입 30% 이상 남용
- `cli_help`: `--help` 옵션 미구현
- `persist_no_pickle`: pickle 사용 (보안 취약)

**Validator 패턴 분류**:
- AST 분석형: `ModelValidator`, `PatternValidator` — `ast` 모듈로 소스코드 구문 분석 + 런타임 검증
- subprocess 실행형: `CLIValidator` — `subprocess.run()`으로 학생 코드 실행 후 출력 검증
- 파일 I/O형: `PersistenceValidator` — `tempfile.TemporaryDirectory()`로 임시 환경 구성

---

### python_level1_mission02 — 서버 접근 로그 분석기

- **제한시간**: 900초 (15분) | **합격**: 70점
- **실행 환경**: macOS/Linux 모두 가능 (subprocess + tmpdir 기반)
- **샘플 데이터**: `missions/python/level1/mission02/template/access_log_sample.csv`

| Validator | 가중치 | CheckItem (총 7개) | 배점 |
|-----------|--------|---------------------|------|
| `LogAnalyzerValidator` | 100 | csv_parse | 10점 |
| | | top_ips | 15점 (**AI 트랩**) |
| | | ip_order | 15점 (**AI 트랩**) |
| | | status_ratio | 20점 (**AI 트랩**) |
| | | slow_order | 15점 |
| | | report_sections | 15점 |
| | | slow_values | 10점 (**AI 트랩**) |

**AI 트랩 포인트**:
- `top_ips`: 빈 IP 행("")을 IP로 집계하는 실수
- `ip_order`: 동점 IP를 오름차순 정렬 → 정답은 내림차순
- `status_ratio`: 1xx 상태코드를 무시하여 비율 오류 (전체 24행 기준)
- `slow_values`: response_time 소수점(33.7)을 정수 처리하여 평균 오차 발생

**Validator 패턴**: subprocess 실행형 + 파일 I/O형 (tmpdir에 CSV 복사 → 학생 코드 실행 → 리포트 파일 검증)

---

### linux_level2_mission01 — 리눅스 서버 보안 감사 도구

- **제한시간**: 1500초 (25분) | **합격**: 70점
- **실행 환경**: macOS/Linux 모두 가능 (subprocess + tmpdir 기반)
- **제출물**: `auditor.py` 1개 파일

| Validator | 가중치 | CheckItem (총 7개) | 배점 |
|-----------|--------|---------------------|------|
| `LinuxAuditorValidator` | 100 | config_parse | 10점 |
| | | ssh_audit | 15점 (**AI 트랩**) |
| | | firewall_audit | 15점 (**AI 트랩**) |
| | | account_audit | 15점 (**AI 트랩**) |
| | | permission_audit | 15점 (**AI 트랩**) |
| | | log_stats | 15점 |
| | | report_sections | 15점 |

**AI 트랩 포인트**:
- `ssh_audit`: PermitRootLogin `prohibit-password`를 "안전"으로 오판 → 정답은 `no`만 안전
- `firewall_audit`: 23/tcp(Telnet) 위험 포트 미탐지
- `account_audit`: agent-test의 agent-core 그룹 포함 RBAC 위반 미탐지
- `permission_audit`: api_keys 디렉토리 775+agent-common 권한 위반 미탐지

**Validator 패턴**: subprocess 실행형 + 파일 I/O형 (tmpdir에 설정 파일 6개 생성 → 학생 코드 실행 → 리포트 파일 검증)

---

### ds_level1_mission01 — Mini LRU 캐시 구현 시험

- **제한시간**: 900초 (15분) | **합격**: 70점
- **실행 환경**: macOS/Linux 모두 가능 (subprocess + Popen 기반)
- **제출물**: `lru_cache.py`, `cli.py` (2개 파일)

| Validator | 가중치 | CheckItem (총 15개) | 배점 |
|-----------|--------|---------------------|------|
| `StructureValidator` | 25 | node_class | 10점 |
| | | no_builtin_cache | 10점 (**AI 트랩**) |
| | | linked_list_ops | 5점 |
| `BasicCommandValidator` | 25 | cli_runnable | 3점 |
| | | set_get | 8점 |
| | | del_command | 4점 |
| | | exists_dbsize | 5점 |
| | | output_format | 5점 (**AI 트랩**) |
| `LRUValidator` | 30 | config_maxmemory | 5점 |
| | | lru_eviction | 8점 |
| | | lru_get_refresh | 10점 (**AI 트랩**) |
| | | info_memory | 7점 |
| `TTLValidator` | 20 | expire_ttl_basic | 6점 |
| | | ttl_expired_get | 8점 (**AI 트랩**) |
| | | ttl_nonexistent | 6점 |

**AI 트랩 포인트**:
- `no_builtin_cache`: OrderedDict/deque/functools.lru_cache 사용 → Node 직접 구현 필요
- `output_format`: Python `True`/`None` 출력 → Redis 형식 `OK`/`(nil)`/`"value"` 필요
- `lru_get_refresh`: SET만 LRU 갱신, GET은 조회만 → GET도 move_to_front 필수
- `ttl_expired_get`: 별도 타이머/스레드 TTL → GET 시 lazy deletion 필요

**Validator 패턴 분류**:
- AST 분석형: `StructureValidator` — Node 클래스, 금지 import, 연결 리스트 메서드 검사
- subprocess 실행형: `BasicCommandValidator`, `LRUValidator` — `subprocess.run()` + stdin pipe
- Popen형: `TTLValidator` — `subprocess.Popen()` + `time.sleep()`으로 TTL 만료 테스트

---

## 시험 문제 출제 가이드 (코디세이 시험 가이드 v1.1 기반)

> 새 미션 문제를 제작할 때 반드시 아래 원칙과 템플릿을 따라야 한다.

### 핵심 설계 원칙

1. **AI 활용 전제**: 시험은 인터넷 연결 환경에서 진행되며, ChatGPT/Claude 등 상용 AI 서비스 자유 이용 가능
2. **AI만으로는 불합격**: LLM에 문제를 넣었을 때 한 번에 정답이 나오지 않아야 함
3. **검토·고도화 능력 평가**: AI가 만든 결과물을 학습자가 검토하고 수정·고도화하여 체크리스트를 전부 통과하는 것이 핵심
4. **유출 전제 설계**: 문항은 학습자 사이에 공유될 것을 전제로, 단순 암기가 아닌 원리 이해 기반의 응용력을 평가
5. **미션 융합 출제**: 하나의 문항에 여러 미션의 개념이 융합·교차 (문항 ↔ 특정 미션 1:1 매핑 금지)

### 난이도 체계 (5문항 / 총 120분)

| 문항 | 난이도 | 권장 시간 | 성격 |
|------|--------|----------|------|
| 1번 | 1 | 15분 | 기본기 확인 + 워밍업. AI가 거의 바로 풀어주지만, 학습자가 의도·결과 검증에 충실해야 함 |
| 2번 | 1 | 15분 | 기본기 확인. 학습 자체를 안 했으면 못 푸는 수준 |
| 3번 | 2 | 25분 | 응용. 여러 개념 조합, 미션 내용의 변형/확장. AI가 50~70% 수준의 답을 주므로 학습자가 심도있게 검토·수정 필요. **엣지 케이스·제약 조건을 꼼꼼히 넣어서 AI 출력물을 그대로 제출하면 Fail** |
| 4번 | 2 | 25분 | 응용 (3번과 동급). 엣지 케이스·제약 조건 포함 |
| 5번 | 3 | 40분 | 심화 통합. 여러 미션을 아우르는 복합 문제. AI가 부분적으로만 도움 → 학습자가 직접 설계·통합. AI 결과물을 조합·고도화해야 Pass |

### 시험 운영 규칙

| 항목 | 내용 |
|------|------|
| 장소 | 오프라인 시험장 |
| 시간 | 최대 2시간 (120분) |
| 문항 수 | 시험당 최대 5문항 |
| 제출 | 문제당 1회만 제출 가능 |
| 합격 조건 | 5문항 All Pass |
| 탈락 시 | 문제 Fail → 즉시 시험 Fail, 다음 문제 진행 불가, 1주일간 재응시 불가 |
| 결과 표시 | Pass/Fail만 표시, 체크 항목 통과/실패 여부 비공개 |
| 채점 방식 | 검증 코드(스크립트)를 통한 자동 채점 + 정답 체크리스트 기반 점수화 |
| 라이브러리 | 각자 알아서 설치 (문제별 제약에 따름) |

### 적용 과정

**AI 올인원** (총 5회 시험):

| 시점 | 시험 범위 | 대상 미션 수 | 문항 수 |
|------|----------|-------------|---------|
| 입학 연수 1 | 미션 1 | 1 | - |
| 입학 연수 2 | 미션 2 | 1 | - |
| 입학 연수 3 | 미션 3 | 1 | - |
| AI/SW 기초 | 미션 4~16 (필수 10개) | 10 | 5 |
| AI/SW 심화 | 미션 17~26 중 도메인별 2개 | 8 | 5 |

**AI 네이티브** (총 2회 시험):

| 시점 | 시험 범위 | 문항 수 |
|------|----------|---------|
| AI 도구 학습 | 미션 1~3 | - |
| AI 활용 학습 | 미션 4~6 | 5 |

### 문항 3종 세트 템플릿

모든 문항은 **문제지 + 정답지 + 검증지** 3종 세트로 구성해야 한다.

#### 1. 문제지 (학습자 배포용) → `problem.md`

```markdown
## 문항 [번호]: [문항 제목]

### 시험 정보
- 과정: [AI 올인원 / AI 네이티브]
- 단계: [입학연수 / AI·SW 기초 / AI·SW 심화 / AI 도구 학습 / AI 활용 학습]
- 난이도: [1 / 2 / 3]
- 권장 시간: [분]
- Pass 기준: 정답 체크리스트 [N]개 중 [M]개 이상 충족

### 문제
[문제 상황 및 요구사항을 구체적으로 서술]

### 제약 사항
- [제약 1]
- [제약 2]

### 입력 형식
[입력 데이터의 형식, 파일명, 구조 등]

### 출력 형식
[기대 출력의 형식, 파일명, 구조 등]

### 제출 방식
[제출할 파일 또는 결과물 명시]
```

#### 2. 정답지 (출제자 보관용, 비공개) → `solution.md`

```markdown
## 문항 [번호] 정답지

### 정답 코드
[모범 정답 코드 전문]

### 정답 체크리스트
| 번호 | 체크 항목 | 배점 | 검증 방법 |
|------|----------|------|----------|
| 1 | [체크 항목 1] | [점수] | [자동 / 수동] |
| 2 | [체크 항목 2] | [점수] | [자동 / 수동] |

- Pass 기준: 총 [N]점 중 [M]점 이상
```

#### 3. 검증지 (채점 시스템용) → Validator 구현체 + `config.yaml`

```markdown
## 문항 [번호] 검증지

### 검증 환경
- 실행 환경: [Python 3.x / Bash / 등]
- 필요 패키지: [패키지 목록]

### 검증 코드
[학습자 제출물을 입력으로 받아 체크리스트 항목별 Pass/Fail 판정, 총점 산출하는 스크립트]

### 실행 방법
[검증 코드 실행 명령어 및 인자 설명]

### 예상 출력 (정답 기준)
[정답 코드로 제출했을 때의 검증 결과 예시]
```

### AI 트랩 설계 가이드

AI 트랩은 **AI가 흔히 범하는 실수를 의도적으로 유도하는 채점 항목**으로, 학습자의 검토·수정 능력을 평가하는 핵심 장치다.

**효과적인 AI 트랩 유형**:
- **엣지 케이스 함정**: 빈 값, 경계값, 소수점 등 AI가 간과하는 데이터 (예: 빈 IP, 소수점 응답시간)
- **정렬/순서 함정**: AI가 기본 정렬을 사용하지만 문제는 역순을 요구 (예: 동점 IP 내림차순)
- **보안/관례 함정**: AI가 '일반적'인 답을 주지만 문제는 엄격한 답을 요구 (예: `prohibit-password` vs `no`)
- **패턴 강제 함정**: 특정 구현 패턴을 요구하지만 AI가 다른 패턴 사용 (예: yield 대신 리스트, pickle 사용)
- **비율/집계 함정**: 전체 모수를 다르게 계산하여 비율이 틀림 (예: 1xx 상태코드 포함 여부)

**AI 트랩 배치 원칙**:
- 난이도 2~3 문항에 집중 배치
- 문항당 2~4개의 AI 트랩 포함 권장
- `CheckItem`의 `ai_trap=True` 플래그로 명시
- `config.yaml`의 `ai_traps` 섹션에 ID와 설명 등록

### 문항 개발 운영 사항

- 대표 문항 개발 후, 동일 구조·다른 데이터/시나리오의 **변형 문항**을 다수 확보 (유출 대비)
- 객관식은 정확히 떨어지는 정답이 없는 경우에만 허용 (재단 검토 필수, AI 네이티브 한정)
- "Exam"이라는 용어 사용 금지 → "시험", "시험 평가", "Test"만 사용

---

## 새 미션/Validator 추가 방법

1. `missions/{category}/level{N}/mission{NN}/` 디렉토리에 `config.yaml`, `problem.md`, `solution.md` 생성
2. `plugins/{category}/validators/`에 `BaseValidator`를 상속하는 Validator 클래스 구현
3. `config.yaml`의 `validators` 목록에 모듈 경로와 클래스명 등록

### config.yaml 구조 예시

```yaml
mission:
  id: python_level1_mission01
  name: "미션 이름"
  level: 1
  category: python          # linux | python
  time_limit: 900
  passing_score: 70

validators:
  - module: plugins.python.validators.model_validator
    class: ModelValidator
    weight: 25

ai_traps:
  - id: trap_id
    description: "AI가 흔히 틀리는 포인트 설명"
```

### Python Validator 구현 패턴

- **AST 분석형** (ModelValidator, PatternValidator): `ast` 모듈로 소스코드 구문 분석 + 런타임 검증
- **subprocess 실행형** (CLIValidator, LogAnalyzerValidator): `subprocess.run()`으로 학생 코드 실행 후 출력/파일 검증
- **파일 I/O형** (PersistenceValidator, LogAnalyzerValidator): `tempfile.TemporaryDirectory()`로 임시 환경 구성, `teardown()`에서 정리

---

## 코딩 컨벤션

- **언어**: 코드 변수/함수명은 영어(snake_case), 문서/주석/커밋은 한국어
- **의존성**: PyYAML 외에는 Python 표준 라이브러리만 사용 (subprocess, os, re, json, pathlib, dataclasses, abc, csv, tempfile, ast)
- **AI 트랩**: `CheckItem`의 `ai_trap=True` 플래그로 AI가 흔히 틀리는 항목 표시
- **subprocess 호출**: 5~10초 타임아웃 적용
- **리눅스 level1 미션 검증은 실제 리눅스 환경 필요** (macOS에서는 프레임워크 동작만 확인 가능)
- **리눅스 level2 미션 검증은 macOS/Linux 모두 가능** (Python 파일 제출 → subprocess + tmpdir 기반)
- **Python 미션 검증은 macOS/Linux 모두 가능** (subprocess + tmpdir 기반)

---

## 현재 프로젝트 현황

### 구현 완료

| 구분 | 수치 |
|------|------|
| 총 미션 수 | 5개 (Linux 2, Python 2, DS 1) |
| 총 Validator 클래스 | 14개 (Linux 5, Python 5, DS 4) |
| 총 CheckItem 수 | 58개 (Linux level1 12 + level2 7, Python mission01 17 + mission02 7, DS mission01 15) |
| 총 AI 트랩 항목 | 18개 (Linux level1 2 + level2 4, Python mission01 4 + mission02 4, DS mission01 4) |
| 채점 결과 파일 | 7쌍 이상 (JSON+MD) 생성 이력 존재 |
| 정답 예시 코드 | `sample_submission/` (Python mission01), `sample_submission_ds/` (DS mission01) |

### 미구현 / 향후 작업

- `tests/` — 테스트 코드 미구현 (디렉토리 구조만 존재)
- `sample_submission/` — mission02 정답 예시 미작성
- 추가 미션 확장 가능: 알고리즘, 자료구조, 데이터베이스 등

### 커밋 히스토리

```
ba8e995  feat: 서버 접근 로그 분석기 미션 추가 (python_level1_mission02)
10cdc99  feat: 코디세이 자동 채점 프레임워크 초기 구현
```
