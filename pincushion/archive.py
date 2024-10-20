import json
import logging
import re
from collections import defaultdict
from pathlib import Path
from shutil import copytree, rmtree
from typing import Generator, Optional, List

import jinja2
import requests
import tqdm
import yt_dlp

logger = logging.getLogger(__name__)

env = jinja2.Environment(
    loader=jinja2.PackageLoader("pincushion"), autoescape=jinja2.select_autoescape()
)


class ArchiveGenerator:
    # TODO: tags, places, comments

    def __init__(self, archive_dir: Path, overwrite: bool = False):
        self.overwrite = overwrite
        self.archive_dir = archive_dir
        if not self.archive_dir.is_dir():
            raise Exception(f"No such archive directory: {archive_dir}")

        self.data = json.load((self.archive_dir / "data.json").open())

    def generate(self) -> None:
        self.download_media()
        self.write_index()
        self.write_collections()
        self.write_tags()
        self.write_map()

    def write_index(self) -> None:
        tmpl = env.get_template("index.html")
        html = tmpl.render(user=self.data["user"], collections=self.collections())
        (self.archive_dir / "index.html").open("w").write(html)

    def write_collections(self) -> None:
        coll_tmpl = env.get_template("collection.html")
        pin_tmpl = env.get_template("pin.html")
        for coll in self.collections():
            pins = list(self.collection_pins(coll["slug"]))
            html = coll_tmpl.render(collection=coll, pins=pins)
            self.write(html, "collections", coll["slug"], "index.html")
            for pin in pins:
                html = pin_tmpl.render(pin=pin, collection=coll, user=self.data["user"])
                self.write(html, f"pins/{pin['id']}/index.html")

    def write_tags(self) -> None:
        tag_index = defaultdict(list)
        for pin in self.data['pins']:
            for tag in pin['tags']:
                text = tag['text']
                tag_index[text].append(pin)

        tags_tmpl = env.get_template("tags.html")
        html = tags_tmpl.render(
            tags=sorted(tag_index.keys()),
            tag_index=tag_index
        )
        self.write(html, "tags", "index.html")

        tag_tmpl = env.get_template("tag.html")
        for tag, pins in tag_index.items():
            html = tag_tmpl.render(tag=tag, pins=pins)
            self.write(html, "tags", f"{tag}.html")

    def write_map(self) -> None:
        geojson = {
            "type": "FeatureCollection",
            "features": []
        }

        for pin in self.data['pins']:
            if pin['location']['lat']:
                geojson["features"].append({
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [
                            pin['location']['lng'],
                            pin['location']['lat']
                        ]
                    },
                    "properties": {
                        "name": pin["caption"],
                        "popupContent": pin["description"],
                        "id": pin["id"]
                    }
                })

        self.write(json.dumps(geojson, indent=2), "map", "pins.geojson")

        tmpl = env.get_template("map.html")
        html = tmpl.render(user=self.data['user'], geojson=json.dumps(geojson, indent=2))
        self.write(html, "map", "index.html")

        leaflet = Path(__file__).parent / "templates" / "leaflet"
        leaflet_dir = self.archive_dir / "map" / "leaflet"
        if leaflet_dir.is_dir():
            rmtree(leaflet_dir)
        copytree(leaflet, leaflet_dir)

    def download_media(self) -> None:
        self.fetch_file(self.data["user"]["image"], "user.jpg")
        collections = list(self.collections())
        for coll in tqdm.tqdm(collections, desc="{:20}".format("collection media")):
            if coll["image_url"]:
                self.fetch_file(
                    coll["image_url"], f"collections/{coll['slug']}/image.jpg"
                )
            # if the collection doesn't have an image use the first pin image
            elif image_url := self.get_first_image_url(coll["slug"]):
                self.fetch_file(image_url, f"collections/{coll['slug']}/image.jpg")

        for pin in tqdm.tqdm(self.data["pins"], desc="{:20}".format("pin media")):
            url = pin["display"]["content"]
            media_type = self.get_media_type(pin)

            if media_type == "image":
                self.fetch_file(url, f"pins/{pin['id']}/image.jpg")
            else:
                self.fetch_media(url, media_type, f"pins/{pin['id']}/media.%(ext)s")

    def fetch_file(self, url_path: str, file_path: str) -> None:
        logger.info(f"downloading {url_path}")
        path = self.archive_dir / file_path
        path.parent.mkdir(exist_ok=True, parents=True)
        url = "https://historypin.org" + url_path

        if path.is_file() and not self.overwrite:
            logger.info(f"skipping download of {url} since it is already present")
            return

        logger.info(f"saving {url} to {path}")
        resp = requests.get(url)
        if resp.status_code == 200:
            path.open("wb").write(resp.content)
        else:
            logger.error(f"received {resp.status_code} when fetching {url}")

    def fetch_media(self, url: str, media_type: str, file_path: str) -> None:
        logger.info(f"downloading media {url}")
        path = self.archive_dir / file_path

        if (
            path.with_suffix(".mp3").is_file() or path.with_suffix(".mp4").is_file()
        ) and not self.overwrite:
            logger.info(f"skipping download of {url} since it is already present")
            return

        opts = {
            "noprogress": True,
            "quiet": True,
            "logger": logger,
            "format": "best/bestvideo+bestaudio",
            "audio_format": "mp3",
            "outtmpl": {"default": str(path)},
        }

        # convert to mp3 or mp4 if needed
        if media_type == "video":
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

    def write(self, html: str, *path_parts: str) -> None:
        path = self.archive_dir.joinpath(*path_parts)
        path.parent.mkdir(exist_ok=True, parents=True)
        path.open("w").write(html)

    def collections(self) -> Generator[dict, None, None]:
        for coll in self.data["collections"]:
            if len(list(self.collection_pins(coll["slug"]))) > 0:
                yield coll

    def collection_pins(self, collection_slug: str) -> Generator[dict, None, None]:
        for pin in self.data["pins"]:
            if collection_slug in [p["slug"] for p in pin["repinned_projects"]]:
                yield pin

    def get_media_type(self, pin: dict) -> str:
        # ideally we could just use pin['type'] but pins can sometimes have type=video but be from soundcloud, sigh
        url = pin["display"]["content"]
        media_type = pin["type"]

        if media_type == "photo":
            media_type = "image"
        elif re.search("youtu.be|youtube|vimeo", url):
            media_type = "video"
        elif re.search("soundcloud|audioboom", url):
            media_type = "audio"

        return media_type

    def get_first_image_url(self, collection_slug: str) -> Optional[str]:
        for pin in self.collection_pins(collection_slug):
            if self.get_media_type(pin) == "image":
                return pin["display"]["content"]
        return None
