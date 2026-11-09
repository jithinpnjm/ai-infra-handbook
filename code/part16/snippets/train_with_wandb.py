import wandb

wandb.init(
    project="churn",
    name=f"churn-{args.dataset_id[:8]}-{args.seed}",
    config={
        "seed": args.seed,
        "n_estimators": 200,
        "dataset_id": args.dataset_id,
        "data_hash": data_hash,
        "code_commit": commit,
    },
    tags=["candidate", f"data-{data_hash[:8]}"],
)

wandb.log({"auc": auc})
wandb.log_model(path="model.pkl", name="churn-model")
