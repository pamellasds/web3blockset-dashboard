# MSR 2027 Short WIP — Bridge Web3BlockSet × GitSkills

**Provocação:** skills de agents falam muito em verificação genérica, mas quase não cobrem preocupações que dominam a prática em consensus/spec/clients Ethereum — gap útil para agentes que traduzem cláusulas de spec em propriedades formais.

## Dados
- Web3BlockSet: `../web3blockset/` (CSVs)
- GitSkills: `../../gitskills/` (a partir de `2026_web3blockset_dashboard`)

## Rodar
```bash
pip install -r requirements.txt
python analyze.py
cd paper && latexmk -pdf -interaction=nonstopmode main.tex
```
