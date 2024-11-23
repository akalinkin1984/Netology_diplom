import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from backend.models import User, Contact, ProductInfo, Product, Category, Shop
from backend.serializers import CategorySerializer


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

@pytest.fixture
def category_list():
    Category.objects.all().delete()
    categories = [
        Category.objects.create(name="Electronics"),
        Category.objects.create(name="Books"),
        Category.objects.create(name="Clothing")
    ]
    return categories


@pytest.mark.django_db
class TestContactView:

    def test_get_contacts(self, authenticated_client, user):
        Contact.objects.create(user=user, city='Test City', street='Test Street', house='123', phone='1234567890')
        url = reverse('backend:user-contact')
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
        url = reverse('backend:user-contact')
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
            'id': 9999,
            'city': 'Updated City'
        }
        response = authenticated_client.put(url, data)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.data['status'] is False


@pytest.mark.django_db
class TestProductInfoView:

    def test_list_product_info(self, api_client, product_info):
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
        url = reverse('backend:products')
        response = api_client.get(url, {'model': 'Test Model'})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        result = response.data['results'][0]
        assert result['model'] == "Test Model"

    def test_filter_by_external_id(self, api_client, product_info):
        url = reverse('backend:products')
        response = api_client.get(url, {'external_id': 1})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        result = response.data['results'][0]
        assert result['external_id'] == 1

    def test_filter_by_category(self, api_client, product_info, category):
        url = reverse('backend:products')
        response = api_client.get(url, {'product__category_id': category.id})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['product']['category'] == category.name

    def test_filter_by_shop(self, api_client, product_info, shop):
        url = reverse('backend:products')
        response = api_client.get(url, {'shop_id': shop.id})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['shop'] == shop.name

    def test_search_by_model(self, api_client, product_info):
        url = reverse('backend:products')
        response = api_client.get(url, {'search': 'Test Model'})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['model'] == "Test Model"

    def test_search_by_product_name(self, api_client, product_info):
        url = reverse('backend:products')
        response = api_client.get(url, {'search': 'Test Product'})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['product']['name'] == "Test Product"

    def test_filter_by_shop_status(self, api_client, product_info, shop):
        Shop.objects.all().delete()
        new_shop = Shop.objects.create(name='New Shop', status=True, user=shop.user)
        new_category = Category.objects.create(name='New Category')
        new_product = Product.objects.create(name='New Product', category=new_category)
        new_product_info = ProductInfo.objects.create(external_id=2, product=new_product, model='New Model',
                                                      quantity=10, price_rrc=120, price=100, shop=new_shop)

        url = reverse('backend:products')
        response = api_client.get(url, {'shop__status': True})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['shop'] == new_shop.name

    def test_filter_by_shop_name(self, api_client, product_info, shop):
        url = reverse('backend:products')
        response = api_client.get(url, {'shop__name': 'Test Shop'})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['shop'] == shop.name

    def test_no_results(self, api_client, product_info):
        url = reverse('backend:products')
        response = api_client.get(url, {'model': 'Nonexistent Model'})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 0


@pytest.mark.django_db
class TestCategoryView:

    @pytest.fixture(autouse=True)
    def setup(self, db):
        Category.objects.all().delete()

    def test_list_categories_empty(self, api_client):
        url = reverse('backend:categories')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 0, f"Expected 0 categories, but got {len(response.data['results'])}"

    def test_list_categories(self, api_client):
        categories = [
            Category.objects.create(name="Electronics"),
            Category.objects.create(name="Books"),
            Category.objects.create(name="Clothing")
        ]
        url = reverse('backend:categories')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == len(categories), f"Expected {len(categories)} categories, but got {len(response.data['results'])}"
        for category in categories:
            assert any(item['name'] == category.name for item in response.data['results'])

    def test_category_ordering(self, api_client):
        categories = [
            Category.objects.create(name="A"),
            Category.objects.create(name="C"),
            Category.objects.create(name="B")
        ]
        url = reverse('backend:categories')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        names = [category['name'] for category in response.data['results']]
        assert names == sorted(names, reverse=True)

    def test_category_serializer(self, api_client):
        categories = [
            Category.objects.create(name="Electronics"),
            Category.objects.create(name="Books"),
            Category.objects.create(name="Clothing")
        ]
        for category in categories:
            category.refresh_from_db()
        serializer = CategorySerializer(categories, many=True)
        url = reverse('backend:categories')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == len(serializer.data)
        results = []
        while True:
            if 'results' in response.data:
                for result in response.data['results']:
                    results.append(result)
            if 'next' in response.data and response.data['next'] is not None:
                next_url = response.data['next']
                if next_url.startswith('/'):
                    next_url = 'http://testserver' + next_url
                response = self.client.get(next_url)
            else:
                break
        assert sorted(results, key=lambda x: x['id']) == sorted(serializer.data, key=lambda x: x['id'])

    @pytest.mark.parametrize("category_name", ["Test Category", "Another Category", "Специальная категория"])
    def test_single_category_creation(self, category_name, api_client):
        Category.objects.create(name=category_name)
        url = reverse('backend:categories')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1, f"Expected 1 category, but got {len(response.data['results'])}"
        assert response.data['results'][0]['name'] == category_name

    def test_large_number_of_categories(self, api_client):
        for i in range(100):
            Category.objects.create(name=f"Category {i}")
        url = reverse('backend:categories')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 100, f"Expected 100 categories, but got {response.data['count']}"

    def test_category_fields(self, api_client):
        Category.objects.create(name="Test Category")
        url = reverse('backend:categories')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1, f"Expected 1 category, but got {len(response.data['results'])}"
        assert set(response.data['results'][0].keys()) == {'id', 'name'}

    def test_invalid_url(self, api_client):
        response = api_client.get('/api/invalid-url/')
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestShopView:

    def test_get_shops(self, api_client, shop, user):
        Shop.objects.all().delete()
        shop = Shop.objects.create(name="Test Shop", user=user, status=True)
        url = reverse('backend:shops')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['name'] == shop.name

    def test_get_shops_filtered_by_status(self, api_client, shop, user):
        Shop.objects.all().delete()
        shop = Shop.objects.create(name="Test Shop", user=user, status=True)
        url = reverse('backend:shops')
        response = api_client.get(url, {'status': 'true'})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['name'] == shop.name

    def test_get_shops_filtered_by_status_false(self, api_client, user):
        Shop.objects.all().delete()
        shop = Shop.objects.create(name="Test Shop", user=user, status=True)
        url = reverse('backend:shops')
        response = api_client.get(url, {'status': 'false'})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['name'] == shop.name

    def test_get_shops_filtered_by_name(self, api_client, user):
        Shop.objects.all().delete()
        shop = Shop.objects.create(name="Test Shop", user=user, status=True)
        url = reverse('backend:shops')
        response = api_client.get(url, {'name': 'Test Shop'})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['name'] == shop.name

    def test_get_shops_filtered_by_user(self, api_client, user):
        Shop.objects.all().delete()
        shop = Shop.objects.create(name="Test Shop", user=user, status=True)
        url = reverse('backend:shops')
        response = api_client.get(url, {'user': user.id})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['name'] == shop.name

    def test_get_shops_empty_filter(self, api_client, user):
        Shop.objects.all().delete()
        shop = Shop.objects.create(name="Test Shop", user=user, status=True)
        url = reverse('backend:shops')
        response = api_client.get(url, {})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['name'] == shop.name


@pytest.mark.django_db
class TestPartnerUpdate:

    def test_post_request(self, api_client, user):
        user.type = 'shop'
        user.save()
        api_client.force_authenticate(user=user)
        url = reverse('backend:partner-update')
        data = {'path': 'path/to/file.yaml'}
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == True

    def test_post_request_invalid_path(self, api_client, user):
        user.type = 'shop'
        user.save()
        api_client.force_authenticate(user=user)
        url = reverse('backend:partner-update')
        data = {'path': 'invalid/path'}
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == True

    def test_post_request_not_shop(self, api_client, user):
        api_client.force_authenticate(user=user)
        url = reverse('backend:partner-update')
        data = {'path': 'path/to/file.yaml'}
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN
