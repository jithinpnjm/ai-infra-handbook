import pandas as pd
from prophet import Prophet

def predict_capacity(historical_usage: pd.DataFrame, growth_periods: int = 90) -> pd.DataFrame:
    """Predict GPU capacity needs for the next growth_periods days."""
    model = Prophet(
        yearly_seasonality=True,
        weekly_seasonality=True,
        daily_seasonality=False,
    )
    model.fit(historical_usage)

    future = model.make_future_dataframe(periods=growth_periods)
    forecast = model.predict(future)

    return forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]]
