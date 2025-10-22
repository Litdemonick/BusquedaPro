
import random
from io import BytesIO
from pathlib import Path

from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

try:
    from faker import Faker
    HAVE_FAKER = True
except Exception:
    HAVE_FAKER = False

from core.models import UserProfile, Follow, Tweet, Like, Comment, Notification

WORDS = [
    "Django", "Tailwind", "IA", "Python", "MachineLearning", "DeepLearning", "Panamá",
    "UTP", "Chiriquí", "OpenSource", "Dev", "Startups", "Data", "Vision", "CV", "NLP",
    "Docker", "API", "Cloud", "GPU", "IAResponsable", "Sostenibilidad", "Educación"
]

PHRASES = [
    "Probando Twittor 🎉",
    "Hoy aprendí algo nuevo sobre {topic}.",
    "¿Alguien recomienda recursos de {topic}?",
    "Pequeño tip de {topic}: {tip}.",
    "Trabajando en un proyecto de {topic} 🚀",
    "¡Buenos días! #productividad",
    "Dejo este hilo sobre {topic}. #aprendizaje",
    "Pequeño experimento con {topic}.",
    "¿Qué opinan de {topic}?",
    "Demo de interfaz con #Tailwind y #Django"
]

TIPS = ["usa virtualenv", "documenta funciones", "mide antes de optimizar", "usa pruebas unitarias", "aplica PEP8", "cuida la accesibilidad"]

def rand_hashtags(k=2):
    tags = random.sample(WORDS, k=k)
    return " ".join(f"#{t}" for t in tags)

def random_mention(usernames):
    if not usernames:
        return ""
    return " @" + random.choice(usernames)


def make_avatar_png(initial: str, size=128):
    """Genera un PNG simple con color de fondo aleatorio y la inicial centrada.
    Compatible con Pillow 10+ (usa textbbox)."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except Exception:
        return None
    img = Image.new("RGB", (size, size), (random.randint(40,200), random.randint(40,200), random.randint(40,200)))
    d = ImageDraw.Draw(img)
    text = (initial or '?')[0].upper()
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", int(size*0.55))
    except Exception:
        try:
            font = ImageFont.truetype("arial.ttf", int(size*0.55))
        except Exception:
            font = ImageFont.load_default()
    # Medir texto de forma robusta
    try:
        bbox = d.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    except Exception:
        try:
            tw, th = font.getsize(text)
        except Exception:
            tw = int(size * 0.5)
            th = int(size * 0.5)
    d.text(((size - tw)/2, (size - th)/2), text, fill=(255,255,255), font=font)
    from io import BytesIO
    bio = BytesIO()
    img.save(bio, format="PNG")
    from django.core.files.base import ContentFile
    return ContentFile(bio.getvalue())


class Command(BaseCommand):
    help = "Seed database with demo users, tweets, comments, likes, follows, and images."

    def add_arguments(self, parser):
        parser.add_argument("--users", type=int, default=25, help="Número de usuarios a crear")
        parser.add_argument("--tweets", type=int, default=150, help="Número de publicaciones a crear (excluye retuits/citas)")
        parser.add_argument("--fresh", action="store_true", help="Borra datos existentes antes de poblar")
        parser.add_argument("--superuser", action="store_true", help="Crea un superusuario demo: admin / admin12345")
        parser.add_argument("--retweet_ratio", type=float, default=0.15, help="Proporción de retuits sobre el total de tweets reales")
        parser.add_argument("--quote_ratio", type=float, default=0.10, help="Proporción de citas sobre el total de tweets reales")
        parser.add_argument("--like_factor", type=float, default=0.25, help="Fracción de usuarios que podrían dar like a cada tweet")
        parser.add_argument("--comment_factor", type=float, default=0.20, help="Fracción de tweets que recibirán 1-3 comentarios")
        parser.add_argument("--images", action="store_true", help="Intenta generar imágenes dummy para algunos tweets")
        parser.add_argument("--password", type=str, default="demo12345", help="Contraseña por defecto para usuarios demo")

    def handle(self, *args, **opts):
        users_n = opts["users"]
        tweets_n = opts["tweets"]
        fresh = opts["fresh"]
        make_images = opts["images"]
        password = opts["password"]
        retweet_ratio = max(0.0, min(0.9, opts["retweet_ratio"]))
        quote_ratio = max(0.0, min(0.9, opts["quote_ratio"]))
        like_factor = max(0.05, min(0.9, opts["like_factor"]))
        comment_factor = max(0.05, min(0.9, opts["comment_factor"]))

        fake = Faker("es_ES") if HAVE_FAKER else None
        random.seed(42)

        if fresh:
            self.stdout.write(self.style.WARNING("Borrando datos existentes..."))
            Like.objects.all().delete()
            Comment.objects.all().delete()
            Tweet.objects.all().delete()
            Follow.objects.all().delete()
            Notification.objects.all().delete()
            UserProfile.objects.all().delete()
            User.objects.filter(is_superuser=False).delete()

            media = Path(settings.MEDIA_ROOT)
            for sub in ["avatars", "tweets"]:
                p = media / sub
                p.mkdir(parents=True, exist_ok=True)
                for f in p.glob("*"):
                    try:
                        f.unlink()
                    except Exception:
                        pass

        if opts["superuser"]:
            if not User.objects.filter(username="admin").exists():
                User.objects.create_superuser("admin", "admin@example.com", "admin12345")
                self.stdout.write(self.style.SUCCESS("Superusuario admin/admin12345 creado."))

        self.stdout.write(self.style.NOTICE("Creando usuarios..."))
        usernames = []
        users = []
        for i in range(users_n):
            if fake:
                uname = fake.unique.user_name()[:20]
                mail = fake.unique.email()
                bio = fake.sentence(nb_words=8)
            else:
                uname = f"user{i+1}"
                mail = f"user{i+1}@example.com"
                bio = "Bio de demostración"

            if User.objects.filter(username=uname).exists():
                uname = f"{uname[:15]}{i}"

            u = User.objects.create_user(username=uname, email=mail, password=password)
            profile, _ = UserProfile.objects.get_or_create(user=u)
            profile.bio = bio
            profile.save()

            avatar_file = make_avatar_png(uname[:1])
            if avatar_file:
                profile.avatar.save(f"{uname}.png", avatar_file, save=True)

            users.append(u)
            usernames.append(uname)

        # Ensure all users (incl. superusers) have a profile
        for uu in User.objects.all():
            UserProfile.objects.get_or_create(user=uu)

        self.stdout.write(self.style.SUCCESS(f"Usuarios creados: {len(users)} (pass: {password})"))

        # Create follows
        self.stdout.write("Creando follows...")
        for u in users:
            k = min(max(3, len(users)//5), max(1, len(users)-1))
            candidates = [x for x in users if x != u]
            for v in random.sample(candidates, k=min(k, len(candidates))):
                Follow.objects.get_or_create(follower=u, following=v)
        self.stdout.write(self.style.SUCCESS("Follows listos."))

        # Base tweets
        self.stdout.write("Creando publicaciones...")
        created_tweets = []
        for i in range(tweets_n):
            author = random.choice(users)
            topic = random.choice(WORDS)
            phrase = random.choice(PHRASES).format(topic=topic, tip=random.choice(TIPS))
            text = f"{phrase} {rand_hashtags(random.randint(1,2))}{random_mention(usernames) if random.random()<0.25 else ''}"
            tw = Tweet.objects.create(user=author, content=text)
            created_tweets.append(tw)

            if make_images and random.random() < 0.25:
                try:
                    from PIL import Image, ImageDraw
                    img = Image.new("RGB", (800, 450), (random.randint(20,220), random.randint(20,220), random.randint(20,220)))
                    d = ImageDraw.Draw(img)
                    d.text((20, 20), f"Demo {topic}", fill=(255,255,255))
                    buf = BytesIO()
                    img.save(buf, format="PNG")
                    tw.image.save(f"demo_{tw.pk}.png", ContentFile(buf.getvalue()), save=True)
                except Exception:
                    pass

        self.stdout.write(self.style.SUCCESS(f"Publicaciones base: {len(created_tweets)}"))

        # Retweets
        r_n = int(len(created_tweets) * retweet_ratio)
        self.stdout.write(f"Creando retuits: {r_n}")
        for _ in range(r_n):
            base = random.choice(created_tweets)
            actor = random.choice(users)
            if actor == base.user:
                continue
            if not Tweet.objects.filter(user=actor, parent=base, is_retweet=True).exists():
                Tweet.objects.create(user=actor, parent=base, is_retweet=True, content="")
                Notification.objects.create(actor=actor, recipient=base.user, verb="retwitteó tu publicación", tweet=base)

        # Quotes
        q_n = int(len(created_tweets) * quote_ratio)
        self.stdout.write(f"Creando citas: {q_n}")
        for _ in range(q_n):
            base = random.choice(created_tweets)
            actor = random.choice(users)
            if actor == base.user:
                continue
            topic = random.choice(WORDS)
            text = f"Mi opinión: {random.choice(PHRASES).format(topic=topic, tip=random.choice(TIPS))} {rand_hashtags(1)}"
            Tweet.objects.create(user=actor, parent=base, is_retweet=False, content=text)
            Notification.objects.create(actor=actor, recipient=base.user, verb="citó tu publicación", tweet=base)

        # Likes
        self.stdout.write("Añadiendo likes...")
        for tw in created_tweets:
            k = max(0, int(len(users)*like_factor*random.random()))
            likers = random.sample(users, k=min(k, len(users)))
            for u in likers:
                if u == tw.user:
                    continue
                obj, created = Like.objects.get_or_create(user=u, tweet=tw)
                if created:
                    Notification.objects.create(actor=u, recipient=tw.user, verb="le gustó tu publicación", tweet=tw)

        # Comments
        self.stdout.write("Creando comentarios...")
        for tw in created_tweets:
            if random.random() < comment_factor:
                c_count = random.randint(1, 3)
                for _ in range(c_count):
                    author = random.choice(users)
                    if author == tw.user and random.random() < 0.5:
                        continue
                    topic = random.choice(WORDS)
                    text = f"Interesante. Sobre {topic}, yo {random.choice(['probé', 'leí', 'vi'])} algo similar."
                    Comment.objects.create(user=author, tweet=tw, content=text)
                    if author != tw.user:
                        Notification.objects.create(actor=author, recipient=tw.user, verb="comentó tu publicación", tweet=tw)

        self.stdout.write(self.style.SUCCESS("Seeding completado ✅"))
        self.stdout.write("Sugerencia: prueba /explore, /search/?q=IA, y /n/ para ver notificaciones.")
