# SimpliFAQ — Prompts iniciais

## 1. Classificação por domínio
Objetivo: decidir quais domínios devem participar do evento.

Instruções centrais:
- use apenas evidências fornecidas;
- não invente aplicabilidade;
- explique brevemente o motivo;
- retorne saída estruturada;
- sinalize revisão humana em caso de dúvida.

## 2. Recuperação orientada
Para cada domínio:
- recuperar evidências do evento atual;
- recuperar FAQs históricas semelhantes;
- recuperar terminologia/estilo relevante;
- manter os três contextos logicamente identificados.

## 3. Geração bilíngue
Instruções:
- gerar PT e EN simultaneamente;
- manter equivalência semântica;
- não adicionar informação sem fonte;
- seguir padrão linguístico recuperado;
- produzir perguntas objetivas;
- apontar fontes usadas;
- marcar revisão humana quando necessário.

## 4. Validação factual
Pergunta:
"Cada afirmação desta resposta está diretamente suportada pelas evidências recuperadas?"

Retornar:
- supported: true/false
- unsupported_claims
- conflicting_sources
- requires_human_review

## 5. Equivalência PT/EN
Verificar se:
- o conteúdo factual é o mesmo;
- números, datas e condições são preservados;
- não há informação extra em apenas um idioma;
- a terminologia segue o guia aprovado.
