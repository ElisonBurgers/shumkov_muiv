"""
Модуль для составления меню на неделю.
"""

import json
import os
from typing import Dict, List, Optional, Any
from recipe_manager import RecipeManager, MealType, Recipe, print_separator


class WeeklyMenu:
    DAYS_OF_WEEK = [
        "Понедельник", "Вторник", "Среда", "Четверг",
        "Пятница", "Суббота", "Воскресенье"
    ]

    def __init__(self, menu_file: str = "weekly_menu.json"):
        self.menu_file = menu_file
        self.plan: Dict[str, List[int]] = {day: [] for day in self.DAYS_OF_WEEK}
        self._load_menu()

    def _load_menu(self) -> None:
        """Загрузка меню из JSON-файла."""
        if not os.path.exists(self.menu_file):
            return
        try:
            with open(self.menu_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for day in self.DAYS_OF_WEEK:
                    self.plan[day] = data.get(day, [])
        except (json.JSONDecodeError, KeyError):
            # Если файл повреждён, начинаем с пустого меню
            pass

    def _save_menu(self) -> None:
        with open(self.menu_file, 'w', encoding='utf-8') as f:
            json.dump(self.plan, f, ensure_ascii=False, indent=2)

    def add_recipe_to_day(self, day: str, recipe_id: int) -> bool:
        if day not in self.plan:
            return False
        if recipe_id not in self.plan[day]:
            self.plan[day].append(recipe_id)
            self._save_menu()
            return True
        return False

    def remove_recipe_from_day(self, day: str, recipe_id: int) -> bool:
        if day not in self.plan:
            return False
        if recipe_id in self.plan[day]:
            self.plan[day].remove(recipe_id)
            self._save_menu()
            return True
        return False

    def get_recipes_for_day(self, day: str, manager: RecipeManager) -> List[Recipe]:
        if day not in self.plan:
            return []
        result = []
        for rid in self.plan[day]:
            recipe = manager.get_recipe_by_id(rid)
            if recipe:
                result.append(recipe)
        return result

    def clear_day(self, day: str) -> None:
        if day in self.plan:
            self.plan[day] = []
            self._save_menu()

    def print_weekly_menu(self, manager: RecipeManager) -> None:
        print_separator()
        print("📅 МЕНЮ НА НЕДЕЛЮ")
        print_separator()
        for day in self.DAYS_OF_WEEK:
            recipes = self.get_recipes_for_day(day, manager)
            print(f"\n{day}:")
            if not recipes:
                print("   (нет блюд)")
            else:
                for recipe in recipes:
                    print(f"   • {recipe.title} (ID: {recipe.id}) - {recipe.meal_type}")
        print_separator()

    def generate_shopping_list(self, manager: RecipeManager) -> Dict[str, Dict[str, Any]]:
        from recipe_manager import Unit

        shopping: Dict[str, Dict[str, Any]] = {}
        for day in self.DAYS_OF_WEEK:
            for recipe in self.get_recipes_for_day(day, manager):
                for ing in recipe.ingredients:
                    if ing.unit in ("по вкусу", "щепотка"):
                        continue
                    # Привод к базовой единице
                    base_amount = None
                    conv = Unit.get_convertible_units()
                    if ing.unit in conv:
                        base_amount = ing.amount * conv[ing.unit]
                        base_unit = "г" if ing.unit in ("г", "кг") else "мл"
                    else:
                        base_unit = None

                    if base_amount is not None:
                        key = ing.name
                        if key not in shopping:
                            shopping[key] = {"amount": 0.0, "unit": base_unit, "base_unit": base_unit}
                        shopping[key]["amount"] += base_amount
                    else:
                        key = f"{ing.name} ({ing.unit})"
                        if key not in shopping:
                            shopping[key] = {"amount": 0.0, "unit": ing.unit, "base_unit": None}
                        shopping[key]["amount"] += ing.amount

        # Обратное преобразование к крупным единицам
        for name, data in shopping.items():
            if data["base_unit"] is not None:
                if data["base_unit"] == "г" and data["amount"] >= 1000:
                    data["amount"] /= 1000
                    data["unit"] = "кг"
                elif data["base_unit"] == "мл" and data["amount"] >= 1000:
                    data["amount"] /= 1000
                    data["unit"] = "л"
                else:
                    data["unit"] = data["base_unit"]
                # Удаляем служебный ключ
                del data["base_unit"]
            else:
                del data["base_unit"]

        return shopping

    def print_shopping_list(self, manager: RecipeManager) -> None:
        shop = self.generate_shopping_list(manager)
        if not shop:
            print("Список покупок пуст. Добавьте блюда в меню.")
            return
        print_separator()
        print("🛒 СПИСОК ПОКУПОК НА НЕДЕЛЮ")
        print_separator()
        for name in sorted(shop.keys()):
            data = shop[name]
            amount_str = f"{data['amount']:.2f}".rstrip('0').rstrip('.')
            print(f"  • {name}: {amount_str} {data['unit']}")
        print_separator()


class WeeklyMenuPlanner:
    def __init__(self):
        self.manager = RecipeManager()
        self.menu = WeeklyMenu()

    def run(self):
        while True:
            print_separator()
            print("📅 ПЛАНИРОВЩИК МЕНЮ НА НЕДЕЛЮ")
            print_separator()
            print("1. Показать меню на неделю")
            print("2. Добавить блюдо в день")
            print("3. Удалить блюдо из дня")
            print("4. Очистить день")
            print("5. Список покупок")
            print("6. Выход")
            print_separator("-")

            choice = input("Выберите действие: ").strip()

            if choice == "1":
                self.menu.print_weekly_menu(self.manager)
            elif choice == "2":
                self._add_meal()
            elif choice == "3":
                self._remove_meal()
            elif choice == "4":
                self._clear_day()
            elif choice == "5":
                self.menu.print_shopping_list(self.manager)
            elif choice == "6":
                print("Выход из планировщика.")
                break
            else:
                print("Неверный выбор.")

    def _select_day(self) -> str:
        print("Выберите день недели:")
        for i, day in enumerate(WeeklyMenu.DAYS_OF_WEEK, 1):
            print(f"  {i}. {day}")
        while True:
            try:
                idx = int(input("Номер дня: ")) - 1
                if 0 <= idx < len(WeeklyMenu.DAYS_OF_WEEK):
                    return WeeklyMenu.DAYS_OF_WEEK[idx]
                print("Неверный номер дня.")
            except ValueError:
                print("Введите число.")

    def _select_meal_filter(self) -> Optional[str]:
        meal_types = MealType.get_all_display()
        print("\nФильтр по типу блюда:")
        print("  0. Показать все")
        for i, mt in enumerate(meal_types, 1):
            print(f"  {i}. {mt}")
        while True:
            try:
                choice = int(input("Выберите тип (0 - все): "))
                if choice == 0:
                    return None
                elif 1 <= choice <= len(meal_types):
                    return meal_types[choice - 1]
                print("Неверный номер.")
            except ValueError:
                print("Введите число.")

    def _add_meal(self):
        day = self._select_day()
        meal_filter = self._select_meal_filter()

        if meal_filter:
            recipes = self.manager.filter_by_meal_type(meal_filter)
            filter_info = f" ({meal_filter})"
        else:
            recipes = self.manager.get_all_recipes()
            filter_info = ""

        if not recipes:
            print(f"Нет доступных рецептов{filter_info}.")
            return

        print(f"\nДоступные рецепты{filter_info}:")
        for r in recipes:
            print(f"  ID {r.id}: {r.title} ({r.meal_type})")

        try:
            rid = int(input("Введите ID рецепта для добавления: "))
            if any(r.id == rid for r in recipes):
                if self.menu.add_recipe_to_day(day, rid):
                    print(f"Рецепт добавлен в меню на {day}.")
                else:
                    print("Рецепт уже присутствует в этом дне.")
            else:
                print("Рецепт с таким ID не найден среди предложенных.")
        except ValueError:
            print("Некорректный ID.")

    def _remove_meal(self):
        self.menu.print_weekly_menu(self.manager)
        day = self._select_day()
        today_recipes = self.menu.get_recipes_for_day(day, self.manager)
        if not today_recipes:
            print(f"На {day} нет блюд.")
            return
        print(f"\nБлюда на {day}:")
        for r in today_recipes:
            print(f"  ID {r.id}: {r.title}")
        try:
            rid = int(input("Введите ID рецепта для удаления: "))
            if self.menu.remove_recipe_from_day(day, rid):
                print("Блюдо удалено из меню.")
            else:
                print("Блюдо с таким ID не найдено в этом дне.")
        except ValueError:
            print("Некорректный ID.")

    def _clear_day(self):
        """Полная очистка меню на день."""
        day = self._select_day()
        confirm = input(f"Удалить все блюда на {day}? (y/n): ").lower()
        if confirm in ('y', 'yes', 'да'):
            self.menu.clear_day(day)
            print(f"Меню на {day} очищено.")
        else:
            print("Отменено.")


if __name__ == "__main__":
    planner = WeeklyMenuPlanner()
    planner.run()