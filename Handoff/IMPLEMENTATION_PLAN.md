# SimpliFAQ — Plano de Implementação do MVP

## Marco 0 — Fundação
Critério de pronto:
- repositório organizado;
- front e back sobem localmente;
- health check;
- configuração por ambiente;
- sem segredos no código.

## Marco 1 — Acesso e shell da aplicação
Critério de pronto:
- React acessível atrás do Nginx;
- FastAPI acessível pelo mesmo host;
- Entra ID integrado;
- autorização por grupo;
- identidade do usuário disponível para auditoria.

## Marco 2 — Evento e uploads
Critério de pronto:
- criar execução/evento;
- aceitar quantidade variável de arquivos;
- validar formato/tamanho;
- persistir metadados;
- exibir status de processamento.

## Marco 3 — Ingestão e RAG
Critério de pronto:
- extrair texto;
- criar chunks;
- gerar embeddings;
- indexar localmente;
- separar fontes lógicas;
- recuperar por domínio com metadados;
- manter rastreabilidade.

## Marco 4 — Geração bilíngue
Critério de pronto:
- gerar PT/EN no mesmo ciclo;
- structured output;
- fontes associadas por item;
- marcar `requires_human_review`.

## Marco 5 — Validação
Critério de pronto:
- groundedness;
- conflito de fontes;
- equivalência PT/EN;
- deduplicação;
- regras de negócio.

## Marco 6 — Revisão humana e documento
Critério de pronto:
- tela de revisão;
- edição;
- aprovação/reprovação;
- geração DOCX;
- FAQ só entra no histórico após aprovação.

## Marco 7 — Operação
Critério de pronto:
- Podman + Quadlet/systemd;
- logs e auditoria;
- Azure DevOps;
- pré-prod;
- smoke tests;
- promoção controlada;
- rollback.

## Ordem para priorização em hackathon
Se o tempo apertar, preservar nesta ordem:
1. upload + ingestão;
2. RAG + geração PT/EN;
3. rastreabilidade;
4. revisão humana;
5. autenticação;
6. auditoria;
7. DOCX;
8. refinamentos visuais/evals avançados.
