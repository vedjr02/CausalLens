"""API-level tests for the synthetic experiment endpoints."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _binary_body(**overrides):
    config = {
        "metric_type": "binary",
        "baseline_rate": 0.10,
        "true_effect": 0.0,
        "n_per_group": 2000,
        "seed": 42,
    }
    config.update(overrides.pop("config", {}))
    body = {"config": config, "alpha": 0.05, "run_validation": False}
    body.update(overrides)
    return body


class TestSyntheticRun:
    def test_binary_run_returns_truth_test_and_comparison(self) -> None:
        response = client.post("/api/experiment/synthetic", json=_binary_body())
        assert response.status_code == 200

        body = response.json()
        assert body["ground_truth"]["is_null"] is True
        assert body["test"]["test"] == "two_proportion_z"
        assert body["comparison"]["true_absolute_effect"] == 0.0
        # Binary metrics have no histogram — the rate is the whole story.
        assert body["distributions"] is None

    def test_continuous_run_uses_welch_and_returns_histograms(self) -> None:
        response = client.post(
            "/api/experiment/synthetic",
            json={
                "config": {
                    "metric_type": "continuous",
                    "baseline_mean": 100.0,
                    "std_dev": 20.0,
                    "true_effect": 5.0,
                    "n_per_group": 800,
                    "seed": 7,
                },
                "run_validation": False,
            },
        )
        assert response.status_code == 200

        body = response.json()
        assert body["test"]["test"] == "welch_t"
        assert body["test"]["degrees_of_freedom"] is not None
        assert len(body["distributions"]) == 2
        # Both groups must share bin edges to be honestly comparable.
        control, treatment = body["distributions"]
        assert [b["start"] for b in control["bins"]] == [b["start"] for b in treatment["bins"]]

    def test_response_never_carries_a_bare_p_value(self) -> None:
        body = client.post("/api/experiment/synthetic", json=_binary_body()).json()
        effect = body["test"]["effect"]
        assert effect["absolute_interval"]["lower"] < effect["absolute_interval"]["upper"]
        assert body["test"]["assumptions"]
        assert body["test"]["interpretation"]

    def test_seed_makes_the_whole_run_reproducible(self) -> None:
        first = client.post("/api/experiment/synthetic", json=_binary_body()).json()
        second = client.post("/api/experiment/synthetic", json=_binary_body()).json()
        assert first["test"]["p_value"] == second["test"]["p_value"]

    def test_validation_runs_when_asked(self) -> None:
        response = client.post(
            "/api/experiment/synthetic",
            json=_binary_body(run_validation=True, replications=500),
        )
        validation = response.json()["validation"]
        assert validation["replications"] == 500
        assert validation["label"] == "False positive rate"
        assert validation["is_null"] is True

    def test_impossible_effect_is_rejected_with_a_readable_message(self) -> None:
        response = client.post(
            "/api/experiment/synthetic",
            json=_binary_body(config={"baseline_rate": 0.95, "true_effect": 0.10}),
        )
        assert response.status_code == 422
        assert "not a valid probability" in str(response.json()["detail"])

    def test_alpha_must_be_a_probability(self) -> None:
        assert client.post("/api/experiment/synthetic", json=_binary_body(alpha=0)).status_code == 422
        assert client.post("/api/experiment/synthetic", json=_binary_body(alpha=1)).status_code == 422


class TestGroundTruthComparison:
    def test_detecting_a_real_effect_reads_as_a_correct_call(self) -> None:
        body = client.post(
            "/api/experiment/synthetic",
            json=_binary_body(
                config={"baseline_rate": 0.10, "true_effect": 0.05, "n_per_group": 20000},
                run_validation=False,
            ),
        ).json()

        assert body["test"]["significant"] is True
        assert body["comparison"]["conclusion_is_correct"] is True
        assert "Correct call" in body["comparison"]["verdict"]

    def test_missing_a_real_effect_is_named_a_false_negative(self) -> None:
        """A genuine effect too small for the sample: the honest answer is
        'not enough data', never 'no effect'."""
        body = client.post(
            "/api/experiment/synthetic",
            json=_binary_body(
                config={
                    "baseline_rate": 0.10,
                    "true_effect": 0.001,
                    "n_per_group": 200,
                    "seed": 3,
                },
                run_validation=False,
            ),
        ).json()

        assert body["test"]["significant"] is False
        assert body["comparison"]["conclusion_is_correct"] is False
        assert "false negative" in body["comparison"]["verdict"]
        assert "never means 'no effect'" in body["comparison"]["verdict"]


class TestValidateEndpoint:
    def test_null_config_reports_false_positive_rate_near_alpha(self) -> None:
        response = client.post(
            "/api/experiment/validate",
            json={
                "config": {
                    "metric_type": "binary",
                    "baseline_rate": 0.10,
                    "true_effect": 0.0,
                    "n_per_group": 2000,
                    "seed": 2024,
                },
                "alpha": 0.05,
                "replications": 5000,
            },
        )
        assert response.status_code == 200

        body = response.json()
        assert body["within_expectation"] is True
        assert abs(body["rejection_rate"] - 0.05) < 0.015

    def test_replication_count_is_capped(self) -> None:
        response = client.post(
            "/api/experiment/validate",
            json={
                "config": {
                    "metric_type": "binary",
                    "baseline_rate": 0.1,
                    "n_per_group": 100,
                },
                "replications": 999_999,
            },
        )
        assert response.status_code == 422
