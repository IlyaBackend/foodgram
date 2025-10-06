from rest_framework.pagination import PageNumberPagination

from backend.constants import MAX_PAGE_SIZE, PAGE_SIZE, PAGE_SIZE_QUERY_PARAM


class CustomPagination(PageNumberPagination):
    """Пагинация."""

    page_size_query_param = PAGE_SIZE_QUERY_PARAM
    page_size = PAGE_SIZE
    max_page_size = MAX_PAGE_SIZE
