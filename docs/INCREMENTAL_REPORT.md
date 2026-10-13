# SimpliFAQ — implementação incremental e revisão final

Data de referência: 12/10/2026, America/Sao_Paulo. Preparação da POC para 13/10/2026. Este relatório complementa os registros históricos `VALIDATION.md` e `FETCH_FIX.md`.

## Diagnóstico e preservação

O repositório existente foi analisado antes das alterações: API FastAPI, React/TypeScript, SQLite/WAL, ingestão Office/PDF/texto, embeddings multilíngues, Ollama, revisão humana, Word, LoRA experimental e operação com Quadlet. Nenhum componente foi recriado. A suíte inicial confirmou **34 testes: 30 backend e 4 frontend**. Os 19 testes citados no início do histórico já estavam incorporados à suíte ampliada.

O estado real diferia do prompt: havia **dois eventos e duas fontes, mas apenas uma FAQ em revisão**, com 12 perguntas; o segundo evento estava em rascunho. Não havia aprovação. O conteúdo do outro arquivo enviado pelo usuário não foi utilizado como fixture. Os testes usam exclusivamente dados fictícios, bancos temporários e PDFs normativos sintéticos. A ingestão funcional dos dois manuais públicos é registrada separadamente abaixo.

O evento Encontro Horizonte permanece em revisão, versão 5, uma fonte, 12 perguntas. O JSON completo antes/depois da atualização apresentou o mesmo SHA-256:

`a0f0e1bf39205272815808f148280973477305d84c909ed1e6bdb3e99b8c5b62`.

A interface identifica explicitamente FAQs do formato anterior. Uma nova geração solicitada pelo revisor aplica as 12 seções e preserva o resultado anterior no histórico; não houve migração automática do conteúdo legado. Para registros já aprovados, é necessário outro evento, preservando sua imutabilidade.

A verificação do volume ativo confirmou SQLite íntegro, dois arquivos originais válidos, dois PDFs normativos válidos, dois eventos, um chunk factual e 36 registros de auditoria. Nenhum evento, documento, FAQ ou aprovação foi apagado. A migração 002 acrescenta tabelas normativas e metadados aos chunks, sem substituir tabelas existentes. É idempotente, inclusive após retorno de uma imagem legada que reajusta `user_version=1`.

A causa anterior do “Failed to fetch” era o encerramento do WSL por inatividade, seguido de indisponibilidade do proxy/API; a interface também não saía do estado de carregamento após falha. A sessão WSL oculta iniciada pelo Windows, o limite de leitura de 15 segundos e a mensagem com nova tentativa foram preservados. A API continua em `/api` na mesma origem, sem liberação de CORS nem exposição da porta 8000. O detalhe do evento foi novamente aberto no Chrome com sucesso. Evidências completas: [FETCH_FIX.md](FETCH_FIX.md).

## Matriz requisito → código → verificação

| Requisito | Implementação | Evidência automatizada ou funcional |
|---|---|---|
| Definição única, ordem A/B/1–10 | `app/faq_template.json`, `template.py`, snapshot no resultado | `test_unique_template_and_additive_idempotent_migration`, ordem na UI e no Word |
| Três estados de aplicabilidade, nenhuma exclusão por ausência | `template_pipeline.conservative_sections`, schemas e API de seções | Ausência de documentos, negação de outro assunto, tema inventado e conflito explícito |
| Documento do evento, financeiro e transcrição distintos | Tipo `financial`, ingestão e contexto do pipeline | Amostra fictícia DOCX/XLSX/TXT; lacunas por tipo ausente |
| Manuais públicos rastreáveis | `normatives.py`, `002_normatives.sql`, tela Manuais públicos | Duas ingestões oficiais funcionais; descoberta e falha HTTP com fixtures sintéticas |
| Câmara e Depositária separadas | Filtros de sistema, versão, vigência/status | `test_separation_versions_deactivation_and_future_manuals`, citação cruzada rejeitada |
| Versões antigas e futuras | Histórico preservado, desativação, revalidação de vigência brasileira | Desativação, referências obsoletas e ativação de documento pendente somente na data válida |
| PT antes de EN, IDs preservados | Schemas `PTGeneration`/`Translations`, UUID5, revisão | Traduções com mesmos IDs, rejeição de afirmações sem fonte e números trocados |
| Evidência por afirmação | `claims.py`, `validation.py`, UI e Word | Fonte específica incorreta bloqueada; claim normativo sintético com página/versão/hash |
| Classificação e deduplicação | Palavras completas/plurais, seção canônica, registro de consolidação | “ativos” não casa com “derivativos”; tema inválido rejeitado; respostas iguais consolidadas |
| Divergências e cronograma | Guardas de aplicabilidade, `timeline_conflicts`, verificador assistivo | Datas distintas mantêm ambas as fontes; início posterior ao fim; negação contraditória não exclui tema |
| Revisão humana integral | API de itens/seções, versão otimista e decisão transacional | Aprovação bloqueada até itens e 12 seções revisados; nenhum item aprovado automaticamente |
| Word exatamente com 12 seções | `output.py`, template/snapshot, status e evidências | Ordem/contagem automatizada, download no Chrome, renderização LibreOffice/Poppler |
| Compatibilidade anterior | Resultado legado preservado; `/runs?mode=legacy` explícito | Os 30 testes backend anteriores continuam executados; helper legado seleciona esse modo |
| Operação e persistência | Quadlet, scripts de início/backup/update/rollback, `verify_storage` | Smoke, checksum, integridade e restauração em volume separado |
| LoRA e integrações futuras | Fluxo existente, exemplos externos vazios, docs de VM | Regressões de treinamento/providers; experimento offline histórico preservado; nenhum acesso corporativo |

Não há subitens ou regras de negócio inventados. Os títulos em inglês são traduções editoriais das seções textuais fornecidas e precisam de revisão linguística corporativa futura. As palavras-chave são auxiliares de recuperação, não regras normativas.

## Manuais públicos ingeridos

Página oficial consultada e arquivada por hash: [B3 — estrutura normativa de pós-negociação](https://www.b3.com.br/pt_br/regulacao/estrutura-normativa/estrutura-normativa/pos-negociacao/). Verificação funcional em 12/10/2026 às 20:41, horário brasileiro. O PDF de abril mencionado no prompt **não foi presumido vigente nem usado**. A página declarava as seguintes versões em vigor e as capas confirmaram as datas:

| Sistema | Versão/vigência declarada | Páginas | Chunks |
|---|---|---:|---:|
| Câmara B3 | 22/06/2026 | 408 | 847 |
| Central Depositária de Renda Variável B3 | 02/01/2026 | 108 | 288 |

São **516 páginas e 1.135 chunks normativos**, com o mesmo modelo de embeddings multilíngues da aplicação. Não foram incorporados documentos internos.

Consulta funcional em inglês também recuperou trechos portugueses: Câmara, páginas 142/201/144, cossenos 0,5671/0,5664/0,5641; Depositária, páginas 88/89/66, 0,5713/0,5681/0,5647. Cada consulta retornou somente o sistema e a versão selecionados. A consulta da versão de abril não ativa retornou zero resultados. Esses escores demonstram recuperação multilíngue, não correção normativa das respostas.

Câmara: [PDF oficial](https://www.b3.com.br/data/files/57/86/30/A8/4C8D0A105BF9020AAC094EA8/MPO%20da%20Camara%20B3.pdf), SHA-256 `11c4ba89908c7f6f5eee4d0de6b5e55b3f1b537ded9bc26d0cea9ab2d22af7dd`.

Depositária: [PDF oficial](https://www.b3.com.br/data/files/10/E4/9B/8B/173D0A105BF9020AAC094EA8/MPO%20da%20Central%20Depositaria%20de%20%20RV%20B3.pdf), SHA-256 `2b5ed6972160b41c04d9e28e44f43893893daececba6808f3ceabbec3107824e`.

Metadados persistidos: título, sistema, URL de catálogo/PDF, hash, versão, vigência, verificação, ingestão, status, origem, página/localização/seção e modelo de embeddings. PDF e snapshot do catálogo permanecem no volume `simplfaq-data`, fora do Git.

### Atualização dos manuais

1. Termine gerações e treinamentos. Faça backup antes de uma atualização importante.
2. Na UI, selecione **Manuais públicos → Verificar e atualizar manuais públicos**, ou execute `bash scripts/update-manuals.sh` no projeto dentro do AlmaLinux.
3. A fila existente redescobre ambos os links “Sem Marca” na página oficial, exige HTTPS no domínio B3, confere capa/data, limita download e texto extraído e registra o resultado.
4. Mesmo hash: atualiza a verificação sem duplicar chunks. Nova versão: preserva a anterior, ativa apenas a versão vigente mais recente. Futuras ficam pendentes; nova verificação na data válida pode ativá-las. Datas consideram America/Sao_Paulo. Uma desativação humana explícita não é revertida automaticamente.
5. Confira o status da tarefa, versões e hashes. Mudança no site, erro HTTP ou capa divergente produz falha explícita. Cada documento é atualizado atomicamente; se o segundo download falhar, a atualização válida do primeiro pode ter sido concluída. Confira ambos os registros antes de continuar.
6. FAQs existentes não são reescritas pela atualização. Citações desativadas aparecem como pendência e bloqueiam aprovação; gere uma nova versão ou revise as evidências. As referências históricas permanecem rastreáveis.

## Testes e avaliação qualitativa

`scripts/test.sh` executa Ruff, pytest, quatro testes Node sem rede e build TypeScript/Vite em Podman. A suíte ampliada executou inicialmente 44 testes backend + 4 frontend. A revisão final acrescentou regressões para aplicabilidade contraditória e avaliação do modelo sem citações pertinentes: **46 backend + 4 frontend = 50 testes**. Um aviso de depreciação Starlette/TestClient persiste; não houve falha funcional. Os testes frontend verificam erro de rede acionável, recuperação de leitura, erro HTML do proxy, cancelamento e ausência de reenvio automático de escritas.

Os testes backend adicionais verificam definição única, migração, ausência de fontes, estrutura Word, estados, deduplicação, seleção por sistema/versão, desativação, vigência futura, cronograma, avaliação do modelo sem citações, rejeição de fatos particulares extraídos somente de manuais gerais, download falho honesto, revisão de todas as seções, fonte por afirmação, números trocados, IDs estáveis e temas inventados. Os **46 testes backend** também passaram diretamente na imagem instalada, sem montar o código-fonte (22,09 segundos). As fixtures normativas são PDFs de teste construídos em memória; não reproduzem regras reais da B3.

A amostra `evaluation/validate_template.py` usa três fontes totalmente fictícias. O modo determinístico produziu 12 seções, três perguntas bilíngues, três consolidações de respostas iguais e cobertura de citações das três fontes. Os valores `100,00`/`100.00`, a data e as negações foram preservados. Nenhuma verificação determinística por afirmação apresentou erro. Todas as perguntas permanecem pendentes e a aprovação foi bloqueada. O verificador semântico é indisponível nesse modo: **0% nas métricas automáticas não significa reprovação factual nem aprovação**.

Qualidade observada além dos testes: perguntas do modo demo são extrativas e genéricas por arquivo; fatos duplicados em resumo/cronograma/estrutura/precificação são consolidados no primeiro item e deixam aviso nas outras seções. A amostra não é uma FAQ editorial final. Sete seções têm informação insuficiente; contratos são explicitamente excluídos pela transcrição fictícia. Não foram criados contatos, tributos, procedimentos ou datas adicionais. O banco da amostra não contém os PDFs públicos; os avisos de falta de normativo nesse banco são esperados. A integração normativa do pipeline é coberta separadamente por teste sintético com citações exatas.

Artefatos locais gerados: `artifacts/template12/sample/event.json`, `summary.json`, `faq.docx` e `artifacts/template12/rendered/faq.pdf`/PNG. O Word foi renderizado em quatro páginas e inspecionado visualmente, com pares PT/EN, todas as seções e fontes. Blocos de avaliação permanecem juntos para evitar justificativa órfã. O download no Chrome retornou HTTP 200 e arquivo DOCX de 39.280 bytes. No ambiente isolado em localhost:8081, a revisão da seção de contatos foi salva, incrementou a versão e manteve a aprovação bloqueada. Esse teste não alterou o banco ativo em localhost:8080.

A avaliação real Ollama/FastEmbed utiliza o mesmo gerador de fixtures, banco temporário e cache local. Seu resultado é registrado após a conclusão, separadamente do modo determinístico. Os resultados históricos de embeddings de 384 dimensões e treinamento LoRA offline permanecem em `VALIDATION.md`; não são novos benchmarks desta versão.

A primeira avaliação real desta revisão terminou em 395 segundos com zero perguntas: o modelo não vinculou corretamente as evidências à avaliação das seções. Isso foi tratado como falha de qualidade, não como validação bem-sucedida. O pipeline foi corrigido para conservar a indicação conservadora nas fontes quando a avaliação do modelo não cita nenhuma evidência pertinente, registrar a lacuna e exigir revisão humana. Exclusões explícitas também preservam a evidência, sem aceitar justificativa inventada pelo modelo. A fixture automatizada reproduz essa falha. O script de avaliação agora exige ao menos uma pergunta para esse cenário com fatos explícitos; uma estrutura vazia sozinha não passa.

**Resultado real após a correção:** Qwen 1.5B/FastEmbed terminou em **1.916 segundos (31 min 56 s)**, com 12 seções, cinco perguntas PT/EN, cinco consolidações, duas das três fontes citadas nas perguntas (66,7%) e todas as revisões pendentes. A transcrição foi utilizada na avaliação de não aplicabilidade, mas não nas perguntas; a métrica de cobertura conta citações dos itens, não as evidências das avaliações de seção. As referências das perguntas pertencem às fontes recuperadas.

**A qualidade dessa saída real não foi aprovada.** Todos os cinco itens têm erros determinísticos: afirmações não cobrem a resposta, traduções/afirmações omitem ou acrescentam conteúdo e há números vinculados ao trecho incorreto. O modelo também introduziu a moeda “$” e explicações de estratégias não informadas nas fontes. O verificador permaneceu inconclusivo (groundedness/equivalência automáticas 0%). Esses problemas foram sinalizados nos itens, e o teste confirmou bloqueio de aprovação. A saída é um rascunho para correção, não uma FAQ factual pronta. A revisão humana deve corrigir texto, tradução e evidências antes de confirmar qualquer item; erros determinísticos impedem salvar uma confirmação de revisão.

O teste real valida ingestão, fluxo, estrutura, rastreabilidade dos IDs, exportação e bloqueios; o resultado **não valida precisão do Qwen 1.5B**. O resumo integral está em `evaluation/samples/summary-ollama-after-fix.json`. O Word real e JSON completo ficam em `artifacts/template12/real-v2`, separados da amostra determinística mais limpa. Não houve promoção de modelo, treinamento desses rascunhos nem aprovação automática. Qualidade linguística/normativa e desempenho em CPU permanecem pendentes de revisão editorial e avaliação com um modelo mais adequado.

A cópia da amostra exclusivamente fictícia em `evaluation/samples/faq-template12-ficticia.docx`, acompanhada do resumo, está versionada para revisão. É um rascunho determinístico, sem documentos reais ou normativos oficiais incorporados no banco da fixture.

Capturas locais da revisão visual: `artifacts/template12/template-interface.jpg` e `manuais-interface.jpg`. A observação do Chrome confirmou exatamente 12 seções, seção de contatos revisada na fixture e aprovação desabilitada. A interação de exportação produziu HTTP 200 e o DOCX esperado na pasta Downloads; a espera de evento de download da ferramenta expirou, mas arquivo e log confirmaram a conclusão. Essa limitação da automação não foi tratada como falha do site.

## Operação e execução

No Windows:

```powershell
powershell -ExecutionPolicy Bypass -File C:\repos\simpliFAQ\scripts\Start-SimpliFAQ.ps1
```

Ou execute `wsl -d AlmaLinux-10 -- bash /mnt/c/repos/simpliFAQ/scripts/start.sh` e abra **http://localhost:8080**. A configuração efetiva é externa: `~/.config/simplfaq/app.env`. Não a inclua no Git. A POC usa autenticação local apenas em desenvolvimento e publica somente loopback.

No AlmaLinux:

```bash
cd /mnt/c/repos/simpliFAQ
bash scripts/status.sh
bash scripts/test.sh
bash scripts/smoke.sh
bash scripts/backup.sh
bash scripts/update.sh --training
bash scripts/update-manuals.sh
```

O update aplicado nesta revisão criou `~/simplfaq-backups/simplfaq-20261013T001900Z.tar` (12/10 às 21:19 local), com SHA-256. Tags de rollback daquela atualização: `localhost/simplfaq-api:previous-20261013T001825Z` e `localhost/simplfaq-web:previous-20261013T001825Z`. O rollback de imagem não reverte dados. Importar backup exige um volume novo; não sobrescreva o ativo. Instruções completas e checksum em README/VM_DEPLOYMENT.

O checksum desse TAR foi conferido e ele foi importado em `simplfaq-restored-template12`. A validação somente de leitura nesse volume separado confirmou integridade SQLite, dois originais e dois manuais com hashes válidos. O volume ativo não foi substituído. A validação de sintaxe dos scripts Bash também passou. `git diff --check` apontou apenas espaços finais que representam quebras Markdown no handoff original preservado; o código novo não apresentou esses avisos.

A correção subsequente da avaliação sem citações foi instalada pela mesma rotina, com novo backup `simplfaq-20261013T002856Z.tar` e tags anteriores `localhost/simplfaq-api:previous-20261013T002842Z` / `localhost/simplfaq-web:previous-20261013T002842Z`. Imagens instaladas: API `9e8224db568a`, web `871e28cd19dc`. Smoke e integridade passaram; o JSON do evento preservado manteve o mesmo hash após essa atualização.

O aviso de formato legado foi acrescentado depois, somente na interface. Novo build TypeScript/Vite e smoke passaram; a imagem web final é `f4d9490d5b96`. Essa atualização reiniciou apenas o proxy, sem interromper Ollama ou alterar o banco.

A última revisão corrigiu a cobertura de fontes para 0% quando não existem documentos, em vez de exibir 100%. O caso de ausência de entradas verifica também essa métrica. A suíte completa manteve **50 testes aprovados**, e os 46 backend passaram novamente na imagem final, sem rede nem montagem de fontes, em 24,45 segundos. Imagem API final: `a25ff21623d7`.

Atualização final concluída com backup `simplfaq-20261013T010641Z.tar` (12/10 às 22:06 local) e checksum válido. Rollback dessa atualização: `bash scripts/rollback.sh localhost/simplfaq-api:previous-20261013T010626Z localhost/simplfaq-web:previous-20261013T010626Z`. Os containers de validação foram encerrados; permanecem somente os três serviços da POC. Verificação final: SQLite e hashes dos dois originais/dois manuais válidos; JSON de Encontro Horizonte idêntico ao baseline. O volume fictício de avaliação permanece separado, sem afetar os dois eventos reais do workspace local.

## Publicação do código

O Git local e o remoto indicado não tinham commits; a entrega constitui o primeiro snapshot versionado do projeto existente e suas melhorias incrementais. Branch `main`, remoto `https://github.com/bsooliveira/poc.git`. O commit contém código, handoff preservado, instruções de operação, relatórios e amostras exclusivamente fictícias. Banco ativo, documentos enviados, PDFs públicos baixados, configuração efetiva, caches, pesos e backups não são publicados. A identificação do autor foi configurada apenas neste repositório, conforme o e-mail fornecido pelo usuário.

Para outra VM Linux, ajuste caminhos e configuração de referência conforme [VM_DEPLOYMENT.md](VM_DEPLOYMENT.md). O mecanismo de manutenção do WSL é ignorado em Linux comum. Entra ID e adapter B3 GPT permanecem opcionais e dependem de contrato/configuração futuros; a POC não exige esses serviços, não armazena credenciais corporativas e não valida integração corporativa real.

## Limitações e decisões pendentes

- Modelo Qwen 1.5B em CPU é lento e pode produzir classificação, justificativas e traduções inconclusivas. A conservação da estrutura não demonstra completude ou precisão normativa; revisão humana continua obrigatória.
- O ensaio real teve erros em todos os cinco itens: não há evidência de qualidade suficiente para publicação sem correção manual. O modo demo serve a testes com fixtures bilíngues; não substitui tradução livre de documentos somente em português.
- Rollback para imagem anterior ao template preserva o armazenamento, mas não oferece o novo fluxo de revisão de seções/normativos. Para revisar ou aprovar resultados do novo template, use a versão atual; não trate compatibilidade de leitura como compatibilidade de todas as políticas de aprovação.
- Heurísticas de palavras completas ajudam a classificar, mas não substituem interpretação do evento. Negação explícita em fontes conflitantes permanece pendente. Conflitos de datas estruturadas são detectados deterministicamente; divergências semânticas gerais dependem do verificador e do revisor.
- O cronograma reconhece rótulos com datas ISO/BR e início/fim. Não calcula dias úteis, feriados, horários-limite, exceções corporativas ou precedência normativa. Essas regras não foram especificadas e não foram inventadas.
- Extração normativa por página usa layout e preserva texto de tabelas quando extraível; não reconstrói todas as células como tabela estruturada. O cabeçalho de seção é heurístico e pode ser aproximado; página, texto e offset permitem conferir o PDF. OCR não está integrado.
- Deduplicação exata consolida respostas idênticas com mesmas fontes. Quase duplicatas são apenas sinalizadas; equivalência semântica e reclassificação editorial precisam de revisão. Não há cobertura garantida de todos os chunks.
- Verificações de números/datas/citações são conservadoras. Idiomas, condições e regras fiscais exigem revisão especializada; nenhum valor sem evidência deve ser aceito como fato do evento.
- O sistema permanece uma POC local de usuário único, sem multitenancy, TLS corporativo ou operação distribuída. Auditoria não resiste ao administrador do host. LoRA continua experimental, sem ativação automática.
- Revalidação de manuais é explícita, sem agenda automática. Acesso à internet é necessário para atualizar fontes públicas e baixar pesos iniciais; inferência e documentos permanecem locais na configuração da POC.
- O repositório GitHub deve conter código, documentação, fixtures fictícias e configuração sem segredos. Volumes, PDFs baixados, documentos enviados, pesos, backups, JSON de eventos e `.env` efetivo ficam fora do commit.
