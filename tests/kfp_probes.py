"""Manual integration probes; submit only against the lab's existing KFP API."""

from kfp import dsl
from kfp.dsl import Dataset, Input, Output

from pipelines.components import (
    MLFLOW_URI,
    PIPELINE_IMAGE,
    evaluate_model,
    ingest_data,
    prepare_features,
    register_model,
    train_model,
    validate_data,
)
from pipelines.scoring_pipeline import TRAIN


@dsl.component(base_image=PIPELINE_IMAGE, install_kfp_package=False)
def corrupt_input(raw: Input[Dataset], bad: Output[Dataset]):
    import pandas as pd

    from src.dataset_config import load_config

    cfg = load_config()
    pd.read_csv(raw.path).drop(columns=[cfg.features[0]]).to_csv(bad.path, index=False)


@dsl.pipeline(name="m2-gate-probe")
def gate_probe():
    raw = ingest_data()
    bad = corrupt_input(raw=raw.outputs["raw_data"])
    gate = validate_data(raw_data=bad.outputs["bad"])
    prepare_features(raw_data=bad.outputs["bad"]).after(gate)


@dsl.pipeline(name="m2-parallel-probe")
def parallel_probe():
    raw = ingest_data()
    gate = validate_data(raw_data=raw.outputs["raw_data"])
    prep = prepare_features(raw_data=raw.outputs["raw_data"]).after(gate)
    for label in ("A", "B"):
        train = train_model(
            raw_data=raw.outputs["raw_data"],
            train_data=prep.outputs["train_data"],
            test_data=prep.outputs["test_data"],
            model_type=TRAIN["model"],
            C=TRAIN["C"],
            class_weight=str(TRAIN["class_weight"]),
            n_estimators=TRAIN["n_estimators"],
            max_depth=str(TRAIN["max_depth"]),
            learning_rate=TRAIN["learning_rate"],
            random_state=TRAIN["random_state"],
            mlflow_uri=MLFLOW_URI,
            kfp_run_id=dsl.PIPELINE_JOB_ID_PLACEHOLDER,
        ).set_display_name(f"train_{label}")
        train.set_cpu_request("500m").set_cpu_limit("2")
        train.set_memory_request("512Mi").set_memory_limit("2Gi")
        train.set_caching_options(False)
        evaluation = evaluate_model(
            model=train.outputs["model"],
            test_data=prep.outputs["test_data"],
            run_id=train.outputs["Output"],
            mlflow_uri=MLFLOW_URI,
        )
        register_model(run_id=train.outputs["Output"], mlflow_uri=MLFLOW_URI).after(evaluation)
