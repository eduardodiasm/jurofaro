#!/usr/bin/env bash
# Dados inteiramente fictícios. Execute com: bash examples/run.sh
set -euo pipefail
cd "$(dirname "$0")/.."
cli=.venv/bin/jurofaro
if [ ! -x "$cli" ]; then
  echo 'Instale primeiro: python3 -m venv .venv && .venv/bin/python -m pip install -e .' >&2
  exit 1
fi
mkdir -p results
for system in SAC PRICE; do
  "$cli" simulate --property-price 500000 --down-payment 100000 \
    --annual-rate 12 --months 360 --system "$system" --format json \
    > "results/financiamento-${system}.json"
  "$cli" compare --property-price 500000 --down-payment 100000 \
    --annual-rate 12 --months 360 --system "$system" \
    --rent 2500 --investment-return 8 --property-growth 4 --rent-growth 4 \
    --purchase-cost 4 --sale-cost 6 --owner-cost 1 --horizon-months 120 --monthly-budget 6000 \
    --format json > "results/comparacao-${system}.json"
done
# Sensibilidade: mesma entrada/imóvel, juros menores. Não representa oferta real.
"$cli" compare --property-price 500000 --down-payment 100000 \
  --annual-rate 10 --months 360 --system SAC \
  --rent 2500 --investment-return 8 --property-growth 4 --rent-growth 4 \
  --purchase-cost 4 --sale-cost 6 --owner-cost 1 --horizon-months 120 --monthly-budget 6000 \
  --format json > results/comparacao-SAC-juros10.json
.venv/bin/python - <<'PY'
import json
from pathlib import Path
print('Cenário | Patrimônio comprador | Patrimônio locatário | Diferença (R$)')
for path in sorted(Path('results').glob('comparacao-*.json')):
    report = json.loads(path.read_text())
    values = report['summary']
    print(f"{path.stem} | {values['buyer_wealth']:.2f} | {values['renter_wealth']:.2f} | {values['wealth_difference']:.2f}")
print('Premissas e cronogramas completos em results/*.json')
PY
