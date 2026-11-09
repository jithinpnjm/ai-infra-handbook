# Feast feature view. Feast is not installed in the test environment: this file is syntax- and structure-checked only.
from datetime import timedelta
from feast import FeatureView, Field, BigQuerySource
from feast.types import Float32, Int64
from entities import user

user_features_source = BigQuerySource(table="project.churn.user_features_v3", timestamp_field="event_timestamp")

user_features = FeatureView(
    name="user_features",
    entities=[user],
    ttl=timedelta(days=90),
    schema=[
        Field(name="tier_gold", dtype=Float32),
        Field(name="tenure_days", dtype=Int64),
        Field(name="avg_session_minutes_30d", dtype=Float32),
    ],
    source=user_features_source,
    online=True,
)
