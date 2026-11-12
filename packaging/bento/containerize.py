"""Containeriser le Bento du cours avec reprises APT pour le réseau WSL.

Usage : uv run python packaging/bento/containerize.py scoring_bento:<version>

BentoML 1.4.39 génère intégralement le contexte, modèle compris. Seule sa
commande APT est adaptée (HTTPS, délais, retries), après l'échec HTTP observé.
Le générateur interne est lié à cette version ; les instructions restantes,
les paquets, le service et l'utilisateur BentoML restent inchangés.
"""

import argparse
import subprocess
from importlib.metadata import version
from pathlib import Path

import bentoml
from bentoml._internal.container import construct_containerfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bento", help="Tag exact du Bento construit")
    parser.add_argument("--tag", default="scoring-api:bentoml")
    args = parser.parse_args()
    if version("bentoml") != "1.4.39":
        raise SystemExit("Ce correctif de transport est vérifié pour BentoML 1.4.39.")
    if (
        subprocess.run(["docker", "image", "inspect", args.tag], capture_output=True).returncode
        == 0
    ):
        raise SystemExit("Le tag existe déjà : inspecter l'image avant de le remplacer.")

    bento = bentoml.get(args.bento)
    with construct_containerfile(bento) as (context, dockerfile):
        path = Path(dockerfile)
        text = path.read_text()
        original = (
            "RUN  apt-get update && apt-get install -q -y --no-install-recommends "
            "--allow-remove-essential ca-certificates gnupg2 bash build-essential git"
        )
        if text.count(original) != 1:
            raise SystemExit("Commande APT BentoML inattendue : aucune modification appliquée.")
        configure = (
            'python -c "from pathlib import Path; '
            "p=Path('/etc/apt/sources.list.d/debian.sources'); "
            "p.write_text(p.read_text().replace('http://deb.debian.org','https://deb.debian.org'))"
            '"'
        )
        apt = "apt-get -o Acquire::Retries=10 -o Acquire::https::Timeout=180"
        replacement = (
            f"RUN {configure} && {apt} update && {apt} install "
            "-q -y --no-install-recommends --allow-remove-essential "
            "ca-certificates gnupg2 bash build-essential git"
        )
        path.write_text(text.replace(original, replacement))
        subprocess.run(
            ["docker", "build", "--progress=plain", "-f", dockerfile, "-t", args.tag, context],
            check=True,
        )


if __name__ == "__main__":
    main()
