import json
import matplotlib

import numexpr as ne
import numpy as np

from functools import partial
from tkinter import *
from tkinter.filedialog import asksaveasfile,askopenfile

from matplotlib import pyplot as plt

from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg,
                                               NavigationToolbar2Tk)

matplotlib.use('TkAgg')

# class for entries storage (класс для хранения текстовых полей)
class Entries:
    def __init__(self):
        self.entries_list : list[Entry] = []
        self.parent_window = None

    def set_parent_window(self, parent_window):
        self.parent_window = parent_window

    # adding of new entry (добавление нового текстового поля)
    def add_entry(self):
        new_entry = Entry(self.parent_window)
        new_entry.icursor(0)
        new_entry.focus()
        new_entry.pack()
        plot_button = self.parent_window.get_button_by_name('plot')
        if plot_button:
            plot_button.pack_forget()
        self.parent_window.add_button('plot', 'Plot', 'plot', hot_key='<Return>')
        self.entries_list.append(new_entry)
        return new_entry

    def remove_entry(self):
        entry = self.parent_window.focus_get()
        # still want to chek if it's an entry
        if entry not in self.entries_list:
            return
        if len(self.entries_list) < 2:
            # don't want to deal with empty list
            mw = ModalWindow(self.parent_window, title='', labeltext= 'Удаление последнего поля ввода невозможно')
            ok_button = Button(master=mw.top, text = 'OK', command=mw.cancel)
            mw.add_button(ok_button)
            return
        else:
            if len(entry.get()) != 0:
                # check content and warn
                mw = ModalWindow(self.parent_window, title='', labeltext = 'Вы точно хотите удалить непустое поле?')
                yes_button = Button(master=mw.top, text = 'Да', command=mw.ok)
                no_button = Button(master=mw.top, text = 'Нет', command=mw.cancel)
                mw.add_button(yes_button)
                mw.add_button(no_button)
                choice = mw.result()
                if choice == 0:
                    return
            entry.pack_forget()
            # move focus to existing entry
            prev_index = max(self.entries_list.index(entry)-1,0)
            self.entries_list.remove(entry)
            self.entries_list[prev_index].focus_set()
        # redraw plot_button
        plot_button = self.parent_window.get_button_by_name('plot')
        if plot_button:
            plot_button.pack_forget()
        self.parent_window.add_button('plot', 'Plot', 'plot', hot_key='<Return>')

    def reset_list(self):
        for entry in self.entries_list:
            entry.pack_forget()
        self.entries_list.clear()

# class for plotting (класс для построения графиков)
class Plotter:
    def __init__(self, x_min=-20, x_max=20, dx=0.01):
        self.x_min = x_min
        self.x_max = x_max
        self.dx = dx
        self._last_plotted_list_of_function = None
        self._last_plotted_figure = None
        self.parent_window = None

    def set_parent_window(self, parent_window):
        self.parent_window = parent_window

    # plotting of graphics (построение графиков функций)
    def plot(self, list_of_function, title='Графики функций', x_label='x', y_label='y', need_legend=True):
        fig = plt.figure()

        x = np.arange(self.x_min, self.x_max, self.dx)

        new_funcs = [f if 'x' in f else 'x/x * ({})'.format(f) for f in list_of_function]

        ax = fig.add_subplot(1, 1, 1)
        for func in new_funcs:
            ax.plot(x, ne.evaluate(func), linewidth=1.5)

        fig.suptitle(title)
        plt.xlabel(x_label)
        plt.ylabel(y_label)
        if need_legend:
            plt.legend(list_of_function)
        self._last_plotted_list_of_function = list_of_function
        self._last_plotted_figure = fig
        return fig


# class for commands storage (класс для хранения команд)
class Commands:
    class State:
        def __init__(self):
            self.list_of_function = []

        def save_state(self):
            tmp_dict = {'list_of_function': self.list_of_function}
            file_out = asksaveasfile(defaultextension=".json")
            if file_out is not None:
                json.dump(tmp_dict, file_out)
            return self

        def load_state(self):
            file_in = askopenfile()
            if file_in is not None:
                tmp_dict = json.load(file_in)
                self.list_of_function = tmp_dict.get('list_of_function')

        def reset_state(self):
            self.list_of_function = []

    def __init__(self):
        self.command_dict = {}
        self.__figure_canvas = None
        self.__navigation_toolbar = None
        self._state = Commands.State()
        self.__empty_entry_counter = 0
        self.parent_window = None

    def set_parent_window(self, parent_window : 'App'):
        self.parent_window = parent_window

    def add_command(self, name, command):
        self.command_dict[name] = command

    def get_command_by_name(self, command_name):
        return self.command_dict[command_name]

    def __forget_canvas(self):
        # in debugger: "Commands object has no attribute '__figure_canvas'". Don't know the reason, but it's _Commands__figure_canvas
        # and it indeed works and has fixed buttons appearing under canvas if loaded from file
        if self._Commands__figure_canvas is not None:
            self._Commands__figure_canvas.get_tk_widget().pack_forget()

    def __forget_navigation(self):
        if self.__navigation_toolbar is not None:
            self.__navigation_toolbar.pack_forget()

    def plot(self, *args, **kwargs):
        def is_not_blank(s):
            return bool(s and not s.isspace())

        self._state.reset_state()
        list_of_function = []
        for entry in self.parent_window.entries.entries_list:
            get_func_str = entry.get()
            self._state.list_of_function.append(get_func_str)
            if is_not_blank(get_func_str):
                list_of_function.append(get_func_str)
            else:
                if self.__empty_entry_counter == 0:
                    mw = ModalWindow(self.parent_window, title='Пустая строка', labeltext='Это пример модального окна, '
                                                                                          'возникающий, если ты ввел '
                                                                                          'пустую '
                                                                                          'строку. С этим ничего '
                                                                                          'делать не нужно. '
                                                                                          'Просто нажми OK :)')
                    ok_button = Button(master=mw.top, text='OK', command=mw.cancel)
                    mw.add_button(ok_button)
                    self.__empty_entry_counter = 1
        self.__empty_entry_counter = 0
        figure = self.parent_window.plotter.plot(list_of_function)
        self._state.figure = figure
        self.__forget_canvas()
        self.__figure_canvas = FigureCanvasTkAgg(figure, self.parent_window)
        self.__forget_navigation()
        self.__navigation_toolbar = NavigationToolbar2Tk(self.__figure_canvas, self.parent_window)
        self.__figure_canvas.get_tk_widget().pack(side=TOP, fill=BOTH, expand=1)
        plot_button = self.parent_window.get_button_by_name('plot')
        if plot_button:
            plot_button.pack_forget()

    def add_func(self, *args, **kwargs):
        self.__forget_canvas()
        self.__forget_navigation()
        self.parent_window.entries.add_entry()

    def rm_func(self, *args, **kwargs):
        self.__forget_canvas()
        self.__forget_navigation()
        self.parent_window.entries.remove_entry()

    def save_as(self):
        self._state.save_state()
        return self
    def load_from_file(self, *args, **kwargs):
        self._state.load_state()
        self.__forget_canvas()
        entries = self.parent_window.entries
        entries.reset_list()
        for func in self._state.list_of_function:
            entry = entries.add_entry()
            entry.insert(0,func)
        entries.entries_list[0].focus_set()
        return self

# class for buttons storage (класс для хранения кнопок)
class Buttons:
    def __init__(self):
        self.buttons = {}
        self.parent_window = None

    def set_parent_window(self, parent_window):
        self.parent_window = parent_window

    def add_button(self, name : str, text : str, command):
        new_button = Button(master=self.parent_window, text=text, command=command)
        self.buttons[name] = new_button
        return new_button

    def delete_button(self, name):
        button = self.buttons.get(name)
        if button:
            button.pack_forget()


# class for generate modal windows (класс для генерации модальных окон)
class ModalWindow:
    def __init__(self, parent, title, labeltext=''):
        self.buttons = []
        self.top = Toplevel(parent)
        self.top.transient(parent)
        self.top.grab_set()
        self.var = 0
        if len(title) > 0:
            self.top.title(title)
        if len(labeltext) == 0:
            labeltext = 'Default text'
        Label(self.top, text=labeltext).pack()

    def add_button(self, button):
        self.buttons.append(button)
        button.pack(pady=5)

    def cancel(self):
        self.var = 0
        self.top.destroy()
    def ok(self):
        self.var = 1
        self.top.destroy()
    def result(self):
        self.top.wait_window()
        return self.var


# app class (класс приложения)
class App(Tk):
    def __init__(self, buttons : Buttons, plotter : Plotter, commands : Commands, entries : Entries):
        super().__init__()
        self.buttons = buttons
        self.plotter = plotter
        self.commands = commands
        self.entries = entries
        self.entries.set_parent_window(self)
        self.plotter.set_parent_window(self)
        self.commands.set_parent_window(self)
        self.buttons.set_parent_window(self)

    def add_button(self, name : str, text : str, command_name : str, *args, **kwargs):
        hot_key = kwargs.get('hot_key')
        if hot_key:
            kwargs.pop('hot_key')
        callback = partial(self.commands.get_command_by_name(command_name), *args, **kwargs)
        new_button = self.buttons.add_button(name=name, text=text, command=callback)
        if hot_key:
            self.bind(hot_key, callback)
        new_button.pack(fill=BOTH)

    def get_button_by_name(self, name : str):
        return self.buttons.buttons.get(name)

    def create_menu(self):
        menu = Menu(self)
        self.config(menu=menu)

        file_menu = Menu(menu)
        file_menu.add_command(label="Save as...", command=self.commands.get_command_by_name('save_as'))
        file_menu.add_command(label="Load file", command=self.commands.get_command_by_name('load_file'))
        self.bind("<Control-o>",self.commands.get_command_by_name('load_file'))
        menu.add_cascade(label="File", menu=file_menu)


if __name__ == "__main__":
    # init buttons (создаем кнопки)
    buttons_main = Buttons()
    # init plotter (создаем отрисовщик графиков)
    plotter_main = Plotter()
    # init commands for executing on buttons or hot keys press
    # (создаем команды, которые выполняются при нажатии кнопок или горячих клавиш)
    commands_main = Commands()
    # init entries (создаем текстовые поля)
    entries_main = Entries()
    # command's registration (регистрация команд)
    commands_main.add_command('plot', commands_main.plot)
    commands_main.add_command('add_func', commands_main.add_func)
    commands_main.add_command('save_as', commands_main.save_as)
    commands_main.add_command('load_file',commands_main.load_from_file)
    commands_main.add_command('rm_func', commands_main.rm_func)
    # init app (создаем экземпляр приложения)
    app = App(buttons_main, plotter_main, commands_main, entries_main)
    # init add func button (добавляем кнопку добавления новой функции)
    app.add_button('add_func', 'Добавить функцию', 'add_func', hot_key='<Control-a>')
    app.add_button('rm_func','Удалить функцию','rm_func', hot_key='<Control-d>')
    # init first entry (создаем первое поле ввода)
    entries_main.add_entry()
    app.create_menu()
    # добавил комментарий для коммита
    # Handle WM_DELETE_WINDOW
    app.protocol("WM_DELETE_WINDOW",app.destroy)
    # application launch (запуск "вечного" цикла приложеня)
    app.mainloop()
