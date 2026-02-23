# 서버 접근 로그 분석기 — 모범 답안

## 프로젝트 구조

```
submission/
└── log_analyzer.py    # 로그 분석기 (단일 파일)
```

---

## log_analyzer.py (100점)

```python
import argparse
import csv
from collections import defaultdict


def parse_log(filepath):
    """CSV 로그 파일을 파싱하여 레코드 리스트 반환"""
    records = []
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append(row)
    return records


def analyze_ip_access(records):
    """IP별 접근 횟수 집계 (빈 IP 제외)"""
    ip_count = defaultdict(int)
    for r in records:
        ip = r["ip"].strip()
        if ip:  # 빈 IP 제외
            ip_count[ip] += 1

    # 접근 횟수 내림차순, 동점 시 IP 내림차순
    sorted_ips = sorted(ip_count.items(), key=lambda x: (x[1], x[0]), reverse=True)
    return sorted_ips[:5]


def analyze_status_codes(records):
    """HTTP 상태코드 그룹별 비율 계산"""
    total = len(records)
    groups = defaultdict(int)

    for r in records:
        code = int(r["status_code"])
        if 100 <= code < 200:
            groups["1xx"] += 1
        elif 200 <= code < 300:
            groups["2xx"] += 1
        elif 300 <= code < 400:
            groups["3xx"] += 1
        elif 400 <= code < 500:
            groups["4xx"] += 1
        elif 500 <= code < 600:
            groups["5xx"] += 1

    result = {}
    for group in ["1xx", "2xx", "3xx", "4xx", "5xx"]:
        count = groups.get(group, 0)
        if count > 0:
            result[group] = round(count / total * 100, 1)
    return result


def analyze_slow_endpoints(records):
    """엔드포인트별 평균 응답시간 계산"""
    endpoint_times = defaultdict(list)
    for r in records:
        endpoint = r["endpoint"]
        response_time = float(r["response_time_ms"])  # 소수점 처리
        endpoint_times[endpoint].append(response_time)

    averages = {}
    for endpoint, times in endpoint_times.items():
        averages[endpoint] = round(sum(times) / len(times), 1)

    # 평균 응답시간 내림차순
    sorted_endpoints = sorted(averages.items(), key=lambda x: x[1], reverse=True)
    return sorted_endpoints[:3]


def generate_report(top_ips, status_ratios, slow_endpoints):
    """리포트 텍스트 생성"""
    lines = []

    lines.append("=== IP Access Top 5 ===")
    for ip, count in top_ips:
        lines.append(f"{ip}: {count}")
    lines.append("")

    lines.append("=== Status Code Distribution ===")
    for group, ratio in sorted(status_ratios.items()):
        lines.append(f"{group}: {ratio:.1f}%")
    lines.append("")

    lines.append("=== Slowest Endpoints Top 3 ===")
    for endpoint, avg_time in slow_endpoints:
        lines.append(f"{endpoint}: {avg_time:.1f}ms")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="서버 접근 로그 분석기")
    parser.add_argument("--log", required=True, help="입력 CSV 로그 파일 경로")
    parser.add_argument("--output", required=True, help="출력 리포트 파일 경로")
    args = parser.parse_args()

    # 1. CSV 파싱
    records = parse_log(args.log)

    # 2. 분석
    top_ips = analyze_ip_access(records)
    status_ratios = analyze_status_codes(records)
    slow_endpoints = analyze_slow_endpoints(records)

    # 3. 리포트 생성 및 저장
    report = generate_report(top_ips, status_ratios, slow_endpoints)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"리포트 생성 완료: {args.output}")


if __name__ == "__main__":
    main()
```

---

## AI 함정 해설 (4개)

### 함정 1: 빈 IP 행 (top_ips)

채점용 CSV에는 IP가 빈 문자열인 행이 포함되어 있습니다.

**❌ AI가 흔히 하는 실수 (빈 IP 포함)**:
```python
for r in records:
    ip_count[r["ip"]] += 1  # 빈 문자열도 IP로 집계됨
```

**✅ 올바른 구현 (빈 IP 제외)**:
```python
for r in records:
    ip = r["ip"].strip()
    if ip:  # 빈 IP 제외
        ip_count[ip] += 1
```

### 함정 2: 동점 IP 내림차순 정렬 (ip_order)

접근 횟수가 같은 IP가 여러 개 있을 때, IP 주소도 내림차순으로 정렬해야 합니다.

**❌ AI가 흔히 하는 실수 (횟수만 정렬)**:
```python
sorted_ips = sorted(ip_count.items(), key=lambda x: x[1], reverse=True)
# 동점 IP 순서가 불확실
```

**✅ 올바른 구현 (복합 정렬)**:
```python
sorted_ips = sorted(ip_count.items(), key=lambda x: (x[1], x[0]), reverse=True)
# 횟수 내림차순 + IP 내림차순
```

### 함정 3: 1xx 상태코드 (status_ratio)

채점용 CSV에 `100` 상태코드가 포함되어 있어, 전체 행 수가 달라집니다.

**❌ AI가 흔히 하는 실수 (2xx~5xx만 처리)**:
```python
if 200 <= code < 300: groups["2xx"] += 1
elif 300 <= code < 400: groups["3xx"] += 1
# 1xx가 누락되어 비율 합계가 100%에 못 미침
```

**✅ 올바른 구현 (1xx 포함)**:
```python
if 100 <= code < 200: groups["1xx"] += 1
elif 200 <= code < 300: groups["2xx"] += 1
# 1xx를 분류하여 전체 행 수 기준 비율 정확
```

### 함정 4: 소수점 response_time (slow_values)

채점용 CSV에 `33.7`처럼 소수점 응답시간이 포함되어 있습니다.

**❌ AI가 흔히 하는 실수 (int 변환)**:
```python
response_time = int(r["response_time_ms"])  # 33.7 → ValueError 또는 33
```

**✅ 올바른 구현 (float 변환)**:
```python
response_time = float(r["response_time_ms"])  # 33.7 → 33.7 정확 처리
```

---

## 채점 결과 예시 (만점)

```
✅ csv_parse        — CSV 정상 파싱 + report.txt 생성 (10점)
✅ top_ips          — IP별 접근 횟수 TOP 5 정확 (15점) ⚠️
✅ ip_order         — 동점 IP 내림차순 정렬 (15점) ⚠️
✅ status_ratio     — HTTP 상태코드 그룹별 비율 정확 (20점) ⚠️
✅ slow_order       — 느린 엔드포인트 TOP 3 순서 정확 (15점)
✅ report_sections  — 리포트 3개 섹션 모두 포함 (15점)
✅ slow_values      — 엔드포인트 평균시간 수치 정확 (10점) ⚠️

총점: 100/100 ✅ PASS
```

---

## 기대 정답값 (채점용 CSV 24행 기준)

### IP 접근 횟수 TOP 5
| 순위 | IP | 횟수 |
|------|-----|------|
| 1 | 192.168.1.1 | 6 |
| 2 | 10.0.0.5 | 6 |
| 3 | 172.16.0.10 | 5 |
| 4 | 192.168.2.20 | 3 |
| 5 | 10.0.0.99 | 3 |

### 상태코드 비율
| 그룹 | 비율 |
|------|------|
| 1xx | 4.2% |
| 2xx | 70.8% |
| 3xx | 4.2% |
| 4xx | 8.3% |
| 5xx | 12.5% |

### 느린 엔드포인트 TOP 3
| 순위 | 엔드포인트 | 평균 응답시간 |
|------|-----------|-------------|
| 1 | /api/orders | 2488.8ms |
| 2 | /api/products | 502.4ms |
| 3 | /api/users | 31.5ms |
