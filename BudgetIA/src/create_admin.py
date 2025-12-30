import sys
import os

# Adiciona o diretório src ao path para imports funcionarem
sys.path.append(os.path.join(os.path.dirname(__file__)))

from interfaces.api.utils.security import create_user

def main():
    username = "admin"
    password = "password123"
    email = "admin@example.com"
    name = "Administrador"

    print(f"Criando usuário '{username}'...")
    try:
        if create_user(username, name, email, password):
            print(f"✅ Usuário '{username}' criado com sucesso!")
            print(f"Senha: {password}")
        else:
            print(f"⚠️  Usuário '{username}' já existe.")
    except Exception as e:
        print(f"❌ Erro ao criar usuário: {e}")

if __name__ == "__main__":
    main()
