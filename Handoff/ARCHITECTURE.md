# SimplFAQ — Arquitetura Conceitual

## Premissa
O MVP deve operar nas VMs corporativas já existentes de pré-produção e produção, sem depender da criação de novos recursos Azure.

## Componentes
### 1. Access Layer
- Nginx/HTTPS;
- autenticação via Entra ID;
- autorização por grupo/perfil corporativo.

### 2. Front-end
React + TypeScript para upload, acompanhamento, resultado, revisão e histórico.

### 3. Ingestion Layer
Responsável por receber arquivos, extrair texto, normalizar conteúdo e gerar metadados.

### 4. Knowledge Preparation
- chunking;
- embeddings;
- indexação local;
- versionamento.

### 5. Retrieval Layer
Coleções lógicas separadas:
- `event_current`
- `faq_history_approved`
- `language_guidelines`

Suportar:
- vector search;
- filtros por metadados;
- top-k;
- score mínimo;
- reranking;
- rastreabilidade dos chunks.

### 6. Orchestration Layer
B3 GPT / LLM como apoio para:
- classificação;
- seleção de domínios;
- geração;
- consolidação;
- identificação de conflitos e lacunas.

### 7. Generation Layer
Gerar PT e EN simultaneamente, a partir das mesmas evidências.
Saída estruturada e rastreável.

### 8. Validation Layer
- groundedness;
- cobertura;
- conflito de fontes;
- equivalência PT/EN;
- duplicidade;
- regras de negócio.

### 9. Review Layer
Human-in-the-loop obrigatório.

### 10. Audit Layer
Registrar usuário, datas, ações, execuções, versões, fontes utilizadas, validações e decisões humanas.

### 11. Feedback Layer
FAQ somente entra no histórico após aprovação humana.

## Princípio de precedência das fontes
1. Documento/fonte oficial do evento atual.
2. Dados estruturados do evento atual.
3. Transcrição da reunião atual.
4. Regras internas aplicáveis.
5. FAQs históricas aprovadas.
6. Referências linguísticas.

Histórico nunca deve superar fonte factual do evento atual.

## Runtime e deploy
- Podman nas VMs existentes;
- Quadlet/systemd para lifecycle;
- Azure DevOps para CI/CD;
- pré-produção antes da promoção para produção;
- rollback por versão de imagem.

## Separação recomendada de responsabilidades
- `auth/`
- `ingestion/`
- `retrieval/`
- `orchestration/`
- `generation/`
- `validation/`
- `audit/`
- `output/`
- `evaluation/`
- `common/`
