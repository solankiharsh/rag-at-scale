from config import Config

from platform_commons.metrics import Metrics

config = Config()

metrics = Metrics(
    enabled=config.metrics_enabled,
    dsn=config.metrics_dsn,
    blossom_id=config.blossom_id,
)
