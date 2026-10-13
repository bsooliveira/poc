# SimpliFAQ — Regras e Guardrails

## Regras de negócio
- Cada domínio deve responder apenas ao seu escopo.
- A geração deve ser rastreável às fontes.
- PT e EN devem representar o mesmo conteúdo.
- A saída final depende de revisão humana.
- Nova FAQ só alimenta o histórico após aprovação.

## Guardrails
- Sem evidência suficiente: não inferir fato.
- Conflito entre fontes: sinalizar conflito.
- Baixa confiança: sinalizar revisão humana.
- FAQ histórica divergente da fonte atual: prevalece a fonte atual.
- Conteúdo não aprovado: não usar como referência histórica.
- Nunca misturar conteúdo de eventos diferentes por similaridade sem checar metadados.
- Qualquer termo normativo ou crítico deve preservar contexto e fonte.

## Observabilidade
Registrar:
- documentos usados;
- chunks recuperados;
- scores;
- reranking;
- prompts/versionamento;
- modelo usado;
- respostas intermediárias;
- validações;
- intervenção humana;
- status de aprovação.

## Segurança e acesso
- Somente usuários autenticados pelo Entra ID.
- Autorizar acesso por grupo/perfil corporativo.
- Não armazenar senhas locais.
- Não versionar tokens, secrets ou credenciais.
- Minimizar privilégios do processo e dos containers.
- Preferir execução rootless no Podman quando permitido.
- Tratar uploads como conteúdo não confiável e validar tipo/tamanho.

## Auditoria
Registrar de forma persistente:
- identidade do usuário;
- data/hora;
- evento;
- ação realizada;
- status da execução;
- versão do modelo e prompt;
- fontes recuperadas;
- alterações humanas;
- aprovação/reprovação.
