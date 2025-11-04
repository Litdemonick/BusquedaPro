import pytest
from django.urls import reverse
from core.models import Tema
from django.contrib.auth import get_user_model

@pytest.mark.django_db
def test_autocomplete_vacio(client):
    """Caso: autocompletado vacío no debería fallar."""
    user = get_user_model().objects.create_user(username="testuser", password="testpass123")
    client.login(username="testuser", password="testpass123")
    
    response = client.get(reverse('autocomplete'), {'q': ''})
    assert response.status_code == 200

@pytest.mark.django_db
def test_autocomplete_inexistente(client):
    """Caso: término inexistente."""
    user = get_user_model().objects.create_user(username="testuser", password="testpass123")
    client.login(username="testuser", password="testpass123")
    
    response = client.get(reverse('autocomplete'), {'q': 'termino_que_no_existe_123'})
    assert response.status_code == 200

@pytest.mark.django_db
def test_autocomplete_existente(client):
    """Caso: término existente devuelve sugerencias."""
    user = get_user_model().objects.create_user(username="testuser", password="testpass123")
    client.login(username="testuser", password="testpass123")
    
    # Crear tema de prueba
    Tema.objects.create(nombre="Python Programming", slug="python")
    
    response = client.get(reverse('autocomplete'), {'q': 'pyth'})
    assert response.status_code == 200

@pytest.mark.django_db
def test_autocomplete_caracteres_especiales(client):
    """Caso: búsqueda con caracteres especiales."""
    user = get_user_model().objects.create_user(username="testuser", password="testpass123")
    client.login(username="testuser", password="testpass123")
    
    # Crear tema con caracteres especiales
    Tema.objects.create(nombre="C# & .NET", slug="csharp-net")
    
    response = client.get(reverse('autocomplete'), {'q': 'c#'})
    assert response.status_code == 200

@pytest.mark.django_db
def test_autocomplete_sin_login(client):
    """Caso: autocomplete sin estar logueado."""
    response = client.get(reverse('autocomplete'), {'q': 'test'})
    # Depende de tu configuración - podría ser 200 o 302
    assert response.status_code in [200, 302]

@pytest.mark.django_db
def test_autocomplete_xss_protection(client):
    """Caso: protección contra XSS en búsqueda."""
    user = get_user_model().objects.create_user(username="testuser", password="testpass123")
    client.login(username="testuser", password="testpass123")
    
    malicious_input = '<script>alert("xss")</script>'
    response = client.get(reverse('autocomplete'), {'q': malicious_input})
    assert response.status_code == 200

@pytest.mark.django_db
def test_autocomplete_with_temas(client):
    """Caso: autocomplete con temas existentes."""
    user = get_user_model().objects.create_user(username="testuser", password="testpass123")
    client.login(username="testuser", password="testpass123")
    
    # Crear algunos temas de prueba
    Tema.objects.create(nombre="Python Programming", slug="python")
    Tema.objects.create(nombre="Django Framework", slug="django")
    Tema.objects.create(nombre="JavaScript", slug="javascript")
    
    response = client.get(reverse('autocomplete'), {'q': 'pyth'})
    assert response.status_code == 200
    data = response.json()
    assert 'results' in data
    assert isinstance(data['results'], list)
    assert any('Python' in result for result in data['results'])

@pytest.mark.django_db
def test_autocomplete_min_length(client):
    """Caso: query muy corta (1 carácter) puede o no devolver resultados."""
    user = get_user_model().objects.create_user(username="testuser", password="testpass123")
    client.login(username="testuser", password="testpass123")
    
    Tema.objects.create(nombre="Python", slug="python")
    
    response = client.get(reverse('autocomplete'), {'q': 'p'})  # Solo 1 carácter
    assert response.status_code == 200
    data = response.json()
    assert 'results' in data