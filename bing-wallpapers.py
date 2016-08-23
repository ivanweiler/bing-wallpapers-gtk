from gi.repository import Gtk, GdkPixbuf, Gio
from bing import *
from cache import *


class MainWindow(Gtk.Window):

    def __init__(self):
        Gtk.Window.__init__(self, title="Bing Wallpapers")

        # self.set_border_width(3)
        self.set_size_request(220*3 + 6*10, 800)
        # self.set_resizable(False)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.connect("delete-event", Gtk.main_quit)

        self.notebook = Gtk.Notebook()
        self.add(self.notebook)

        self.pages = []

        for i, label in enumerate(Bing.labels):
            spinner = Gtk.Spinner()
            spinner.start()

            loader = Gtk.HBox()
            loader.add(spinner)

            self.pages.append(loader)
            self.notebook.append_page(loader, Gtk.Label(label))

        self.show_all()

        self.liststores = []
        self.iconviews = []
        for i in range(0, 4):
            liststore = Gtk.ListStore(GdkPixbuf.Pixbuf, str)
            iconview = Gtk.IconView.new()
            iconview.set_model(liststore)
            iconview.set_pixbuf_column(0)
            iconview.set_text_column(1)
            iconview.set_columns(3)
            iconview.set_item_width(100)
            # iconview.set_activate_on_single_click(True)
            iconview.connect("item-activated", self._item_activated)

            self.liststores.append(liststore)
            self.iconviews.append(iconview)

        self.bing = Bing()
        self.load()

    def load(self):
        if not self.bing.load():
            # alert here
            return

        self.current_group_index = 0
        self.load_current_group()

    def load_current_group(self):
        self.current_group = self.bing.get_category_data(self.bing.keys[self.current_group_index])
        self.current_group_count = 0

        for index, wallpaper in enumerate(self.current_group):
            cache = WallpaperCache(wallpaper, self._on_wallpaper_load, index)
            cache.lookup()

    def _on_wallpaper_load(self, wallpaper, path, index):
        cache = ThumbnailCache(wallpaper["id"], 220, 160, self._on_thumbnail_load, [index, wallpaper["query"]])
        cache.lookup()

    def _on_thumbnail_load(self, pixbuf, path, data):
        (index, label) = data

        self.liststores[self.current_group_index].insert(index, [pixbuf, label])

        self.current_group_count += 1
        if self.current_group_count == len(self.current_group):
            self._on_group_load()

    def _on_group_load(self):
        # show loaded group
        print("Group loaded: %d" % self.current_group_index)

        # remove loader and show group
        self.clear_all(self.pages[self.current_group_index])
        self.pages[self.current_group_index].add(self.iconviews[self.current_group_index])
        self.pages[self.current_group_index].show_all()

        # goto next group if needed
        self.current_group_index += 1
        if self.current_group_index < 4:
            self.load_current_group()

    @classmethod
    def _item_activated(self, iconview, path):
        liststore = iconview.get_model()
        print(liststore[path][1])

    @staticmethod
    def clear_all(container):
        for child in container.get_children():
            container.remove(child)


app = MainWindow()
Gtk.main()
