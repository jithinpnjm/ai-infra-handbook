"""Great Expectations 1.x: validate a cleaned churn DataFrame. Tested with great_expectations 1.24."""
import great_expectations as gx
import pandas as pd

def validate(df: pd.DataFrame, project_dir: str = "./gx") -> bool:
    context = gx.get_context(mode="file", project_root_dir=project_dir)
    suite = context.suites.add_or_update(gx.ExpectationSuite(name="churn_clean_suite"))
    suite.add_expectation(gx.expectations.ExpectColumnValuesToNotBeNull(column="user_id", mostly=1.0))
    suite.add_expectation(gx.expectations.ExpectColumnValueLengthsToBeBetween(column="tier", min_value=1, max_value=16))
    suite.add_expectation(gx.expectations.ExpectTableRowCountToBeBetween(min_value=2, max_value=10_000_000))
    suite.save()

    source = context.data_sources.add_or_update_pandas(name="churn")
    asset = source.add_dataframe_asset(name="churn_clean")
    batch_def = asset.add_batch_definition_whole_dataframe("whole")
    batch = batch_def.get_batch(batch_parameters={"dataframe": df})
    return bool(batch.validate(suite).success)

if __name__ == "__main__":
    df = pd.read_parquet("churn_clean.parquet")
    if not validate(df):
        raise SystemExit("DATA VALIDATION FAILED")
