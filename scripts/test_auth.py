import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import sys
import os
import bcrypt

print('Chemin courant :', os.getcwd())
config_path = 'config.yaml'
print('Fichier config.yaml existe ? ', os.path.isfile(config_path))

try:
    with open(config_path) as file:
        config = yaml.load(file, Loader=SafeLoader)
    print('YAML credentials:', config['credentials'])
    print('Hash dans YAML (admin):', config['credentials']['usernames']['admin']['password'])
    print('Hash généré localement pour password123:', stauth.Hasher(['password123']).generate()[0])
except Exception as e:
    import traceback
    print('Exception:', e)
    traceback.print_exc()
sys.stdout.flush()

password = b'password123'
hash = bcrypt.hashpw(password, bcrypt.gensalt(rounds=12))
print(f"Bcrypt hash for password123: {hash.decode()}")

# input("Appuyez sur Entrée pour quitter...") 