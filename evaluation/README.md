# Avaliação da POC

## Avaliação do template de 12 seções

`validate_template.py` cria um evento isolado com DOCX oficial fictício, XLSX financeiro fictício e transcrição TXT fictícia. Verifica a ordem das 12 seções, bloqueio de aprovação, citações por afirmação, equivalência numérica e estrutura Word; salva JSON, resumo e DOCX em `artifacts/template12`. O relatório não confunde essas verificações com precisão semântica ou validação de uma operação real.

Exemplo determinístico, no AlmaLinux WSL, após o build:

```bash
cd /mnt/c/repos/simpliFAQ
podman volume create simplfaq-sample-data
podman run --rm --network none --env PYTHONPATH=/app \
  --env ENVIRONMENT=development --env AUTH_MODE=local \
  --env LLM_PROVIDER=demo --env EMBEDDING_PROVIDER=hash \
  --volume simplfaq-sample-data:/data:U \
  --volume "$PWD/evaluation:/evaluation:ro" \
  --volume "$PWD/artifacts:/artifacts:rw" \
  localhost/simplfaq-api:poc python /evaluation/validate_template.py
```

Para avaliar Ollama/FastEmbed, utilize rede `simplfaq`, `LLM_PROVIDER=ollama`, `EMBEDDING_PROVIDER=fastembed`, `DATA_DIR=/tmp/template-real` e cache em `/data/models` montado do volume existente. Isso mantém o banco temporário separado do banco ativo. Execute isoladamente de qualquer geração/treinamento da interface. O importador dos manuais oficiais é validado funcionalmente em separado; os testes normativos automatizados usam PDFs sintéticos e `MockTransport`, sem documentos reais ou internos.

`training-fixture.jsonl` contém quatro exemplos **sintéticos**, com dois contextos bilíngues. Serve apenas ao smoke test de treinamento; não representa um dataset histórico corporativo aprovado.

O conjunto de testes em `backend/tests` cobre extração de Office/texto, uploads inválidos, versões, chunks, isolamento por evento/empresa, histórico apenas aprovado, números sem suporte, citações indevidas, deduplicação, concorrência por versão, DOCX, auditoria e recuperação após interrupção. Usa embeddings lexicais e provedor determinístico para ser rápido e independente de rede.

Os testes reais do modelo local são descritos em `docs/VALIDATION.md`. Resultados de avaliação devem separar:

- Cobertura de documentos e chunks: calculada pela aplicação, não mede completude semântica.
- Groundedness/equivalência automática: julgamento do modelo + verificações determinísticas; não é uma garantia de qualidade.
- Revisão humana: itens confirmados explicitamente e intervenções registradas.
- Fine-tuning: loss de treino/validação, número de exemplos, modelo, seed e duração. Não interpretar redução de loss como melhora factual.

Para ampliar a avaliação desta POC, crie mais eventos inteiramente fictícios, com perguntas esperadas, fatos obrigatórios, perguntas sem resposta e conflitos. Separe eventos completos entre treino e teste. Faça revisão independente do inglês e das condições normativas. Não inclua documentos internos, credenciais ou dados pessoais reais.

`validate_local.py` exercita ingestão de cinco fontes fictícias, embeddings, geração, citações, bloqueio de aprovação, busca e Word, em banco temporário. `smoke_pipeline.py` exercita um cenário menor com o modelo padrão. Ambos precisam de `ENVIRONMENT=development`, `AUTH_MODE=local`, `LLM_PROVIDER=ollama`, `EMBEDDING_PROVIDER=fastembed`, `DATA_DIR` temporário, cache de modelos já baixado e acesso à rede privada Podman `simplfaq`; não use o banco ativo como `DATA_DIR`. As inferências são demoradas e devem ser executadas isoladamente das tarefas da interface.

`bash evaluation/validate_training.sh` executa treinamento real com a fixture e recarrega o adapter sem rede; recusa execução durante geração da aplicação ou diagnósticos locais ativos. Os resultados ficam em `artifacts/training-smoke` e não são inseridos no histórico aprovado.
