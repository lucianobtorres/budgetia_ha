# 💰 BudgetIA - Seu Assistente Financeiro Pessoal

O **BudgetIA** é um assistente de finanças pessoais inteligente e privado, projetado para rodar localmente no seu Home Assistant. Ele combina o poder de LLMs (como GPT-4, Llama 3) com a simplicidade de planilhas do Excel ou Google Sheets.

![BudgetIA Dashboard](https://github.com/lucianobtorres/BudgetIA/raw/main/pwa/public/pwa-512x512.png)

## ✨ Funcionalidades
- 💬 **Chat Natural**: Converse com suas finanças ("Quanto gastei em Uber esse mês?").
- 📊 **Dashboard Rico**: Gráficos e indicadores financeiros em tempo real.
- 📱 **Interface Mobile**: Funciona como um app nativo no seu celular (PWA).
- 🔒 **Privacidade**: Seus dados ficam no seu Home Assistant e na sua planilha.
- 🔄 **Híbrido**: Use uma planilha local (.xlsx) ou conecte ao Google Sheets.

---

## 🚀 Instalação no Home Assistant

### Opção 1: Adicionar Repositório (Recomendado)
1. Vá em **Settings** > **Add-ons** > **Add-on Store**.
2. Clique nos três pontos (menu) no canto superior direito > **Repositories**.
3. Adicione a URL do repositório do BudgetIA:
   ```
   https://github.com/lucianobtorres/BudgetIA
   ```
4. Procure por "BudgetIA" na lista e clique em **Install**.

### Opção 2: Instalação Local (Para Desenvolvedores)
1. Copie a pasta do projeto para `/addons/local/budgetia` no seu Home Assistant.
2. Reinicie o Home Assistant ou recarregue a loja de Add-ons.
3. Instale o Add-on "BudgetIA" que aparecerá na seção "Local".

---

## ⚙️ Configuração

Antes de iniciar, vá na aba **Configuration** do Add-on e preencha conforme abaixo:

### 1. Inteligência Artificial (Obrigatório)
Você precisa de *pelo menos uma* chave de API para o cérebro do assistente. Recomendamos a **Groq** pela velocidade extrema e custo zero (atualmente).

| Opção | Descrição | Exemplo |
| :--- | :--- | :--- |
| `groq_api_key` | Chave da [Groq Cloud](https://console.groq.com) (**Recomendado**) | `gsk_...` |
| `gemini_api_key` | Chave do [Google AI Studio](https://aistudio.google.com) | `AIza...` |
| `openai_api_key` | Chave da OpenAI (GPT-4) | `sk-...` |

### 2. Planilha (Opcional)
Se você já tem uma planilha do BudgetIA ou quer conectar uma existente:

| Opção | Descrição |
| :--- | :--- |
| `planilha_path` | URL da sua Planilha Google **OU** link de visualização de um .xlsx no Drive. |

> **Dica:** Se deixar este campo vazio, o BudgetIA iniciará no **Modo de Onboarding**, onde você poderá criar uma planilha nova ou fazer upload de uma existente através da interface visual.

### 3. Outras Configurações

| Opção | Padrão | Descrição |
| :--- | :--- | :--- |
| `log_level` | `info` | Nível de detalhe dos logs (`debug` para solução de problemas). |
| `upstash_redis_url` | (Vazio) | URL de um Redis externo (opcional). Se vazio, usa cache em memória/disco local (limitado). |

---

## 🖥️ Como Usar

1. Inicie o Add-on. Aguarde alguns segundos (veja a aba **Log** para confirmar se iniciou: `🚀 Iniciando Servidor API...`).
2. Clique em **OPEN WEB UI**.
3. **Primeiro Acesso**:
   - Se você configurou o `planilha_path`, verá seus dados.
   - Se não, siga o assistente de configuração na tela para criar sua planilha.
4. **Login**: O sistema usa autenticação integrada. No primeiro uso, pode pedir para criar um usuário/senha local.

---

## 🛠️ Solução de Problemas

- **Erro "AttributeError: 'GoogleDriveFileHandler'..."**:
  - *Solução*: Certifique-se de que está rodando a versão 1.0.0 ou superior. Este erro foi corrigido.
- **Não carrega a planilha**:
  - *Solução*: Verifique se a planilha está compartilhada com o e-mail da conta de serviço (se estiver usando modo avançado) ou se o link é público/acessível.
- **Groq/OpenAI Error**:
  - *Solução*: Verifique se a chave da API está correta e não tem espaços extras.

## 📄 Licença
MIT License - Sinta-se livre para modificar e usar.
