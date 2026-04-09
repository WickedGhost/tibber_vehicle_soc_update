from __future__ import annotations

DOMAIN = "tibber_vehicle_soc_update"

CONF_CAR_NAME = "car_name"
CONF_CURRENT_SOC = "current_soc"
CONF_EMAIL = "email"
CONF_CONFIG_ENTRY_ID = "config_entry_id"
CONF_HOME_ID = "home_id"
CONF_PASSWORD = "password"
CONF_SOC = "soc"
CONF_VEHICLE_ID = "vehicle_id"

DEFAULT_CURRENT_SOC = 0

APP_HEADERS = {
    "Accept-Language": "en",
    "Origin": "https://app.tibber.com",
    "Referer": "https://app.tibber.com/",
    "User-Agent": (
        "Tibber/25.20.0 "
        "(versionCode: 2520004Dalvik/2.1.0 "
        "(Linux; U; Android 10; Android SDK built for x86_64 "
        "Build/QSR1.211112.011))"
    ),
    "x-tibber-new-ui": "true",
}

TIBBER_GRAPHQL_URL = "https://app.tibber.com/v4/gql"
TIBBER_LOGIN_URL = "https://app.tibber.com/login.credentials"

SERVICE_SET_SOC = "set_soc"