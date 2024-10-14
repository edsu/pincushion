import json
import logging
import re
from pathlib import Path

import jinja2
import requests
import tqdm
import yt_dlp

logger = logging.getLogger(__name__)

env = jinja2.Environment(
    loader=jinja2.PackageLoader("pincushion"), autoescape=jinja2.select_autoescape()
)


class Generator:
    # TODO: tags, places

    def __init__(self, archive_dir, overwrite=False):
        self.overwrite = overwrite
        self.archive_dir = Path(archive_dir)
        if not self.archive_dir.is_dir():
            raise Exception(f"No such archive directory: {archive_dir}")

        self.data = json.load((self.archive_dir / "data.json").open())

    def generate(self):
        self.download_media()
        self.write_index()
        self.write_collections()

    def write_index(self):
        tmpl = env.get_template("index.html")
        html = tmpl.render(user=self.data["user"], collections=self.collections())
        (self.archive_dir / "index.html").open("w").write(html)

    def write_collections(self):
        coll_tmpl = env.get_template("collection.html")
        pin_tmpl = env.get_template("pin.html")
        for coll in self.collections():
            pins = list(self.collection_pins(coll["slug"]))
            html = coll_tmpl.render(collection=coll, pins=pins)
            self.write(html, "collections", coll["slug"], "index.html")
            for pin in pins:
                html = pin_tmpl.render(pin=pin, collection=coll)
                self.write(html, f"pins/{pin['id']}/index.html")

    def download_media(self):
        self.fetch_file(self.data["user"]["image"], "user.jpg")
        collections = list(self.collections())
        for coll in tqdm.tqdm(collections, desc="{:20}".format("collection media")):
            if coll["image_url"]:
                self.fetch_file(
                    coll["image_url"], f"collections/{coll['slug']}/image.jpg"
                )
            # if the collection doesn't have an image use the first pin image
            elif image_url := self.get_first_image_url(coll['slug']):
                self.fetch_file(image_url, f"collections/{coll['slug']}/image.jpg")

        for pin in tqdm.tqdm(self.data["pins"], desc="{:20}".format("pin media")):
            url = pin['display']['content']
            media_type = self.get_media_type(pin)

            if media_type == "image":
                self.fetch_file(url, f"pins/{pin['id']}/image.jpg")
            else:
                self.fetch_media(url, media_type, f"pins/{pin['id']}/media.%(ext)s")

    def fetch_file(self, url_path, file_path):
        logger.info(f"downloading {url_path}")
        file_path = self.archive_dir / file_path
        file_path.parent.mkdir(exist_ok=True, parents=True)
        url = "https://historypin.org" + url_path

        if file_path.is_file() and not self.overwrite:
            logging.info(f"skipping download of {url} since it is already present")
            return

        logger.info(f"saving {url} to {file_path}")
        resp = requests.get(url)
        resp.raise_for_status()

        file_path.open("wb").write(resp.content)

    def fetch_media(self, url, media_type, file_path):
        logger.info(f"downloading media {url}")
        file_path = self.archive_dir / file_path

        if (file_path.with_suffix('.mp3').is_file() or file_path.with_suffix('.mp4').is_file()) and not self.overwrite:
            logging.info(f'skipping download of {url} since it is already present')
            return

        opts = {
            "noprogress": True,
            "quiet": True,
            "logger": logger,
            "format": "best/bestvideo+bestaudio",
            "audio_format": "mp3",
            "outtmpl": {"default": str(file_path)},
        }

        # convert to mp3 or mp4 if needed
        if media_type == 'video':
            opts["postprocessors"] = [
                {"key": "FFmpegVideoConvertor", "preferedformat": "mp4"}
            ]
        else:
            opts["postprocessors"] = [
                {"key": "FFmpegExtractAudio", "preferredcodec": "mp3"}
            ]

        with yt_dlp.YoutubeDL(params=opts) as ydl:
            try:
                meta = ydl.extract_info(url)
                return meta
            except Exception as e:
                logger.warn(f"Unable to download media {url}: {e}")

    def write(self, html, *path_parts):
        path = self.archive_dir.joinpath(*path_parts)
        path.parent.mkdir(exist_ok=True, parents=True)
        path.open("w").write(html)

    def collections(self):
        for coll in self.data["collections"]:
            if len(list(self.collection_pins(coll["slug"]))) > 0:
                yield coll

    def collection_pins(self, collection_slug):
        for pin in self.data["pins"]:
            if collection_slug in [p["slug"] for p in pin["repinned_projects"]]:
                yield pin

    def get_media_type(self, pin):
        # ideally we could just use pin['type'] but pins can sometimes have type=video but be from soundcloud, sigh
        url = pin["display"]["content"]
        media_type = pin['type']

        if media_type == 'photo':
            media_type = 'image'
        elif re.search('youtu.be|youtube|vimeo', url):
            media_type = 'video'
        elif re.search('soundcloud|audioboom', url):
            media_type = 'audio'

        return media_type

    def get_first_image_url(self, collection_slug):
        print(f"getting first image for {collection_slug}")
        for pin in self.collection_pins(collection_slug):
            if self.get_media_type(pin) == 'image':
                print(pin['display']['content'])
                return pin['display']['content']
        return None


