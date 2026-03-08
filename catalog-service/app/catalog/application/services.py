from catalog.infrastructure.orm_models import Category


class CategoryService:
    @staticmethod
    def get_category(category_id: int):
        try:
            return Category.objects.get(pk=category_id)
        except Category.DoesNotExist:
            return None

    @staticmethod
    def get_all():
        return Category.objects.all()
