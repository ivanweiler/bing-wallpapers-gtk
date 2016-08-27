import os
import logging
from gi.repository import Gio, GLib, GdkPixbuf

logging.basicConfig()
logger = logging.getLogger(__name__)

CACHEPATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'cache')
# CACHEPATH = os.path.join(GLib.get_user_cache_dir(), 'bing-wallpapers', 'cache')
if not os.path.exists(CACHEPATH):
    Gio.file_new_for_path(CACHEPATH).make_directory(None)


# https://github.com/GNOME/gnome-music/blob/master/gnomemusic/albumartcache.py
class WallpaperCache:

    def __init__(self, item, callback, data=None):
        # GObject.GObject.__init__(self)
        try:
            self.item = item        # remove item, pass identifier
            self.callback = callback
            self.data = data

            self.local_path = os.path.join(CACHEPATH, str(item["id"]) + ".jpg")
            # print(self.local_path)

        except Exception as e:
            logger.warn("Error: %s", e)

        # self.default_icon = DefaultIcon()

    def lookup(self):

        try:
            if os.path.exists(self.local_path):
                self.finish(None, self.local_path)
                # print("exists")
            else:
                self.download_thumb()
        except Exception as e:
            logger.warn("Error: %s, %s", e.__class__, e)

    def finish(self, pixbuf, path):
        try:
            if self.data is None:
                GLib.idle_add(self.callback, self.item, self.local_path, priority=GLib.PRIORITY_HIGH_IDLE)
                # self.callback(self.local_path)
            else:
                GLib.idle_add(self.callback, self.item, self.local_path, self.data, priority=GLib.PRIORITY_HIGH_IDLE)
        except Exception as e:
            logger.warn("Error: %s", e)

    def download_thumb(self):

        try:
            src = Gio.File.new_for_uri(self.item["url"])
            src.read_async(GLib.PRIORITY_DEFAULT, None, self.open_remote_wallpaper, ["123"])

        except Exception as e:
            logger.warn("Error: %s", e)
            self.finish(None, None)

    def open_remote_wallpaper(self, src, result, arguments=None):
        dest = Gio.File.new_for_path(self.local_path)

        try:
            istream = src.read_finish(result)
            dest.replace_async(None, False, Gio.FileCreateFlags.REPLACE_DESTINATION,
                               GLib.PRIORITY_LOW, None, self.open_local_wallpaper, [istream])
        except Exception as e:
            logger.warn("Error: %s", e)
            self.finish(None, None)

    def open_local_wallpaper(self, dest, result, arguments=None):
        (istream,) = arguments

        try:
            ostream = dest.replace_finish(result)
            ostream.splice_async(istream,
                                 Gio.OutputStreamSpliceFlags.CLOSE_SOURCE | Gio.OutputStreamSpliceFlags.CLOSE_TARGET,
                                 GLib.PRIORITY_LOW, None, self.copy_finished)
        except Exception as e:
            logger.warn("Error: %s", e)
            self.finish(None, None)

    def copy_finished(self, ostream, result, arguments=None):

        try:
            ostream.splice_finish(result)
            # self.lookup(item, width, height, callback, itr, artist, album, False)
        except Exception as e:
            logger.warn("Error: %s", e)

        self.finish(None, None)


class ThumbnailCache:
    def __init__(self, identifier, width, height, callback, data=None):
        self.identifier = identifier
        self.dimensions = [width, height]
        self.callback = callback
        self.data = data

        self.src = os.path.join(CACHEPATH, str(identifier) + ".jpg")
        self.dest = os.path.join(CACHEPATH, str(identifier) + ".thumb.jpg")

    def lookup(self):
        try:
            exists = os.path.exists(self.dest)
            src = self.dest if exists else self.src

            stream = Gio.File.new_for_path(src)
            stream.read_async(GLib.PRIORITY_DEFAULT, None, self._on_stream_read, exists)

            # if os.path.exists(self.dest):
            #     pixbuf = GdkPixbuf.Pixbuf.new_from_file(self.dest)  # should be fast?
            #     self.finish(pixbuf, self.dest)
            # else:
            #     stream = Gio.File.new_for_path(self.src)    # slow, async?!
            #     GdkPixbuf.Pixbuf.new_from_stream_at_scale_async(
            #         stream.read(),
            #         self.dimensions[0],
            #         self.dimensions[1],
            #         False,
            #         None,
            #         self._on_pixbuf_loaded
            #     )

        except Exception as e:
            logger.warn("Error: %s, %s", e.__class__, e)
            self.finish(None, None)

    def _on_stream_read(self, src, result, exists):
        try:
            stream = src.read_finish(result)

            if exists:
                GdkPixbuf.Pixbuf.new_from_stream_async(stream, None, self._on_pixbuf_loaded, exists)
            else:
                GdkPixbuf.Pixbuf.new_from_stream_at_scale_async(
                        stream,
                        self.dimensions[0], self.dimensions[1],
                        False,
                        None,
                        self._on_pixbuf_loaded, exists)

        except Exception as e:
            logger.warn("Error: %s, %s", e.__class__, e)
            self.finish(None, None)

    def _on_pixbuf_loaded(self, stream, result, exists):
        try:
            pixbuf = GdkPixbuf.Pixbuf.new_from_stream_finish(result)
            if not exists:
                pixbuf.savev(self.dest, "jpeg", ["quality"], ["90"])

            self.finish(pixbuf, self.dest)

        except Exception as e:
            logger.warn("Error: %s, %s", e.__class__, e)
            self.finish(None, None)

    def finish(self, pixbuf, path):
        # returns pixbuf and path to callback
        try:
            if self.data is None:
                GLib.idle_add(self.callback, pixbuf, path, priority=GLib.PRIORITY_HIGH_IDLE)
            else:
                GLib.idle_add(self.callback, pixbuf, path, self.data, priority=GLib.PRIORITY_HIGH_IDLE)
        except Exception as e:
            logger.warn("Error: %s", e)


def cache_clean(leave):
    # list cache folder, delete all except passed ids
    import glob
    for path in glob.glob(os.path.join(CACHEPATH, "*.jpg")):
        basename = os.path.basename(path)
        if int(basename.split(".")[0]) in leave:
            continue
        # print path
        os.remove(path)
