from __future__ import annotations

from fastapi.testclient import TestClient

from web.api.main import app


client = TestClient(app)


def test_health_and_presets() -> None:
    assert client.get("/health").json() == {"status": "ok"}
    presets = client.get("/api/presets")
    assert presets.status_code == 200
    assert len(presets.json()["presets"]) >= 3


def test_snr_endpoint_smoke() -> None:
    response = client.post(
        "/api/snr-from-time",
        json={
            "source": {"mode": "point", "spectral_type": "stellar_g2v", "magnitude": 20.0, "band": "r"},
            "config": {"n_steps": 64, "n_sigma": 256, "strategy": "probabilistic"},
            "t_total_s": 120.0,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["snr"]["wavelength_nm"]
    assert payload["stats"]["snr_max"] >= 0.0


def test_time_from_snr_endpoint_smoke() -> None:
    response = client.post(
        "/api/time-from-snr",
        json={
            "source": {"mode": "point", "spectral_type": "stellar_g2v", "magnitude": 20.0, "band": "r"},
            "config": {"n_steps": 64, "n_sigma": 256},
            "target_snr": 5.0,
            "ref_nm": 656.3,
        },
    )
    assert response.status_code == 200
    assert response.json()["t_total_s"] > 0.0


def test_observation_and_strategy_endpoints_smoke() -> None:
    body = {
        "source": {"mode": "point", "spectral_type": "hii_region", "line_flux": 0.02},
        "config": {"n_steps": 64, "n_sigma": 256, "R_energy_ref": 40.0},
    }
    rates = client.post("/api/observation-rates", json=body)
    assert rates.status_code == 200
    assert rates.json()["rates"]["source_rate_per_nm"]

    compare = client.post("/api/compare-strategies", json={**body, "t_total_s": 120.0})
    assert compare.status_code == 200
    assert compare.json()["ratio_prob_over_hard"]["ratio"]


def test_request_validation_rejects_bad_values() -> None:
    response = client.post(
        "/api/snr-from-time",
        json={
            "source": {"mode": "point", "spectral_type": "stellar_g2v"},
            "config": {"strategy": "not-a-strategy"},
            "t_total_s": -1.0,
        },
    )
    assert response.status_code == 422
