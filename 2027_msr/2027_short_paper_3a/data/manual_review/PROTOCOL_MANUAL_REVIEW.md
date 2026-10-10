# Protocolo de Validação Manual (cega) — Papéis de Colaboração (3a)

Valida a heurística automática de **core vs occasional** (top 10% dos autores por Issues/PRs abertos no repositório).

## Objetivo

Julgar, para cada autor amostrado, se o papel automático faz sentido à luz da atividade pública no GitHub.

## Arquivos

| Arquivo | Quem usa |
|---|---|
| `blind_sample.csv` | Revisores (sem label `role` / categoria) |
| `key_mapping.csv` | Só a autora |
| `stratum_counts.csv` | Auditoria |

Estratificação: `repository_category × role` automático (até 8 por estrato; seed `20270303`).

## Passo a passo

Para cada `review_id`:

1. Veja `repo_key`, `author`, `n_docs_opened`, `example_titles`.
2. Opcional: abra `https://github.com/{repo_key}` e o perfil do autor.
3. **Não** consulte `key_mapping.csv`.
4. Preencha:

### `inferred_role`
- `core_maintainer` — maintainer/membro frequente, alta responsabilidade aparente
- `regular` — contribui com recorrência, mas não parece núcleo
- `occasional` — contribuições esparsas / one-off
- `bot_or_automation` — bot ou conta automatizada
- `unsure`

### `is_org_affiliated`
`yes` / `no` / `unsure` — se o autor parece afiliado à organização dona do repo.

### `evidence` / `notes` / `reviewer_id`
Trecho ou observação curta; id do revisor.

## Acordo
Dois revisores quando possível; Cohen’s κ em `inferred_role` (agrupar `regular` com `occasional` se necessário para κ binário core vs não-core).

## Depois
Join com `key_mapping.csv` → precisão da heurística 80%-mass; reportar no paper.
