from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect, render
from django.http import HttpResponseForbidden
from django.db.models import Q
import re
from django.template.loader import render_to_string
from django.http import JsonResponse

from .models import Tweet, Like, Comment, Follow, UserProfile, Tema, Hashtag
from .forms import TweetForm, CommentForm, SignUpForm, ProfileForm
from django.views.decorators.http import require_GET
from django.contrib.auth import get_user_model

# Importaciones adicionales
from django.db.models import Q
from django.contrib.auth import get_user_model
from django.shortcuts import render

HASHTAG_RE = re.compile(r"(#\w+)")

# modelo de usuario actual del proyecto
UserModel = get_user_model()

# helper para leer/limpiar el query param
def _q(request):
    return (request.GET.get('q') or '').strip().lstrip('@#')[:30]

def _create_notification(actor, recipient, verb, tweet=None):
    if actor == recipient:
        return
    from .models import Notification
    Notification.objects.create(actor=actor, recipient=recipient, verb=verb, tweet=tweet)

# views.py
def toggle_theme(request):
    if request.method == 'POST':
        theme = request.POST.get('theme', 'light')
        request.session['theme'] = theme
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'error'})

def signup_view(request):
    if request.user.is_authenticated:
        return redirect('timeline')
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('timeline')
    else:
        form = SignUpForm()
    return render(request, 'registration/signup.html', {'form': form})

@login_required
def timeline(request):
    # Users to show: me + I'm following
    following_ids = list(Follow.objects.filter(follower=request.user).values_list('following_id', flat=True))
    qs = Tweet.objects.filter(user_id__in=[request.user.id, *following_ids]).select_related('user', 'user__userprofile')
    
    # Obtener usuarios sugeridos
    User = get_user_model()
    excluded_ids = [request.user.id] + following_ids
    
    suggested_users = User.objects.exclude(
        id__in=excluded_ids
    ).select_related('userprofile').annotate(
        followers_count=Count('followers')
    ).order_by('-followers_count', '-date_joined')[:5]

    if request.method == 'POST':
        form = TweetForm(request.POST, request.FILES)
        if form.is_valid():
            tw = form.save(commit=False)
            tw.user = request.user
            tw.save()
            form.save_m2m()
            return redirect('timeline')
    else:
        form = TweetForm()
    
    return render(request, 'core/timeline.html', {
        'tweets': qs, 
        'form': form,
        'suggested_users': suggested_users,
        'following_ids': following_ids  # ¡IMPORTANTE! Agregar esto
    })

@login_required
def explore(request):
    qs = Tweet.objects.select_related('user', 'user__userprofile').all()[:100]
    return render(request, 'core/timeline.html', {'tweets': qs, 'form': TweetForm()})

@login_required
def like_toggle(request, pk):
    if request.method != 'POST':
        return HttpResponseForbidden('Solo POST')
    tweet = get_object_or_404(Tweet, pk=pk)
    like, created = Like.objects.get_or_create(user=request.user, tweet=tweet)
    if not created:
        like.delete()
    else:
        _create_notification(request.user, tweet.user, 'le gustó tu publicación', tweet=tweet)

    if request.headers.get('Hx-Request'):
        html = render_to_string('components/like_button.html', {'t': tweet, 'user': request.user})
        return JsonResponse({'html': html})
    return redirect(request.META.get('HTTP_REFERER', tweet.get_absolute_url()))

@login_required
def tweet_detail(request, pk):
    tw = get_object_or_404(Tweet.objects.select_related('user', 'user__userprofile'), pk=pk)
    if request.method == 'POST':
        cform = CommentForm(request.POST)
        if cform.is_valid():
            c = cform.save(commit=False)
            c.user = request.user
            c.tweet = tw
            c.save()
            return redirect(tw.get_absolute_url())
    else:
        cform = CommentForm()
    return render(request, 'core/tweet_detail.html', {'tweet': tw, 'cform': cform})

@login_required
def profile(request, username):
    user = get_object_or_404(User, username=username)
    profile = get_object_or_404(UserProfile, user=user)
    is_me = request.user == user
    is_following = Follow.objects.filter(follower=request.user, following=user).exists()
    tweets = Tweet.objects.filter(user=user)
    
    # Obtener conteos de seguidores y seguidos
    followers_count = user.followers.count()
    following_count = user.following.count()
    
    # Obtener listas de seguidores y seguidos
    followers = User.objects.filter(following__following=user).select_related('userprofile')
    following = User.objects.filter(followers__follower=user).select_related('userprofile')

    # Obtener los IDs de usuarios que el usuario actual sigue
    current_user_following_ids = set(Follow.objects.filter(follower=request.user).values_list('following_id', flat=True))

    if request.method == 'POST':
        # follow/unfollow or edit profile
        action = request.POST.get('action')
        if action == 'follow':
            if request.user != user:
                Follow.objects.get_or_create(follower=request.user, following=user)
        elif action == 'unfollow':
            Follow.objects.filter(follower=request.user, following=user).delete()
        elif action == 'edit' and is_me:
            form = ProfileForm(request.POST, request.FILES, instance=profile)
            if form.is_valid():
                form.save()
        return redirect('profile', username=username)

    form = ProfileForm(instance=profile) if is_me else None
    ctx = {
        'profile_user': user, 
        'profile': profile, 
        'is_me': is_me, 
        'is_following': is_following, 
        'tweets': tweets, 
        'form': form,
        'followers_count': followers_count,
        'following_count': following_count,
        'followers': followers,
        'following': following,
        'current_user_following_ids': current_user_following_ids,  # Agregar esta línea
    }
    return render(request, 'core/profile.html', ctx)




@login_required
def search(request):
    q = request.GET.get('q', '').strip()
    tweets = Tweet.objects.none()
    users = User.objects.none()
    if q:
        tweets = Tweet.objects.filter(Q(content__icontains=q) | Q(user__username__icontains=q)).select_related('user')[:100]
        users = User.objects.select_related('userprofile').filter(username__icontains=q)[:50]
    return render(request, 'core/search.html', {'q': q, 'tweets': tweets, 'users': users})

@login_required
def tag(request, tag):
    tag_lower = tag.lower()
    tweets = Tweet.objects.filter(content__iregex=rf'(^|\s)#({tag_lower})\b').select_related('user')
    return render(request, 'core/tag.html', {'tag': tag, 'tweets': tweets})

@login_required
def notifications(request):
    from .models import Notification
    notifs = Notification.objects.filter(recipient=request.user).select_related('actor', 'actor__userprofile', 'tweet').order_by('-created_at')[:50]
    # mark as read
    Notification.objects.filter(recipient=request.user, read=False).update(read=True)
    return render(request, 'core/notifications.html', {'notifs': notifs})

@login_required
def retweet(request, pk):
    if request.method != 'POST':
        return HttpResponseForbidden('Solo POST')
    tw = get_object_or_404(Tweet.objects.select_related('user', 'user__userprofile'), pk=pk)
    # Avoid duplicate pure-retweets by same user
    exists = Tweet.objects.filter(user=request.user, parent=tw, is_retweet=True).exists()
    if not exists:
        new_tw = Tweet.objects.create(user=request.user, content='', parent=tw, is_retweet=True)
        _create_notification(request.user, tw.user, 'retwitteó tu publicación', tweet=tw)
    return redirect(request.META.get('HTTP_REFERER', 'timeline'))

@login_required
def quote(request, pk):
    tw = get_object_or_404(Tweet.objects.select_related('user', 'user__userprofile'), pk=pk)
    if request.method == 'POST':
        form = TweetForm(request.POST, request.FILES)
        if form.is_valid():
            quote_tw = form.save(commit=False)
            quote_tw.user = request.user
            quote_tw.parent = tw
            quote_tw.is_retweet = False
            quote_tw.save()
            form.save_m2m()  # Importante para guardar los temas
            _create_notification(request.user, tw.user, 'citó tu publicación', tweet=tw)
            return redirect('timeline')
    else:
        form = TweetForm()
    return render(request, 'core/quote.html', {'original': tw, 'form': form})

# NUEVAS VISTAS PARA TEMAS
@login_required
def tema_feed(request, slug):
    tema = get_object_or_404(Tema, slug=slug)
    tweets = Tweet.objects.filter(temas=tema).select_related('user', 'user__userprofile').order_by('-created_at')
    
    return render(request, 'core/tema_feed.html', {
        'tema': tema,
        'tweets': tweets,
        'form': TweetForm()
    })

@login_required
def busqueda_avanzada(request):
    q = request.GET.get('q', '').strip()
    tema_id = request.GET.get('tema', '')
    
    tweets = Tweet.objects.all().select_related('user', 'user__userprofile')
    
    # DETECTAR SI ES UN HASHTAG
    if q.startswith('#'):
        hashtag = q[1:].lower()  # Remover el # y hacer lowercase
        tweets = tweets.filter(content__iregex=rf'(^|\s)#({hashtag})\b')
    elif q:
        # Búsqueda normal
        tweets = tweets.filter(Q(content__icontains=q) | Q(user__username__icontains=q))
    
    if tema_id:
        tweets = tweets.filter(temas__id=tema_id)
    
    tweets = tweets[:100]
    
    return render(request, 'core/busqueda_avanzada.html', {
        'q': q,
        'tweets': tweets,
        'users': User.objects.none(),  # No mostrar usuarios en búsqueda avanzada
        'temas': Tema.objects.all(),
        'tema_seleccionado': tema_id
    })

@require_GET
@login_required
def autocomplete(request):
    q = request.GET.get('q', '').strip().lower()
    print(f"🔍 Autocomplete buscando: '{q}'")
    
    resultados = []

    if len(q) >= 2:
        # OPCIÓN 1: Buscar en los Temas (model Tema)
        temas = Tema.objects.filter(nombre__icontains=q)[:10]
        if temas.exists():
            resultados = [tema.nombre for tema in temas]
            print(f"✅ Encontrados {len(resultados)} temas: {resultados}")
        else:
            # OPCIÓN 2: Buscar hashtags en contenido de tweets
            todos_tweets = Tweet.objects.all()[:50]
            hashtags_encontrados = set()
            
            for tweet in todos_tweets:
                hashtags = re.findall(r'#(\w+)', tweet.content.lower())
                for hashtag in hashtags:
                    if q in hashtag:
                        hashtags_encontrados.add(f"#{hashtag}")
            
            resultados = list(hashtags_encontrados)[:10]
            print(f"✅ Encontrados {len(resultados)} hashtags: {resultados}")

    return JsonResponse({'results': resultados})


@require_GET
@login_required
def autocomplete_hashtag(request):
    q = _q(request)
    if not q:
        return JsonResponse({"results": []})
    tags = Hashtag.objects.filter(name__istartswith=q).values('name')[:8]
    return JsonResponse({
        "results": [{"value": f"#{t['name']}", "label": f"#{t['name']}"} for t in tags]
    })

@require_GET
@login_required
def autocomplete_mention(request):
    q = _q(request)
    if not q:
        return JsonResponse({"results": []})
    users = (UserModel.objects.filter(is_active=True)
             .filter(Q(username__istartswith=q) |
                     Q(first_name__istartswith=q) |
                     Q(last_name__istartswith=q))
             .values('username', 'first_name', 'last_name')[:8])
    results = []
    for u in users:
        full = f"{u['first_name']} {u['last_name']}".strip()
        label = f"@{u['username']}" + (f" · {full}" if full else "")
        results.append({"value": f"@{u['username']}", "label": label})
    return JsonResponse({"results": results})


from django.views.generic import DetailView
from django.db.models import Count

# Vista para obtener sugerencias de usuarios
def get_user_suggestions(request, count=5):
    """Obtener sugerencias de usuarios para el usuario actual"""
    if not request.user.is_authenticated:
        return []
    
    User = get_user_model()
    current_user = request.user
    
    # Excluir al usuario actual y usuarios que ya sigue
    excluded_users = [current_user.id]
    if hasattr(current_user, 'following'):
        excluded_users.extend(current_user.following.values_list('id', flat=True))
    
    # Lógica de sugerencias (puedes ajustar esto)
    suggestions = User.objects.exclude(
        id__in=excluded_users
    ).annotate(
        followers_count=Count('followers')
    ).order_by('-followers_count')[:count]
    
    return suggestions


# Agrega esta importación al principio del archivo si no está
from django.db.models import Count

# Agrega estas vistas después de tu vista timeline
@login_required
def follow_user(request, user_id):
    """Vista para seguir a un usuario"""
    user_to_follow = get_object_or_404(User, id=user_id)
    
    # Verificar que no es el mismo usuario y que no lo sigue ya
    if request.user != user_to_follow and not Follow.objects.filter(follower=request.user, following=user_to_follow).exists():
        Follow.objects.create(follower=request.user, following=user_to_follow)
        # Opcional: agregar mensaje de éxito
        from django.contrib import messages
        messages.success(request, f'Ahora sigues a @{user_to_follow.username}')
    
    return redirect('timeline')

@login_required
def unfollow_user(request, user_id):
    """Vista para dejar de seguir a un usuario"""
    user_to_unfollow = get_object_or_404(User, id=user_id)
    
    Follow.objects.filter(follower=request.user, following=user_to_unfollow).delete()
    # Opcional: agregar mensaje de info
    from django.contrib import messages
    messages.info(request, f'Has dejado de seguir a @{user_to_unfollow.username}')
    
    return redirect('timeline')

@login_required
def explore_users(request):
    """Página para descubrir más usuarios"""
    # Excluir al usuario actual y usuarios que ya sigue
    following_ids = list(Follow.objects.filter(follower=request.user).values_list('following_id', flat=True))
    excluded_ids = [request.user.id] + following_ids
    
    users = User.objects.exclude(
        id__in=excluded_ids
    ).select_related('userprofile').annotate(
        followers_count=Count('followers')
    ).order_by('-followers_count', '-date_joined')
    
    return render(request, 'core/explore_users.html', {'users': users})

@login_required
def load_more_suggested_users(request):
    """Vista para cargar más usuarios sugeridos via AJAX"""
    page = int(request.GET.get('page', 1))
    users_per_page = 5
    
    # Calcular offset
    offset = (page - 1) * users_per_page
    
    User = get_user_model()
    following_ids = list(Follow.objects.filter(follower=request.user).values_list('following_id', flat=True))
    excluded_ids = [request.user.id] + following_ids
    
    # Obtener usuarios con paginación
    users = User.objects.exclude(
        id__in=excluded_ids
    ).select_related('userprofile').annotate(
        followers_count=Count('followers')
    ).order_by('-followers_count', '-date_joined')[offset:offset + users_per_page]
    
    # Renderizar el template con los usuarios
    html = render_to_string('components/suggested_users_items.html', {
        'suggested_users': users,
        'following_ids': following_ids  # ¡IMPORTANTE! Agregar esto
    })
    
    return JsonResponse({
        'html': html,
        'has_more': len(users) == users_per_page,
        'next_page': page + 1
    })

@login_required
def toggle_follow(request, user_id):
    """Vista para seguir/dejar de seguir a un usuario via AJAX"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    User = get_user_model()
    user_to_toggle = get_object_or_404(User, id=user_id)
    
    # Verificar que no es el mismo usuario
    if request.user == user_to_toggle:
        return JsonResponse({'error': 'No puedes seguirte a ti mismo'}, status=400)
    
    # Verificar si ya sigue al usuario
    follow_exists = Follow.objects.filter(
        follower=request.user, 
        following=user_to_toggle
    ).exists()
    
    if follow_exists:
        # Dejar de seguir
        Follow.objects.filter(follower=request.user, following=user_to_toggle).delete()
        action = 'unfollow'
        button_text = 'Seguir'
        button_class = 'bg-blue-600 hover:bg-blue-700'
    else:
        # Seguir
        Follow.objects.create(follower=request.user, following=user_to_toggle)
        action = 'follow'
        button_text = 'Dejar de seguir'
        button_class = 'bg-gray-600 hover:bg-gray-700'
    
    # Obtener el nuevo conteo de seguidores
    followers_count = user_to_toggle.followers.count()
    
    return JsonResponse({
        'action': action,
        'button_text': button_text,
        'button_class': button_class,
        'followers_count': followers_count,
        'success': True
    })

@login_required
def search_users(request):
    """Vista para búsqueda de usuarios via AJAX (para la barra de búsqueda)"""
    q = request.GET.get('q', '').strip()
    users = []
    
    if q and len(q) >= 2:
        users = User.objects.filter(
            username__icontains=q
        ).select_related('userprofile')[:10]
    
    # Preparar datos para JSON
    users_data = []
    for user in users:
        users_data.append({
            'username': user.username,
            'bio': user.userprofile.bio if hasattr(user, 'userprofile') and user.userprofile.bio else ''
        })
    
    return JsonResponse({'users': users_data})