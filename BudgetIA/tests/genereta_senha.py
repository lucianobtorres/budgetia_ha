import streamlit_authenticator as stauth

# Mude 'sua_senha_super_secreta' para a senha que você quer usar
hashed_password = stauth.Hasher(["sua_senha_super_secreta"]).generate()
print(hashed_password[0])
