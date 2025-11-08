from django.urls import path
from . import views

urlpatterns = [
    path('', views.timeline, name='timeline'),
    path('load_more_suggested_users/', views.load_more_suggested_users, name='load_more_suggested_users'),
    path('explore/', views.explore, name='explore'),
    path('signup/', views.signup_view, name='signup'),
    path('t/<int:pk>/', views.tweet_detail, name='tweet_detail'),
    path('t/<int:pk>/like/', views.like_toggle, name='like_toggle'),
    path('t/<int:pk>/retweet/', views.retweet, name='retweet'),
    path('t/<int:pk>/quote/', views.quote, name='quote'),
    path('u/<str:username>/', views.profile, name='profile'),
    path('toggle-theme/', views.toggle_theme, name='toggle_theme'),
    path('autocomplete/mention/', views.autocomplete_mention, name='autocomplete_mention'),
    path('autocomplete/hashtag/', views.autocomplete_hashtag, name='autocomplete_hashtag'),
    path('toggle_follow/<int:user_id>/', views.toggle_follow, name='toggle_follow'),
    path('search_users/', views.search_users, name='search_users'),
    path('u/<str:username>/', views.profile, name='profile'),
    path('profile/<str:username>/', views.profile), 
    

    
    # URLs de búsqueda y autocomplete
    path('search/', views.search, name='search'),
    path('autocomplete/', views.autocomplete, name='autocomplete'),  # ¡Esta línea es importante!
    path('tag/<str:tag>/', views.tag, name='tag'),
    path('n/', views.notifications, name='notifications'),
    path('follow/<int:user_id>/', views.follow_user, name='follow_user'),
    path('follow/<int:user_id>/', views.follow_user, name='follow_user'),
    path('unfollow/<int:user_id>/', views.unfollow_user, name='unfollow_user'),
    path('explore/users/', views.explore_users, name='explore_users'),
    
    # URLs para temas
    path('tema/<slug:slug>/', views.tema_feed, name='tema_feed'),
    
]