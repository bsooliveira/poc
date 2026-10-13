# SimplFAQ — START HERE (Cursor)

> Leia este arquivo primeiro. Ele contém as decisões já fechadas. Não reabra essas decisões sem solicitação explícita.

## Objetivo
Construir o SimplFAQ: aplicação web interna para gerar uma primeira versão avançada de FAQs/relatórios de perguntas e respostas sobre eventos corporativos, em **português e inglês no mesmo ciclo**, com rastreabilidade e revisão humana obrigatória.

## Stack fechada do MVP
- Infraestrutura: **VMs corporativas existentes** de pré-produção e produção
- Front-end: **React + TypeScript + Vite**
- Back-end: **Python + FastAPI**
- Reverse proxy/TLS: **Nginx**
- Containers: **Podman**
- Lifecycle: **Quadlet/systemd**
- Autenticação: **Microsoft Entra ID**
- Autorização: **grupo corporativo**
- CI/CD: **Azure DevOps → pré-prod → produção**
- IA: **B3 GPT** como LLM principal; manter adapter para troca de provedor
- RAG: **local na infraestrutura existente** ou tecnologia corporativa já disponível
- Documento final: **python-docx**
- Auditoria: persistente e obrigatória
- Publicação: sempre com **human-in-the-loop**

## NÃO fazer no MVP
- Não propor nova infraestrutura Azure como dependência.
- Não trocar Podman por Docker.
- Não introduzir Kubernetes.
- Não criar microserviços sem necessidade.
- Não introduzir framework pesado de agentes sem necessidade concreta.
- Não usar fine-tuning como requisito inicial.
- Não publicar FAQ automaticamente.
- Não permitir que histórico sobrescreva fonte factual do evento atual.

## Uploads
A quantidade de arquivos é **variável**. Um evento pode ter 2–3 arquivos; outro pode ter vários.
Todos os arquivos do evento entram na ingestão e podem contribuir para o contexto, conforme tipo, metadados e prioridade de fonte.

## Fontes lógicas do RAG
1. **Evento atual** — fonte factual principal.
2. **FAQs históricas aprovadas** — referência de casos, cobertura e estrutura.
3. **Referências linguísticas** — glossário, estilo e padrão de inglês.

## Prioridade factual
1. Documento/fonte oficial do evento atual
2. Dados estruturados do evento atual
3. Transcrição da reunião atual
4. Regras internas aplicáveis
5. FAQs históricas aprovadas
6. Referências linguísticas

## Fluxo obrigatório
Upload → ingestão → extração/normalização → chunking/metadados → embeddings/indexação → classificação por domínio → retrieval → reranking → geração PT/EN simultânea → groundedness → equivalência PT/EN → deduplicação/consolidação → documento final → revisão humana → aprovação → somente então reindexar a nova FAQ no histórico.

## Papel do B3 GPT
Usar para:
- classificação por domínio;
- identificação de cobertura;
- geração PT/EN;
- detecção de lacunas, conflitos e duplicidades;
- apoio à validação.

Não usar como:
- repositório de documentos;
- fonte factual isolada;
- decisor final em tema crítico/regulatório.

## Segurança e auditoria
Registrar no mínimo:
- usuário;
- timestamp;
- evento;
- arquivos carregados;
- início/fim/falha;
- versão do modelo;
- versão do prompt;
- chunks/fontes utilizados;
- validações;
- edições humanas;
- aprovação/reprovação;
- geração/download do documento.

## Como trabalhar no Cursor com baixo consumo
1. Leia este arquivo uma vez.
2. Antes de codificar, consulte apenas o arquivo específico da tarefa:
   - arquitetura → `ARCHITECTURE.md`
   - stack/deploy → `TECH_STACK.md`
   - segurança → `RULES_AND_GUARDRAILS.md`
   - contratos → `SCHEMAS.md`
   - IA/prompts → `PROMPTS.md`
   - trabalho pendente → `BACKLOG.md`
3. Não releia todo o pacote a cada mudança.
4. Faça alterações pequenas e focadas.
5. Não refatore módulos fora do escopo sem necessidade.
6. Reutilize decisões já tomadas; não gere novas alternativas de arquitetura.
7. Ao terminar uma tarefa, informe somente:
   - arquivos alterados;
   - testes executados;
   - riscos/pendências reais.

## Primeira sequência de implementação
1. Estrutura do repositório.
2. FastAPI mínimo + health check.
3. React/Vite mínimo.
4. Nginx local.
5. Containerização Podman.
6. Autenticação Entra ID.
7. Upload variável de arquivos.
8. Ingestão/extrator.
9. Persistência/metadados/auditoria.
10. RAG local.
11. Adapter B3 GPT.
12. Geração bilíngue estruturada.
13. Validações.
14. Revisão/aprovação.
15. DOCX.
16. Pipeline Azure DevOps.
17. Deploy pré-prod + smoke tests.
