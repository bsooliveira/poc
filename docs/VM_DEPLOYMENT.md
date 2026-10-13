# Preparação para VM Linux e B3 GPT

Esta orientação prepara a transição da POC; nenhuma credencial ou integração corporativa real foi usada nos testes.

## POC em outra VM Linux

Copie o repositório para uma VM com Podman 5+ e systemd. Execute como usuário dedicado sem privilégios, com espaço para imagens, pesos e backups:

```bash
bash scripts/build.sh --training
bash scripts/install-wsl.sh
```

O instalador funciona em Linux comum apesar do nome. O endereço publicado continua em `127.0.0.1:8080`. Para acesso individual enquanto as integrações são preparadas, use um túnel SSH autorizado: `ssh -L 8080:127.0.0.1:8080 usuario@vm`. Os caminhos do projeto podem ser diferentes; os Quadlets usam o home do usuário, volumes nomeados e imagens locais.

Para início dos serviços sem sessão interativa, um administrador configura `loginctl enable-linger USUARIO`. No WSL usado para esta POC, linger já está habilitado. Isso não liga o notebook nem inicia sozinho uma distribuição WSL parada.

## Contrato do adapter B3 GPT

`backend/app/generation.py` é a fronteira do provedor. `LLM_PROVIDER=b3` usa um endpoint HTTPS compatível com Chat Completions:

- URL completa em `B3_API_URL`.
- Header `Authorization: Bearer ...`, vindo de `B3_API_KEY`.
- Corpo com `model`, `messages`, `temperature` e `response_format`.
- Resposta esperada: `choices[0].message.content`, contendo JSON.
- Validação por Pydantic, com uma tentativa de reparo do JSON; falhas não são aprovadas nem enviadas ao histórico.

Os testes de contrato usam `httpx.MockTransport`, chave e modelo fictícios, sem chamada de rede. Antes da integração real, confirmar com o responsável pelo B3 GPT a URL, autenticação, formato de resposta, suporte a structured output, limites, retenção e versão do modelo. Se o contrato for diferente, alterar somente a fronteira do provedor e seus testes, preservando os schemas internos e a revisão humana.

## Configuração corporativa futura

Use `.env.corporate.example` como referência e guarde o arquivo preenchido **fora do repositório e da imagem**, em `~/.config/simplfaq/app.env`, com permissão 600. A configuração incompleta falha ao iniciar, por projeto.

Entra ID exige tenant, client ID da aplicação web, audience GUID da API, scope delegado `access_as_user` e grupo autorizado. A API valida assinatura RS256/JWKS, issuer do tenant, audience, validade, tenant, escopo e grupo. Configure access tokens v2 e as group claims; usuários com group overage são bloqueados até a organização definir uma resolução segura via Graph ou role mapping. Os redirects MSAL precisam incluir o hostname HTTPS escolhido. Não usar `AUTH_MODE=local` no acesso corporativo.

## TLS e operação

Mantenha o container web na porta de loopback 8080. O Nginx existente na VM pode terminar TLS com certificado corporativo e encaminhar para essa porta. Preserve o `Host` original no proxy e configure o redirect HTTPS correspondente no Entra. Não inclua certificados ou chaves na imagem. A configuração de TLS real depende do hostname/certificado e não foi executada nesta POC.

Para smoke de um ambiente protegido, use `SMOKE_HEALTH_ONLY=1 bash scripts/smoke.sh https://HOST` para checks públicos; para validar a API protegida, forneça um access token de teste em `SMOKE_AUTH_TOKEN`, sem colocá-lo na linha de comando ou versioná-lo.

Atualização local: `bash scripts/update.sh --training`. Ela preserva tags anteriores, testa se não há tarefas ativas, cria backup, reconstrói e verifica os serviços. Se o build/deploy falhar, restaura as tags anteriores. Para mudanças de schema futuras, garantir migração compatível ou restauração de dados junto com o rollback.

CI/CD corporativo pode executar os mesmos scripts em agente Linux autorizado e promover tags imutáveis entre pré-produção e produção. Configuração do Azure DevOps, agentes, certificados e aprovação de promoção permanece pendente da organização; não é uma dependência da POC.
