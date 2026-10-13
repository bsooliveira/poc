# SimplFAQ — Backlog inicial

## Epic 1 — Ingestão
- [ ] Upload/entrada de documentos
- [ ] Extração de texto
- [ ] Normalização
- [ ] Identificação de tipo de fonte
- [ ] Metadados
- [ ] Versionamento

## Epic 2 — Indexação
- [ ] Chunking configurável
- [ ] Embeddings
- [ ] Índice vetorial
- [ ] Separação lógica das fontes
- [ ] Filtros por metadados

## Epic 3 — Retrieval
- [ ] Busca por domínio
- [ ] Top-k
- [ ] Threshold
- [ ] Reranking
- [ ] Priorização da fonte atual

## Epic 4 — Orquestração
- [ ] Classificação de domínios
- [ ] Detecção de lacunas
- [ ] Detecção de conflitos
- [ ] Detecção de duplicidades

## Epic 5 — Geração
- [ ] Structured output
- [ ] PT/EN simultâneo
- [ ] Referências às fontes
- [ ] Few-shot com FAQ aprovada

## Epic 6 — Validação
- [ ] Groundedness
- [ ] Equivalência PT/EN
- [ ] Validação de regras
- [ ] Marcação de revisão humana

## Epic 7 — Consolidação
- [ ] Organização por domínio
- [ ] Deduplicação
- [ ] Padronização
- [ ] Geração de documento

## Epic 8 — Aprovação e Feedback
- [ ] Workflow de revisão humana
- [ ] Aprovação
- [ ] Reindexação somente após aprovação

## Epic 9 — Evals
- [ ] Dataset de eventos históricos
- [ ] Métrica de cobertura
- [ ] Precisão factual
- [ ] Aderência às fontes
- [ ] Qualidade do inglês
- [ ] Equivalência PT/EN
- [ ] Taxa de intervenção humana

## Epic 10 — Segurança, acesso e operação
- [ ] Autenticação Microsoft Entra ID
- [ ] Autorização por grupo corporativo
- [ ] Nginx + HTTPS/certificado corporativo
- [ ] Headers de segurança e limites de upload
- [ ] Auditoria persistente de ações e execuções
- [ ] Tratamento seguro de segredos/configurações
- [ ] Health checks

## Epic 11 — Empacotamento e CI/CD
- [ ] Containers compatíveis com Podman
- [ ] Quadlet/systemd
- [ ] Pipeline Azure DevOps
- [ ] Deploy automático em pré-produção
- [ ] Promoção controlada para produção
- [ ] Rollback por versão
- [ ] Smoke tests pós-deploy
