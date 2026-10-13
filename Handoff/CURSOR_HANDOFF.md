# SimpliFAQ — Cursor Handoff

## 1. Objetivo
Implementar o **SimpliFAQ**, uma solução para automatizar a criação de relatórios/FAQs bilíngues (PT/EN) relacionados a eventos corporativos.

Hoje, o processo é executado por várias áreas humanas. Cada área responde perguntas referentes ao seu próprio domínio (por exemplo: Negociação, Garantias, Liquidação etc.), e uma pessoa consolida o material final para envio ao negócio.

O SimpliFAQ deve produzir uma primeira versão avançada, rastreável e revisável por humano.

---

## 2. Entradas principais
O sistema deve aceitar, conforme disponibilidade:
- fato relevante / documento principal do evento;
- documentos complementares;
- dados estruturados do evento;
- transcrição da reunião sobre o evento;
- FAQs históricas aprovadas;
- glossários, guias de estilo e padrões de inglês da B3.

---

## 3. Princípios de arquitetura de IA
### 3.1 RAG factual
Usar RAG para recuperar evidências do evento atual.
Essas fontes têm prioridade factual.

### 3.2 RAG histórico
Usar FAQs históricas aprovadas para:
- encontrar casos semelhantes;
- apoiar cobertura de tópicos;
- servir de referência estrutural;
- fornecer exemplos de perguntas e respostas aprovadas.

FAQ histórica nunca deve sobrescrever evidência factual do evento atual.

### 3.3 RAG linguístico
Manter uma fonte lógica separada para:
- glossários PT/EN;
- terminologia oficial;
- estilo de escrita;
- padrões de comunicação;
- exemplos aprovados em inglês.

O objetivo é orientar **como escrever**, sem misturar esse conteúdo com a fonte factual do evento.

---

## 4. Papel do B3 GPT / LLM
Usar o B3 GPT como LLM/orquestrador para apoiar:
- classificação por domínio;
- identificação dos tópicos aplicáveis;
- detecção de lacunas;
- detecção de conflitos;
- detecção de duplicidades;
- recomendação de revisão humana;
- geração estruturada de perguntas e respostas.

Decisões críticas de negócio ou regulatórias não devem depender exclusivamente do LLM.

---

## 5. Geração bilíngue
Português e inglês são gerados **no mesmo ciclo**, a partir das mesmas evidências.

Estrutura sugerida por item:
```json
{
  "domain": "Negociação",
  "question_pt": "...",
  "answer_pt": "...",
  "question_en": "...",
  "answer_en": "...",
  "sources": [],
  "confidence": null,
  "requires_human_review": false
}
```

Depois da geração, executar checagem de equivalência semântica PT/EN.

---

## 6. Fluxo-alvo
1. Receber arquivos e dados.
2. Extrair e normalizar conteúdo.
3. Criar chunks.
4. Gerar embeddings.
5. Indexar em coleções lógicas separadas:
   - evento atual;
   - FAQs históricas aprovadas;
   - linguagem/glossário.
6. Classificar os domínios aplicáveis.
7. Recuperar evidências por domínio.
8. Aplicar reranking.
9. Gerar perguntas e respostas PT/EN simultaneamente.
10. Validar aderência factual às fontes.
11. Validar equivalência PT/EN.
12. Remover duplicidades e consolidar.
13. Gerar documento final.
14. Revisão humana.
15. Somente após aprovação, indexar a nova FAQ no histórico.

---

## 7. Guardrails obrigatórios
- Não inventar resposta quando não houver evidência suficiente.
- Marcar `requires_human_review=true` quando houver lacuna, conflito ou baixa confiança.
- Não misturar eventos diferentes.
- Não usar FAQ histórica como autoridade superior ao documento atual.
- Só usar FAQ histórica aprovada como referência.
- Preservar rastreabilidade das fontes.
- Registrar metadados e versão.
- Não publicar automaticamente o resultado final.
- Revisão humana é obrigatória antes de disponibilização ao negócio.

---

## 8. Técnicas a aplicar
- Prompt engineering
- Few-shot prompting com exemplos aprovados
- RAG
- Embeddings
- Vector search
- Metadata filtering
- Reranking
- Structured output
- Groundedness / factuality checking
- Semantic equivalence PT/EN
- Human-in-the-loop
- Evals
- Fine-tuning apenas se necessário após estabilização das etapas anteriores

---

## 9. Fine-tuning
Não usar fine-tuning para memorizar fatos de eventos.

Fine-tuning pode ser avaliado futuramente para:
- estilo;
- consistência;
- formato;
- padrão de redação;
- comportamento esperado.

Antes de fine-tuning, priorizar:
- prompt engineering;
- few-shot;
- RAG;
- exemplos históricos;
- validação.

---

## 10. Estratégia de implementação sugerida
### Fase 1 — MVP
- ingestão local de arquivos;
- extração de texto;
- chunks e metadados;
- busca simples / vetorial;
- geração PT/EN;
- saída JSON;
- validação manual.

### Fase 2 — Qualidade
- filtros por domínio;
- reranking;
- groundedness checking;
- equivalência PT/EN;
- deduplicação;
- controle de versão.

### Fase 3 — Produto
- interface;
- upload;
- acompanhamento por execução;
- auditoria;
- geração do documento final;
- aprovação humana;
- feedback loop para FAQs aprovadas.

### Fase 4 — Avaliação e evolução
- evals automatizados;
- comparação com casos históricos;
- métricas de intervenção humana;
- eventual fine-tuning.

---


## 10A. Premissas técnicas oficiais do MVP
- Executar somente nas VMs corporativas existentes de pré-produção e produção.
- Não exigir criação de App Service, Static Web Apps, Azure AI Search, Functions, Container Apps ou Kubernetes.
- Usar Podman, não Docker.
- Usar Nginx para HTTPS/reverse proxy.
- Integrar autenticação com Microsoft Entra ID e autorização por grupo corporativo.
- Usar Azure DevOps para CI/CD nas VMs.
- Manter RAG/índice vetorial local ou em tecnologia já disponível internamente.
- Manter trilha de auditoria persistente das execuções e ações humanas.

## 11. Orientação para o Cursor
Antes de implementar:
1. Ler este arquivo inteiro.
2. Ler `ARCHITECTURE.md`.
3. Ler `TECH_STACK.md`.
4. Ler `RULES_AND_GUARDRAILS.md`.
5. Ler `SCHEMAS.md`.
6. Ler `PROMPTS.md`.
7. Ler `BACKLOG.md`.

Ao sugerir código:
- priorizar arquitetura modular;
- evitar acoplamento a um único provedor de LLM;
- separar retrieval, orchestration, generation, validation e persistence;
- manter interfaces claras;
- escrever testes desde o início;
- registrar decisões arquiteturais importantes;
- nunca inserir segredos, tokens ou credenciais no código.

---

## 12. Definição de sucesso
O SimpliFAQ é bem-sucedido se:
- cobre os domínios aplicáveis;
- não inventa fatos;
- cita evidências;
- mantém PT/EN equivalentes;
- segue o padrão de comunicação;
- reduz o esforço humano;
- permite auditoria;
- deixa claro quando precisa de revisão.
