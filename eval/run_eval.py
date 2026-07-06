import sys, json, requests

sys.path.append("../backend")

API = "http://localhost:8000"
results = {"passed": 0, "failed": 0, "blocked_correctly": 0, "total": 0}

with open("golden_queries.json") as f:
    queries = json.load(f)

for q in queries:
    results["total"] += 1
    resp = requests.post(f"{API}/v1/query", json={"question": q["question"]}).json()

    if q.get("expected_blocked"):
        if resp.get("blocked"):
            results["blocked_correctly"] += 1
            results["passed"] += 1
            print(f"✅ [{q['category']}] Correctly blocked: {q['question'][:50]}")
        else:
            results["failed"] += 1
            print(f"❌ [{q['category']}] Should have been blocked: {q['question'][:50]}")
    else:
        if not resp.get("blocked") and resp.get("result", {}).get("row_count", 0) > 0:
            results["passed"] += 1
            conf = resp.get("hallucination", {}).get("final_confidence", 0)
            print(f"✅ [{q['category']}] {q['question'][:50]} | conf={conf:.2f}")
        else:
            results["failed"] += 1
            print(f"❌ [{q['category']}] {q['question'][:50]}")

print(f"\n📊 RESULTS: {results['passed']}/{results['total']} passed")
print(f"   Destructive queries blocked: {results['blocked_correctly']}")
accuracy = results['passed'] / results['total'] * 100
print(f"   Accuracy: {accuracy:.0f}%")
