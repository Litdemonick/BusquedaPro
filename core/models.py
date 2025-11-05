from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.text import slugify

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.CharField(max_length=180, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Perfil de {self.user.username}'

class Follow(models.Model):
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following')
    following = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followers')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('follower', 'following')

    def __str__(self):
        return f'{self.follower.username} → {self.following.username}'

class Tema(models.Model):
    nombre = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True)
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nombre)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.nombre
    
    class Meta:
        verbose_name_plural = "Temas"

class Tweet(models.Model):
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='children')
    is_retweet = models.BooleanField(default=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.CharField(max_length=280)
    image = models.ImageField(upload_to='tweets/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    # NUEVO CAMPO
    temas = models.ManyToManyField(Tema, blank=True, related_name='tweets')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.username}: {self.content[:30]}'

    def get_absolute_url(self):
        return reverse('tweet_detail', args=[self.pk])

    @property
    def like_count(self) -> int:
        return self.likes.count()

class Like(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    tweet = models.ForeignKey(Tweet, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'tweet')

    def __str__(self):
        return f'{self.user.username} ♥ {self.tweet_id}'

class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    tweet = models.ForeignKey(Tweet, on_delete=models.CASCADE, related_name='comments')
    content = models.CharField(max_length=280)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Coment de {self.user.username} en {self.tweet_id}'


class Notification(models.Model):
    actor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications_sent')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    verb = models.CharField(max_length=80)
    tweet = models.ForeignKey(Tweet, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.actor} -> {self.recipient}: {self.verb}'
class Hashtag(models.Model):
    name = models.CharField(max_length=64, unique=True, db_index=True)  # guarda SIN '#'

    def __str__(self):
        return f"#{self.name}"
