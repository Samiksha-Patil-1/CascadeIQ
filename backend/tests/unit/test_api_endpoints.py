"""Unit and integration tests for FastAPI routes."""

from typing import Any

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_api_health_check() -> None:
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


def test_api_graphs_endpoints() -> None:
    # Samples
    res = client.get("/api/graphs/samples")
    assert res.status_code == 200
    samples = res.json()
    assert len(samples) >= 1
    assert any(s["id"] == "ecommerce-platform" for s in samples)

    # Fetch graph
    res_g = client.get("/api/graphs/ecommerce-platform")
    assert res_g.status_code == 200
    graph_data = res_g.json()
    assert len(graph_data["nodes"]) == 34
    assert len(graph_data["edges"]) == 46

    # Structure
    res_st = client.get("/api/graphs/ecommerce-platform/structure")
    assert res_st.status_code == 200
    st_data = res_st.json()
    assert "cycles" in st_data
    assert "layers" in st_data
    assert "single_points_of_failure" in st_data
    assert "pagerank_reversed" in st_data


def test_api_simulate_deterministic_and_mc() -> None:
    payload: dict[str, Any] = {
        "scenario": {
            "failures": [{"node_id": "auth-db", "severity": 1.0, "start_s": 0.0}],
            "outage_minutes": 30.0,
            "seed": 42,
        },
        "mode": "deterministic",
    }
    # Deterministic
    res = client.post("/api/graphs/ecommerce-platform/simulate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "run_id" in data
    assert "summary" in data
    assert data["summary"]["affected"] > 0
    assert len(data["nodes"]) == 34

    # Monte Carlo
    mc_payload: dict[str, Any] = {
        "scenario": payload["scenario"],
        "mode": "monte_carlo",
        "trials": 200,
    }
    res_mc = client.post("/api/graphs/ecommerce-platform/simulate", json=mc_payload)
    assert res_mc.status_code == 200
    data_mc = res_mc.json()
    assert data_mc["mode"] == "monte_carlo"
    assert "p_fail" in data_mc
    assert "ci95" in data_mc


def test_api_why_explain_endpoint() -> None:
    payload = {
        "scenario": {
            "failures": [{"node_id": "auth-db", "severity": 1.0, "start_s": 0.0}],
            "outage_minutes": 30.0,
            "seed": 42,
        }
    }
    res = client.post("/api/graphs/ecommerce-platform/why/checkout-service", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["node_id"] == "checkout-service"
    assert "narrative" in data
    assert len(data["chain"]) > 0

    # Healthy node test
    res_h = client.post("/api/graphs/ecommerce-platform/why/notification-service", json=payload)
    assert res_h.status_code == 200
    assert res_h.json()["node_id"] == "notification-service"
    assert res_h.json()["damage"] == 0.0


def test_api_risk_ranking() -> None:
    res = client.post("/api/graphs/ecommerce-platform/risk")
    assert res.status_code == 200
    data = res.json()
    assert data["total_nodes"] == 34
    assert len(data["rankings"]) == 34
    assert data["rankings"][0]["rank"] == 1


def test_api_mitigation_catalog() -> None:
    res = client.get("/api/mitigations/catalog")
    assert res.status_code == 200
    cat = res.json()
    assert len(cat) >= 7


def test_api_optimize_and_compare() -> None:
    scenario = {
        "failures": [{"node_id": "auth-db", "severity": 1.0, "start_s": 0.0}],
        "outage_minutes": 30.0,
        "seed": 42,
    }
    opt_payload = {
        "scenarios": [{"scenario": scenario, "weight": 1.0}],
        "budget": 15.0,
        "algorithm": "greedy",
    }
    res_opt = client.post("/api/graphs/ecommerce-platform/optimize", json=opt_payload)
    assert res_opt.status_code == 200
    opt_data = res_opt.json()
    assert "plan" in opt_data
    assert "curve" in opt_data
    assert "knee_index" in opt_data

    # Compare
    plan_items = [p["item"] for p in opt_data["plan"]]
    comp_payload = {
        "scenario": scenario,
        "plan": plan_items,
    }
    res_comp = client.post("/api/graphs/ecommerce-platform/compare", json=comp_payload)
    assert res_comp.status_code == 200
    comp_data = res_comp.json()
    assert "baseline" in comp_data
    assert "mitigated" in comp_data
    assert "mitigated_graph" in comp_data
    assert "delta" in comp_data
    assert comp_data["delta"]["pct_loss_reduction"] >= 0.0
