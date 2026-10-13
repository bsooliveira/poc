# Prompt — revisão documental e continuidade do SimpliFAQ na B3

Copie o conteúdo entre **INÍCIO DO PROMPT** e **FIM DO PROMPT** para a IA que executará a revisão. Este arquivo prepara essa execução; sua criação não significa que as atividades abaixo já foram concluídas.

## INÍCIO DO PROMPT

Você dará continuidade ao **SimpliFAQ existente**. Faça uma revisão documental completa e prepare a transferência do projeto para o Cursor, a IA corporativa da B3. A próxima implantação será diretamente em **uma VM Linux de desenvolvimento**, com Podman. O usuário fará o commit e levará o repositório para o ambiente corporativo.

Entregue documentação suficiente para outro desenvolvedor ou agente instalar, validar, operar e continuar o projeto a partir de um clone limpo, sem depender desta conversa, do notebook original ou de arquivos locais não versionados. Preserve o código funcional, as decisões válidas e os dados existentes. Trabalhe incrementalmente até concluir os entregáveis possíveis no ambiente disponível.

### 1. Escopo, limites e precedência

- A grafia oficial do projeto é **SimpliFAQ**. Use-a em todo conteúdo de produto. Preserve os identificadores técnicos de compatibilidade documentados no README; eles apontam para dados, serviços e clientes já instalados.
- Revise todos os Markdown do projeto, consolide os requisitos do TXT mencionado abaixo, atualize a apresentação HTML e produza um handoff executável para o Cursor e para o deploy Linux.
- Não recrie o projeto, não gere novos scaffolds e não substitua componentes, banco, containers ou arquitetura por conveniência.
- O destino imediato é a VM Linux de **desenvolvimento**. Pré-produção, produção, Azure DevOps e novos serviços de nuvem não são pré-requisitos dessa entrega; registre como evolução futura o que ainda fizer sentido.
- A POC local continua funcionando sem recursos corporativos. Integração real com B3 GPT, identidade e infraestrutura corporativa será concluída dentro do ambiente autorizado, aproveitando os pontos de extensão existentes.
- Instruções atuais do usuário prevalecem sobre planos antigos. Diferencie requisitos desejados de comportamento implementado: código e testes comprovam implementação, mas não eliminam um requisito pendente.
- Não transforme descrições aspiracionais em funcionalidades concluídas. Distingua: **implementado e validado**, **implementado com limitações**, **preparado sem validação corporativa** e **pendente**.
- Use exclusivamente dados fictícios nos testes. Não inclua documentos internos, dados pessoais, credenciais, tokens, bancos, backups, pesos ou arquivos de ambiente reais no Git, na apresentação ou nos relatórios.
- Não apague eventos, documentos, FAQs, volumes ou backups. Não execute reset, clean, restauração sobre dados ativos ou limpeza global de containers/volumes. Preserve alterações locais anteriores à sua execução.
- Faça correções de código ou scripts somente quando necessárias para tornar as instruções verdadeiras e o deploy reproduzível, com alterações pequenas e testes correspondentes. Não expanda para uma reimplementação das integrações corporativas sem acesso ao contrato real.
- Prepare o conteúdo para revisão e commit pelo usuário. Não faça commit, push ou publicação sem uma solicitação adicional explícita.

### 2. Inspeção inicial e referências conhecidas

Antes de alterar arquivos, verifique branch, commit, `git status`, diffs, instruções locais aplicáveis, estrutura do projeto, scripts e resultados anteriores. Leia primeiro:

1. `README.md`;
2. `docs/INCREMENTAL_REPORT.md`;
3. `docs/VM_DEPLOYMENT.md`;
4. `Handoff/00_START_HERE.md` e `Handoff/CURSOR_HANDOFF.md`;
5. a especificação textual original e `backend/app/faq_template.json`.

Depois, inventarie os demais Markdown com `rg --files`, incluindo arquivos novos relevantes. Cubra a raiz, `Handoff/`, `docs/` e `evaluation/`. Exclua `.git`, dependências, caches, ambientes virtuais, artefatos gerados e dados de execução. Registre quais arquivos foram revisados, consolidados, mantidos como histórico ou removidos e por quê.

**Referência observada em 12/10/2026, a reconfirmar na execução:**

- Repositório: `https://github.com/bsooliveira/poc`; commit de referência `5150c00`. Use o HEAD efetivo para a nova revisão, sem retornar à força a esse commit.
- POC executada em Podman rootless/Quadlet no AlmaLinux-10 do WSL. React/TypeScript/Vite, FastAPI, Nginx, SQLite/WAL e fila persistente já existem.
- Último relatório: **50 testes aprovados, sendo 46 backend e 4 frontend**, além de Ruff e build TypeScript/Vite. Os totais 19, 30 e 34 pertencem a etapas anteriores.
- Template canônico com 12 seções, ingestão de documentos, RAG multilíngue, manuais públicos versionados, geração PT seguida de tradução EN, revisão humana e exportação Word já estão implementados.
- Ollama usa `qwen2.5:1.5b`; embeddings FastEmbed usam `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, com 384 dimensões. LoRA é experimental e não é promovido automaticamente.
- O ensaio real mais recente com três fontes fictícias demorou aproximadamente 32 minutos e produziu cinco itens com erros de afirmações/tradução sinalizados. Testes de regressão aprovados não significam qualidade editorial ou factual aprovada do modelo.
- O relatório registra dois eventos preservados, dois documentos originais, uma FAQ em revisão e nenhuma aprovada. Isso descreve o ambiente local anterior; um clone novo não inclui esses dados.
- O erro anterior de carregamento do evento foi corrigido e está documentado em `docs/FETCH_FIX.md`. Preserve `/api` na mesma origem, tratamento de falha e limites de leitura.
- Manuais públicos foram ingeridos no ambiente local e estão registrados no relatório. PDFs, índices, pesos e configurações efetivas não acompanham um clone Git. B3 GPT, Entra ID e TLS corporativo ainda exigem validação real.

Trate esses pontos como referências de partida, não como resultados de testes executados agora. Se houver diferenças, registre a evidência atual e atualize a documentação.

### 3. Consolidar a especificação e remover o TXT com rastreabilidade

Arquivo de origem: `CODEX — IMPLEMENTAÇÃO INCREMENTAL DO Sim.txt`, na raiz.

**Atenção:** na preparação deste prompt, o arquivo estava vazio na cópia de trabalho e marcado como modificado. O conteúdo completo ainda existia no commit `5150c00`. Não interprete o arquivo vazio como ausência de requisitos e não desfaça a alteração local para recuperá-lo. Consulte o histórico somente para leitura, por exemplo:

```bash
git show '5150c00:CODEX — IMPLEMENTAÇÃO INCREMENTAL DO Sim.txt'
```

Se o estado tiver mudado, examine a versão local e o histórico relevante. Identifique as diferenças antes de consolidar. Se a origem não puder ser recuperada, registre o impedimento e não declare a consolidação concluída.

Crie ou atualize uma especificação canônica em `Handoff/ESCOPO_PROJETO.md`. Converta o conteúdo recuperado em requisitos permanentes do produto, com estado de implementação e links para evidências. Remova comandos circunstanciais e estatísticas antigas da descrição do estado atual, preservando os requisitos válidos. Inclua, no mínimo:

- Produto voltado à elaboração e revisão de FAQs bilíngues sobre eventos corporativos, com documento Word como saída e revisão humana obrigatória. Não é um chatbot de perguntas avulsas.
- Entradas variáveis, distinguindo documento do evento, arquivo financeiro, transcrição, referências normativas e outras fontes suportadas; lacunas devem ser explícitas.
- Definição única e versionada das 12 seções, na ordem existente em `backend/app/faq_template.json`: A. Resumo da operação; B. Cronograma; 1. Estrutura do evento e ativos envolvidos; 2. Tratamento operacional na Central Depositária; 3. Exercício e manifestação de direitos; 4. Contratos de empréstimo, contratos a termo, opções e derivativos; 5. Precificação e modelos teóricos; 6. Fluxos de exceção e restrições; 7. Falhas, recomposição e recompras; 8. Tributação; 9. Exemplos práticos e simulações; 10. Contatos operacionais.
- Todas as seções avaliadas em cada geração, com estados aplicável, não aplicável e informação insuficiente. Não inventar subitens, fatos, regras fiscais, contatos, datas ou instruções não fornecidas. Não solicitar fotografias do template.
- RAG com os manuais públicos da Câmara B3 e da Central Depositária de Renda Variável, separação por sistema, vigência e versão; URLs oficiais verificadas, hash, página/trecho, status e histórico. Não presumir que um PDF antigo é a versão vigente.
- Evidência por afirmação, distinção entre fatos do evento e regras gerais, conflitos explícitos, identificadores estáveis, equivalência PT/EN, consistência de cronograma e deduplicação.
- Pipeline efetivamente implementado: ingestão, recuperação de evidências, avaliação das 12 seções, geração PT, tradução EN, validações, revisão e aprovação humana. Exportação anterior à aprovação deve ser identificada como rascunho.
- UI com fontes e pendências, bloqueios de aprovação, histórico aprovado no RAG, imutabilidade dos resultados aprovados e Word compatível com o template/snapshot.
- Preservação de dados e compatibilidade legada, migrações incrementais, regressões, avaliação qualitativa com fontes fictícias, backups, restore e rollback.
- Limitações atuais, requisitos parcialmente atendidos e próximos incrementos corporativos, sem ocultar a qualidade insuficiente do ensaio com o modelo pequeno.

Mantenha uma matriz concisa **requisito → estado → código → teste/evidência → pendência**. Reaproveite a matriz existente em vez de duplicar relatórios extensos.

Somente após confirmar que todos os requisitos relevantes estão documentados, remova o TXT. Procure e atualize suas referências em todo o repositório, inclusive o campo `source` de `backend/app/faq_template.json`, quando aplicável. Não altere IDs, ordem, títulos ou política de versionamento do template apenas por mudar a referência documental; preserve snapshots já gravados. Atualize também este prompt para que uma execução posterior não dependa de um arquivo removido: identifique a especificação consolidada e deixe a referência ao TXT apenas como proveniência histórica explícita.

### 4. Revisar todos os Markdown

Corrija contradições, links quebrados, caminhos locais obrigatórios, comandos inexistentes, contagens desatualizadas, descrições de arquitetura superadas e funcionalidades apresentadas como futuras que já existem.

Reescreva apenas os trechos necessários. Evite acrescentar um aviso de atualização no topo enquanto o restante continua dando instruções erradas. Consolide conteúdo repetido em uma fonte principal e use links relativos nos demais arquivos.

Dedique atenção a:

- `Handoff/00_START_HERE.md`: instruir a **continuar** o produto existente, retirando a sequência antiga de criar backend, frontend e infraestrutura do zero.
- `Handoff/CURSOR_HANDOFF.md`, `IMPLEMENTATION_PLAN.md` e `BACKLOG.md`: separar concluído, dívida de qualidade e integração/deploy corporativo pendentes; definir a próxima tarefa executável.
- `Handoff/ARCHITECTURE.md`, `TECH_STACK.md`, `SCHEMAS.md`, `PROMPTS.md` e `RULES_AND_GUARDRAILS.md`: refletir módulos, contratos, geração PT→EN, template, normativos, revisão e limitações reais.
- `README.md` e `Handoff/README.md`: apresentar estado atual, entrada única de leitura e caminhos de instalação local e Linux corporativo.
- `docs/ARCHITECTURE.md` e `docs/VM_DEPLOYMENT.md`: descrever a implementação existente e os requisitos concretos da VM de desenvolvimento.
- Relatórios `VALIDATION.md`, `FETCH_FIX.md` e `INCREMENTAL_REPORT.md`: preservar evidências históricas úteis, com data, versão e rótulo de histórico; indicar claramente qual validação é a mais recente. Não alterar retroativamente resultados medidos.
- `evaluation/README.md` e `evaluation/samples/README.md`: explicar como reproduzir as avaliações e distinguir amostra determinística, execução real e aprovação editorial.

A nova direção corporativa substitui a ideia de que a integração foi retirada permanentemente do projeto: ela passa a ser a próxima etapa. Ao mesmo tempo, não apresente B3 GPT, Entra ID, TLS ou Azure DevOps como já validados. Não crie vários documentos concorrentes para o mesmo assunto.

### 5. Atualizar a apresentação HTML

Revise `Handoff/SIMPLIFAQ_APRESENTACAO.html`, preservando identidade visual e navegação úteis. Corrija conteúdo desatualizado em todas as seções, incluindo diagramas, badges, fluxo e rodapé.

A apresentação deve permitir entender:

1. Objetivo e funcionamento do produto.
2. O que já funciona na POC: ingestão, RAG multilíngue, template, manuais versionados, fontes, revisão, Word e operação em Podman.
3. Stack e arquitetura atuais, distinguindo modelos locais da integração futura com B3 GPT.
4. Resultados comprovados, com data/versão, sem confundir testes automatizados com qualidade das respostas.
5. Limitações do modelo, revisão humana obrigatória e caráter experimental do LoRA.
6. Próxima etapa: clone dentro da B3, deploy em VM Linux de desenvolvimento e validação das integrações corporativas.
7. Dependências e pendências reais da implantação, sem prometer integração já concluída.

Revise afirmações de “PT/EN simultâneos”, “B3 GPT/OpenAI”, login corporativo ativo e pipeline de pré-produção/produção à luz do comportamento atual. Inspecione a página em navegador, incluindo navegação, alternância de arquitetura, legibilidade, responsividade e impressão, se houver estilo para isso. Registre limitações caso a validação visual não esteja disponível.

### 6. Handoff enxuto e acionável para o Cursor

Atualize `Handoff/CURSOR_HANDOFF.md` para que uma sessão nova continue o trabalho sem reler toda a história. Use `Handoff/00_START_HERE.md` como entrada curta e os demais documentos como consulta sob demanda.

O handoff deve conter:

- Data da revisão, commit de base inspecionado e indicação de alterações locais ainda não commitadas; não invente um hash para a entrega futura.
- Resumo do estado atual e decisões estabelecidas que devem ser preservadas.
- Ordem mínima de leitura: ponto de partida, estado/pendências e runbook de deploy; demais arquivos somente conforme a tarefa.
- Mapa dos módulos e pontos de extensão, com caminhos reais para provedores, auth/configuração, ingestão/RAG, normativos, template, validação/revisão, Word, treinamento, persistência/migrações, frontend e operação.
- Comandos reais para construir imagens, instalar, iniciar, obter status/logs, testar, executar smoke, atualizar manuais, fazer backup, restaurar em outro volume e atualizar/voltar imagens.
- Tabela do que está versionado e do que precisa ser criado ou provisionado na VM. Um clone não traz eventos, uploads, banco, cache de embeddings, modelos, manuais baixados ou configuração efetiva.
- Backlog priorizado com dependências, arquivos afetados, critérios de aceite e testes por tarefa. Priorize preflight/deploy de desenvolvimento, contrato B3 GPT, identidade/acesso/TLS e avaliação da qualidade do novo provedor.
- Informações corporativas ainda necessárias: distribuição e recursos da VM, permissões, hostname, certificados, registries/proxy/CA, contrato e autenticação B3 GPT, Entra/grupo e políticas de modelos/dados. Peça informações não secretas; segredos devem ser configurados por meio autorizado fora do Git.
- Um prompt curto de retomada que mande inspecionar estado e diffs, escolher a primeira tarefa pendente, preservar o que funciona, validar o incremento e atualizar o registro de continuidade.
- Um registro compacto de “última atividade concluída / evidência / próxima atividade / bloqueios”, sem transcrições extensas de conversas ou logs.

O Cursor deve conseguir iniciar pelo deploy e integrações pendentes. Não deve gastar uma nova sessão reconstruindo estrutura, redescobrindo decisões ou implementando funcionalidades já prontas.

### 7. Runbook reproduzível para a VM Linux de desenvolvimento

Consolide o runbook principal em `docs/VM_DEPLOYMENT.md`. Cada etapa deve indicar pré-condições, comando, resultado esperado e diagnóstico de falha. Use caminhos relativos ao clone e variáveis documentadas; não dependa de `C:\repos\simpliFAQ`, `/mnt/c`, nome de usuário do notebook ou WSL no servidor.

Cubra a sequência abaixo:

1. **Preflight:** distribuição/arquitetura, Podman compatível, Quadlet, systemd do usuário, usuário dedicado rootless, UID/subuid/subgid, permissões, linger, CPU/RAM/disco, armazenamento persistente, SELinux, DNS, horário, firewall, proxy, CA corporativa e acesso autorizado a registries, pacotes e modelos. Separe requisitos medidos de estimativas; não invente dimensionamento garantido.
2. **Clone:** origem aprovada, branch/commit/tag, diretório, permissões e conferência de arquivos necessários. Não suponha acesso irrestrito ao GitHub dentro da B3; documente transferência/importação pelo meio corporativo autorizado quando necessário.
3. **Build/provisionamento:** imagens de API/web, opção de treinamento, imagens-base, cache e pesos. Documente dependências de download e a alternativa de provisionamento por registry/artefatos aprovados em rede restrita, sem burlar controles.
4. **Configuração:** tabela das variáveis realmente utilizadas, finalidade, obrigatoriedade por perfil, padrão e momento de aplicação (build do frontend ou runtime). Arquivo efetivo fora do repositório, permissões restritas, exemplos somente com placeholders. Confira se a instalação conserva configuração existente.
5. **Instalação Linux nativa:** valide `scripts/install-wsl.sh`, `start.sh`, `lib.sh` e Quadlets. O nome do instalador não comprova portabilidade. Atualmente ele inicia Ollama e baixa `qwen2.5:1.5b`; esclareça e, se necessário, corrija pontualmente esse comportamento para um perfil corporativo que use apenas B3 GPT e não autorize modelos locais. Preserve compatibilidade da POC e evite duplicar instaladores sem necessidade.
6. **Perfis de IA:** documente POC local e B3 GPT separadamente. Confirme o contrato real antes de ativar o adapter em `backend/app/generation.py`; o formato compatível com Chat Completions existente é uma hipótese testada com mocks. Liste autenticação, modelos, structured output, limites, timeout, proxy/CA e política de dados a confirmar. Mantenha schemas internos e validações/revisão. Não crie fallback silencioso para provedores externos.
7. **Acesso:** preserve API por `/api` na mesma origem e proxy interno em loopback. Enquanto o acesso corporativo não estiver pronto, acesso individual por túnel SSH autorizado pode servir ao diagnóstico. Acesso compartilhado exige autenticação/autorização e HTTPS adequados. Confirme Entra, audiência, escopos, grupo/overage, redirects, hostname e confiança de certificados; não libere CORS amplo ou desative TLS para fazer o teste passar.
8. **Persistência e primeiro uso:** volumes, SQLite/WAL, usuário/permissões, migrações, worker único, cache e dados fictícios de demonstração. Manuais públicos devem ser ingeridos novamente ou provisionados por caminho aprovado e rastreável; confirme vigência, origem e hashes. Não leve dados internos ou bancos locais no clone.
9. **Operação:** start/stop/restart, status, logs, health, comportamento após logout/reboot da VM, tarefas interrompidas, atualização da aplicação e dos manuais, backup com checksum, restore em volume separado e rollback de imagem versus dados. Não prometa que retorno de imagem desfaz uma migração incompatível.
10. **Aceite funcional:** abra o site e um evento fictício; processe entradas sintéticas; confira as 12 seções, PT/EN, citações, estados, revisão e bloqueios; baixe Word; execute smoke; valide persistência após reinício e restauração isolada. Inclua teste do acesso autorizado e rejeição de acesso não autorizado quando a integração estiver disponível.
11. **Troubleshooting:** indisponibilidade da API, logs de proxy/API/modelos, resolução de nomes na rede Podman, origem/rotas, porta em uso, systemd do usuário, permissões/SELinux, downloads bloqueados, CA/proxy, recursos insuficientes e configuração corporativa incompleta. Separe o problema específico de inatividade do WSL dos problemas da VM Linux nativa.

Não copie variáveis presumidas ou comandos de outros projetos. Verifique o comportamento nos scripts e configurações existentes. Separe ações do administrador da VM das ações do usuário da aplicação.

**Critério de garantia:** demonstrar instalação reproduzível e critérios verificáveis, sem afirmar sucesso em um ambiente inacessível. Se houver acesso autorizado à VM, execute o runbook e registre distribuição, versões, commit, comandos e resultados. Se não houver, valide o que for possível em ambiente Linux isolado disponível e entregue checklist de preflight, evidências e bloqueios explícitos para execução na B3. Validação no WSL não comprova boot, rede, identidade ou políticas da VM corporativa. Identifique claramente o que falta para declarar o deploy concluído.

### 8. Testes, consistência e aceite da revisão

- Execute a suíte existente pelos scripts do projeto, em isolamento e com dados fictícios, e registre o total real, comando, ambiente, duração e resultado. Use os 50 testes anteriores como referência histórica; não ajuste testes apenas para manter essa contagem.
- Valide sintaxe dos scripts e execute checks/build/smoke pertinentes às alterações. Se modificar configuração, metadados de template ou código para corrigir o deploy, cubra a mudança com testes que avaliem comportamento relevante.
- Reexecute avaliações longas com modelos somente quando necessárias para verificar mudanças em seu fluxo; não apresente um resultado antigo como uma execução nova.
- Confira links relativos, âncoras importantes, nomes de arquivos, comandos, referências ao TXT removido, consistência entre documentos e renderização do HTML. Diferencie referências históricas intencionais de links operacionais quebrados.
- Faça inspeção final do diff e `git diff --check`. Verifique que nenhum artefato sensível ou dado de execução será incluído no futuro commit.
- Evite afirmações absolutas sobre precisão, segurança corporativa, completude normativa ou desempenho. Cada conclusão deve ter evidência ou condição de validação.

A revisão será aceita quando:

1. Todos os Markdown relevantes tiverem sido revisados e o escopo textual estiver consolidado, sem perda de requisitos.
2. O TXT estiver removido somente após consolidação, com referências operacionais corrigidas.
3. A apresentação refletir produto, implementação, limitações e próxima etapa reais.
4. O Cursor tiver uma entrada curta, mapa de código, estado atual e próxima tarefa clara, sem instrução para reconstruir o projeto.
5. O runbook cobrir um clone limpo em VM Linux de desenvolvimento, com comandos verificáveis, pré-requisitos, operação, persistência, testes e bloqueios corporativos explícitos.
6. Código e dados existentes permanecerem preservados, e os testes executados e limites de validação estiverem registrados com honestidade.

### 9. Entrega final

Registre a revisão em `docs/DOCUMENTATION_REVIEW.md`, de forma concisa: data, base inspecionada, matriz dos arquivos revisados, contradições resolvidas, requisitos consolidados, testes efetivamente executados, validação do deploy por ambiente e pendências para a B3. Evite duplicar o runbook ou os relatórios anteriores.

Ao finalizar, informe em português:

- Arquivos criados, atualizados e removidos, com links.
- Onde está a especificação que substitui o TXT.
- Qual arquivo o Cursor deve ler primeiro e qual é a próxima atividade.
- Testes executados, resultados e limitações.
- Estado do preparo para deploy e o que ainda precisa ser confirmado ou executado na VM.
- Pendências reais e situação do repositório para o commit do usuário.

Não encerre apenas com um plano: execute esta revisão e produza os arquivos. Quando houver dependências corporativas indisponíveis, conclua as partes independentes e deixe o procedimento e o ponto de retomada precisos, sem simular validação.

## FIM DO PROMPT
