# Documentação: BudgetIA (Monorepo)

O **BudgetIA** é um assistente financeiro inteligente que processa seus gastos utilizando IA e mantém tudo organizado em uma planilha Excel (ou Google Sheets).

## 🚀 Configuração Inicial

### 1. Provedores de IA
O sistema suporta múltiplos provedores. Você deve informar ao menos uma chave de API:
- **OpenAI**: Para o modelo GPT-4o (recomendado para precisão).
- **Gemini**: Modelo Flash 2.0 (excelente custo-benefício).
- **Groq**: Llama 3.3 (ultra-rápido).

### 2. Planilha Financeira
O Add-on busca por uma planilha mestra para iniciar. 
- Se você não informar um caminho, ele criará uma nova em `/data/MinhasFinancas.xlsx`.
- Você pode mapear colunas customizadas na interface web.

### 3. Notificações e Telegram
Para receber avisos proativos:
1. Crie um bot no [@BotFather](https://t.me/botfather).
2. Informe o `TELEGRAM_TOKEN` nas configurações.
3. Inicie uma conversa com seu bot e o BudgetIA detectará seu Chat ID automaticamente.

## 🧠 Inteligência e Cache
O sistema utiliza um servidor **Redis** interno para:
- **Categorização Semântica**: Aprender como você categoriza seus gastos.
- **Cache de Embeddings**: Economizar tokens de API ao processar descrições repetidas.
- **Fact Checking**: Auditar respostas da IA para evitar alucinações financeiras.

## 🛠️ Solução de Problemas
- **Logs**: Verifique a aba "Log" do Add-on para mensagens de erro detalhadas.
- **Redis**: O banco de dados de cache é persistente e sobrevive a reinicializações.
