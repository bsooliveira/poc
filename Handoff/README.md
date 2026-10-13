# SimplFAQ Cursor Handoff

Pacote consolidado para implementar o SimplFAQ no Cursor com o mínimo de recontextualização possível.

## Comece aqui
**Leia primeiro `00_START_HERE.md`.** Ele contém as decisões fechadas, as proibições do MVP e a estratégia para reduzir consumo de contexto/créditos no Cursor.

## Arquitetura oficial do MVP
- VMs corporativas já existentes (pré-produção e produção)
- React + TypeScript + Vite
- Python + FastAPI
- Nginx + HTTPS
- Podman + Quadlet/systemd
- Microsoft Entra ID + grupo corporativo
- RAG/índice vetorial local ou recurso corporativo já existente
- B3 GPT como LLM principal
- Azure DevOps para CI/CD
- auditoria persistente
- revisão humana obrigatória

## Ordem de leitura sob demanda
1. `00_START_HERE.md`
2. `IMPLEMENTATION_PLAN.md`
3. `ARCHITECTURE.md`
4. `TECH_STACK.md`
5. `RULES_AND_GUARDRAILS.md`
6. `SCHEMAS.md`
7. `PROMPTS.md`
8. `BACKLOG.md`

Não é necessário reler todos os arquivos para cada tarefa. Consulte somente o documento relacionado ao trabalho atual.

## Apresentação visual
Abra `SIMPLFAQ_APRESENTACAO.html` no navegador para uma visão navegável do produto, fluxo e arquitetura.

## Segurança
Este pacote não contém credenciais, tokens, segredos ou dados reais de eventos.
