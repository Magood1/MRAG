import json
import time
import requests
from statistics import mean

# إعدادات
API_URL = "http://127.0.0.1:8000/api/v1/assistant/chat"
API_KEY = "secret-key-123"
DATASET_PATH = "evaluation/golden_dataset.json"
REPORT_PATH = "evaluation/PERFORMANCE_REPORT.md"

# معدل الاستعلامات: 5 طلبات / دقيقة → طلب كل 12 ثانية
RATE_LIMIT_SECONDS = 0.1


def call_api(payload):
    """إرسال طلب للـ API مع معالجة أخطاء احترافية."""
    headers = {"X-API-Key": API_KEY}
    start_t = time.perf_counter()

    try:
        response = requests.post(API_URL, json=payload, headers=headers)
        latency = (time.perf_counter() - start_t) * 1000
        return response, latency

    except requests.exceptions.RequestException as e:
        return None, None


def evaluate_case(case):
    """تقييم حالة واحدة وإرجاع النتيجة."""
    payload = {"kb_id": case["kb_id"], "query": case["question"]}

    response, latency = call_api(payload)

    if response is None:
        return {
            "id": case["id"],
            "passed": False,
            "latency": 0,
            "status": "error",
            "expected": case["expected_status"],
            "note": "Connection Error"
        }

    if response.status_code != 200:
        return {
            "id": case["id"],
            "passed": False,
            "latency": latency,
            "status": f"HTTP {response.status_code}",
            "expected": case["expected_status"],
            "note": "HTTP Error"
        }

    data = response.json()
    actual_status = data.get("status")
    answer = data.get("answer", "")

    # مقارنة الحالة المتوقعة
    status_match = (actual_status == case["expected_status"])

    # فحص الكلمات المفتاحية
    keyword_match = True
    if case["expected_status"] == "success":
        keyword_match = any(k in answer for k in case["expected_keywords"])

    passed = status_match and keyword_match

    return {
        "id": case["id"],
        "passed": passed,
        "latency": latency,
        "status": actual_status,
        "expected": case["expected_status"],
        "note": "Keyword mismatch" if status_match and not keyword_match else ""
    }


def generate_report(results, latencies):
    total = len(results)
    passed = sum(r["passed"] for r in results)
    success_rate = (passed / total) * 100 if total else 0
    avg_latency = mean(latencies) if latencies else 0
    p95_latency = sorted(latencies)[int(len(latencies) * 0.95)] if latencies else 0

    report = f"""# 📊 MRAG Performance Report
**Date:** {time.strftime("%Y-%m-%d %H:%M:%S")}
**Environment:** Local Dev

## 📈 Summary Metrics
| Metric | Value | Target | Status |
| :--- | :--- | :--- | :--- |
| **Total Tests** | {total} | - | - |
| **Success Rate** | {success_rate:.1f}% | > 90% | {'✅' if success_rate >= 90 else '⚠️'} |
| **Avg Latency** | {avg_latency:.0f} ms | < 2000 ms | {'✅' if avg_latency < 2000 else '⚠️'} |
| **P95 Latency** | {p95_latency:.0f} ms | < 3000 ms | {'✅' if p95_latency < 3000 else '⚠️'} |

## 📝 Detailed Breakdown
| ID | Passed | Status | Expected | Latency (ms) | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
"""

    for r in results:
        icon = "✅" if r["passed"] else "❌"
        report += (
            f"| {r['id']} | {icon} | {r['status']} | {r['expected']} | "
            f"{r['latency']:.0f} | {r['note']} |\n"
        )

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\n📄 Report generated at: {REPORT_PATH}")


def run_evaluation():
    print("🚀 Starting System Evaluation...")

    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    print(f"📋 Loaded {len(dataset)} test cases.")

    results = []
    latencies = []

    last_request_time = 0

    for i, case in enumerate(dataset):
        print(f"   Testing: {case['id']}...", end=" ", flush=True)

        # احترام الـ Rate Limit
        now = time.time()
        elapsed = now - last_request_time

        if elapsed < RATE_LIMIT_SECONDS:
            wait_time = RATE_LIMIT_SECONDS - elapsed
            time.sleep(wait_time)

        last_request_time = time.time()

        result = evaluate_case(case)
        results.append(result)

        if result["latency"]:
            latencies.append(result["latency"])

        print("✅" if result["passed"] else "❌")

    generate_report(results, latencies)


if __name__ == "__main__":
    run_evaluation()
