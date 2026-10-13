# Amostras inteiramente fictícias

- `faq-template12-ficticia.docx`: rascunho determinístico com 12 seções, três perguntas PT/EN, três fontes sintéticas e revisão humana pendente. Não representa operação ou procedimento real.
- `summary-demo.json`: métricas técnicas dessa amostra. Cobertura de citações não mede completude; o modo demo não dispõe de validação semântica.
- `summary-ollama-before-fix.json`: falha de qualidade observada antes da correção da avaliação sem citações: zero perguntas. Mantido para transparência, não como resultado aprovado.
- `summary-ollama-after-fix.json`: ensaio real com cinco rascunhos, ainda com erros de consistência por afirmação/PT/EN. Registra funcionamento do fluxo e bloqueios; a qualidade editorial não foi aprovada.

O gerador reproduzível está em `../validate_template.py`; instruções em `../README.md` e resultados em `docs/INCREMENTAL_REPORT.md`. PDFs reais dos manuais públicos, bancos ativos, uploads, credenciais e pesos não integram esta pasta.
