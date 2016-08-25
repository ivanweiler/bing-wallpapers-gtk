# import urllib2
import json
from gi.repository import Gio, GLib


class Bing():

    keys = ["bing", "animal", "nature", "hot"]
    labels = ["Bing", "Animal", "Scenery", "Other"]
    url_pattern = "http://az542455.vo.msecnd.net/%s/en-us"

    data = {}

    def load(self, callback):
        self.callback = callback

        for category in self.keys:
            url = self.url_pattern % category

            # response = urllib2.urlopen(url)     # make async?
            # data = json.load(response)
            # self.data[category] = data

            src = Gio.File.new_for_uri(url)
            src.load_contents_async(None, self._on_feed_read, category)

        # print("Bing data loaded")
        # return True

    def _on_feed_read(self, src, result, category):
        data = src.load_contents_finish(result)[1]
        # print(data)
        self.data[category] = json.loads(data)

        if len(self.data) == 4:
            print("Bing data loaded")
            self.callback()

    def get_data(self):
        return self.data

    def get_category_data(self, category):
        return self.data[category]

    def get_label(self, category):
        return self.labels[self.keys.index(category)]

    def get_ids(self):
        ids = []
        for category, wallpapers in self.data.items():
            for wallpaper in wallpapers:
                ids.append(wallpaper["id"])
        return ids

    def get_thumbnail(self, item):
        if item["thumbnail"]:
            return item["thumbnail"]
        else:
            return item["url"]