#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
public-image-collector
Scraper simple y responsable para recopilar imágenes públicas.
"""

import hashlib
import mimetypes
import os
import re
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO


DEFAULT_USER_AGENT = "PublicImageCollector/0.1 (+https://github.com/Caarrasco22/public-image-collector)"
DEFAULT_DELAY = 0.5
DEFAULT_MAX_IMAGES = 50


class ImageInfo:
    def __init__(self, url, source_page, width=None, height=None, size_approx=None, fmt=None):
        self.url = url
        self.source_page = source_page
        self.width = width
        self.height = height
        self.size_approx = size_approx
        self.format = fmt
        self.selected = True
        self._thumb = None

    @property
    def filename(self):
        parsed = urlparse(self.url)
        base = os.path.basename(parsed.path) or "image"
        base = re.sub(r"[^\w\-.]", "_", base)
        if not base.lower().endswith((".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".svg")):
            ext = self.format.lower() if self.format else "jpg"
            base = f"{base}.{ext}"
        return base


class Scraper:
    def __init__(self, user_agent=DEFAULT_USER_AGENT, delay=DEFAULT_DELAY, max_images=DEFAULT_MAX_IMAGES):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": user_agent})
        self.delay = delay
        self.max_images = max_images
        self.cancelled = False

    def check_robots_txt(self, url):
        parsed = urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        try:
            resp = self.session.get(robots_url, timeout=10)
            if resp.status_code != 200:
                return True
            rp = RobotFileParser()
            rp.parse(resp.text.splitlines())
            return rp.can_fetch(self.session.headers.get("User-Agent", "*"), url)
        except Exception:
            return True

    def analyze(self, url):
        self.cancelled = False
        results = []

        if not self.check_robots_txt(url):
            raise PermissionError("robots.txt bloquea el acceso a esta URL.")

        resp = self.session.get(url, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        seen = set()
        sources = []

        # <img src> and srcset
        for tag in soup.find_all("img"):
            if self.cancelled:
                break
            src = tag.get("src") or tag.get("data-src")
            if src:
                sources.append(("img", src))
            srcset = tag.get("srcset")
            if srcset:
                for part in srcset.split(","):
                    url_part = part.strip().split(" ")[0]
                    if url_part:
                        sources.append(("srcset", url_part))

        # OpenGraph
        og = soup.find("meta", property="og:image")
        if og and og.get("content"):
            sources.append(("og:image", og["content"]))

        # Limit
        sources = sources[: self.max_images]

        for kind, raw in sources:
            if self.cancelled:
                break
            resolved = urljoin(url, raw.strip())
            if resolved in seen:
                continue
            seen.add(resolved)

            info = self._probe_image(resolved)
            if info:
                results.append(info)

        return results

    def _probe_image(self, url):
        try:
            head = self.session.head(url, timeout=10, allow_redirects=True)
            if head.status_code != 200:
                return None
            ct = head.headers.get("Content-Type", "")
            if not ct.startswith("image/"):
                return None
            size = head.headers.get("Content-Length")
            size_approx = int(size) if size else None

            # fetch a few bytes to detect format/size
            r = self.session.get(url, timeout=10, stream=True)
            r.raise_for_status()
            data = b""
            for chunk in r.iter_content(chunk_size=8192):
                data += chunk
                if len(data) >= 32768:
                    break
            r.close()

            fmt = None
            w = h = None
            try:
                img = Image.open(BytesIO(data))
                fmt = img.format
                w, h = img.size
            except Exception:
                pass

            return ImageInfo(
                url=url,
                source_page=url,
                width=w,
                height=h,
                size_approx=size_approx,
                fmt=fmt,
            )
        except Exception:
            return None

    def download(self, images, dest_folder, on_progress=None, on_log=None):
        self.cancelled = False
        dest = Path(dest_folder)
        dest.mkdir(parents=True, exist_ok=True)

        downloaded_hashes = {}
        results = []

        total = len(images)
        for idx, info in enumerate(images):
            if self.cancelled:
                if on_log:
                    on_log("Descarga cancelada por el usuario.")
                break

            if not info.selected:
                continue

            try:
                time.sleep(self.delay)
                resp = self.session.get(info.url, timeout=20, stream=True)
                resp.raise_for_status()

                content = b""
                for chunk in resp.iter_content(chunk_size=8192):
                    if self.cancelled:
                        break
                    content += chunk

                if self.cancelled:
                    break

                h = hashlib.sha1(content).hexdigest()
                if h in downloaded_hashes:
                    if on_log:
                        on_log(f"Duplicado omitido: {info.filename}")
                    continue
                downloaded_hashes[h] = True

                ext = Path(info.filename).suffix.lower()
                if not ext:
                    ext = mimetypes.guess_extension(resp.headers.get("Content-Type", "")) or ".jpg"
                base = Path(info.filename).stem
                out_name = f"{base}{ext}"
                out_path = dest / out_name

                counter = 1
                while out_path.exists():
                    out_name = f"{base}_{counter}{ext}"
                    out_path = dest / out_name
                    counter += 1

                out_path.write_bytes(content)
                results.append(str(out_path))

                if on_log:
                    on_log(f"Descargado: {out_name}")
                if on_progress:
                    on_progress(idx + 1, total)
            except Exception as e:
                if on_log:
                    on_log(f"Error descargando {info.url}: {e}")
                if on_progress:
                    on_progress(idx + 1, total)

        return results

    def generate_thumb(self, info, size=(64, 64)):
        try:
            r = self.session.get(info.url, timeout=10, stream=True)
            r.raise_for_status()
            data = b""
            for chunk in r.iter_content(chunk_size=8192):
                data += chunk
                if len(data) >= 65536:
                    break
            r.close()
            img = Image.open(BytesIO(data))
            img.thumbnail(size, Image.LANCZOS)
            return img
        except Exception:
            return None
