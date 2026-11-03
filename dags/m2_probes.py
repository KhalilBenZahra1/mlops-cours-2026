"""Manual Lab 2 probes: isolated S3 prefixes, no schedule, no production data changes."""

from datetime import UTC, datetime

from airflow.sdk import DAG
from scoring_dag import stage

with DAG(
    dag_id="m2_debug_probe",
    schedule=None,
    start_date=datetime(2026, 1, 1, tzinfo=UTC),
    catchup=False,
    tags=["lab2", "probe"],
) as debug_probe:
    workspace = "s3://airflow-data/probes/missing-input/{{ run_id }}"
    bad = stage("validate_missing_input", "src.validate_data", workspace=workspace)
    blocked = stage("prepare_must_not_run", "src.prepare", workspace=workspace)
    bad >> blocked


with DAG(
    dag_id="m2_parallel_probe",
    schedule=None,
    start_date=datetime(2026, 1, 1, tzinfo=UTC),
    catchup=False,
    tags=["lab2", "probe"],
) as parallel_probe:
    for label in ("a", "b"):
        workspace = "s3://airflow-data/probes/parallel/{{ run_id }}/" + label
        ingest = stage("ingest_" + label, "src.download", workspace=workspace, retries=3)
        validate = stage("validate_" + label, "src.validate_data", workspace=workspace)
        prepare = stage("prepare_" + label, "src.prepare", workspace=workspace)
        train = stage("train_" + label, "src.train", workspace=workspace, xcom=True, memory="2Gi")
        evaluate = stage("evaluate_" + label, "src.evaluate", workspace=workspace, xcom=True)
        register = stage(
            "register_" + label,
            "src.promote",
            "--run-id",
            "{{ ti.xcom_pull(task_ids='train_" + label + "')['mlflow_run_id'] }}",
            workspace=workspace,
        )
        ingest >> validate >> prepare >> train >> evaluate >> register
