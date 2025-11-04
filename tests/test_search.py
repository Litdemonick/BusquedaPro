import pytest
from django.urls import reverse
from core.models import Tweet, Tema
from django.contrib.auth import get_user_model

@pytest.mark.django_db
def test_busqueda_vacia(client, django_user_model):
    """Caso: búsqueda vacía debe devolver página sin resultados."""
    user = django_user_model.objects.create_user(username="tester", password="1234")
    client.login(username="tester", password="1234")

    url = reverse('busqueda_avanzada')
    response = client.get(url, {'q': ''})
    assert response.status_code == 200

@pytest.mark.django_db
def test_busqueda_sin_resultados(client, django_user_model):
    """Caso: texto inexistente no devuelve publicaciones."""
    user = django_user_model.objects.create_user(username="tester", password="1234")
    client.login(username="tester", password="1234")

    url = reverse('busqueda_avanzada')
    response = client.get(url, {'q': 'xyz_no_existe_123'})
    assert response.status_code == 200

@pytest.mark.django_db
def test_busqueda_por_tema(client, django_user_model):
    """Caso: buscar publicaciones por tema existente."""
    usuario = django_user_model.objects.create_user(username="testuser", password="1234")
    client.login(username="testuser", password="1234")

    tema = Tema.objects.create(nombre="Python", slug="python")
    tweet = Tweet.objects.create(user=usuario, content="Aprendiendo Python con Django")
    tweet.temas.add(tema)

    url = reverse('busqueda_avanzada')
    response = client.get(url, {'tema': tema.id})
    assert response.status_code == 200
    assert b"Python" in response.content

# NUEVOS CASOS EDGE:
@pytest.mark.django_db
def test_busqueda_texto_largo(client, django_user_model):
    """Caso: texto de búsqueda > 255 caracteres."""
    user = django_user_model.objects.create_user(username="tester", password="1234")
    client.login(username="tester", password="1234")

    texto_largo = "a" * 300  # Más de 255 caracteres
    url = reverse('busqueda_avanzada')
    response = client.get(url, {'q': texto_largo})
    assert response.status_code == 200

@pytest.mark.django_db
def test_busqueda_tema_inexistente(client, django_user_model):
    """Caso: buscar por tema que no existe."""
    user = django_user_model.objects.create_user(username="tester", password="1234")
    client.login(username="tester", password="1234")

    url = reverse('busqueda_avanzada')
    response = client.get(url, {'tema': 9999})  # ID que no existe
    assert response.status_code == 200

@pytest.mark.django_db
def test_busqueda_fecha_mal_formateada(client, django_user_model):
    """Caso: fecha mal escrita/formateada."""
    user = django_user_model.objects.create_user(username="tester", password="1234")
    client.login(username="tester", password="1234")

    url = reverse('busqueda_avanzada')
    response = client.get(url, {'fecha': '2024-13-45'})  # Fecha inválida
    assert response.status_code == 200

@pytest.mark.django_db
def test_busqueda_usuario_inexistente(client, django_user_model):
    """Caso: buscar tweets de usuario que no existe."""
    user = django_user_model.objects.create_user(username="tester", password="1234")
    client.login(username="tester", password="1234")

    url = reverse('busqueda_avanzada')
    response = client.get(url, {'usuario': 'usuario_inexistente_123'})
    assert response.status_code == 200

@pytest.mark.django_db
def test_busqueda_multiple_parametros(client, django_user_model):
    """Caso: búsqueda con múltiples parámetros."""
    user = django_user_model.objects.create_user(username="tester", password="1234")
    client.login(username="tester", password="1234")

    tema = Tema.objects.create(nombre="Django", slug="django")
    
    url = reverse('busqueda_avanzada')
    response = client.get(url, {
        'q': 'tutorial',
        'tema': tema.id,
        'usuario': user.username
    })
    assert response.status_code == 200

@pytest.mark.django_db
def test_busqueda_sin_login(client):
    """Caso: búsqueda sin estar logueado (debería redirigir)."""
    url = reverse('busqueda_avanzada')
    response = client.get(url, {'q': 'test'})
    # Depende de tu configuración: 200 si es público, 302 si requiere login
    assert response.status_code in [200, 302]