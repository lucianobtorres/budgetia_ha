# Changelog

## v1.0.68
- **Estabilização Frontend**: Correção de tipos TypeScript no PWA (DistributionPieChart e Chat).
- **Correção de Testes**: Ajuste nos caminhos de importação para os modelos de domínio no frontend.
- **Sincronização de Dependências**: Garantia de paridade entre `pyproject.toml` e `poetry.lock` no repositório do Home Assistant.

## v1.0.65 - v1.0.67
- **Blindagem de Elite (AI Shielding)**: Implementação de *Strict Grounding* e *FactChecker* (Chain of Verification) para eliminar alucinações financeiras.
- **Otimização Semântica**: Implementação de cache de embeddings no Redis, reduzindo custos de API e acelerando a categorização em até 10x.
- **Correção de Deploy**: Ajuste nos caminhos do GitHub Actions para suportar a nova estrutura DDD e templates de planilha.
- **Redis Persistente**: Configuração de persistência AOF para o cache de inteligência.

## v1.0.64
- **Refatoração DDD**: Migração completa para Arquitetura Limpa (Domain-Driven Design).
- **Suporte Multi-LLM**: Integração estável com OpenAI, Gemini 2.0 e Groq.
- **Nova UI PWA**: Interface moderna em React com suporte a notificações Push.

## v1.0.63
- Correções de estabilidade na persistência Excel.
- Melhoria na detecção automática de colunas.
