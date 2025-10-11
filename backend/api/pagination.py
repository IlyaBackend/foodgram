from rest_framework.pagination import PageNumberPagination

from .constants import MAX_PAGE_SIZE, PAGE_SIZE


class StandardPagination(PageNumberPagination):
    """Пагинация."""

    page_size_query_param = 'limit'
    page_size = PAGE_SIZE
    max_page_size = MAX_PAGE_SIZE
