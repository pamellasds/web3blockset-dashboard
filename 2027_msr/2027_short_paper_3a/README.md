# MSR 2027 Short WIP — Colaboração core vs occasional (3a)

Foco **apenas** na RQ3a: padrões de colaboração entre *core maintainers* e *occasional contributors* em repositórios **provider** do Web3BlockSet.

## Provocação

A “comunidade” observável em muitos projetos Web3 pode ser ilusória: poucos autores concentram a maior parte da atenção (Issues/PRs).

## Como rodar

Dados CSV: `../web3blockset/issues_prs.csv` e `repositories.csv`.

```bash
pip install -r requirements.txt
python analyze.py
cd paper && latexmk -pdf -interaction=nonstopmode main.tex
```

## Estrutura

```
analyze.py
data/manual_review/
results/
paper/main.pdf
```
