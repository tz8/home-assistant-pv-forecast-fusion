"""Constants for PV Forecast Fusion."""

DOMAIN = "pv_forecast_fusion"

CONF_SOURCE_1_BIAS_FACTOR = "source_1_bias_factor"
CONF_SOURCE_1_CONFIDENCE = "source_1_confidence"
CONF_SOURCE_1_NAME = "source_1_name"
CONF_SOURCE_1_REMAINING_ENTITY = "source_1_remaining_entity"
CONF_SOURCE_1_TODAY_ENTITY = "source_1_today_entity"
CONF_SOURCE_1_TOMORROW_ENTITY = "source_1_tomorrow_entity"
CONF_SOURCE_1_WEIGHT = "source_1_weight"

CONF_SOURCE_2_BIAS_FACTOR = "source_2_bias_factor"
CONF_SOURCE_2_CONFIDENCE = "source_2_confidence"
CONF_SOURCE_2_NAME = "source_2_name"
CONF_SOURCE_2_REMAINING_ENTITY = "source_2_remaining_entity"
CONF_SOURCE_2_TODAY_ENTITY = "source_2_today_entity"
CONF_SOURCE_2_TOMORROW_ENTITY = "source_2_tomorrow_entity"
CONF_SOURCE_2_WEIGHT = "source_2_weight"

CONF_SOURCE_3_BIAS_FACTOR = "source_3_bias_factor"
CONF_SOURCE_3_CONFIDENCE = "source_3_confidence"
CONF_SOURCE_3_NAME = "source_3_name"
CONF_SOURCE_3_REMAINING_ENTITY = "source_3_remaining_entity"
CONF_SOURCE_3_TODAY_ENTITY = "source_3_today_entity"
CONF_SOURCE_3_TOMORROW_ENTITY = "source_3_tomorrow_entity"
CONF_SOURCE_3_WEIGHT = "source_3_weight"

DEFAULT_BIAS_FACTOR = 1.0
DEFAULT_CONFIDENCE = 1.0
DEFAULT_NAME = "PV Forecast Fusion"
DEFAULT_SCAN_INTERVAL_MINUTES = 15
DEFAULT_WEIGHT = 1.0
SOURCE_SLOTS = (1, 2, 3)
