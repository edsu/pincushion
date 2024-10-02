import json
import logging
from pathlib import Path

import jinja2
import requests
import tqdm
import yt_dlp

logger = logging.getLogger(__name__)

env = jinja2.Environment(
    loader=jinja2.PackageLoader("pincushion"),
    autoescape=jinja2.select_autoescape()
)

class Generator:

    # TODO: video/audio, tags, places

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
        html = tmpl.render(user=self.data['user'], collections=self.collections())
        (self.archive_dir / "index.html").open("w").write(html)

    def write_collections(self):
        tmpl = env.get_template("collection.html")
        for coll in self.collections():
            pins = self.pins(coll['slug'])
            html = tmpl.render(collection=coll, pins=pins)
            self.write(html, "collections", coll['slug'], "index.html")

    def download_media(self):
        self.fetch_file(
            self.data['user']['image'],
            'images/user.jpg'
        )
        collections = list(self.collections())
        for coll in tqdm.tqdm(collections, desc="{:20}".format('collection media')):
            if coll['image_url']:
                self.fetch_file(
                    coll['image_url'], 
                    f"images/collections/{coll['slug']}.jpg"
                )
        for pin in tqdm.tqdm(self.data['pins'], desc="{:20}".format("pin media")):
            if pin['type'] == 'photo':
                self.fetch_file(
                    pin['display']['content'],
                    f"images/pins/{pin['id']}.jpg"
                )
            elif pin['type'] == 'audio':
                self.fetch_media(
                    pin['display']['content'],
                    f"audio/pins/{pin['id']}.mp3"
                )
            elif pin['type'] == 'video':
                self.fetch_media(
                    pin['display']['content'],
                    f"video/pins/{pin['id']}.mp4"
                )

    def fetch_file(self, url_path, file_path):
        logger.info(f"downloading {url_path}")
        file_path = self.archive_dir / file_path
        file_path.parent.mkdir(exist_ok=True, parents=True)
        if file_path.is_file() and not self.overwrite:
            return

        resp = requests.get("https://historypin.org" + url_path)
        resp.raise_for_status()

        file_path.open('wb').write(resp.content)

    def fetch_media(self, url, file_path):
        logger.info(f"downloading media {url}")
        file_path = self.archive_dir / file_path

        opts = {
            'noprogress': True,
            'quiet': True,
            'logger': logger,
            'format': 'best/bestvideo+bestaudio',
            'audio_format': 'mp3',
            'outtmpl': {
                'default': f'{file_path}'
            },
        }

        # convert to mp3 and mp4 depending on whether it is audio or video
        if file_path.suffix == '.mp4':
            opts['postprocessors'] = [{'key': 'FFmpegVideoConvertor', 'preferedformat' : 'mp4'}]
        else:
            opts['postprocessors'] = [{'key': 'FFmpegExtractAudio', 'preferredcodec' : 'mp3'}]
 
        with yt_dlp.YoutubeDL(params=opts) as ydl:
            try:
                meta = ydl.extract_info(url)
                return meta
            except Exception as e:
                logger.warn(f"Unable to download media {url}: {e}")

    def write(self, html, *path_parts):
        path = self.archive_dir.joinpath(*path_parts)
        path.parent.mkdir(exist_ok=True, parents=True)
        path.open('w').write(html)

    def collections(self):
        for coll in self.data['collections']:
            if len(list(self.pins(coll['slug']))) > 0:
                yield coll

    def pins(self, collection_slug):
        for pin in self.data['pins']:
            if collection_slug in [p['slug'] for p in pin['repinned_projects']]:
                yield pin

