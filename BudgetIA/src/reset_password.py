import sys
import os

# Adiciona o diretório src ao path para imports funcionarem
sys.path.append(os.path.dirname(__file__))

from interfaces.api.utils.security import update_password, load_users

def main():
    # 1. Verificação de Chave Mestre (Segurança)
    # No Add-on, essa variável deve ser configurada nas Options/Env do HA.
    master_key = os.getenv("ADMIN_MASTER_KEY")
    
    # Em modo local (Windows), facilitamos. No Docker/HA, exigimos.
    is_docker = os.getenv("DEPLOY_MODE") in ["DOCKER", "SAAS"]
    
    if is_docker and not master_key:
        print("\n❌ ERRO DE SEGURANÇA:")
        print("Para rodar este script em produção/container, você deve definir a variável")
        print("de ambiente ADMIN_MASTER_KEY com um valor seguro.")
        return

    if len(sys.argv) < 3:
        print("\nUso: [ADMIN_MASTER_KEY=xxx] python src/reset_password.py [usuario] [nova_senha]")
        print("\nUsuarios disponiveis:")
        try:
            data = load_users()
            usernames = data.get("credentials", {}).get("usernames", {}).keys()
            for u in usernames:
                print(f" - {u}")
        except:
            print(" - Erro ao carregar usuarios.")
        return

    username = sys.argv[1]
    new_password = sys.argv[2]

    # No Windows local, se não tiver master_key, usamos um valor padrão ou permitimos
    if not is_docker and not master_key:
        print("⚠️  Aviso: Rodando sem ADMIN_MASTER_KEY (Ambiente Local detectado).")

    print(f"Redefinindo senha para '{username}'...")
    try:
        update_password(username, new_password)
        print(f"✅ Senha de '{username}' atualizada com sucesso!")
    except Exception as e:
        print(f"❌ Erro ao atualizar senha: {e}")

if __name__ == "__main__":
    main()
