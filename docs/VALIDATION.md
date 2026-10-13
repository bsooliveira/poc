# Entrega da POC SimplFAQ — 12 de outubro de 2026

Este documento registra a primeira entrega. A versão incremental posterior, com template de 12 seções, manuais públicos e regressão dos 34 testes existentes, está em [INCREMENTAL_REPORT.md](INCREMENTAL_REPORT.md). As contagens e limites abaixo são históricos dessa primeira entrega.

Preparação para a demonstração de 13/10/2026. Desenvolvimento incremental sobre o projeto existente, com preservação do handoff, dos dados persistidos e do evento fictício anterior. Não foram usadas credenciais reais, documentos internos ou informações sensíveis. Builds, API, modelos, testes Python, treinamento e renderização de Word foram executados em containers Podman rootless no AlmaLinux-10 do WSL.

## Funcionalidades concluídas

- Interface React para eventos, upload de várias fontes, acompanhamento da fila, FAQs PT/EN, consulta RAG, revisão, aprovação/rejeição e experimentos de fine-tuning.
- Extração de PDF com texto, DOCX, PPTX, XLSX, CSV, TXT, Markdown e JSON, com limites, validação de conteúdo e versionamento de fontes.
- Embeddings multilíngues ONNX de 384 dimensões; busca por cosseno e reranking híbrido. Isolamento factual por evento e uso separado de histórico aprovado/guia linguístico.
- Ollama local com Qwen 1.5B, JSON estruturado, citações rastreáveis a arquivo/localização/chunk e lacunas de cobertura explícitas.
- Verificações determinísticas de citações e números; verificação semântica assistiva, com sinalização de justificativas repetidas como inconclusivas. Aprovação exclusivamente após revisão humana documentada de todos os itens.
- Edição de domínio, perguntas, respostas e citações, controle otimista de versão, aprovação imutável, auditoria append-only e recuperação de tarefas interrompidas.
- Exportação Word bilíngue com fontes, notas e marcação de rascunho; layout revisado para evitar separação desnecessária dos blocos.
- Dataset aprovado para LoRA, divisão por contexto para evitar vazamento entre PT/EN, artefatos ZIP com métricas/proveniência e utilitário de inferência do adapter. Sem promoção automática ao gerador.
- Quadlets/systemd, volumes persistentes, configuração externa, scripts de início/parada/status, backup com checksum, atualização e rollback. Resolução dinâmica do backend no Nginx após reinício da API.
- Adapter opcional B3 GPT e autenticação Entra preparados no código; configuração de referência e instruções para VM Linux, sem dependência desses serviços para a POC.

## Testes executados e evidências

| Verificação | Resultado observado |
|---|---|
| Baseline antes de alterações | 20 testes aprovados: os 19 anteriores e uma regressão da gramática Ollama já presente |
| Suíte final `scripts/test.sh` | **30 testes aprovados**, Ruff sem erros e build TypeScript/Vite aprovado |
| Imagem final instalada | Os mesmos **30 testes aprovados** novamente diretamente na imagem, sem montagem do código-fonte; 11,37 s |
| Ingestão e fluxo automatizado | Fixtures fictícias de Office/PDF/texto; uploads inválidos, versões, isolamento de fontes, revisão, aprovação, auditoria e recuperação |
| Contratos de providers | Ollama e B3 via `httpx.MockTransport`; normalização do JSON, autenticação fictícia e reparo limitado; nenhuma chamada corporativa |
| Guardas adicionais | Contexto excessivo recusado antes da inferência e antes de um reparo que exceda o limite; verificador repetitivo inconclusivo; erro de configuração sem eco de segredo sintético |
| Embeddings reais | Consulta inglesa sobre inscrição recupera texto português relacionado: cosseno **0,6575**, contra **−0,1285** para texto sem relação; 384 dimensões |
| Pipeline real com Qwen 3B, prompt 1.1 | Cinco fontes fictícias, quatro chunks factuais, seis itens PT/EN em **1.767 s**; citações válidas, aprovação bloqueada sem revisão, busca em inglês e Word válidos |
| Cobertura nessa amostra | **75%** dos chunks/fontes factuais citados; `acesso.pdf` identificado como lacuna. Não é cobertura total nem benchmark representativo |
| Verificador real Qwen 1.5B | Dois pares e um controle negativo numérico; detectada justificativa genérica repetida. O controle 120→999 é bloqueado independentemente pelo verificador numérico |
| Pipeline final Qwen 1.5B, prompt 1.2 | Banco temporário, uma fonte fictícia, cinco itens PT/EN em cerca de **12 minutos**, cobertura de citações 100%, Word em rascunho e todos os itens pendentes. O cenário ainda apresentou domínio incorreto e redundâncias; justificativas repetidas foram sinalizadas como inconclusivas |
| LoRA real offline | Quatro exemplos sintéticos, dois passos, dois exemplos de treino e dois de validação; loss de validação **1,7471→1,6723**; adapter salvo e recarregado, resposta de formato online correta |
| Interface no Chrome | Lista e detalhe, PT/EN, controles de revisão, aprovação desabilitada e download Word verificados; screenshot em `artifacts/simplfaq-interface.jpg` |
| Word visual | Documento revisado renderizado com LibreOffice/Poppler em container isolado; quatro páginas inspecionadas, sem cortes, com títulos, pares PT/EN e referências legíveis |
| Operação | Backup, SHA-256, importação em volume separado, integridade SQLite e checksums dos originais válidos; atualização e rollback automático exercitados; API reiniciada sem necessidade de reiniciar o proxy |

A suíte usa provider determinístico e mocks para ser rápida e repetível. A inferência e o treinamento reais foram verificados separadamente. Os testes de contrato não comprovam integração real com B3/Entra. O aviso de depreciação `Starlette/TestClient/httpx` não falhou a suíte; é uma atualização futura de dependências de teste. O healthcheck efetivo é o definido no Quadlet, mesmo quando Podman avisa que o HEALTHCHECK do Containerfile base é ignorado no formato OCI.

Artefatos locais, ignorados pelo Git: `artifacts/local-model/{event.json,summary.json,faq.docx,verifier-check.json}`, `artifacts/training-smoke/adapter/metrics.json`, `artifacts/qa/revised/` e `artifacts/final-smoke/`. O teste de treinamento levou 8,42 s de treino, excluindo carregamento dos pesos; não se compara diretamente ao tempo total de uma geração.

## Estado instalado após a atualização

Os três containers estão **healthy**, e `scripts/start.sh`/smoke passaram após o deploy final. Imagens instaladas: API `9a874e0b38bc`, web `f231da025339` após a [correção de conexão](FETCH_FIX.md); Ollama 0.18.0. O evento anterior `602267a9-87b1-4ed1-9362-0b48af10c693` continua em revisão, versão 5, com seus 12 itens preservados. Os diagnósticos reais utilizaram bancos temporários, sem aprovar ou sobrescrever esse resultado.

Backup final: `/home/bruno/simplfaq-backups/simplfaq-20261012T141759Z.tar`, com SHA-256 conferido. A verificação do volume ativo retornou integridade SQLite `ok`, dois originais com checksums válidos, dois eventos, um chunk e 32 registros de auditoria. A restauração histórica de teste foi feita em `simplfaq-restorecheck-20261012`, sem trocar o volume ativo.

Rollback das imagens desta atualização, sem reverter os dados:

```bash
bash scripts/rollback.sh \
  localhost/simplfaq-api:previous-20261012T141745Z \
  localhost/simplfaq-web:previous-20261012T141745Z
```

## Correções desta continuação

Gramática Ollama simplificada mantendo validação Pydantic completa; restrição de IDs de evidência e limitação do tamanho de contexto. Normalização numérica corrigida para não confundir 1,5 com 15. Entrada do verificador sem os próprios flags de julgamento do gerador. Justificativas repetidas não contam como validação positiva. Correção manual de domínio na interface e métrica que distingue edição efetiva de simples confirmação. Exportador Word com agrupamento dos blocos, títulos pretos e metadados. Configuração sem exposição dos valores de entrada em erros. Auditoria da interrupção de treinamento. Scripts operacionais com guarda de tarefas ativas, backup consistente, recuperação de imagens e smoke com repetição de todas as verificações.

## Limitações e trabalho futuro

1. **Qualidade do modelo local:** 1.5B/3B podem repetir perguntas, escolher domínio incorreto, omitir fontes ou avaliar equivalência incorretamente. As taxas `grounded_rate`/`equivalence_rate` são julgamentos do próprio modelo, não medidas certificadas de precisão. O 3B retornou equivalência 0% nessa amostra apesar de pares aparentemente equivalentes. A revisão humana é obrigatória; nenhum ajuste de prompt transforma esses modelos em validadores confiáveis.
2. **Desempenho:** notebook com quatro threads, cerca de 7,7 GiB disponíveis ao WSL e sem GPU NVIDIA. Geração pode demorar vários minutos; o 3B é apenas diagnóstico e não substitui o padrão 1.5B. Bases grandes precisam de avaliação de capacidade, cobertura e índice ANN.
3. **Fine-tuning:** o smoke de dois passos prova execução/salvamento/recarga, não melhora factual ou linguística. A configuração normal usa oito passos. É necessário ampliar dataset aprovado, holdout e avaliação antes de servir adapters.
4. **Documentos:** PDFs digitalizados precisam de OCR externo. Limites de upload/contexto são explícitos. O limite de caracteres não garante ajuste ao orçamento de tokens do modelo.
5. **Corporativo:** contrato real B3, tenant/grupos Entra, TLS, CI/CD, VM autorizada e teste de acesso corporativo permanecem pendentes. A POC não exige nenhum deles.
6. **Revisão final de UI:** a indisponibilidade anterior do Chrome foi superada na investigação de conexão de 12/10. O evento e seus 12 itens carregaram, o campo de domínio foi inspecionado e a revisão foi cancelada sem salvar. Consulte [a correção de conexão](FETCH_FIX.md) para os testes de falha e recuperação.

## Executar e validar

No PowerShell:

```powershell
wsl -d AlmaLinux-10 -- bash /mnt/c/repos/simpliFAQ/scripts/start.sh
```

Acesse **http://localhost:8080**. Use **Explorar um evento de exemplo** ou documentos fictícios. Confira fontes e PT/EN antes de aprovar; exportação em revisão é rascunho.

No AlmaLinux, no diretório do projeto:

```bash
bash scripts/test.sh
bash scripts/smoke.sh
bash scripts/status.sh
bash scripts/backup.sh
bash scripts/update.sh --training
```

Configuração efetiva fora do repositório: `~/.config/simplfaq/app.env`. Backup: `~/simplfaq-backups`. Procedimentos completos, restauração e rollback no [README](../README.md); implantação futura em [VM_DEPLOYMENT.md](VM_DEPLOYMENT.md). Mantenha acesso local em loopback e execute somente um worker da API. Para repetir LoRA offline, sem jobs ativos: `bash evaluation/validate_training.sh`.
