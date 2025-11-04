from django.urls import path
from . import views

urlpatterns = [
    path('', views.timeline, name='timeline'),
    path('explore/', views.explore, name='explore'),
    path('signup/', views.signup_view, name='signup'),
    path('t/<int:pk>/', views.tweet_detail, name='tweet_detail'),
    path('t/<int:pk>/like/', views.like_toggle, name='like_toggle'),
    path('t/<int:pk>/retweet/', views.retweet, name='retweet'),
    path('t/<int:pk>/quote/', views.quote, name='quote'),
    path('u/<str:username>/', views.profile, name='profile'),
    
    # URLs de búsqueda y autocomplete
    path('search/', views.search, name='search'),
    path('autocomplete/', views.autocomplete, name='autocomplete'),  # ¡Esta línea es importante!
    path('tag/<str:tag>/', views.tag, name='tag'),
    path('n/', views.notifications, name='notifications'),
    
    # URLs para temas
    path('tema/<slug:slug>/', views.tema_feed, name='tema_feed'),
]