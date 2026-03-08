from .orm_models import Category


class CategoryRepository:
    def get_by_id(self, category_id: int):
        try:
            return Category.objects.get(pk=category_id)
        except Category.DoesNotExist:
            return None

    def get_all(self):
        return Category.objects.all()

    def save(self, category):
        category.save()
        return category

    def delete(self, category):
        category.delete()
