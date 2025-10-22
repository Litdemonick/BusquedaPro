# Twittor — Mini Twitter con Django + Tailwind (CDN)

Proyecto educativo minimalista que imita lo básico de Twitter: timeline, publicar (texto + imagen), likes, respuestas, perfiles y seguir/dejar de seguir.

## Requisitos
- Python 3.10+
- pip y venv (recomendado)
- (Opcional) Node NO es necesario: usamos Tailwind por CDN.

## Instalación
```bash
cd twittor
python -m venv .venv
source .venv/bin/activate  # En Windows: .venv\Scripts\activate
pip install -r requirements.txt

python manage.py migrate
python manage.py createsuperuser  # opcional
python manage.py runserver
```

Visita: http://127.0.0.1:8000/

## Funcionalidades
- Registro, login, logout (Django auth)
- Timeline: tus posts + los de la gente que sigues
- Crear publicación (hasta 280 caracteres, imagen opcional)
- Likes y respuestas
- Perfiles con avatar y bio
- Seguir / dejar de seguir

## Notas
- Archivos subidos (avatars, imágenes) se guardan en `media/`.
- En producción: cambia `SECRET_KEY`, desactiva `DEBUG`, configura `ALLOWED_HOSTS` y un servidor para estáticos/media.


## Novedades
- Retuits y citas (quote tweet)
- Búsqueda y hashtags con linkify
- Notificaciones por likes, comentarios, follows y retuits/citas
- Botón de like con HTMX (no recarga)

**Importante:** como se agregaron campos nuevos, ejecuta:
```bash
python manage.py makemigrations
python manage.py migrate
```


## Poblar con datos de demostración

Instala Faker y ejecuta el comando `seed`:

```bash
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py seed --fresh --users 25 --tweets 150 --images --superuser
# usuario superuser (opcional): admin / admin12345
# usuarios normales: contraseña por defecto demo12345
```

Parámetros útiles:
- `--users N` cantidad de usuarios (por defecto 25)
- `--tweets N` cantidad de publicaciones base (por defecto 150)
- `--retweet_ratio 0.15` proporción de retuits respecto a tweets base
- `--quote_ratio 0.10` proporción de citas
- `--like_factor 0.25` fracción aproximada de usuarios que dan like a cada tweet
- `--comment_factor 0.20` fracción de tweets con 1–3 comentarios
- `--images` genera imágenes dummy para algunos tweets
- `--fresh` elimina datos previos (excepto superusuarios)
- `--password` cambia la contraseña por defecto de los usuarios demo
