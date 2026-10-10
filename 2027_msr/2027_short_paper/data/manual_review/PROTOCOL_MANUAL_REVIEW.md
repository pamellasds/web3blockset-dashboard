# Protocolo de Validação Manual (cega) — Construto de Atenção

As **categorias de repositório** já foram validadas no Web3BlockSet (acordo 92,4%) e **não** devem ser relabeladas aqui.

Esta revisão valida se Issues/PRs dos **providers** são um proxy razoável de **atenção de desenvolvimento** (em oposição a ruído / off-topic).

## Objetivo

Para cada documento da amostra, julgar:

1. O item reflete atenção de desenvolvimento no repositório?
2. Que tipo de atenção (manutenção, feature, bug, suporte, docs…)?

## Arquivos

| Arquivo | Quem usa |
|---|---|
| `blind_sample.csv` | Revisores (sem `repository_category`) |
| `key_mapping.csv` | Só a autora — contém a categoria (**não enviar**) |
| `stratum_counts.csv` | Auditoria da estratificação |

A amostra é estratificada por `repository_category` validada (até 10 itens/categoria; seed `20270227`), depois embaralhada.

## Passo a passo

Para cada `review_id`:

1. Leia `issue_title`, `type`, `labels`, `owner/repository`.
2. Se precisar de contexto, abra o Issue/PR no GitHub.
3. **Não** tente adivinhar nem consultar a categoria automática.
4. Preencha as colunas abaixo.

### `is_development_attention`
- `yes` — bugfix, feature, refatoração, infra de build/CI, docs técnicas do projeto, design de API do provider.
- `no` — spam, off-topic, mensagem vazia/sem sentido, conteúdo claramente não relacionado ao desenvolvimento.
- `unsure` — ambíguo (ex.: só “thanks”, thread sem corpo).

### `attention_kind` (se `yes` ou `unsure`)
Use um de:
`maintenance` | `feature` | `bugfix` | `support_question` | `docs` | `other`

Notas:
- Pergunta de usuário no repo oficial → `support_question` (ainda conta como atenção se for sobre o produto).
- PR de correção → `bugfix` ou `maintenance`.

### `evidence_span`
Trecho curto (≤200 caracteres) ou `n/a`.

### `notes` / `reviewer_id`
Dúvidas e id do revisor (`R1`, `R2`).

## Dupla anotação

- Ideal: 2 revisores; overlap ≥30%.
- Reportar % acordo e Cohen’s κ em `is_development_attention`.
- Consenso → `annotations_FINAL.csv`.

## Depois (autora)

1. Join com `key_mapping.csv` via `review_id`.
2. Reportar no paper: % `yes` global e por categoria (sem expor o processo de cegamento como se a categoria fosse nova).
3. Não reamostrar após ver os números.

## Tempo
~1 min/caso → ~2–3 h para amostra típica (~150–200 itens).
