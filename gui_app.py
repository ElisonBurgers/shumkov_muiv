"""
Графический интерфейс приложения
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from recipe_manager import RecipeManager, MealType, Ingredient
from weekly_menu_planner import WeeklyMenu


class RecipeBookFrame(ttk.Frame):
    """Вкладка 'Книга рецептов'"""

    def __init__(self, parent, recipe_manager):
        super().__init__(parent)
        self.manager = recipe_manager
        self.current_recipes = self.manager.get_all_recipes()
        self._setup_ui()
        self._refresh_list()

    def _setup_ui(self):
        # Левая панель: список рецептов
        left_frame = ttk.Frame(self)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Панель поиска и фильтрации
        search_frame = ttk.Frame(left_frame)
        search_frame.pack(fill=tk.X, pady=2)
        ttk.Label(search_frame, text="Поиск:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=15)
        self.search_entry.pack(side=tk.LEFT, padx=2)
        self.search_entry.bind('<Return>', lambda e: self._search())

        ttk.Label(search_frame, text="Тип:").pack(side=tk.LEFT, padx=(10,0))
        self.filter_var = tk.StringVar(value="Все")
        meal_types = ["Все"] + MealType.get_all_display()
        self.filter_combo = ttk.Combobox(search_frame, textvariable=self.filter_var,
                                         values=meal_types, state="readonly", width=10)
        self.filter_combo.pack(side=tk.LEFT, padx=2)
        self.filter_combo.bind('<<ComboboxSelected>>', lambda e: self._filter())

        # Таблица рецептов
        columns = ("ID", "Название", "Тип", "Время")
        self.tree = ttk.Treeview(left_frame, columns=columns, show="headings", height=15)
        self.tree.heading("ID", text="ID")
        self.tree.heading("Название", text="Название")
        self.tree.heading("Тип", text="Тип")
        self.tree.heading("Время", text="Время (мин)")
        self.tree.column("ID", width=40, anchor=tk.CENTER)
        self.tree.column("Тип", width=80)
        self.tree.column("Время", width=80, anchor=tk.CENTER)
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.bind('<<TreeviewSelect>>', self._on_select)

        # Кнопки под таблицей
        btn_frame = ttk.Frame(left_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        ttk.Button(btn_frame, text="Добавить", command=self._add_recipe).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Удалить", command=self._delete_recipe).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="В избранное", command=self._toggle_favorite).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Обновить", command=self._refresh_list).pack(side=tk.LEFT, padx=2)

        # Правая панель: детали рецепта
        right_frame = ttk.Frame(self)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.detail_text = tk.Text(right_frame, width=50, wrap=tk.WORD, state=tk.DISABLED)
        self.detail_text.pack(fill=tk.BOTH, expand=True)

    def _refresh_list(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.current_recipes = self.manager.get_all_recipes()
        for r in self.current_recipes:
            self.tree.insert("", tk.END, values=(r.id, r.title, r.meal_type, r.get_total_time()))

    def _on_select(self, event):
        selection = self.tree.selection()
        if not selection:
            return
        rid = int(self.tree.item(selection[0], "values")[0])
        recipe = self.manager.get_recipe_by_id(rid)
        if recipe:
            self._show_recipe_details(recipe)

    def _show_recipe_details(self, recipe):
        self.detail_text.config(state=tk.NORMAL)
        self.detail_text.delete(1.0, tk.END)
        lines = [
            f"Название: {recipe.title}",
            f"Категория: {recipe.meal_type}",
            f"Время: {recipe.get_total_time()} мин (подг. {recipe.prep_time_min}, готовка {recipe.cook_time_min})",
            f"Порций: {recipe.servings}",
            f"Калорийность порции: {recipe.get_calories_per_serving():.1f} ккал",
            f"Описание: {recipe.description}",
            f"Рейтинг: {recipe.rating}",
            f"Избранное: {'Да' if recipe.is_favorite else 'Нет'}",
            f"\nИнгредиенты:",
        ]
        for ing in recipe.ingredients:
            lines.append(f"  - {ing}")
        lines.append("\nПриготовление:")
        for i, step in enumerate(recipe.steps, 1):
            lines.append(f"  {i}. {step}")
        if recipe.tags:
            lines.append(f"\nТеги: {', '.join(recipe.tags)}")
        self.detail_text.insert(tk.END, "\n".join(lines))
        self.detail_text.config(state=tk.DISABLED)

    def _search(self):
        query = self.search_var.get().strip()
        if query:
            results = self.manager.search_by_title(query)
        else:
            results = self.manager.get_all_recipes()
        self._update_list_from_results(results)

    def _filter(self):
        meal = self.filter_var.get()
        if meal == "Все":
            self._refresh_list()
        else:
            results = self.manager.filter_by_meal_type(meal)
            self._update_list_from_results(results)

    def _update_list_from_results(self, recipes):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.current_recipes = recipes
        for r in recipes:
            self.tree.insert("", tk.END, values=(r.id, r.title, r.meal_type, r.get_total_time()))

    def _add_recipe(self):
        AddRecipeDialog(self, self.manager, self._refresh_list)

    def _delete_recipe(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите рецепт для удаления.")
            return
        rid = int(self.tree.item(selection[0], "values")[0])
        if messagebox.askyesno("Удаление", "Удалить выбранный рецепт?"):
            self.manager.delete_recipe(rid)
            self._refresh_list()
            self.detail_text.config(state=tk.NORMAL)
            self.detail_text.delete(1.0, tk.END)
            self.detail_text.config(state=tk.DISABLED)

    def _toggle_favorite(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите рецепт.")
            return
        rid = int(self.tree.item(selection[0], "values")[0])
        if self.manager.toggle_favorite(rid):
            self._refresh_list()
            recipe = self.manager.get_recipe_by_id(rid)
            self._show_recipe_details(recipe)
        else:
            messagebox.showerror("Ошибка", "Рецепт не найден.")


class AddRecipeDialog(tk.Toplevel):

    def __init__(self, parent, manager, callback):
        super().__init__(parent)
        self.manager = manager
        self.callback = callback
        self.title("Добавить рецепт")
        self.ingredients = []
        self.steps = []
        self._setup_ui()

    def _setup_ui(self):
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Основные поля
        ttk.Label(main_frame, text="Название:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.title_entry = ttk.Entry(main_frame, width=30)
        self.title_entry.grid(row=0, column=1, pady=2)

        ttk.Label(main_frame, text="Описание:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.desc_entry = ttk.Entry(main_frame, width=30)
        self.desc_entry.grid(row=1, column=1, pady=2)

        ttk.Label(main_frame, text="Тип:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.type_var = tk.StringVar(value=MealType.get_all_display()[0])
        self.type_combo = ttk.Combobox(main_frame, textvariable=self.type_var,
                                       values=MealType.get_all_display(), state="readonly")
        self.type_combo.grid(row=2, column=1, pady=2)

        ttk.Label(main_frame, text="Время подготовки (мин):").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.prep_spin = ttk.Spinbox(main_frame, from_=0, to=999, width=5)
        self.prep_spin.grid(row=3, column=1, pady=2)

        ttk.Label(main_frame, text="Время готовки (мин):").grid(row=4, column=0, sticky=tk.W, pady=2)
        self.cook_spin = ttk.Spinbox(main_frame, from_=0, to=999, width=5)
        self.cook_spin.grid(row=4, column=1, pady=2)

        ttk.Label(main_frame, text="Порций:").grid(row=5, column=0, sticky=tk.W, pady=2)
        self.serv_spin = ttk.Spinbox(main_frame, from_=1, to=50, width=5)
        self.serv_spin.grid(row=5, column=1, pady=2)

        # Ингредиенты
        ttk.Label(main_frame, text="Ингредиенты:").grid(row=6, column=0, sticky=tk.W, pady=5)
        ing_frame = ttk.Frame(main_frame)
        ing_frame.grid(row=6, column=1, pady=5, sticky=tk.W)
        self.ing_listbox = tk.Listbox(ing_frame, height=5, width=40)
        self.ing_listbox.pack(side=tk.LEFT)
        ing_btn_frame = ttk.Frame(ing_frame)
        ing_btn_frame.pack(side=tk.LEFT, padx=5)
        ttk.Button(ing_btn_frame, text="Добавить", command=self._add_ingredient).pack(fill=tk.X)
        ttk.Button(ing_btn_frame, text="Удалить", command=self._remove_ingredient).pack(fill=tk.X, pady=2)

        # Шаги
        ttk.Label(main_frame, text="Шаги:").grid(row=7, column=0, sticky=tk.W, pady=5)
        step_frame = ttk.Frame(main_frame)
        step_frame.grid(row=7, column=1, pady=5, sticky=tk.W)
        self.step_listbox = tk.Listbox(step_frame, height=5, width=40)
        self.step_listbox.pack(side=tk.LEFT)
        step_btn_frame = ttk.Frame(step_frame)
        step_btn_frame.pack(side=tk.LEFT, padx=5)
        ttk.Button(step_btn_frame, text="Добавить", command=self._add_step).pack(fill=tk.X)
        ttk.Button(step_btn_frame, text="Удалить", command=self._remove_step).pack(fill=tk.X, pady=2)

        # Теги
        ttk.Label(main_frame, text="Теги (через запятую):").grid(row=8, column=0, sticky=tk.W, pady=2)
        self.tags_entry = ttk.Entry(main_frame, width=30)
        self.tags_entry.grid(row=8, column=1, pady=2)

        # Кнопки OK/Cancel
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=9, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="Сохранить", command=self._save).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Отмена", command=self.destroy).pack(side=tk.LEFT, padx=5)

    def _add_ingredient(self):
        IngredientDialog(self, self.ingredients, self.ing_listbox)

    def _remove_ingredient(self):
        sel = self.ing_listbox.curselection()
        if sel:
            idx = sel[0]
            del self.ingredients[idx]
            self.ing_listbox.delete(idx)
            self._refresh_ing_list()

    def _refresh_ing_list(self):
        self.ing_listbox.delete(0, tk.END)
        for ing in self.ingredients:
            self.ing_listbox.insert(tk.END, str(ing))

    def _add_step(self):
        step = simpledialog.askstring("Шаг", "Введите текст шага:")
        if step:
            self.steps.append(step)
            self.step_listbox.insert(tk.END, step)

    def _remove_step(self):
        sel = self.step_listbox.curselection()
        if sel:
            idx = sel[0]
            del self.steps[idx]
            self.step_listbox.delete(idx)

    def _save(self):
        title = self.title_entry.get().strip()
        if not title:
            messagebox.showwarning("Предупреждение", "Введите название.")
            return
        try:
            prep = int(self.prep_spin.get())
            cook = int(self.cook_spin.get())
            servings = int(self.serv_spin.get())
        except ValueError:
            messagebox.showerror("Ошибка", "Некорректное число в полях времени или порций.")
            return
        tags = [t.strip() for t in self.tags_entry.get().split(",") if t.strip()]
        data = {
            'title': title,
            'description': self.desc_entry.get().strip(),
            'meal_type': self.type_var.get(),
            'prep_time_min': prep,
            'cook_time_min': cook,
            'servings': servings,
            'ingredients': self.ingredients,
            'steps': self.steps,
            'tags': tags
        }
        try:
            self.manager.add_recipe(data)
            messagebox.showinfo("Успех", "Рецепт добавлен.")
            self.destroy()
            self.callback()
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))


class IngredientDialog(tk.Toplevel):

    def __init__(self, parent, ingredients_list, listbox):
        super().__init__(parent)
        self.ingredients = ingredients_list
        self.listbox = listbox
        self.title("Добавить ингредиент")
        self._setup_ui()

    def _setup_ui(self):
        frame = ttk.Frame(self, padding=10)
        frame.pack()
        ttk.Label(frame, text="Название:").grid(row=0, column=0, pady=2)
        self.name_entry = ttk.Entry(frame, width=20)
        self.name_entry.grid(row=0, column=1, pady=2)

        ttk.Label(frame, text="Количество:").grid(row=1, column=0, pady=2)
        self.amount_entry = ttk.Entry(frame, width=10)
        self.amount_entry.grid(row=1, column=1, pady=2)

        ttk.Label(frame, text="Ед.изм.:").grid(row=2, column=0, pady=2)
        self.unit_var = tk.StringVar(value="г")
        units = ["г", "кг", "мл", "л", "шт.", "ст.л.", "ч.л.", "стакан", "щепотка", "по вкусу"]
        self.unit_combo = ttk.Combobox(frame, textvariable=self.unit_var, values=units, state="readonly")
        self.unit_combo.grid(row=2, column=1, pady=2)

        ttk.Label(frame, text="Калорий на ед.:").grid(row=3, column=0, pady=2)
        self.cal_entry = ttk.Entry(frame, width=10)
        self.cal_entry.insert(0, "0")
        self.cal_entry.grid(row=3, column=1, pady=2)

        ttk.Button(frame, text="Добавить", command=self._add).grid(row=4, columnspan=2, pady=10)

    def _add(self):
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showwarning("Ошибка", "Введите название ингредиента.")
            return
        try:
            amount = float(self.amount_entry.get())
            cal = float(self.cal_entry.get())
        except ValueError:
            messagebox.showerror("Ошибка", "Некорректное число.")
            return
        ing = Ingredient(name, amount, self.unit_var.get(), cal)
        self.ingredients.append(ing)
        self.listbox.insert(tk.END, str(ing))
        self.destroy()


class WeeklyMenuFrame(ttk.Frame):
    """Вкладка Меню на неделю"""

    def __init__(self, parent, recipe_manager, weekly_menu):
        super().__init__(parent)
        self.recipe_manager = recipe_manager
        self.weekly_menu = weekly_menu
        self._setup_ui()

    def _setup_ui(self):
        # Верхняя панель управления
        control_frame = ttk.Frame(self)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(control_frame, text="День:").pack(side=tk.LEFT)
        self.day_var = tk.StringVar(value=WeeklyMenu.DAYS_OF_WEEK[0])
        self.day_combo = ttk.Combobox(control_frame, textvariable=self.day_var,
                                      values=WeeklyMenu.DAYS_OF_WEEK, state="readonly", width=12)
        self.day_combo.pack(side=tk.LEFT, padx=5)
        self.day_combo.bind('<<ComboboxSelected>>', lambda e: self._load_day())

        ttk.Button(control_frame, text="Обновить", command=self._load_day).pack(side=tk.LEFT, padx=5)

        ttk.Label(control_frame, text="Тип блюда:").pack(side=tk.LEFT, padx=(20,0))
        self.meal_filter_var = tk.StringVar(value="Все")
        meal_types = ["Все"] + MealType.get_all_display()
        self.meal_combo = ttk.Combobox(control_frame, textvariable=self.meal_filter_var,
                                       values=meal_types, state="readonly", width=12)
        self.meal_combo.pack(side=tk.LEFT, padx=5)
        # Привязываем событие для обновления списка доступных рецептов
        self.meal_combo.bind('<<ComboboxSelected>>', lambda e: self._load_available())

        ttk.Button(control_frame, text="Добавить блюдо", command=self._add_meal).pack(side=tk.LEFT, padx=5)

        # Основная область: меню дня и доступные рецепты
        paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Левая: блюда на день
        left_frame = ttk.Frame(paned)
        paned.add(left_frame, weight=1)
        ttk.Label(left_frame, text="Блюда на день:").pack()
        self.day_listbox = tk.Listbox(left_frame, height=15, width=30)
        self.day_listbox.pack(fill=tk.BOTH, expand=True)
        day_btn_frame = ttk.Frame(left_frame)
        day_btn_frame.pack(fill=tk.X)
        ttk.Button(day_btn_frame, text="Удалить выбранное", command=self._remove_meal).pack(side=tk.LEFT, padx=2)
        ttk.Button(day_btn_frame, text="Очистить день", command=self._clear_day).pack(side=tk.LEFT, padx=2)

        # Правая: доступные рецепты
        right_frame = ttk.Frame(paned)
        paned.add(right_frame, weight=1)
        ttk.Label(right_frame, text="Доступные рецепты:").pack()
        self.avail_listbox = tk.Listbox(right_frame, height=15, width=40)
        self.avail_listbox.pack(fill=tk.BOTH, expand=True)

        # Нижняя панель: общие действия
        bottom_frame = ttk.Frame(self)
        bottom_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(bottom_frame, text="Показать всё меню", command=self._show_full_menu).pack(side=tk.LEFT, padx=2)
        ttk.Button(bottom_frame, text="Список покупок", command=self._shopping_list).pack(side=tk.LEFT, padx=2)
        ttk.Button(bottom_frame, text="График калорий", command=self._calorie_chart).pack(side=tk.LEFT, padx=2)

        self._load_day()
        self._load_available()

    def _load_day(self):
        self.day_listbox.delete(0, tk.END)
        day = self.day_var.get()
        recipes = self.weekly_menu.get_recipes_for_day(day, self.recipe_manager)
        for r in recipes:
            self.day_listbox.insert(tk.END, f"ID {r.id}: {r.title} ({r.meal_type})")

    def _load_available(self):
        self.avail_listbox.delete(0, tk.END)
        meal = self.meal_filter_var.get()
        if meal == "Все":
            recipes = self.recipe_manager.get_all_recipes()
        else:
            recipes = self.recipe_manager.filter_by_meal_type(meal)
        for r in recipes:
            self.avail_listbox.insert(tk.END, f"ID {r.id}: {r.title} ({r.meal_type})")

    def _add_meal(self):
        sel = self.avail_listbox.curselection()
        if not sel:
            messagebox.showwarning("Предупреждение", "Выберите рецепт из доступных.")
            return
        rid = int(self.avail_listbox.get(sel[0]).split(":")[0].split()[1])
        day = self.day_var.get()
        if self.weekly_menu.add_recipe_to_day(day, rid):
            self._load_day()
        else:
            messagebox.showinfo("Информация", "Рецепт уже есть в этом дне.")

    def _remove_meal(self):
        sel = self.day_listbox.curselection()
        if not sel:
            messagebox.showwarning("Предупреждение", "Выберите блюдо для удаления.")
            return
        rid = int(self.day_listbox.get(sel[0]).split(":")[0].split()[1])
        day = self.day_var.get()
        if self.weekly_menu.remove_recipe_from_day(day, rid):
            self._load_day()
        else:
            messagebox.showerror("Ошибка", "Не удалось удалить блюдо.")

    def _clear_day(self):
        if messagebox.askyesno("Очистка", "Удалить все блюда в этот день?"):
            self.weekly_menu.clear_day(self.day_var.get())
            self._load_day()

    def _show_full_menu(self):
        menu_win = tk.Toplevel(self)
        menu_win.title("Меню на неделю")
        text = tk.Text(menu_win, width=70, height=20)
        text.pack(fill=tk.BOTH, expand=True)
        for day in WeeklyMenu.DAYS_OF_WEEK:
            text.insert(tk.END, f"{day}:\n")
            recipes = self.weekly_menu.get_recipes_for_day(day, self.recipe_manager)
            if not recipes:
                text.insert(tk.END, "  (нет блюд)\n")
            else:
                for r in recipes:
                    text.insert(tk.END, f"  - {r.title} ({r.meal_type})\n")
            text.insert(tk.END, "\n")
        text.config(state=tk.DISABLED)

    def _shopping_list(self):
        shop = self.weekly_menu.generate_shopping_list(self.recipe_manager)
        if not shop:
            messagebox.showinfo("Список покупок", "Список покупок пуст.")
            return
        win = tk.Toplevel(self)
        win.title("Список покупок")
        text = tk.Text(win, width=50, height=15)
        text.pack(fill=tk.BOTH, expand=True)
        for name, data in sorted(shop.items()):
            amount_str = f"{data['amount']:.2f}".rstrip('0').rstrip('.')
            text.insert(tk.END, f"{name}: {amount_str} {data['unit']}\n")
        text.config(state=tk.DISABLED)

    def _calorie_chart(self):
        days = WeeklyMenu.DAYS_OF_WEEK
        calories = []
        for day in days:
            recipes = self.weekly_menu.get_recipes_for_day(day, self.recipe_manager)
            total = sum(r.get_calories_per_serving() for r in recipes)
            calories.append(total)

        fig, ax = plt.subplots(figsize=(8, 4))
        ax.bar(days, calories, color='skyblue')
        ax.set_title("Калорийность блюд по дням недели")
        ax.set_ylabel("Калории (ккал)")
        ax.grid(axis='y', linestyle='--', alpha=0.7)

        chart_win = tk.Toplevel(self)
        chart_win.title("График калорийности")
        canvas = FigureCanvasTkAgg(fig, master=chart_win)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)


class Application(tk.Tk):
    """Главное окно приложения"""

    def __init__(self):
        super().__init__()
        self.title("Книга рецептов и планировщик меню")
        self.geometry("900x600")
        self.recipe_manager = RecipeManager()
        self.weekly_menu = WeeklyMenu()
        self._setup_ui()

    def _setup_ui(self):
        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True)
        self.recipe_frame = RecipeBookFrame(notebook, self.recipe_manager)
        self.menu_frame = WeeklyMenuFrame(notebook, self.recipe_manager, self.weekly_menu)
        notebook.add(self.recipe_frame, text="Книга рецептов")
        notebook.add(self.menu_frame, text="Меню на неделю")


if __name__ == "__main__":
    app = Application()
    app.mainloop()