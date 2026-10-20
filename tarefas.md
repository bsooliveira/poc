# Tarefas

## Papel e resultado esperado
Atue como arquiteto especialista em Microsoft Azure Backup, segurança de nuvem, IAM, recuperação de desastres, Terraform e FinOps. Crie um documento técnico em português brasileiro, em formato Markdown, chamado `proposta-arquitetura-backup-azure.md`, destinado a um Cloud Center of Excellence, engenharia de cloud, SRE, operações, segurança e FinOps. O objetivo é apresentar **uma alternativa para avaliação**, e não desqualificar ou substituir automaticamente uma arquitetura existente. Use tom profissional, colaborativo e baseado em evidências.

## Contexto genérico
Considere um ambiente Azure corporativo com numerosas subscrições de projetos, sob um mesmo tenant Microsoft Entra ID, e uma subscrição de serviços compartilhados. O modelo de referência concentra serviços de backup em infraestrutura compartilhada. Avalie uma alternativa na qual cada subscrição de projeto recebe um Resource Group específico e padronizado para sua infraestrutura de backup.

**Não insira nome de empresa, número real de subscrições, identificadores, nomes de times internos, regiões específicas reais ou quaisquer outros dados internos.**

## Material de referência fornecido ao Cursor
O usuário apontará para um direcionador interno de arquitetura de backup. Leia o material **somente se ele estiver disponível em ambiente corporativo autorizado**. Use-o como base técnica para identificar requisitos, controles e pressupostos que merecem ser mantidos, reavaliados ou submetidos a uma PoC. Não copie diagramas, textos internos ou configurações específicas. Não revele nomes, IDs, endpoints, quantidades reais, falhas reais, políticas internas ou outros detalhes reidentificáveis. O documento final deve ser genérico e independente do material original. Não invente detalhes não documentados. Se houver conflito entre o material e a documentação pública atual da Microsoft, sinalize o ponto para revisão técnica, sem afirmar que a arquitetura atual está incorreta.

## Arquitetura proposta para avaliação
1. Criar em cada subscrição de projeto um **Resource Group dedicado a backup**, administrado operacionalmente pelo SRE do projeto.
2. Estabelecer um **baseline completo de infraestrutura** com Recovery Services Vault, Backup Vault e componentes auxiliares. Identifique Storage Accounts, identidades e demais serviços somente quando exigidos pelo workload ou pela arquitetura; diferencie padrão solicitado, necessidade técnica e possíveis recursos ociosos. Não pressuponha que Storage Account externa seja sempre necessária ao Azure Backup.
3. Provisionar e governar os recursos por módulos Terraform homologáveis, Azure Policy, hierarquia de Management Groups, tags e padrões de configuração. Proponha como evitar deriva de configurações e como manter inventário, auditoria e monitoramento centralizados.
4. Manter Azure Key Vault com Customer Managed Keys (CMK) sob governança centralizada em serviços compartilhados, **condicionado à compatibilidade técnica por tipo de vault, workload e região**. Comparar chaves gerenciadas pela plataforma e CMK, apontar dependência compartilhada e riscos de revogação, rotação e indisponibilidade de chaves.
5. Definir autonomia operacional dos SREs por RBAC de menor privilégio, com **Microsoft Entra PIM** para elevação temporária, aprovação, justificativa e registro de auditoria em alterações privilegiadas.
6. Proteger dados por imutabilidade bloqueada, soft delete e controles compatíveis com cada tipo de vault e workload. Considerar **Resource Guard / Multi-User Authorization**, sob equipe administrativamente independente, para operações críticas suportadas. PIM não substitui imutabilidade ou autorização independente. Resource Group não deve ser descrito como fronteira segura contra administradores privilegiados da subscrição.
7. Identificar riscos residuais do tenant compartilhado, inclusive comprometimento de identidades com privilégios abrangentes. Não alegar que subscrições distintas garantem isolamento absoluto.

## Análises obrigatórias
- Examinar as possíveis fragilidades do modelo centralizado: atribuição de custo/FinOps, dependência operacional, permissões cross-subscription, concentração de privilégios e alterações administrativas, escala, requisitos regionais, restaurações em massa e blast radius. **Não afirmar que comprometer uma subscrição implica automaticamente perda de todos os backups**; considerar os mecanismos de proteção habilitados.
- Comparar vantagens potenciais da alternativa descentralizada: custos apropriados por projeto, autonomia de SRE, segregação granular, redução de interdependências operacionais, personalização controlada de políticas e recuperação em cenários de incidente. Distinguir vantagem intrínseca de benefício dependente de controles bem implementados.
- Avaliar contrapartidas: maior quantidade de recursos, custos e manutenção, padronização, consistência de segurança, limites por vault, dependência do tenant e do Key Vault central, monitoramento e governança em escala.
- Verificar a capacidade de recuperação entre subscrições, limites de suporte, condições regionais, tipos de workload e restrições de CMK, sem assumir aplicabilidade universal.
- Propor modelo RACI entre COE, engenharia de cloud, SRE, segurança/IAM, operações e FinOps. Especificar quem aprova operações destrutivas e quem mantém controles independentes.
- Criar matriz comparativa entre arquiteturas centralizada e descentralizada nos eixos segurança, ransomware, RBAC/PIM, FinOps, operação, escalabilidade, governança, disponibilidade, DR, complexidade, custo e riscos residuais.
- Elaborar PoC com critérios verificáveis: Terraform, RBAC, PIM, operações com Resource Guard, imutabilidade locked, soft delete, compatibilidade CMK, backup e restore, cenários de comprometimento, monitoramento e custo por projeto. Incluir critérios de aprovação e condições para não adoção.

## Requisitos de rigor e fontes
Priorize **documentação oficial e atual da Microsoft**, com URLs verificáveis. Diferencie Recovery Services Vault e Backup Vault em **cada afirmação técnica relevante**. Diferencie recursos suportados, pré-requisitos, restrições regionais, licenciamento/custo, workload e limitações. Não invente suporte ou números. Se não houver acesso à documentação atual, sinalize explicitamente os itens a validar em vez de afirmar certezas. Separe fatos documentados, observações da arquitetura de referência, hipóteses e recomendações. Não inclua configurações internas reais nem copie diagramas da fonte. Use exemplos inteiramente fictícios.

## Estrutura mínima do Markdown
1. Resumo executivo e propósito da avaliação
2. Premissas e escopo
3. Modelo centralizado — benefícios e desafios potenciais
4. Arquitetura descentralizada proposta e organização por Resource Group
5. Segurança contra ransomware: imutabilidade, soft delete, Resource Guard, RBAC e PIM
6. Criptografia e dependências de CMK / Key Vault centralizado
7. Governança e automação com Terraform / Azure Policy
8. FinOps e atribuição de custos
9. Modelo operacional e matriz RACI
10. Matriz comparativa das arquiteturas
11. Riscos residuais e decisões em aberto
12. Plano de PoC, testes e critérios de aceite
13. Recomendação condicionada a validação
14. Referências oficiais Microsoft

Inclua tabelas úteis e, se agregarem valor, diagramas Mermaid genéricos. Gere o arquivo `proposta-arquitetura-backup-azure.md` sem revelar informações que identifiquem uma organização ou seu ambiente.

## Revisão final de confidencialidade
Antes de concluir, revise o arquivo resultante para evitar: nomes reais de empresas, nomes de projetos/equipes internas, quantidades reais, tenant/subscription IDs, endpoints, URLs internas, diagramas reais, exposições de vulnerabilidades particulares, políticas internas literais ou dados financeiros. Não apresente a ausência desses termos como prova de anonimização absoluta: preserve apenas informações arquiteturais genéricas e publique somente após revisão humana e validação de conformidade interna.
