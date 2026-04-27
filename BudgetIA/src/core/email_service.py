import logging

import resend

from config import EMAIL_FROM, RESEND_API_KEY

logger = logging.getLogger(__name__)

if RESEND_API_KEY:
    resend.api_key = RESEND_API_KEY
else:
    logger.warning("⚠️ RESEND_API_KEY não encontrada. EmailService inativo.")


class EmailService:
    """
    Serviço centralizado para envio de emails transacionais via Resend.
    """

    @staticmethod
    def send_email(
        to: str | list[str],
        subject: str,
        html_content: str,
        text_content: str | None = None,
    ) -> bool:
        """
        Envia um email genérico.
        """
        if not RESEND_API_KEY:
            logger.info(f"📧 [MOCK EMAIL] Para: {to} | Assunto: {subject}")
            return True

        try:
            params = {
                "from": EMAIL_FROM,
                "to": to,
                "subject": subject,
                "html": html_content,
            }
            if text_content:
                params["text"] = text_content

            r = resend.Emails.send(params)
            logger.info(f"✅ Email enviado via Resend: {r}")
            return True
        except Exception as e:
            logger.error(f"❌ Erro ao enviar email: {e}")
            return False

    @staticmethod
    def send_welcome_email(to: str, name: str) -> bool:
        """
        Envia email de boas-vindas.
        """
        subject = "Bem-vindo ao BudgetIA! 🚀"
        html = f"""
        <h1>Olá, {name}!</h1>
        <p>Estamos muito felizes em ter você conosco.</p>
        <p>O BudgetIA é o seu assistente financeiro pessoal, powered by AI.</p>
        <p>Você pode acessar seu dashboard aqui: <a href="https://budgetia.app">Acessar BudgetIA</a></p>
        <br>
        <p>Qualquer dúvida, responda este email.</p>
        <p>Equipe BudgetIA</p>
        """
        return EmailService.send_email(to, subject, html)

    @staticmethod
    def send_password_reset(to: str, token: str) -> bool:
        """
        Envia email com token de reset de senha.
        """
        subject = "Recuperação de Senha - BudgetIA"
        link = f"http://localhost:5173/reset-password?token={token}"

        html = f"""
        <h1>Recuperação de Senha</h1>
        <p>Recebemos uma solicitação para redefinir sua senha.</p>
        <p>Clique no link abaixo para criar uma nova senha:</p>
        <a href="{link}" style="padding: 10px 20px; background-color: #3b82f6; color: white; text-decoration: none; border-radius: 5px;">Redefinir Senha</a>
        <p>Ou copie o token: {token}</p>
        <p>Se não foi você, ignore este email.</p>
        """
        return EmailService.send_email(to, subject, html)

    @staticmethod
    def send_verification_email(to: str, token: str, name: str) -> bool:
        """
        Envia email de verificação de conta.
        """
        subject = "Verifique sua conta - BudgetIA"
        link = f"http://localhost:5173/verify?token={token}"  # Frontend Route

        html = f"""
        <h1>Bem-vindo, {name}!</h1>
        <p>Obrigado por se cadastrar no BudgetIA.</p>
        <p>Para ativar sua conta, clique no link abaixo:</p>
        <a href="{link}" style="padding: 10px 20px; background-color: #10b981; color: white; text-decoration: none; border-radius: 5px;">Verificar Email</a>
        <p>Ou copie o token: {token}</p>
        """
        return EmailService.send_email(to, subject, html)
