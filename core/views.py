from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect, render
from django.http import HttpResponseForbidden
from django.db.models import Q
import re
from django.template.loader import render_to_string
from django.http import JsonResponse

from .models import Tweet, Like, Comment, Follow, UserProfile, Tema
from .forms import TweetForm, CommentForm, SignUpForm, ProfileForm

HASHTAG_RE = re.compile(r"(#\w+)")

def _create_notification(actor, recipient, verb, tweet=None):
    if actor == recipient:
        return
    from .models import Notification
    Notification.objects.create(actor=actor, recipient=recipient, verb=verb, tweet=tweet)

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
    if request.method == 'POST':
        form = TweetForm(request.POST, request.FILES)
        if form.is_valid():
            tw = form.save(commit=False)
            tw.user = request.user
            tw.save()
            form.save_m2m()  # Importante para guardar los temas
            return redirect('timeline')
    else:
        form = TweetForm()
    return render(request, 'core/timeline.html', {'tweets': qs, 'form': form})

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
    ctx = {'profile_user': user, 'profile': profile, 'is_me': is_me, 'is_following': is_following, 'tweets': tweets, 'form': form}
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
    users = User.objects.none()
    
    if q:
        tweets = tweets.filter(Q(content__icontains=q) | Q(user__username__icontains=q))
        users = User.objects.select_related('userprofile').filter(username__icontains=q)[:50]
    
    if tema_id:
        tweets = tweets.filter(temas__id=tema_id)
    
    tweets = tweets[:100]
    
    return render(request, 'core/busqueda_avanzada.html', {
        'q': q,
        'tweets': tweets,
        'users': users,
        'temas': Tema.objects.all(),
        'tema_seleccionado': tema_id
    })