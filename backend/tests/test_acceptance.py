from pathlib import Path


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert "СВОД" in response.json()["app_name"]


def test_acc_001_authentication(client):
    response = client.post(
        "/api/auth/login",
        json={"email": "analyst@example.com", "password": "valid_password"},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()

    unauthorized = client.get("/api/scenarios")
    assert unauthorized.status_code == 401

    me = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {response.json()['access_token']}"},
    )
    assert me.status_code == 200
    assert me.json()["role"] == "budget_analyst"


def test_acc_002_versions_recalculate_and_archive_listing(client, analyst_headers):
    created = client.post(
        "/api/scenarios",
        headers=analyst_headers,
        json={"name": "Бюджет 2026 v1", "type": "budget", "scope": "all_objects"},
    )
    assert created.status_code == 201, created.text
    scenario_id = created.json()["id"]
    assert created.json()["version_number"] == 1

    recalc = client.post(f"/api/scenarios/{scenario_id}/recalculate", headers=analyst_headers)
    assert recalc.status_code == 200, recalc.text

    child = client.post(
        "/api/scenarios",
        headers=analyst_headers,
        json={
            "name": "Бюджет 2026 v2",
            "type": "budget",
            "scope": "all_objects",
            "parent_version_id": scenario_id,
        },
    )
    assert child.status_code == 201, child.text
    assert child.json()["version_number"] == 2

    listed = client.get("/api/scenarios?include_archived=true", headers=analyst_headers)
    assert listed.status_code == 200
    assert len(listed.json()) >= 2


def test_acc_003_scenario_creation_validation(client, analyst_headers, object_a):
    forecast = client.post(
        "/api/scenarios",
        headers=analyst_headers,
        json={"name": "Прогноз - все объекты", "type": "forecast", "scope": "all_objects"},
    )
    assert forecast.status_code == 201
    assert forecast.json()["type"] == "forecast"
    assert forecast.json()["scope"] == "all_objects"
    assert forecast.json()["status"] == "draft"

    single = client.post(
        "/api/scenarios",
        headers=analyst_headers,
        json={
            "name": "Бюджет - объект А",
            "type": "budget",
            "scope": "single_object",
            "construction_object_id": object_a["id"],
        },
    )
    assert single.status_code == 201, single.text
    assert single.json()["scope"] == "single_object"

    invalid = client.post(
        "/api/scenarios",
        headers=analyst_headers,
        json={"name": "Без объекта", "type": "budget", "scope": "single_object"},
    )
    assert invalid.status_code == 422


def test_acc_004_patch_cash_flow_recalculates_consensus(client, analyst_headers, demo_scenario):
    lines = client.get(
        f"/api/cash-flow-lines?scenario_id={demo_scenario['id']}",
        headers=analyst_headers,
    )
    assert lines.status_code == 200
    line = next(item for item in lines.json() if item["line_item"] == "Материалы")

    patched = client.patch(
        f"/api/cash-flow-lines/{line['id']}",
        headers=analyst_headers,
        json={"adjustment": 50000.0},
    )
    assert patched.status_code == 200, patched.text
    assert patched.json()["consensus_amount"] == line["base_amount"] + 50000.0


def test_acc_005_and_006_recalculate_financial_results(client, analyst_headers, demo_scenario, object_a):
    recalc = client.post(f"/api/scenarios/{demo_scenario['id']}/recalculate", headers=analyst_headers)
    assert recalc.status_code == 200, recalc.text
    assert recalc.json()["status"] == "calculated"
    assert recalc.json()["calculated_at"] is not None

    results = client.get(
        f"/api/financial-results?scenario_id={demo_scenario['id']}&construction_object_id={object_a['id']}",
        headers=analyst_headers,
    )
    assert results.status_code == 200
    assert results.json()
    row = next(item for item in results.json() if item["revenue"] > 0)
    assert {"revenue", "costs", "profit"} <= set(row)
    assert row["profit"] == row["revenue"] - row["costs"]


def test_acc_007_consolidation(client, analyst_headers, demo_scenario):
    client.post(f"/api/scenarios/{demo_scenario['id']}/recalculate", headers=analyst_headers)
    consolidated = client.get(
        f"/api/financial-results/consolidated?scenario_id={demo_scenario['id']}",
        headers=analyst_headers,
    )
    assert consolidated.status_code == 200
    rows = consolidated.json()
    assert rows
    assert all(row["is_consolidated"] for row in rows)
    assert {"2026-01", "2026-09"} <= {row["period"] for row in rows}

    object_rows = client.get(
        f"/api/financial-results?scenario_id={demo_scenario['id']}",
        headers=analyst_headers,
    ).json()
    assert sum(row["profit"] for row in rows) == sum(row["profit"] for row in object_rows)


def test_acc_008_compare_versions(client, analyst_headers):
    v1 = client.post(
        "/api/scenarios",
        headers=analyst_headers,
        json={"name": "Compare v1", "type": "budget", "scope": "all_objects"},
    ).json()
    client.post(f"/api/scenarios/{v1['id']}/recalculate", headers=analyst_headers)
    v2 = client.post(
        "/api/scenarios",
        headers=analyst_headers,
        json={
            "name": "Compare v2",
            "type": "budget",
            "scope": "all_objects",
            "parent_version_id": v1["id"],
        },
    ).json()
    lines = client.get(f"/api/cash-flow-lines?scenario_id={v2['id']}", headers=analyst_headers).json()
    client.patch(
        f"/api/cash-flow-lines/{lines[0]['id']}",
        headers=analyst_headers,
        json={"adjustment": 1000.0},
    )
    client.post(f"/api/scenarios/{v2['id']}/recalculate", headers=analyst_headers)

    compared = client.get(
        f"/api/scenarios/compare?version_a={v1['id']}&version_b={v2['id']}",
        headers=analyst_headers,
    )
    assert compared.status_code == 200, compared.text
    assert "variance" in compared.json()[0]
    assert "variance_percent" in compared.json()[0]


def test_acc_009_fact_loading(client, admin_headers):
    triggered = client.post("/api/fact-loading/trigger", headers=admin_headers)
    assert triggered.status_code == 200, triggered.text
    assert triggered.json()["records_loaded"] >= 1

    token = admin_headers
    lines = client.get("/api/cash-flow-lines?source=accounting_system", headers=token)
    assert lines.status_code == 200
    assert len(lines.json()) >= 1

    logs = client.get("/api/fact-loading/log", headers=admin_headers)
    assert logs.status_code == 200
    assert {"status", "timestamp"} <= set(logs.json()[0])


def test_acc_010_reports(client, analyst_headers, demo_scenario):
    client.post(f"/api/scenarios/{demo_scenario['id']}/recalculate", headers=analyst_headers)
    for report_format in ["excel", "pdf"]:
        response = client.post(
            "/api/reports/generate",
            headers=analyst_headers,
            json={"scenario_id": demo_scenario["id"], "type": "consolidated", "format": report_format},
        )
        assert response.status_code == 201, response.text
        assert "file_path" in response.json()
        assert Path(response.json()["file_path"]).exists()


def test_acc_011_construction_object_validation(client, analyst_headers):
    ok = client.post(
        "/api/construction-objects",
        headers=analyst_headers,
        json={
            "name": "ЖК Северный",
            "code": "OBJ-003",
            "construction_start": "2025-01-01",
            "construction_end": "2027-06-30",
            "status": "in_progress",
        },
    )
    assert ok.status_code == 201, ok.text

    invalid = client.post(
        "/api/construction-objects",
        headers=analyst_headers,
        json={
            "name": "Некорректный",
            "code": "OBJ-004",
            "construction_start": "2027-01-01",
            "construction_end": "2025-01-01",
        },
    )
    assert invalid.status_code == 422
