# CDQAI file version: 2.3.6
import os
# Runtime model assets must be installed separately before processing protected inputs.
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
from cdqai.core.build_info import PROJECT_NAME as __project_name__
from cdqai.core.build_info import RELEASE_NAME as __milestone__
from cdqai.core.build_info import SHORT_NAME as __short_name__
from cdqai.core.build_info import VERSION as __version__
