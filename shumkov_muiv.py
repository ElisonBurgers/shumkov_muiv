import json
import os
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field, asdict
from enum import Enum


class MealType(Enum):
    BREAKFAST = "завтрак"
    LUNCH = "обед"
    DINNER = "ужин"
    DESSERT = "десерт"
    SNACK = "перекус"
    SOUP = "суп"
    SALAD = "салат"
    DRINK = "напиток"
    OTHER = "другое"

    @classmethod
    def get_all_display(cls) -> List[str]:
        return [meal.value for meal in cls]


class Unit(Enum):
    GRAM = "г"
    KILOGRAM = "кг"
    MILLILITER = "мл"
    LITER = "л"
    PIECE = "шт."
    TABLESPOON = "ст.л."
    TEASPOON = "ч.л."
    CUP = "стакан"
    PINCH = "щепотка"
    TO_TASTE = "по вкусу"

    @classmethod
    def get_convertible_units(cls) -> Dict[str, float]:
        return {
            "г": 1.0,
            "кг": 1000.0,
            "мл": 1.0,
            "л": 1000.0,
            "ст.л.": 15.0,
            "ч.л.": 5.0,
            "стакан": 250.0
        }


@dataclass
class Ingredient:
    name: str
    amount: float
    unit: str
    calories_per_unit: float = 0.0

    def __post_init__(self):
        self.name = self.name.lower().strip()

    def get_calories(self) -> float:
        return self.amount * self.calories_per_unit

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Ingredient':
        return cls(**data)

    def __str__(self) -> str:
        return f"{self.name}: {self.amount} {self.unit}"


@dataclass
class Recipe:
    id: int
    title: str
    description: str
    meal_type: str
    prep_time_min: int
    cook_time_min: int
    servings: int
    ingredients: List[Ingredient] = field(default_factory=list)
    steps: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    rating: float = 0.0
    is_favorite: bool = False

    def get_total_time(self) -> int:
        return self.prep_time_min + self.cook_time_min

    def get_calories_per_serving(self) -> float:
        total_calories = sum(ing.get_calories() for ing in self.ingredients)
        return total_calories / self.servings if self.servings > 0 else 0.0

    def scale_ingredients(self, factor: float) -> List[Ingredient]:
        scaled = []
        for ing in self.ingredients:
            new_ing = Ingredient(
                name=ing.name,
                amount=ing.amount * factor,
                unit=ing.unit,
                calories_per_unit=ing.calories_per_unit
            )
            scaled.append(new_ing)
        return scaled

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['ingredients'] = [ing.to_dict() for ing in self.ingredients]
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Recipe':
        ingredients_data = data.pop('ingredients', [])
        ingredients = [Ingredient.from_dict(ing) for ing in ingredients_data]
        return cls(**data, ingredients=ingredients)

    def __str__(self) -> str:
        return f"[{self.id}] {self.title} ({self.meal_type}) - {self.get_total_time()} мин"


class RecipeManager:
    def __init__(self, data_file: str = "recipes.json"):
        self.data_file = data_file
        self.recipes: List[Recipe] = []
        self.next_id = 1
        self._load_recipes()

    def _load_recipes(self) -> None:
        if not os.path.exists(self.data_file):
            self._save_recipes()
            return
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.recipes = [Recipe.from_dict(item) for item in data.get('recipes', [])]
                self.next_id = data.get('next_id', 1)
        except (json.JSONDecodeError, KeyError):
            self.recipes = []
            self.next_id = 1

    def _save_recipes(self) -> None:
        data = {
            'recipes': [recipe.to_dict() for recipe in self.recipes],
            'next_id': self.next_id
        }
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def add_recipe(self, recipe_data: Dict[str, Any]) -> Recipe:
        recipe_data['id'] = self.next_id
        self.next_id += 1
        new_recipe = Recipe(**recipe_data)
        self.recipes.append(new_recipe)
        self._save_recipes()
        return new_recipe

    def delete_recipe(self, recipe_id: int) -> bool:
        for i, recipe in enumerate(self.recipes):
            if recipe.id == recipe_id:
                del self.recipes[i]
                self._save_recipes()
                return True
        return False

    def get_recipe_by_id(self, recipe_id: int) -> Optional[Recipe]:
        for recipe in self.recipes:
            if recipe.id == recipe_id:
                return recipe
        return None

    def search_by_title(self, query: str) -> List[Recipe]:
        query = query.lower()
        return [r for r in self.recipes if query in r.title.lower()]

    def search_by_ingredient(self, ingredient_name: str) -> List[Recipe]:
        ingredient_name = ingredient_name.lower()
        result = []
        for recipe in self.recipes:
            for ing in recipe.ingredients:
                if ingredient_name in ing.name:
                    result.append(recipe)
                    break
        return result

    def filter_by_meal_type(self, meal_type: str) -> List[Recipe]:
        return [r for r in self.recipes if r.meal_type == meal_type]

    def get_all_recipes(self) -> List[Recipe]:
        return self.recipes.copy()

    def toggle_favorite(self, recipe_id: int) -> bool:
        recipe = self.get_recipe_by_id(recipe_id)
        if recipe:
            recipe.is_favorite = not recipe.is_favorite
            self._save_recipes()
            return True
        return False

    def get_favorites(self) -> List[Recipe]:
        return [r for r in self.recipes if r.is_favorite]


def print_separator(char: str = "=", length: int = 60) -> None:
    print(char * length)


def print_recipe_details(recipe: Recipe) -> None:
    print_separator()
    print(f"🍽️  {recipe.title.upper()}")
    print(f"Категория: {recipe.meal_type}")
    print(f"Время подготовки: {recipe.prep_time_min} мин | Готовка: {recipe.cook_time_min} мин | Всего: {recipe.get_total_time()} мин")
    print(f"Порций: {recipe.servings}")
    print(f"Калорийность порции: {recipe.get_calories_per_serving():.1f} ккал")
    print(f"Рейтинг: {'⭐' * int(recipe.rating) if recipe.rating else 'нет оценок'}")
    print(f"Избранное: {'❤️' if recipe.is_favorite else '🤍'}")
    print(f"\n📝 Описание: {recipe.description}")
    print("\n📋 Ингредиенты:")
    for ing in recipe.ingredients:
        print(f"   • {ing}")
    print("\n👨‍🍳 Приготовление:")
    for i, step in enumerate(recipe.steps, 1):
        print(f"   {i}. {step}")
    if recipe.tags:
        print(f"\n🏷️ Теги: {', '.join(recipe.tags)}")
    print_separator()


def input_ingredient() -> Ingredient:
    name = input("  Название ингредиента: ").strip()
    while True:
        try:
            amount = float(input("  Количество: "))
            break
        except ValueError:
            print("  Ошибка: введите число.")
    print("  Доступные единицы: г, кг, мл, л, шт., ст.л., ч.л., стакан, щепотка, по вкусу")
    unit = input("  Единица измерения: ").strip()
    while True:
        try:
            cal = float(input("  Калорийность на единицу (0 если неизвестно): "))
            break
        except ValueError:
            print("  Ошибка: введите число.")
    return Ingredient(name, amount, unit, cal)


def input_recipe_data() -> Dict[str, Any]:
    print_separator("-", 40)
    print("Добавление нового рецепта")
    title = input("Название блюда: ").strip()
    description = input("Краткое описание: ").strip()

    print("\nВыберите категорию:")
    meal_types = MealType.get_all_display()
    for i, mt in enumerate(meal_types, 1):
        print(f"  {i}. {mt}")
    while True:
        try:
            choice = int(input("Номер категории: "))
            if 1 <= choice <= len(meal_types):
                meal_type = meal_types[choice - 1]
                break
        except ValueError:
            pass
        print("Неверный ввод, попробуйте снова.")

    while True:
        try:
            prep_time = int(input("Время подготовки (мин): "))
            cook_time = int(input("Время готовки (мин): "))
            servings = int(input("Количество порций: "))
            break
        except ValueError:
            print("Ошибка: введите целое число.")

    print("\nДобавление ингредиентов (пустое название для завершения):")
    ingredients = []
    while True:
        print(f"\nИнгредиент #{len(ingredients) + 1}")
        name = input("  Название (Enter для окончания): ").strip()
        if not name:
            break
        ing = input_ingredient()
        ing.name = name
        ingredients.append(ing)

    print("\nШаги приготовления (пустая строка для завершения):")
    steps = []
    step_num = 1
    while True:
        step = input(f"  Шаг {step_num}: ").strip()
        if not step:
            break
        steps.append(step)
        step_num += 1

    tags_input = input("Теги (через запятую): ").strip()
    tags = [t.strip() for t in tags_input.split(",") if t.strip()] if tags_input else []

    return {
        'title': title,
        'description': description,
        'meal_type': meal_type,
        'prep_time_min': prep_time,
        'cook_time_min': cook_time,
        'servings': servings,
        'ingredients': ingredients,
        'steps': steps,
        'tags': tags
    }


def main_menu(manager: RecipeManager) -> None:
    while True:
        print_separator()
        print("📖 КНИГА РЕЦЕПТОВ - ГЛАВНОЕ МЕНЮ")
        print_separator()
        print("1. Показать все рецепты")
        print("2. Просмотреть рецепт подробно")
        print("3. Добавить новый рецепт")
        print("4. Удалить рецепт")
        print("5. Поиск по названию")
        print("6. Поиск по ингредиенту")
        print("7. Фильтр по категории")
        print("8. Избранные рецепты")
        print("9. Выход")
        print_separator("-")

        choice = input("Выберите действие (1-9): ").strip()

        if choice == "1":
            recipes = manager.get_all_recipes()
            if not recipes:
                print("Нет ни одного рецепта.")
            else:
                for recipe in recipes:
                    print(f"  {recipe}")
        elif choice == "2":
            try:
                rid = int(input("Введите ID рецепта: "))
                recipe = manager.get_recipe_by_id(rid)
                if recipe:
                    print_recipe_details(recipe)
                else:
                    print("Рецепт с таким ID не найден.")
            except ValueError:
                print("Некорректный ID.")
        elif choice == "3":
            try:
                data = input_recipe_data()
                new_recipe = manager.add_recipe(data)
                print(f"Рецепт '{new_recipe.title}' добавлен с ID {new_recipe.id}.")
            except Exception as e:
                print(f"Ошибка при добавлении: {e}")
        elif choice == "4":
            try:
                rid = int(input("Введите ID рецепта для удаления: "))
                if manager.delete_recipe(rid):
                    print("Рецепт удалён.")
                else:
                    print("Рецепт не найден.")
            except ValueError:
                print("Некорректный ID.")
        elif choice == "5":
            query = input("Введите часть названия для поиска: ")
            results = manager.search_by_title(query)
            if results:
                print(f"Найдено {len(results)} рецептов:")
                for r in results:
                    print(f"  {r}")
            else:
                print("Ничего не найдено.")
        elif choice == "6":
            ing = input("Введите название ингредиента: ")
            results = manager.search_by_ingredient(ing)
            if results:
                print(f"Найдено {len(results)} рецептов с ингредиентом '{ing}':")
                for r in results:
                    print(f"  {r}")
            else:
                print("Ничего не найдено.")
        elif choice == "7":
            print("Категории:")
            meal_types = MealType.get_all_display()
            for i, mt in enumerate(meal_types, 1):
                print(f"  {i}. {mt}")
            try:
                idx = int(input("Номер категории: ")) - 1
                if 0 <= idx < len(meal_types):
                    results = manager.filter_by_meal_type(meal_types[idx])
                    if results:
                        for r in results:
                            print(f"  {r}")
                    else:
                        print("Нет рецептов в этой категории.")
                else:
                    print("Неверный номер.")
            except ValueError:
                print("Некорректный ввод.")
        elif choice == "8":
            favs = manager.get_favorites()
            if favs:
                print("Избранные рецепты:")
                for r in favs:
                    print(f"  {r}")
            else:
                print("Нет избранных рецептов.")
        elif choice == "9":
            print("До свидания!")
            break
        else:
            print("Неверный выбор. Попробуйте снова.")


if __name__ == "__main__":
    manager = RecipeManager()
    main_menu(manager)