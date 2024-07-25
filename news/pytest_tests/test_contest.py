import pytest

from django.urls import reverse

from yanews.settings import NEWS_COUNT_ON_HOME_PAGE


@pytest.mark.django_db
def test_news_value_at_homepage(client):
    """Количество новостей на главной странице — не более 10"""
    url = reverse('news:home')
    response = client.get(url)
    object_list = response.context['object_list']
    value_list = object_list.count()
    assert value_list > 0 and value_list < NEWS_COUNT_ON_HOME_PAGE + 1


@pytest.mark.django_db
@pytest.mark.parametrize(
    'name, args',
    (
        ('news:detail', pytest.lazy_fixture('news_id')),
    )
)
def test_pages_anonymous_has_no_form(client, name, args):
    """Анонимному пользователю не видна форма для отправки комментария"""
    url = reverse(name, args=args)
    response = client.get(url)
    assert 'form' not in response.context


@pytest.mark.django_db
@pytest.mark.parametrize(
    'name, args',
    (
        ('news:detail', pytest.lazy_fixture('news_id')),
    )
)
def test_pages_user_has_form(author_client, name, args):
    """Авторизованному пользователю видна форма для отправки комментария"""
    url = reverse(name, args=args)
    response = author_client.get(url)
    # Проверяем, есть ли объект формы в словаре контекста:
    assert 'form' in response.context


@pytest.mark.django_db
def test_ordered_news(client):
    """Новости отсортированы от самой свежей к самой старой"""
    url = reverse('news:home')
    response = client.get(url)
    object_list = response.context['object_list']
    all_dates = [news.date for news in object_list]
    sorted_dates = sorted(all_dates, reverse=True)
    assert all_dates == sorted_dates


@pytest.mark.django_db
def test_ordered_comments(client, news):
    """Комментарии отсортированы от старых к новым"""
    url = reverse('news:detail', args=(news.id,))
    response = client.get(url)
    news = response.context['news']
    all_comments = news.comment_set.all()
    all_timestamps = [comment.created for comment in all_comments]
    # Сортируем временные метки, менять порядок сортировки не надо.
    sorted_timestamps = sorted(all_timestamps)
    # Проверяем, что временные метки отсортированы правильно.
    assert all_timestamps == sorted_timestamps
