import pytest

from django.urls import reverse

from http import HTTPStatus

from pytest_django.asserts import assertFormError, assertRedirects

from news.forms import BAD_WORDS, WARNING
from news.models import Comment, News


@pytest.mark.django_db
def test_anonymous_user_cant_create_comment(client, news_id, form_data):
    """Анонимный пользователь не может отправить комментарий"""
    url = reverse('news:detail', args=news_id,)
    login_url = reverse('users:login')
    expected_url = f'{login_url}?next={url}'
    response = client.post(url, data=form_data)
    assertRedirects(response, expected_url)
    comments_count = Comment.objects.count()
    # comments_count == 11, так как в conftest.py 2 autouse fixtures (
    # comment + comment_bulk_create)
    assert comments_count == 11


@pytest.mark.django_db
def test_authorized_user_can_create_comment(author_client, news_id, form_data):
    """Авторизованный пользователь может отправить комментарий"""
    url = reverse('news:detail', args=news_id,)
    response = author_client.post(url, data=form_data)
    assertRedirects(response, f'{url}#comments')
    comments_count = Comment.objects.count()
    assert comments_count == 12


@pytest.mark.django_db
def test_user_cant_use_bad_words(author_client, news_id):
    """Если комментарий содержит запрещённые слова, он не будет опубликован"""
    url = reverse('news:detail', args=news_id)
    bad_words_data = {'text': f'Я не хочу ругаться, но {BAD_WORDS[0]}, ...'}
    response = author_client.post(url, data=bad_words_data)
    assertFormError(
        response,
        form='form',
        field='text',
        errors=WARNING
    )
    comments_count = Comment.objects.count()
    assert comments_count == 11


@pytest.mark.django_db
def test_author_can_delete_comment(author_client, news_id, form_data, comment):
    """Авторизованный пользователь может удалять свои комментарии"""
    url = reverse('news:detail', args=(news_id))
    comment_delete_url = reverse('news:delete', args=(comment.id,))
    response = author_client.post(comment_delete_url, form_data)
    assertRedirects(response, f'{url}#comments')
    comments_count = Comment.objects.count()
    assert comments_count == 10


@pytest.mark.django_db
def test_author_can_edit_comment(
    author_client,
    news_id, comment,
    form_data,
    comment_id
):
    """Авторизованный пользователь может редактировать свои комментарии"""
    url = reverse('news:detail', args=(news_id))
    comment_edit_url = reverse('news:edit', args=comment_id)
    response = author_client.post(comment_edit_url, form_data)
    assertRedirects(response, f'{url}#comments')
    comment.refresh_from_db()
    assert comment.text == form_data['text']


@pytest.mark.django_db
def test_other_author_cant_delete_comment(
    not_author_client,
    comment_id,
    form_data
):
    """Авторизованный пользователь не может удалять чужие комментарии"""
    comment_delete_url = reverse('news:delete', args=comment_id)
    response = not_author_client.post(comment_delete_url, form_data)
    assert response.status_code == HTTPStatus.NOT_FOUND
    comments_count = Comment.objects.count()
    assert comments_count == 11


@pytest.mark.django_db
def test_other_author_cant_edit_comment(
    not_author_client,
    news_id,
    comment,
    form_data
):
    """Авторизованный пользователь не может редактировать чужие комментарии"""
    url = reverse('news:edit', args=news_id,)
    response = not_author_client.post(url, form_data)
    assert response.status_code == HTTPStatus.NOT_FOUND
    comment_from_db = Comment.objects.get(id=comment.id)
    assert comment.text == comment_from_db.text
