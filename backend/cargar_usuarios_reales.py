import os
import sys
from pathlib import Path

# Add backend directory to sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')

if os.environ.get('DATABASE_URL'):
    os.environ['DEBUG'] = 'False'

import django
django.setup()

from django.contrib.auth.models import User

usuarios = [
    {
        'id': 1,
        'username': 'james',
        'email': 'jairo.lm@gmail.com',
        'password': 'pbkdf2_sha256$1000000$tWjyljyFeh7vWGlmS4qYVc$6EMWV1EVaCf2gu7Ih7G3z2QjnUtEEQrHcaoXHybXIVY=',
        'is_superuser': True,
        'is_staff': True,
        'is_active': True,
    },
    {
        'id': 2,
        'username': 'admin',
        'email': 'qqqq@gmail.cl',
        'password': 'pbkdf2_sha256$1000000$nJ0vCgPNJxnURydOYkj5Sx$OsDoBqnPlFnCKwI0bdBwpLtWwjxyNDG2pzk0WqmDd9M=',
        'is_superuser': True,
        'is_staff': True,
        'is_active': True,
    },
    {
        'id': 3,
        'username': 'jairo',
        'email': 'jjj@gmail.com',
        'password': 'pbkdf2_sha256$1000000$Nw23FUHgWnWuhNpqqRyXhR$O1JcGjmTxZgfuovxwfiS+fJlHMwOjI2jA55OXAKJEgs=',
        'is_superuser': True,
        'is_staff': True,
        'is_active': True,
    },
]

def cargar_usuarios():
    print("Iniciando carga de usuarios reales...")
    for u_data in usuarios:
        user_id = u_data['id']
        username = u_data['username']
        
        user = None
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                user = User(pk=user_id)

        user.pk = user_id
        user.username = username
        user.email = u_data['email']
        user.password = u_data['password']
        user.is_superuser = u_data['is_superuser']
        user.is_staff = u_data['is_staff']
        user.is_active = u_data['is_active']
        user.save()
        print(f"Usuario {username} (ID: {user_id}) sincronizado correctamente.")

    print("¡Sincronización de usuarios completada con éxito!")

if __name__ == '__main__':
    cargar_usuarios()
