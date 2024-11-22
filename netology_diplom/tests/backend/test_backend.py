import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from backend.models import User, Contact, ProductInfo, Product, Category, Shop
from backend.serializers import ProductInfoSerializer


@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def user(db):
    return User.objects.create_user(email='test@test.com', password='testpass')

@pytest.fixture
def authenticated_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client

@pytest.fixture
def category(db):
    return Category.objects.create(name="Test Category")

@pytest.fixture
def shop(db, user):
    return Shop.objects.create(name="Test Shop", user=user, status=True)

@pytest.fixture
def product(db, category):
    return Product.objects.create(name="Test Product", category=category)

@pytest.fixture
def product_info(db, product, shop):
    return ProductInfo.objects.create(
        product=product,
        shop=shop,
        model="Test Model",
        external_id=1,
        quantity=10,
        price=100,
        price_rrc=120
    )


@pytest.mark.django_db
class TestContactView:

    def test_get_contacts(self, authenticated_client, user):
        Contact.objects.create(user=user, city='Test City', street='Test Street', house='123', phone='1234567890')
        url = reverse('backend:user-contact')  # предполагается, что у вас есть URL с именем 'contact-list'
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]['city'] == 'Test City'

    def test_create_contact(self, authenticated_client):
        url = reverse('backend:user-contact')
        data = {
            'city': 'New City',
            'street': 'New Street',
            'house': '456',
            'phone': '0987654321'
        }
        response = authenticated_client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['status'] is True
        assert Contact.objects.count() == 1

    def test_create_contact_missing_fields(self, authenticated_client):
        url = reverse('backend:user-contact')
        data = {
            'city': 'New City',
            'street': 'New Street'
        }
        response = authenticated_client.post(url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['status'] is False
        assert 'error' in response.data

    def test_delete_contact(self, authenticated_client, user):
        contact = Contact.objects.create(user=user, city='Test City', street='Test Street', house='123', phone='1234567890')
        url = reverse('backend:user-contact')  # предполагается, что у вас есть URL с именем 'contact-detail'
        data = {'items': str(contact.id)}
        response = authenticated_client.delete(url, data)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] is True
        assert Contact.objects.count() == 0

    def test_update_contact(self, authenticated_client, user):
        contact = Contact.objects.create(user=user, city='Test City', street='Test Street', house='123', phone='1234567890')
        url = reverse('backend:user-contact')
        data = {
            'id': contact.id,
            'city': 'Updated City'
        }
        response = authenticated_client.put(url, data)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] is True
        contact.refresh_from_db()
        assert contact.city == 'Updated City'

    def test_update_nonexistent_contact(self, authenticated_client):
        url = reverse('backend:user-contact')
        data = {
            'id': 9999,  # несуществующий ID
            'city': 'Updated City'
        }
        response = authenticated_client.put(url, data)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.data['status'] is False


@pytest.mark.django_db
class TestProductInfoView:

    def test_list_product_info(self, api_client, product_info):
        # Тест на получение списка информации о продуктах
        url = reverse('backend:products')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data
        assert len(response.data['results']) == 1
        result = response.data['results'][0]
        assert result['model'] == "Test Model"
        assert result['external_id'] == 1
        assert result['quantity'] == 10
        assert result['price_rrc'] == 120
        assert result['shop'] == "Test Shop"
        assert 'product' in result
        assert result['product']['name'] == "Test Product"
        assert 'product_parameters' in result

    def test_filter_by_model(self, api_client, product_info):
        # Тест на фильтрацию по модели
        url = reverse('backend:products')
        response = api_client.get(url, {'model': 'Test Model'})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        result = response.data['results'][0]
        assert result['model'] == "Test Model"

    def test_filter_by_external_id(self, api_client, product_info):
        # Тест на фильтрацию по внешнему ID
        url = reverse('backend:products')
        response = api_client.get(url, {'external_id': 1})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        result = response.data['results'][0]
        assert result['external_id'] == 1

    # def test_filter_by_category(self, api_client, product_info, category):
    #     # Тест на фильтрацию по категории
    #     url = reverse('backend:products')
    #     response = api_client.get(url, {'product__category_id': category.id})
    #     assert response.status_code == status.HTTP_200_OK
    #     assert len(response.data['results']) == 1
    #     assert response.data['results'][0]['product']['category'] == category.id

    # def test_filter_by_shop(self, api_client, product_info, shop):
    #     # Тест на фильтрацию по магазину
    #     url = reverse('backend:products')
    #     response = api_client.get(url, {'shop_id': shop.id})
    #     assert response.status_code == status.HTTP_200_OK
    #     assert len(response.data['results']) == 1
    #     assert response.data['results'][0]['shop'] == shop.id

    def test_search_by_model(self, api_client, product_info):
        # Тест на поиск по модели
        url = reverse('backend:products')
        response = api_client.get(url, {'search': 'Test Model'})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['model'] == "Test Model"

    def test_search_by_product_name(self, api_client, product_info):
        # Тест на поиск по названию продукта
        url = reverse('backend:products')
        response = api_client.get(url, {'search': 'Test Product'})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['product']['name'] == "Test Product"

    # def test_filter_by_shop_status(self, api_client, product_info, shop):
    #     # Тест на фильтрацию по статусу магазина
    #     url = reverse('backend:products')
    #     response = api_client.get(url, {'shop__status': True})
    #     assert response.status_code == status.HTTP_200_OK
    #     assert len(response.data['results']) == 1
    #     assert response.data['results'][0]['shop'] == shop.id

        # shop.status = False
        # shop.save()
        # response = api_client.get(url, {'shop__status': True})
        # assert response.status_code == status.HTTP_200_OK
        # assert len(response.data['results']) == 0

    # def test_filter_by_shop_name(self, api_client, product_info, shop):
    #     # Тест на фильтрацию по названию магазина
    #     url = reverse('backend:products')
    #     response = api_client.get(url, {'shop__name': 'Test Shop'})
    #     assert response.status_code == status.HTTP_200_OK
    #     assert len(response.data['results']) == 1
    #     assert response.data['results'][0]['shop'] == shop.id

    def test_no_results(self, api_client, product_info):
        # Тест на отсутствие результатов
        url = reverse('backend:products')
        response = api_client.get(url, {'model': 'Nonexistent Model'})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 0

    # def test_pagination(self, api_client, product_info):
        # Тест на пагинацию
        # for i in range(9):  # Создаем 9 дополнительных объектов, чтобы всего было 10
        #     ProductInfo.objects.create(
        #         product=product_info.product,
        #         shop=product_info.shop,
        #         model=f"Test Model {i}",
        #         external_id=i + 2,
        #         quantity=10,
        #         price=100,
        #         price_rrc=120
        #     )
        #
        # url = reverse('backend:products')
        # response = api_client.get(url)
        # assert response.status_code == status.HTTP_200_OK
        # assert 'results' in response.data
        # assert 'count' in response.data
        # assert 'next' in response.data
        # assert 'previous' in response.data
        #
        # # Размер страницы по умолчанию равен 5
        # assert len(response.data['results']) == 5
        # assert response.data['count'] == 10  # 9 новых + 1 исходный
        # # Проверяем вторую страницу
        # response = api_client.get(url, {'page': 2})
        # assert response.status_code == status.HTTP_200_OK
        # assert len(response.data['results']) == 5
        # # Проверяем третью страницу
        # response = api_client.get(url, {'page': 3})
        # assert response.status_code == status.HTTP_200_OK
        # assert len(response.data['results']) == 0
