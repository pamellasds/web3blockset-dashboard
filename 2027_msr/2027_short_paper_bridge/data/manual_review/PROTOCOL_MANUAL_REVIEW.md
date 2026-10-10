# Protocolo cego — candidatos a propriedades (consensus practice)

Amostra estratificada por `concern_bucket` automático (Web3BlockSet).  
Objetivo: esboçar propriedades verificáveis / componentes da spec — **não** relabelar categorias de repo.

## Colunas

| Campo | Valores |
|---|---|
| `maps_to_spec_component` | `fork_choice` \| `finality` \| `attestation` \| `state_transition` \| `networking` \| `other` \| `unsure` |
| `property_sketch` | 1–2 frases: safety / liveness / reachability (mesmo informal) |
| `is_verification_relevant` | `yes` \| `no` \| `unsure` |
| `notes` / `reviewer_id` | livre |

## Passos
1. Leia título + abra o Issue/PR se precisar.
2. Não consulte `key_mapping.csv`.
3. Se for bug de tooling/CI sem relação com spec → `is_verification_relevant=no`.
4. Se puder esboçar propriedade (“nunca dois heads finalizados…”) → preencha `property_sketch`.

## Depois
Join com `key_mapping.csv` → precisão dos buckets + backlog de propriedades para agentes/BMC.
