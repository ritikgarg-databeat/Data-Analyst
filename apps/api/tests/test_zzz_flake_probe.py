from fastapi.testclient import TestClient

CORRECT_CODE = """
payments_success = payments[payments["status"] == "success"].copy()
merged = payments_success.merge(
    orders[["order_id", "customer_id", "order_date"]], on="order_id"
).merge(customers[["customer_id", "customer_segment"]], on="customer_id")
merged["quarter"] = pd.to_datetime(merged["payment_date"]).dt.to_period("Q").astype(str)
result = (
    merged.groupby(["quarter", "customer_segment"])["amount"]
    .sum()
    .round(2)
    .reset_index()
    .rename(columns={"amount": "revenue"})
    .sort_values(["quarter", "revenue"], ascending=[True, False])
    .reset_index(drop=True)
)
"""


def test_probe_repeated_submissions_for_timing_flake(client: TestClient) -> None:
    scores = []
    for i in range(25):
        response = client.post(
            "/api/v1/python/exercises/quarterly-revenue-by-segment/submit",
            json={"submitted_code": CORRECT_CODE},
        )
        body = response.json()
        scores.append(body.get("score"))
        print(f"attempt {i}: score={body.get('score')} status={body.get('status')}")
    print("all scores:", scores)
    assert True
