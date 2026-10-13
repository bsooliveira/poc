# Correção de conexão ao abrir o evento — 12/10/2026

## Causa identificada

A interface aberta no Chrome exibia `Failed to fetch`. A investigação reproduziu a falha: a API respondeu HTTP 200 logo após iniciar o WSL, mas a distribuição voltou a aparecer como `Stopped` sem uma sessão WSL de usuário mantida aberta. Nas verificações seguintes, os containers haviam desaparecido; novas chamadas `wsl.exe` iniciavam novamente a distribuição e os serviços.

Os logs do Nginx também registraram `connect() failed (111: Connection refused)` e HTTP 502 durante a inicialização, antes de o Uvicorn completar o startup. Quadlet/systemd e linger iniciam os serviços dentro do Linux, mas **não mantêm a instância WSL ligada**. Esse comportamento é [documentado pela Microsoft](https://learn.microsoft.com/en-us/windows/wsl/systemd).

Havia uma segunda falha no frontend: o detalhe fazia uma única leitura e, após a rejeição da promessa, mantinha `event=null` e renderizava indefinidamente “Carregando evento…”. Não havia nova tentativa disponível.

A rota correta é `GET /api/events/602267a9-87b1-4ed1-9362-0b48af10c693`. O frontend usa `/api` na mesma origem da página; Nginx preserva o caminho e o Host até a API. Não foi necessário liberar CORS, alterar autenticação, publicar a porta interna 8000 ou trocar a configuração de rede.

## Alterações

- `scripts/start.sh` inicia uma sessão WSL oculta, lançada pelo Windows, além dos serviços. `Keep-SimplFAQWSL.ps1` registra PID e instante de início fora do repositório e reutiliza a sessão existente. `keep-wsl-alive.sh` mantém um processo de usuário ativo.
- `scripts/stop.sh` para os containers e sinaliza a saída dessa sessão em até cinco segundos. Nenhum volume é removido. VM Linux comum não utiliza o mecanismo Windows.
- Instalação, atualização e rollback também passam pelo início comum, garantindo a sessão WSL quando esses comandos forem usados diretamente.
- `frontend/src/api.ts` traduz falhas de rede para uma mensagem acionável em português. Requisições que escrevem dados não são reenviadas automaticamente.
- `EventWorkspace` distingue carregamento de erro, limita a leitura a 15 segundos e oferece **Tentar novamente** e **Voltar aos eventos**. A nova tentativa lê o mesmo evento, sem gerar novamente a FAQ.
- Acrescentados quatro testes do cliente e sua execução com Node 22 em Podman, sem rede; nenhum pacote adicional necessário.

## Preservação

Backup antes da atualização web: `/home/bruno/simplfaq-backups/simplfaq-20261012T223830Z.tar`, acompanhado de SHA-256. API, schema do banco e volumes não foram alterados. A imagem web anterior está em `localhost/simplfaq-web:before-fetch-fix-20261012`.

As respostas JSON do evento antes e após a atualização são idênticas, com SHA-256 `a0f0e1bf39205272815808f148280973477305d84c909ed1e6bdb3e99b8c5b62`. Permanecem versão 5, uma fonte e 12 itens, em revisão. A verificação de armazenamento retornou SQLite íntegro, dois originais válidos, dois eventos, um chunk e 32 registros de auditoria.

## Validação

- **30 testes do backend** aprovados; Ruff sem erros.
- **4 testes do cliente** aprovados: falha de rede seguida de nova leitura bem-sucedida, ausência de reenvio automático de escrita, erro HTML do proxy e preservação de erros HTTP/cancelamento.
- Compilação TypeScript/Vite aprovada; imagem web aplicada e smoke aprovado.
- Bash e PowerShell sem erros de sintaxe. Início repetido reutilizou o mesmo PID. Parada encerrou a sessão; novo início criou uma nova sessão e restaurou os serviços.
- Chrome: abertura do evento com FAQ PT/EN, fonte e 12 controles de revisão. Falha real simulada com API parada: a página mostrou a mensagem em português e **Tentar novamente**, sem spinner permanente. Após reiniciar os serviços, o botão carregou o mesmo evento. Nenhuma FAQ foi editada ou aprovada.
- Campo de domínio inspecionado no formulário de revisão; cancelamento sem salvar.
- Estabilidade sem chamadas de terminal WSL: HTTP 200 aos 30, 60 e 90 segundos, sempre com versão 5 e 12 itens. A sessão oculta permaneceu ativa, e os três containers ficaram healthy.
- Origem `localhost:8080` com Host correspondente: HTTP 200. Origem `127.0.0.1:8080` com Host correspondente: HTTP 200. Origem diferente do Host: HTTP 403 esperado. Nenhuma proteção de origem foi relaxada.
- Checksum do backup conferido; integridade do armazenamento novamente válida após os testes de parada/reinício.

Evidências locais em `artifacts/fetch-fix/`: JSON anterior/posterior, screenshot da falha recuperável e screenshot do evento carregado. Os artefatos usam o exemplo fictício existente e não são versionados.

## Operação

```powershell
wsl -d AlmaLinux-10 -- bash /mnt/c/repos/simpliFAQ/scripts/start.sh
```

Depois, acesse http://localhost:8080. Não é necessário manter um terminal visível. Para desligar e liberar a sessão:

```powershell
wsl -d AlmaLinux-10 -- bash /mnt/c/repos/simpliFAQ/scripts/stop.sh
```

Reiniciar o Windows ou executar `wsl --shutdown` encerra a sessão; execute o início novamente quando quiser usar o sistema. Essa correção não altera a configuração global de outras distribuições WSL nem mantém o notebook ligado.
