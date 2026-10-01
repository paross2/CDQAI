# CDQAI file version: 2.3.6
from cdqai.core.config import load_config
from cdqai.core.build_info import VERSION
from cdqai.core.config import apply_application_metadata


def test_config_loads():
    config = load_config()
    assert config.short_name == "CDQAI"
    assert config.version == VERSION


def test_stale_local_version_cannot_override_running_code():
    raw = apply_application_metadata({"project": {"version": "0.0.1"}})
    assert raw["project"]["version"] == VERSION
