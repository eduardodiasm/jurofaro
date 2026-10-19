#!/usr/bin/env python3
"""Execute o motor deste clone sem instalação, a partir de qualquer diretório."""

import sys
from pathlib import Path


def main() -> int:
    if sys.version_info < (3, 11):
        print("Erro: a skill JuroFaro requer Python 3.11 ou superior.", file=sys.stderr)
        return 2
    # resolve também segue o symlink da skill instalada em ~/.agents/skills.
    repo = Path(__file__).resolve().parents[4]
    src = repo / "src"
    if not (src / "jurofaro" / "cli.py").is_file():
        print(
            "Erro: motor JuroFaro não encontrado. Mantenha o clone completo e "
            "use a skill nele, ou um link simbólico para a pasta original da skill.",
            file=sys.stderr,
        )
        return 2
    sys.path.insert(0, str(src))
    from jurofaro.cli import main as cli_main

    return cli_main()


if __name__ == "__main__":
    raise SystemExit(main())
