# SimpliFAQ — Stack Tecnológica Recomendada

## Contexto
O SimpliFAQ nasce como iniciativa de hackathon com time multifuncional e sem desenvolvedor dedicado. O objetivo é entregar um MVP completo, simples de sustentar e evoluir, reutilizando infraestrutura já existente.

## Premissa de infraestrutura
**Não criar novos recursos Azure como dependência do MVP.**

A aplicação deve utilizar as VMs corporativas já existentes de pré-produção e produção.

## Front-end
**React + TypeScript + Vite**

Responsabilidades principais:
- login/acesso à aplicação;
- upload de arquivos;
- acompanhamento do processamento;
- visualização da FAQ por domínio;
- exibição PT/EN lado a lado;
- apresentação de alertas e fontes;
- revisão humana;
- download do documento final.

## Back-end
**Python + FastAPI**

Responsabilidades principais:
- APIs da aplicação;
- autenticação/autorização integrada;
- ingestão e processamento;
- RAG;
- orquestração do B3 GPT/OpenAI;
- validações;
- auditoria;
- geração do documento final.

## Execução em containers
**Podman** é o runtime oficial do projeto.

Não tratar Docker como dependência.

Recomendações:
- containers rootless, quando permitido;
- Quadlet/systemd para lifecycle;
- restart automático;
- health checks;
- imagens versionadas por release;
- rollback para imagem anterior;
- configuração e segredos fora da imagem.

## Reverse proxy / HTTPS
**Nginx** na VM, na frente do front-end e da API.

Responsabilidades:
- TLS/HTTPS com certificado corporativo;
- hostname corporativo, por exemplo `simplifaq.br.b3.com.br`;
- reverse proxy;
- headers de segurança;
- limite de tamanho de upload;
- timeouts adequados ao processamento.

## Autenticação e autorização
**Microsoft Entra ID** usando o domínio corporativo existente.

Requisitos:
- acesso somente a usuários autenticados;
- autorização preferencialmente por grupo corporativo;
- princípio de menor privilégio;
- não manter senha local na aplicação;
- registrar usuário/identidade nas ações auditáveis.

## Pipeline de IA
Implementar em Python, modularizado em:
- ingestion;
- retrieval;
- orchestration;
- generation;
- validation;
- evaluation.

Evitar frameworks pesados de agentes no início. Usar código explícito e modular.

## RAG / busca local
O RAG deve funcionar **localmente na infraestrutura existente**, sem exigir Azure AI Search.

Opções adequadas para o MVP:
- PostgreSQL + pgvector, se já houver PostgreSQL disponível ou puder ser executado na VM;
- índice vetorial local compatível com Python, caso a necessidade seja menor.

Requisitos:
- busca vetorial;
- filtros por metadados;
- separação lógica entre evento atual, histórico aprovado e referências linguísticas;
- reranking;
- rastreabilidade dos chunks usados.

## LLM
**B3 GPT** como opção principal, via interface/API corporativa existente.

Caso necessário, OpenAI/Azure OpenAI pode ser usado como motor externo, mas a aplicação deve manter uma camada de abstração para troca do provedor/modelo.

O LLM não é o repositório de documentos. Ele recebe o contexto recuperado pelo RAG e executa classificação, geração e validações assistidas.

## Armazenamento
Preferir recursos já disponíveis na VM/ambiente corporativo.

Separar logicamente:
- arquivos originais;
- artefatos temporários;
- metadados;
- índice vetorial;
- histórico aprovado;
- resultados finais;
- trilha de auditoria.

## Geração de Word
**python-docx**, preferencialmente usando um template corporativo DOCX quando disponível.

## Observabilidade e auditoria
Registrar no mínimo:
- usuário;
- timestamp;
- evento/processamento;
- upload de arquivos;
- início/fim/falha de execução;
- versão do modelo;
- versão do prompt;
- fontes/chunks usados;
- validações executadas;
- alterações humanas;
- aprovação/reprovação;
- geração/download do documento.

Os logs devem evitar conteúdo sensível desnecessário e seguir as políticas internas de retenção.

## CI/CD
**Azure DevOps** para build e deploy nas VMs existentes.

Pipeline recomendado:
1. lint e testes;
2. build do front-end;
3. build das imagens compatíveis com Podman;
4. versionamento/tag da release;
5. deploy em pré-produção;
6. smoke test;
7. promoção controlada para produção;
8. rollback rápido para imagem anterior.

Credenciais e segredos não devem ficar no repositório.

## Arquitetura sugerida

```text
[ Usuário corporativo ]
          |
          | Entra ID
          v
[ Nginx / HTTPS na VM ]
          |
     +----+----+
     |         |
     v         v
[ React ]   [ FastAPI ]
                |
                +--> Ingestion
                +--> RAG local
                +--> B3 GPT / OpenAI
                +--> Validation
                +--> Document Generation
                +--> Audit / Logs
                |
                +--> Storage / Vector Index local

Execução: Podman + Quadlet/systemd
Deploy: Azure DevOps -> VM pré-prod -> VM prod
```

## Fluxo de tela sugerido

### Tela 1 — Acesso
- autenticação corporativa;
- validação de grupo/perfil autorizado.

### Tela 2 — Novo evento
- identificação do evento;
- upload dos arquivos;
- seleção/configuração mínima;
- iniciar processamento.

### Tela 3 — Processamento
- arquivos recebidos;
- extração;
- indexação;
- classificação por domínio;
- geração;
- validação;
- consolidação.

### Tela 4 — Resultado e revisão
- perguntas e respostas por domínio;
- PT e EN lado a lado;
- fontes utilizadas;
- alertas de revisão;
- edição humana;
- aprovação/reprovação.

### Tela 5 — Histórico/Auditoria
- execuções anteriores;
- data/hora;
- usuário;
- status;
- versão;
- ações relevantes.

## O que evitar no MVP
- criação de novos serviços Azure sem necessidade;
- Kubernetes;
- microserviços demais;
- múltiplos frameworks de agentes;
- banco complexo sem necessidade;
- Next.js sem necessidade real;
- Node.js no back-end apenas para acompanhar o React;
- fine-tuning no início;
- publicação automática sem revisão humana.

## Decisão oficial do MVP

**Infraestrutura:** VMs corporativas existentes de pré-produção e produção  
**Front-end:** React + TypeScript + Vite  
**Back-end:** Python + FastAPI  
**Proxy/TLS:** Nginx + certificado corporativo  
**Containers:** Podman  
**Lifecycle:** Quadlet/systemd  
**Autenticação:** Microsoft Entra ID + grupo corporativo  
**RAG:** índice vetorial local / PostgreSQL + pgvector, conforme disponibilidade  
**LLM:** B3 GPT; OpenAI apenas se necessário  
**Documento:** python-docx  
**CI/CD:** Azure DevOps  
**Auditoria:** trilha persistente de ações e execuções  

Essa é a arquitetura de referência para o hackathon.
