from kivy.graphics import Color, Rectangle
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.app import App
from kivy.core.window import Window
import webbrowser
import finder


class MainScreen(FloatLayout):
    def on_size(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(.5, .5, 1, 1)
            Rectangle(pos=self.pos, size=self.size)


def open_url(instance):
    webbrowser.open_new_tab(instance.__getattribute__("url"))


class FinderApp(App):
    scroll_layout = ScrollView(size_hint=(1, None), size=(Window.width*.9, Window.height * .9))
    layout = MainScreen()
    text = ""
    # urls = ["https://www.javatpoint.com/python-tutorial", "https://yandex.ru", "https://habr.com/ru/post/244561/", "https://discord.com"]
    urls = []

    def build2(self):
        Window.size = (312, 672)  # 260 560

        text = TextInput(pos_hint={"x": 0, "y": .9}, size_hint=(.8, .1), multiline=False, font_size=32)
        text.bind(text=self.text_update)
        text.bind(on_text_validate=self.find)
        self.layout.add_widget(text)

        button = Button(text="найти", pos_hint={"x": .8, "y": .9}, size_hint=(.2, .1))
        button.bind(on_press=self.find)
        self.layout.add_widget(button)

        lay = GridLayout(cols=1, size_hint_y=None)
        lay.bind(minimum_height=lay.setter('height'))
        for url in self.urls:
            btn = Button(
                text=url,
                text_size=(Window.width, None),
                size_hint=(Window.width * .9, None),
                font_size=24,
                height=100,
                background_color=(1, 1, 1, 0)
            )
            btn.__setattr__("url", url)
            btn.bind(on_press=open_url)
            lay.add_widget(btn)
        self.scroll_layout = ScrollView(size_hint=(1, None), size=(Window.width*.9, Window.height * .9))
        self.scroll_layout.add_widget(lay)
        self.layout.add_widget(self.scroll_layout)
        return self.layout

    def build(self):
        Window.size = (312, 672)  # 260 560

        text = TextInput(pos_hint={"x": 0, "y": .9}, size_hint=(.8, .1), multiline=False, font_size=32)
        text.bind(text=self.text_update)
        text.bind(on_text_validate=self.find)
        self.layout.add_widget(text)

        button = Button(text="найти", pos_hint={"x": .8, "y": .9}, size_hint=(.2, .1))
        button.bind(on_press=self.find)
        self.layout.add_widget(button)

        self.update_scroll(text="Введите запрос")
        return self.layout

    def text_update(self, instance, text: str):
        self.text = text

    def update_scroll(self, text="По Вашему запросу ничего не найдено"):
        if len(self.urls) == 0 or self.text == "":
            if len(self.layout.children) > 2:
                self.layout.remove_widget(self.layout.children[0])
            self.layout.add_widget(Label(
                size_hint=(.9, 1),
                pos_hint={"x": 0.05, "y": 0},
                size=(0, 0),
                text=text,
                halign="center",
                text_size=(Window.width, None),
                font_size=24,
            ))
            return
        lay = GridLayout(cols=1, size_hint_y=None)
        lay.bind(minimum_height=lay.setter('height'))
        for url in self.urls:
            btn = Button(
                text=url,
                text_size=(Window.width, None),
                size_hint=(Window.width * .9, None),
                font_size=24,
                height=100,
                background_color=(1, 1, 1, 0)
            )
            btn.__setattr__("url", url)
            btn.bind(on_press=open_url)
            lay.add_widget(btn)
        self.scroll_layout = ScrollView(size_hint=(1, None), size=(Window.width * .9, Window.height * .9))
        self.scroll_layout.add_widget(lay)
        if len(self.layout.children) > 2:
            self.layout.remove_widget(self.layout.children[0])
        self.layout.add_widget(self.scroll_layout)

    def find(self, *args):
        self.urls = finder.find(self.text)
        self.update_scroll()


if __name__ == "__main__":
    app = FinderApp()
    app.run()
