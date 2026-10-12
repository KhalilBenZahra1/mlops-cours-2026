# Mes notes du cours MLOps

## Reproduire le projet (Lab 1)
- Cloner le repo, puis `make up`, `make pf`, `uv sync` et `source .venv/bin/activate`.
- Configurer les identifiants du remote DVC localement :
  `dvc remote modify --local storage access_key_id mlops` et
  `dvc remote modify --local storage secret_access_key mlops-lab-secret`.
- Même cluster : `dvc pull` puis `dvc repro`.
- Remote vide : `dvc repro` puis `dvc push`.
