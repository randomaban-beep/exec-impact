"""Skeleton and locked research-config checks."""

from __future__ import annotations

from exec_impact import __version__, load_config


def test_version() -> None:
    assert __version__ == "0.1.0"


def test_config_main_month(config: dict) -> None:
    assert config["month"] == "2024-01"
    assert config["robustness_month"] == "2024-07"
    assert config["run_robustness"] is False


def test_config_sigma_is_close_to_close(config: dict) -> None:
    assert config["sigma"]["method"] == "close_to_close_1m"
    assert config["bars"]["fill_empty_minutes"] is True
    assert config["bars"]["empty_return"] == 0.0
    assert config["sigma"]["intra_bar_diagnostic"] is True


def test_config_ac_value_match_child_slice(config: dict) -> None:
    lin = config["ac_linearization"]
    assert lin["match"] == "value"
    assert lin["ref_adv_frac"] == 0.1
    assert lin["ref_adv_frac_sensitivity"] == [0.05, 0.1, 0.5]


def test_config_seed_and_grid(config: dict) -> None:
    assert config["seed"] == 42
    assert len(config["lambda_grid"]) >= 6
    assert config["simulation"]["n_replay_starts"] >= 500
    assert config["grid"]["adv_frac"] == [0.01, 0.05, 0.1, 0.5, 1.0]


def test_load_config_default_path_matches_fixture(config: dict, repo_root) -> None:
    assert load_config(repo_root / "config.yaml") == config
