# SimplFAQ · POC local

Aplicação completa de FAQs bilíngues, executada com **Podman rootless + Quadlet/systemd no AlmaLinux-10 do WSL**. React/TypeScript/Vite, FastAPI, Nginx e modelos locais. Sem dependência corporativa para usar a POC.

**Acesse: http://localhost:8080**

## Iniciar e parar

No PowerShell, dentro deste repositório:

```powershell
wsl -d AlmaLinux-10 -- bash /mnt/c/repos/simpliFAQ/scripts/start.sh
wsl -d AlmaLinux-10 -- bash /mnt/c/repos/simpliFAQ/scripts/status.sh
wsl -d AlmaLinux-10 -- bash /mnt/c/repos/simpliFAQ/scripts/stop.sh
```

O script `scripts/Start-SimplFAQ.ps1` inicia os serviços e abre o site. No WSL, `start.sh` também inicia uma sessão oculta pelo Windows para impedir o encerramento da distribuição por inatividade. O WSL não permanece ligado apenas pelos serviços systemd. `stop.sh` encerra os containers e libera essa sessão em até cinco segundos. Iniciar novamente reutiliza a sessão existente, sem criar processos duplicados. Quadlet inicia os serviços quando a distribuição WSL inicia; o notebook precisa estar ligado. Após reiniciar o Windows, execute o script de início. Os volumes permanecem após parar os containers. Em uma VM Linux comum, essa sessão Windows não é utilizada.

## Usar a aplicação

1. Crie um evento ou escolha **Explorar um evento de exemplo** (dados fictícios).
2. Adicione quantos documentos precisar. Selecione o tipo de fonte por lote: documento oficial do evento, arquivo financeiro, dados estruturados, transcrição, regras internas ou guia linguístico. Use apenas dados fictícios na demonstração.
3. Clique em **Gerar FAQ**. O processamento acontece em segundo plano, com etapas visíveis.
4. Confira as perguntas PT/EN, os trechos citados, as lacunas e conflitos. **Explorar RAG** permite pesquisar diretamente as fontes.
5. Revise as **12 seções** do template: aplicabilidade, justificativas PT/EN, fontes e nota. Em cada pergunta, clique em **Revisar pergunta**, corrija a seção, perguntas, respostas e citações por afirmação quando necessário, descreva sua revisão e confirme a equivalência bilíngue.
6. Aprove a FAQ e registre uma nota. Só então ela passa à base aprovada. Documentos aprovados são imutáveis; crie um novo evento para outra versão aprovada.
7. Exporte Word quando desejar. Documentos não aprovados têm marcação de rascunho.

Se houver falha ao abrir um evento, a página informa o erro e permite **Tentar novamente** ou **Voltar aos eventos**. O carregamento do detalhe tem limite de 15 segundos. Uma falha de rede não reenvia uploads, decisões ou outras escritas automaticamente.

Arquivos: PDF com texto, DOCX, PPTX, XLSX, CSV, TXT, Markdown e JSON UTF-8. Limite padrão de 25 MB por arquivo e 100 MB por lote. PDFs digitalizados precisam de OCR antes do upload. Um novo upload com o mesmo nome cria uma versão; a ingestão usa a versão mais recente, preservando o original e a auditoria.

## Template e manuais públicos

Novas gerações utilizam as 12 seções definidas exclusivamente em `backend/app/faq_template.json`, incluindo resumo e cronograma. A definição é congelada no resultado para preservar a versão usada. Ausência de evidências produz **informação insuficiente**, nunca uma exclusão presumida. É possível gerar a estrutura sem documentos, mas não aprovar uma FAQ sem perguntas. FAQs anteriores conservam seu formato e conteúdo até uma nova geração solicitada explicitamente.

Em **Manuais públicos**, consulte, pesquise ou atualize os dois manuais oficiais da B3. A aplicação confirma links e vigência na página oficial, verifica a capa e registra SHA-256, sistema, versão, páginas e data de ingestão. Câmara e Depositária são recuperadas separadamente. Desativar um manual preserva PDF e chunks; citações desativadas impedem aprovação. Os manuais públicos são contexto normativo geral, não fornecem os fatos particulares do evento e não representam integração com B3 GPT.

Para atualizar pelo terminal, aguarde as tarefas terminarem e execute:

```bash
bash scripts/update-manuals.sh
```

A atualização redescobre os links oficiais; não fixe URLs de versões antigas. Consulte [a matriz de requisitos, evidências e limitações desta versão](docs/INCREMENTAL_REPORT.md). Se a B3 mudar a estrutura da página, a tarefa falha explicitamente e exige revisão do importador.

## Modelos locais e fine-tuning

- **Geração:** Ollama, `qwen2.5:1.5b`, quantizado. Classificação, geração estruturada PT/EN e validação em chamadas separadas.
- **Embeddings:** FastEmbed/ONNX, `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, 384 dimensões. Busca vetorial por cosseno e reranking híbrido por similaridade, termos e prioridade de fonte.
- **Fine-tuning:** PEFT/LoRA sobre `Qwen/Qwen2.5-0.5B-Instruct`, CPU, rank 4, 8 passos por experimento. Incluído na imagem instalada.

Em **Fine-tuning**, exporte o dataset JSONL ou inicie um experimento após aprovar pelo menos duas perguntas bilíngues. O dataset inclui as evidências nas mensagens de entrada. Apenas respostas aprovadas entram no treinamento. Os exemplos com o mesmo contexto permanecem juntos na separação de treino/validação. Quando só existe um contexto, não há holdout e a interface mostra isso. O resultado é um ZIP com adapter, tokenizer, métricas e proveniência.

O adapter **não é ativado automaticamente**. É um experimento pequeno de estilo e formato, não substitui o RAG nem demonstra melhora de precisão factual. O modelo de treinamento é menor que o de geração para caber neste notebook; adapters desses dois tamanhos não são intercambiáveis. A POC não tem publicação automática de modelos.

Para avaliar um adapter salvo, sem promovê-lo ao gerador de FAQs, use o utilitário no container após terminar as demais tarefas:

```bash
podman exec simplfaq-api python -m app.predict_lora \
  --adapter /data/training/ID_DO_EXPERIMENTO/adapter \
  --prompt 'Evidence: O evento é online. Question: What is the event format?'
```

O primeiro uso baixa os pesos públicos. Após o cache, os documentos e inferências ficam locais. Geração e treinamento compartilham uma fila para evitar disputa de memória. Em CPU, a geração pode levar vários minutos.

O ensaio do template com três documentos fictícios levou cerca de 32 minutos neste notebook e gerou rascunhos com erros de afirmações/tradução sinalizados pelos verificadores. Planeje a geração com antecedência e corrija as pendências antes de aprovar. A POC não fornece uma FAQ pronta para publicação sem revisão.

O modelo pequeno pode repetir temas, classificar seções incorretamente e avaliar traduções de forma inconsistente. A validação semântica é assistiva: justificativas repetidas entre itens são marcadas como inconclusivas, e nenhum item é aprovado automaticamente. Confira também as fontes não cobertas. O fluxo atual avalia todas as 12 seções e gera até três perguntas PT por seção aplicável antes de traduzi-las para EN. O fluxo anterior, limitado a três domínios, permanece disponível na API com `POST /api/events/ID/runs?mode=legacy` para compatibilidade e regressão. `OLLAMA_MAX_PROMPT_CHARS=18000` evita contextos excessivos com erro explícito; é uma proteção por caracteres, não uma garantia de contagem de tokens.

## Instalação reproduzível

Pré-requisitos: AlmaLinux WSL com Podman 5+, rede para baixar imagens/pesos e systemd do usuário ativo. Não requer Node/Python no Windows nem Docker.

```bash
cd /mnt/c/repos/simpliFAQ
bash scripts/build.sh --training
bash scripts/install-wsl.sh
```

Configuração efetiva: `~/.config/simplfaq/app.env`, copiada de `.env.example` na primeira instalação. Não sobrescrever esse arquivo ao atualizar. Quadlets: `~/.config/containers/systemd/simplfaq-*`. Para aplicar uma alteração de configuração, reinicie API e proxy:

```bash
systemctl --user restart simplfaq-api.service simplfaq-web.service
```

`AUTH_MODE=local` só é permitido em `ENVIRONMENT=development`. O proxy publica **127.0.0.1:8080**, sem exposição à LAN. Há proteção de origem, cabeçalho obrigatório de acesso local, CSP, limite de uploads e processos sem privilégios. Esta POC é de usuário único; não deve ser exposta publicamente com autenticação local.

## Persistência, operação e testes

- `simplfaq-data`: SQLite/WAL, arquivos originais, metadados, chunks/vetores, revisões, documentos, cache de embeddings e treinamento.
- `simplfaq-models`: pesos Ollama.
- Auditoria append-only no aplicativo, com triggers bloqueando alteração/exclusão; não é uma trilha inviolável contra o administrador do host.
- Fila persistida em SQLite. Execuções interrompidas pelo reinício são marcadas como falha recuperável; podem ser reenviadas. Use um único processo Uvicorn, conforme o container.
- Todos os membros de um workspace local compartilham os eventos. Sem multitenancy nesta POC.

```bash
bash scripts/test.sh
bash scripts/smoke.sh
podman logs --tail 100 simplfaq-api
podman logs --tail 100 simplfaq-ollama
bash scripts/backup.sh
bash scripts/update.sh --training
```

O backup recusa tarefas ativas, para temporariamente a API, exporta o volume completo e gera checksum SHA-256. Os arquivos ficam em `~/simplfaq-backups`, com permissões restritas. Para restaurar, preserve o volume original e importe o TAR em **um novo volume** (`podman volume create simplfaq-restored` seguido de `podman volume import simplfaq-restored ARQUIVO.tar`). Verifique o checksum do TAR e a integridade do volume antes de ajustar o Quadlet e reiniciar. Uma restauração em volume separado foi validada nesta entrega:

```bash
cd ~/simplfaq-backups
sha256sum -c ARQUIVO.tar.sha256
podman run --rm --network none --volume simplfaq-restored:/data:ro \
  --env ENVIRONMENT=development --env AUTH_MODE=local --env LLM_PROVIDER=ollama \
  localhost/simplfaq-api:poc python -m app.verify_storage
```

`scripts/update.sh` preserva as imagens anteriores, faz build e backup, aplica os Quadlets e executa smoke; uma falha restaura as tags anteriores. O script imprime o comando de rollback com as tags específicas daquela atualização. Rollback também recusa tarefas ativas. O rollback de imagens não reverte dados; migrações futuras incompatíveis exigirão backup.

Resultados e limitações da entrega: [relatório de validação](docs/VALIDATION.md). Preparação sem recursos corporativos: [VM Linux e B3 GPT](docs/VM_DEPLOYMENT.md).

## Estrutura

```text
backend/app/      API, auth, ingestão, RAG, geração, validação, revisão, DOCX, LoRA
backend/tests/    Testes de fluxo, segurança, isolamento e recuperação
frontend/        Interface React/TypeScript, estilos e exemplo fictício
infra/           Nginx e unidades Quadlet
scripts/         Build, instalação, operação, smoke, backup e rollback
docs/            Arquitetura, avaliação e limitações verificadas
Handoff/         Requisitos originais preservados
```

O handoff foi seguido com a alteração de escopo solicitada: a POC usa modelos locais e acesso local, e inclui fine-tuning experimental. Entra ID e adapter B3 GPT permanecem opcionais no código, mas não fazem parte da validação local e não exigem credenciais. Deploy corporativo, TLS corporativo e Azure DevOps foram retirados do escopo a pedido do usuário.

## Referências técnicas

[Quadlet/Podman](https://docs.podman.io/en/stable/markdown/podman-systemd.unit.5.html), [FastEmbed](https://github.com/qdrant/fastembed), [Ollama](https://docs.ollama.com/api/chat), [PEFT LoRA](https://huggingface.co/docs/peft/main/en/package_reference/lora), [validação Entra ID opcional](https://learn.microsoft.com/en-us/entra/identity-platform/claims-validation).
