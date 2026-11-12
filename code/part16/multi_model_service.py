import bentoml
import joblib
from bentoml.models import BentoModel


@bentoml.service(
    resources={"cpu": "2", "memory": "4Gi"},
)
class MultiModelService:
    # Declared at class scope so the Bento packages both models.
    ref_a = BentoModel("model_a:latest")
    ref_b = BentoModel("model_b:latest")

    def __init__(self):
        # BentoModel gives a model reference, not a model. Load the real
        # object from the stored files yourself.
        self.models = {
            "model_a": joblib.load(self.ref_a.path_of("model.pkl")),
            "model_b": joblib.load(self.ref_b.path_of("model.pkl")),
        }

    @bentoml.api
    def predict(self, rows: list[list[float]], model_name: str) -> list:
        if model_name not in self.models:
            raise ValueError(f"unknown model: {model_name}")
        return self.models[model_name].predict(rows).tolist()
