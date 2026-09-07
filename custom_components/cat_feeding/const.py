"""Constants for the Cat Feeding Tracker integration."""

DOMAIN = "cat_feeding"

CONF_DEFAULT_PORTION = "default_portion_g"
CONF_DAILY_TARGET = "daily_target_g"

DEFAULT_PORTION_G = 40
DEFAULT_DAILY_TARGET_G = 200
HISTORY_RETENTION_DAYS = 180

SERVICE_LOG_FEEDING = "log_feeding"
ATTR_AMOUNT = "amount_g"
ATTR_FOOD_TYPE = "food_type"
ATTR_NOTE = "note"

SIGNAL_UPDATE = f"{DOMAIN}_update_{{entry_id}}"
