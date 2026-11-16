# CDQAI file version: 2.5.1
from copy import deepcopy
from datetime import datetime

import pytest

from cdqai.core.config import CDQAIConfig, DEFAULT_CONFIG
from cdqai.main import _create_dated_output_directory, build_parser, main
from tools.ensure_dependencies import missing_requirements


def _config(tmp_path):
    raw = deepcopy(DEFAULT_CONFIG)
    raw["paths"]["outputs_dir"] = "outputs"
    (tmp_path / "outputs").mkdir()
    return CDQAIConfig(raw, tmp_path)


def test_dated_output_uses_requested_name_and_redirects_config(tmp_path):
    config = _config(tmp_path)

    output_dir = _create_dated_output_directory(
        config, datetime(2026, 11, 13, 15, 8)
    )

    assert output_dir == tmp_path / "outputs" / "test_run_live_11__13_2026_15-08"
    assert output_dir.is_dir()
    assert config.outputs_dir == output_dir


def test_dated_output_refuses_to_overwrite_an_existing_run(tmp_path):
    config = _config(tmp_path)
    run_time = datetime(2026, 11, 13, 15, 8)
    first = _create_dated_output_directory(config, run_time)

    config.raw["paths"]["outputs_dir"] = "outputs"
    with pytest.raises(FileExistsError):
        _create_dated_output_directory(config, run_time)

    assert first.is_dir()


def test_dated_output_option_is_only_valid_with_run_all():
    args = build_parser().parse_args(["--run-all", "--dated-output"])
    assert args.run_all
    assert args.dated_output

    with pytest.raises(SystemExit):
        main(["--dated-output"])


def test_dependency_check_selectively_identifies_missing_openpyxl():
    requirements = "pandas>=2.0\nopenpyxl>=3.1\n"

    missing = missing_requirements(
        requirements,
        module_exists=lambda module: module != "openpyxl",
    )

    assert missing == ["openpyxl>=3.1"]
