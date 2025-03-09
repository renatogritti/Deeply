import hashlib
import getpass

password = getpass.getpass("Digite a senha do admin: ")
password_hash = hashlib.sha256(password.encode()).hexdigest()
print(f"Hash da senha: {password_hash}")