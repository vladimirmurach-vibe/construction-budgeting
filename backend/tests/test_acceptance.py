"""Приёмочные тесты из acceptance.yaml (ACC-REQ-001..011)."""


def _seed_scenario(client, auth_headers):
    scenarios = client.get("/api/scenarios", headers=auth_headers).json()
    for s in scenarios:
        if s["name"] == "Демо-сценарий":
            return s["id"]
    return scenarios[0]["id"]


def test_acc_req_001_auth(client):
    resp = client.post("/api/auth/login", json={"email": "analyst@example.com", "password": "valid_password"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()

    resp = client.get("/api/scenarios")
    assert resp.status_code == 401


def test_acc_req_002_version_storage(client, auth_headers):
    resp = client.post(
        "/api/scenarios",
        json={"name": "Бюджет 2026 v1", "type": "budget", "scope": "all_objects"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    scenario_id = resp.json()["id"]
    assert "version_number" in resp.json()

    client.post(f"/api/scenarios/{scenario_id}/recalculate", headers=auth_headers)

    resp = client.post(
        "/api/scenarios",
        json={
            "name": "Бюджет 2026 v2",
            "type": "budget",
            "scope": "all_objects",
            "parent_version_id": scenario_id,
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    assert resp.json()["version_number"] == 2

    resp = client.get("/api/scenarios?include_archived=true", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) >= 2


def test_acc_req_003_scenario_creation(client, auth_headers):
    resp = client.post(
        "/api/scenarios",
        json={"name": "Прогноз — все объекты", "type": "forecast", "scope": "all_objects"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["type"] == "forecast"
    assert body["scope"] == "all_objects"
    assert body["status"] == "draft"

    objects = client.get("/api/construction-objects", headers=auth_headers).json()
    obj_id = objects[0]["id"]
    resp = client.post(
        "/api/scenarios",
        json={
            "name": "Бюджет — объект А",
            "type": "budget",
            "scope": "single_object",
            "construction_object_id": obj_id,
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    assert resp.json()["scope"] == "single_object"

    resp = client.post(
        "/api/scenarios",
        json={"name": "Без объекта", "type": "budget", "scope": "single_object"},
        headers=auth_headers,
    )
    assert resp.status_code == 422


def test_acc_req_004_cash_flow_adjustment(client, auth_headers):
    scenario_id = _seed_scenario(client, auth_headers)
    lines = client.get(f"/api/cash-flow-lines?scenario_id={scenario_id}", headers=auth_headers).json()
    line = next(l for l in lines if l["period"] == "2026-03" and l["form_code"] == "FORM-01")
    base = line["base_amount"]
    resp = client.patch(
        f"/api/cash-flow-lines/{line['id']}",
        json={"adjustment": 50000},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["consensus_amount"] == base + 50000


def test_acc_req_005_financial_result(client, auth_headers):
    scenario_id = _seed_scenario(client, auth_headers)
    client.post(f"/api/scenarios/{scenario_id}/recalculate", headers=auth_headers)
    objects = client.get("/api/construction-objects", headers=auth_headers).json()
    obj_id = objects[0]["id"]
    resp = client.get(
        f"/api/financial-results?scenario_id={scenario_id}&construction_object_id={obj_id}",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    for row in resp.json():
        assert "revenue" in row
        assert "costs" in row
        assert "profit" in row
        assert abs(row["profit"] - (row["revenue"] - row["costs"])) < 0.01


def test_acc_req_006_recalculation(client, auth_headers):
    scenario_id = _seed_scenario(client, auth_headers)
    resp = client.post(f"/api/scenarios/{scenario_id}/recalculate", headers=auth_headers)
    assert resp.status_code == 200
    resp = client.get(f"/api/scenarios/{scenario_id}", headers=auth_headers)
    assert resp.json()["status"] == "calculated"
    assert resp.json()["calculated_at"] is not None


def test_acc_req_007_consolidation(client, auth_headers):
    scenario_id = _seed_scenario(client, auth_headers)
    client.post(f"/api/scenarios/{scenario_id}/recalculate", headers=auth_headers)
    resp = client.get(f"/api/financial-results/consolidated?scenario_id={scenario_id}", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) > 0
    assert data[0]["is_consolidated"] is True
    assert "profit" in data[0]
    assert "period" in data[0]


def test_acc_req_008_version_compare(client, auth_headers):
    scenario_id = _seed_scenario(client, auth_headers)
    s2 = client.post(
        "/api/scenarios",
        json={"name": "Compare v2", "type": "budget", "scope": "all_objects", "parent_version_id": scenario_id},
        headers=auth_headers,
    ).json()
    client.post(f"/api/scenarios/{scenario_id}/recalculate", headers=auth_headers)
    client.post(f"/api/scenarios/{s2['id']}/recalculate", headers=auth_headers)
    resp = client.get(
        f"/api/scenarios/compare?version_a={scenario_id}&version_b={s2['id']}",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) > 0
    assert "variance" in data[0]
    assert "variance_percent" in data[0]


def test_acc_req_009_fact_loading(client, admin_headers, tmp_path, monkeypatch):  # noqa: ARG001
    from app.core.config import settings
    import_dir = tmp_path / "imports"
    import_dir.mkdir()
    fact_file = import_dir / "fact_data.csv"
    fact_file.write_text(
        "construction_object_code,form_code,line_item,period,actual_amount\n"
        "OBJ-A,FORM-01,Материалы,2026-01,95000\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(settings, "fact_import_dir", str(import_dir))
    resp = client.post("/api/fact-loading/trigger", headers=admin_headers)
    assert resp.status_code == 200
    assert "records_loaded" in resp.json()
    resp = client.get("/api/fact-loading/log", headers=admin_headers)
    assert resp.status_code == 200
    assert len(resp.json()) > 0


def test_acc_req_010_reports(client, auth_headers):
    scenario_id = _seed_scenario(client, auth_headers)
    client.post(f"/api/scenarios/{scenario_id}/recalculate", headers=auth_headers)
    for fmt in ["excel", "pdf"]:
        resp = client.post(
            "/api/reports/generate",
            json={"scenario_id": scenario_id, "type": "consolidated", "format": fmt},
            headers=auth_headers,
        )
        assert resp.status_code == 201
        assert "file_path" in resp.json()


def test_acc_req_011_construction_objects(client, auth_headers):
    resp = client.post(
        "/api/construction-objects",
        json={
            "name": "ЖК Северный",
            "code": "OBJ-NEW",
            "construction_start": "2025-01-01",
            "construction_end": "2027-06-30",
            "status": "in_progress",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    resp = client.post(
        "/api/construction-objects",
        json={
            "name": "Некорректный",
            "code": "OBJ-BAD",
            "construction_start": "2027-01-01",
            "construction_end": "2025-01-01",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 422


def test_health(client):
    assert client.get("/health").json()["status"] == "ok"
