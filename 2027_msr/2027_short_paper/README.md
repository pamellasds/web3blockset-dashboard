# MSR 2027 Short WIP — Atenção dos desenvolvedores no stack Web3

Análise **somente providers** do Web3BlockSet, usando `repository_category` já validada.

## Ideia (WIP)

A atenção observável em repositórios oficiais **migra entre camadas** (ranks mudam; composição do stack observável é instável) — mesmo quando a concentração top-3 diminui. Provocação contra tratar Web3 como domínio estável/homogêneo.

Resultado preliminar: ~361k docs, 378 repos, 33 categorias; top-3 share 52%→45% (2018→2025); risers incluem Development Platform e Wallet.

## Como rodar

Dados CSV: `../web3blockset/issues_prs.csv` e `repositories.csv`.

```bash
pip install -r requirements.txt
python analyze.py
```

Saídas:
- `data/processed/provider_attention.parquet`
- `results/tables/` e `results/figures/`
- `data/manual_review/blind_sample.csv` + `PROTOCOL_MANUAL_REVIEW.md`
- `paper/` — draft IEEE em português

## Estrutura

```
analyze.py                 # único script (prepare → analyze → plots → sample)
data/manual_review/        # amostra cega + protocolo
results/                   # tabelas e figuras
paper/                     # LaTeX IEEE
```
