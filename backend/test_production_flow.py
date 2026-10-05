import os
import io
from app.main import app
from fastapi.testclient import TestClient

def main():
    client = TestClient(app)

    print("=== Testing All Required InsightForge Production Endpoints ===")

    # 1. GET /api/health
    h = client.get('/api/health')
    assert h.status_code == 200, f"/api/health failed with status {h.status_code}"
    health_json = h.json()
    print("[PASS] 1. GET /api/health ->", health_json)
    assert health_json == {"status": "ok", "service": "InsightForge AI"}, f"Health JSON mismatch: {health_json}"

    # Also test /health alias
    h_alias = client.get('/health')
    assert h_alias.status_code == 200
    assert h_alias.json() == {"status": "ok", "service": "InsightForge AI"}
    print("[PASS]    GET /health (alias) ->", h_alias.json())

    # 2. GET /api/sample
    s = client.get('/api/sample')
    assert s.status_code == 200, f"/api/sample failed: {s.status_code}"
    sample_data = s.json()
    sample_dataset_id = sample_data['dataset_id']
    print(f"[PASS] 2. GET /api/sample -> Filename: {sample_data['filename']}, Rows: {sample_data['rows']}, Cols: {sample_data['columns']}, ID: {sample_dataset_id}")
    assert sample_data['rows'] == 1000
    assert sample_data['columns'] == 9

    # 3. POST /api/upload
    csv_content = b"date,product,category,region,quantity,unit_price,revenue,customer,sales_rep\n2026-01-01,Running Shoes,Sports,North,3,4915.86,14747.58,Alpha Corp,Rohan\n2026-02-02,Wireless Headphones,Electronics,South,6,6586.1,39516.6,Beta Co,Aarav\n"
    files = {
        'file': ('test_upload.csv', io.BytesIO(csv_content), 'text/csv')
    }
    up = client.post('/api/upload', files=files)
    assert up.status_code == 200, f"/api/upload failed: {up.status_code} - {up.text}"
    up_data = up.json()
    uploaded_id = up_data['dataset_id']
    print(f"[PASS] 3. POST /api/upload -> Filename: {up_data['filename']}, Rows: {up_data['rows']}, Cols: {up_data['columns']}, ID: {uploaded_id}")
    assert up_data['rows'] == 2

    # 4. GET /api/dataset/{dataset_id}/profile
    prof_res = client.get(f'/api/dataset/{sample_dataset_id}/profile')
    assert prof_res.status_code == 200, f"/api/dataset/{sample_dataset_id}/profile failed: {prof_res.status_code}"
    prof_json = prof_res.json()
    print(f"[PASS] 4. GET /api/dataset/{{dataset_id}}/profile -> Total Rows: {prof_json['overview']['total_rows']}, Cols: {len(prof_json['columns'])}")
    assert prof_json['overview']['total_rows'] == 1000

    # 5. GET /api/dataset/{dataset_id}/preview
    prev_res = client.get(f'/api/dataset/{sample_dataset_id}/preview?limit=5')
    assert prev_res.status_code == 200, f"/api/dataset/{sample_dataset_id}/preview failed: {prev_res.status_code}"
    prev_json = prev_res.json()
    print(f"[PASS] 5. GET /api/dataset/{{dataset_id}}/preview -> Retrieved {len(prev_json['rows'])} preview records")
    assert len(prev_json['rows']) == 5

    # 6. POST /api/analyze
    analyze_payload = {
        "dataset_id": sample_dataset_id,
        "question": "What is the total revenue?"
    }
    an_res = client.post('/api/analyze', json=analyze_payload)
    assert an_res.status_code == 200, f"/api/analyze failed: {an_res.status_code} - {an_res.text}"
    an_json = an_res.json()
    print(f"[PASS] 6. POST /api/analyze -> Answer: '{an_json.get('answer')}', Key Metric: '{an_json.get('key_metric')}'")
    assert "revenue" in an_json.get("answer", "").lower() or an_json.get("key_metric") is not None

    # 7. POST /api/chat
    chat_payload = {
        "dataset_id": sample_dataset_id,
        "message": "Which product generated the highest revenue?"
    }
    chat_res = client.post('/api/chat', json=chat_payload)
    assert chat_res.status_code == 200, f"/api/chat failed: {chat_res.status_code} - {chat_res.text}"
    chat_json = chat_res.json()
    print(f"[PASS] 7. POST /api/chat -> Answer: '{chat_json.get('answer')[:60]}...', ConvID: {chat_json.get('conversation_id')}")
    assert chat_json.get("conversation_id") is not None

    print("\n========================================================")
    print("ALL 7 REQUIRED PRODUCTION ENDPOINTS ARE WORKING PERFECTLY!")
    print("========================================================")

if __name__ == '__main__':
    main()
