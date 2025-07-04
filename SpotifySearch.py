from .. import loader, utils
from telethon.tl.types import Message, InputMediaUploadedDocument
from telethon.tl.types import DocumentAttributeAudio
import requests
from urllib.parse import quote
import io
import json
import time
import asyncio

__version__ = (1, 0, 9)

#        █████  ██████   ██████ ███████  ██████  ██████   ██████ 
#       ██   ██ ██   ██ ██      ██      ██      ██    ██ ██      
#       ███████ ██████  ██      █████   ██      ██    ██ ██      
#       ██   ██ ██      ██      ██      ██      ██    ██ ██      
#       ██   ██ ██       ██████ ███████  ██████  ██████   ██████
#
#              © Copyright 2025
#           https://t.me/apcecoc
#
# 🔒      Licensed under the GNU AGPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html

# meta developer: @apcecoc
# scope: hikka_only
# scope: hikka_min 1.2.10

@loader.tds
class SpotifySearchMod(loader.Module):
    """Spotify Track and Podcast Search and Download"""

    strings = {
        "name": "SpotifySearch",
        "enter_query": "🎵 Enter a query to search for Spotify tracks:",
        "search_error": "❌ Error in API response format",
        "not_found": "😕 Nothing found",
        "search_error_generic": "❌ Error during search: {error}",
        "found_tracks": "🎵 Found tracks: {count}\nSelect a track for more information:",
        "track_info": """
🎵 <b>Title:</b> {title}
👤 <b>Artist:</b> {artist}
💿 <b>Album:</b> {album}
⏱️ <b>Duration:</b> {duration}
🔗 <b>Link:</b> {link}
        """,
        "podcast_info": """
🎙️ <b>Podcast:</b> {title}
👤 <b>Creator:</b> {creator}
⏱️ <b>Duration:</b> {duration}
🔗 <b>Link:</b> {link}
        """,
        "download_error": "❌ Error downloading: {error}",
        "download_success": "✅ Track successfully downloaded!",
        "podcast_download_success": "✅ Podcast successfully downloaded!",
        "download_failed": "❌ Failed to download content",
        "downloading": "⏳ Downloading, please wait...",
        "api_response_error": "❌ API returned an invalid response (possibly HTML). Please try again later.",
        "rate_limit_error": "❌ Too many requests to the API. Please wait {seconds} seconds and try again.",
        "bot_not_responding": "❌ The download bot is not responding. Please try again later."
    }

    strings_ru = {
        "name": "SpotifySearch",
        "_cls_doc": "Скачивание треков и подкастов с Spotify",
        "enter_query": "🎵 Введите запрос для поиска треков Spotify:",
        "search_error": "❌ Ошибка в формате ответа API",
        "not_found": "😕 Ничего не найдено",
        "search_error_generic": "❌ Ошибка при поиске: {error}",
        "found_tracks": "🎵 Найдено треков: {count}\nВыберите трек для подробной информации:",
        "track_info": """
🎵 <b>Название:</b> {title}
👤 <b>Исполнитель:</b> {artist}
💿 <b>Альбом:</b> {album}
⏱️ <b>Длительность:</b> {duration}
🔗 <b>Ссылка:</b> {link}
        """,
        "podcast_info": """
🎙️ <b>Подкаст:</b> {title}
👤 <b>Автор:</b> {creator}
⏱️ <b>Длительность:</b> {duration}
🔗 <b>Ссылка:</b> {link}
        """,
        "download_error": "❌ Ошибка при скачивании: {error}",
        "download_success": "✅ Трек успешно загружен!",
        "podcast_download_success": "✅ Подкаст успешно загружен!",
        "download_failed": "❌ Не удалось скачать контент",
        "downloading": "⏳ Загрузка, пожалуйста, подождите...",
        "api_response_error": "❌ API вернул некорректный ответ (возможно, HTML). Попробуйте позже.",
        "rate_limit_error": "❌ Слишком много запросов к API. Пожалуйста, подождите {seconds} секунд и попробуйте снова.",
        "bot_not_responding": "❌ Бот для скачивания не отвечает. Пожалуйста, попробуйте снова позже."
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue("SEARCH_LIMIT", 50, "Максимальное количество результатов поиска"),
            loader.ConfigValue("RATE_LIMIT_DELAY", 10, "Задержка (в секундах) перед повторной попыткой после ошибки 429")
        )
        self.search_results = {}
        self.current_search = None
        self.download_bot = "@MusicsHuntersbot"

    async def client_ready(self, client, db):
        """Инициализация клиента"""
        self.client = client
        self.db = db
        if not hasattr(self, 'config'):
            self.config = loader.ModuleConfig(
                loader.ConfigValue("SEARCH_LIMIT", 50, "Максимальное количество результатов поиска"),
                loader.ConfigValue("RATE_LIMIT_DELAY", 10, "Задержка (в секундах) перед повторной попыткой после ошибки 429")
            )

    def format_duration(self, seconds: int) -> str:
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        return f"{minutes}:{remaining_seconds:02d}"

    def is_valid_json(self, data):
        """Проверяет, является ли строка валидным JSON"""
        try:
            json.loads(data)
            return True
        except json.JSONDecodeError:
            return False

    async def spotifycmd(self, message: Message):
        """<название трека> Поиск и скачивание треков Spotify."""
        query = utils.get_args_raw(message)
        if not query:
            await self.inline.form(
                message=message,
                text=self.strings["enter_query"],
                reply_markup=[
                    [{"text": "🔍 Поиск", "input": "Введите название трека:"}]
                ],
                silent=True,
                ttl=60
            )
        else:
            await self.search_and_show_tracks(message, query)

    async def spotifydlcmd(self, message: Message):
        """<ссылка> Скачать трек или подкаст Spotify по ссылке. Можно ответить на сообщение со ссылкой или указать ссылку напрямую."""
        url = utils.get_args_raw(message)

        if not url and message.is_reply:
            reply = await message.get_reply_message()
            url = reply.raw_text

        if not url or ("open.spotify.com" not in url):
            await utils.answer(message, "❌ Укажите ссылку на трек или подкаст Spotify или ответьте на сообщение со ссылкой")
            return

        try:
            content_id = url.split("/")[-1].split("?")[0]
            is_podcast = "/episode/" in url
            api_endpoint = "episode" if is_podcast else "track"
            response = requests.get(f"https://api.paxsenix.biz.id/spotify/{api_endpoint}?id={content_id}")
            response.raise_for_status()
            content = response.text

            if not self.is_valid_json(content):
                await utils.answer(message, self.strings["api_response_error"])
                return

            content = response.json()

            duration_seconds = content['duration_ms'] // 1000
            if is_podcast:
                creator_name = content.get('name', 'Unknown')
            else:
                creator_name = ', '.join(a['name'] for a in content['artists']) if 'artists' in content else 'Unknown'
            content_name = content['name']
            cover_url = (content['album']['images'][0]['url'] if not is_podcast and 'album' in content 
                        else content['images'][0]['url'] if 'images' in content 
                        else None)

            await utils.answer(message, self.strings["downloading"])
            track_message = await self.download_via_bot(message.chat_id, url, content_name, creator_name, duration_seconds, is_podcast)

            if track_message:
                thumb = None
                if cover_url:
                    cover_response = requests.get(cover_url)
                    thumb = io.BytesIO(cover_response.content)
                    thumb.name = "cover.jpg"

                await self._client.send_file(
                    message.chat_id,
                    track_message.media,
                    attributes=track_message.media.document.attributes,
                    title=content_name,
                    performer=creator_name,
                    supports_streaming=True,
                    thumb=thumb,
                    caption=f"{'🎙️' if is_podcast else '🎵'} {creator_name} - {content_name}"
                )

                await utils.answer(message, self.strings["podcast_download_success"] if is_podcast else self.strings["download_success"])
            else:
                await utils.answer(message, self.strings["download_failed"])

        except requests.RequestException as e:
            await utils.answer(message, self.strings["download_error"].format(error=str(e)))
        except Exception as e:
            await utils.answer(message, self.strings["download_error"].format(error=str(e)))

    async def search_and_show_tracks(self, message: Message, query: str):
        try:
            response = requests.get(
                f"https://api.paxsenix.biz.id/spotify/search?q={quote(query)}",
                headers={"Accept": "application/json"}
            )
            response.raise_for_status()
            content = response.text

            if not self.is_valid_json(content):
                await utils.answer(message, self.strings["api_response_error"])
                return

            data = response.json()

            if "tracks" not in data or "items" not in data["tracks"]:
                await utils.answer(message, self.strings["search_error"])
                return

            tracks = data["tracks"]["items"]
            self.search_results[message.chat_id] = tracks
            self.current_search = query

            if not tracks:
                await utils.answer(message, self.strings["not_found"])
                return

            await self.show_search_results(message, tracks)

        except requests.RequestException as e:
            await utils.answer(message, self.strings["search_error_generic"].format(error=str(e)))
        except Exception as e:
            await utils.answer(message, self.strings["search_error_generic"].format(error=str(e)))

    async def show_search_results(self, message, tracks):
        markup = []
        for track in tracks[:self.config["SEARCH_LIMIT"]]:
            artist_name = track["artists"][0]["name"] if track["artists"] else "Unknown Artist"
            track_name = track["name"] if track["name"] else "Unknown Track"
            
            markup.append([{
                "text": f"🎵 {track_name} - {artist_name}",
                "callback": self.show_track_details,
                "args": (track["id"],)
            }])

        await self.inline.form(
            message=message,
            text=self.strings["found_tracks"].format(count=len(tracks)),
            reply_markup=markup
        )

    async def show_track_details(self, call, track_id: str):
        try:
            response = requests.get(f"https://api.paxsenix.biz.id/spotify/track?id={track_id}")
            response.raise_for_status()
            content = response.text

            if not self.is_valid_json(content):
                await call.edit(self.strings["api_response_error"])
                return

            track = response.json()

            duration_seconds = track['duration_ms'] // 1000
            formatted_duration = self.format_duration(duration_seconds)
            
            artist_name = ', '.join(a['name'] for a in track['artists']) if 'artists' in track else 'Unknown'
            track_name = track['name']
            track_url = track['external_urls']['spotify']
            is_podcast = "/episode/" in track_url

            if is_podcast:
                response = requests.get(f"https://api.paxsenix.biz.id/spotify/episode?id={track_id}")
                response.raise_for_status()
                content = response.text

                if not self.is_valid_json(content):
                    await call.edit(self.strings["api_response_error"])
                    return

                track = response.json()
                artist_name = track.get('name', 'Unknown')

            text = self.strings["podcast_info" if is_podcast else "track_info"].format(
                title=track_name,
                artist=artist_name,
                creator=artist_name,
                album=track['album']['name'] if not is_podcast else "N/A",
                duration=formatted_duration,
                link=track_url
            )

            markup = [
                [{"text": "⬇️ Скачать", "callback": self.download_track, "args": (
                    track_url,
                    track_name,
                    artist_name,
                    duration_seconds
                )}]
            ]

            await call.edit(text=text, reply_markup=markup)
        except requests.RequestException as e:
            await call.edit(self.strings["search_error_generic"].format(error=str(e)))
        except Exception as e:
            await call.edit(self.strings["search_error_generic"].format(error=str(e)))

    async def download_track(self, call, track_url: str, track_name: str, artist_name: str, duration: int):
        is_podcast = "/episode/" in track_url

        try:
            api_endpoint = "episode" if is_podcast else "track"
            content_id = track_url.split("/")[-1].split("?")[0]
            response = requests.get(f"https://api.paxsenix.biz.id/spotify/{api_endpoint}?id={content_id}")
            response.raise_for_status()
            content = response.text

            if not self.is_valid_json(content):
                await call.edit(self.strings["api_response_error"])
                return

            content = response.json()
            cover_url = (content['album']['images'][0]['url'] if not is_podcast and 'album' in content 
                        else content['images'][0]['url'] if 'images' in content 
                        else None)
            if is_podcast:
                artist_name = content.get('name', 'Unknown')

            await call.edit(text=self.strings["downloading"])
            track_message = await self.download_via_bot(call.form["chat"], track_url, track_name, artist_name, duration, is_podcast)

            if track_message:
                thumb = None
                if cover_url:
                    cover_response = requests.get(cover_url)
                    thumb = io.BytesIO(cover_response.content)
                    thumb.name = "cover.jpg"

                await self._client.send_file(
                    call.form["chat"],
                    track_message.media,
                    attributes=track_message.media.document.attributes,
                    title=track_name,
                    performer=artist_name,
                    supports_streaming=True,
                    thumb=thumb,
                    caption=f"{'🎙️' if is_podcast else '🎵'} {artist_name} - {track_name}"
                )

                await call.edit(text=self.strings["podcast_download_success"] if is_podcast else self.strings["download_success"])
            else:
                await call.edit(text=self.strings["download_failed"])

        except requests.RequestException as e:
            await call.edit(self.strings["download_error"].format(error=str(e)))
        except Exception as e:
            await call.edit(self.strings["download_error"].format(error=str(e)))

    async def download_via_bot(self, original_chat_id: int, track_url: str, track_name: str, artist_name: str, duration: int, is_podcast: bool):
        """Скачивание трека через бота @MusicsHuntersbot"""
        try:
            bot_chat = await self.client.get_entity(self.download_bot)
            bot_chat_id = bot_chat.id

            start_message = await self.client.send_message(bot_chat_id, "/start")
            await asyncio.sleep(1)
            start_response = await self.client.get_messages(bot_chat_id, limit=1)

            sent_message = await self.client.send_message(bot_chat_id, track_url)

            track_message = None
            for _ in range(60):
                messages = await self.client.get_messages(bot_chat_id, limit=1)
                if messages and messages[0].id != sent_message.id and messages[0].media:
                    track_message = messages[0]
                    break
                await asyncio.sleep(1)

            if not track_message:
                await self.client.delete_messages(bot_chat_id, [start_message.id, sent_message.id])
                if start_response:
                    await self.client.delete_messages(bot_chat_id, [start_response[0].id])
                return None

            messages_to_delete = [start_message.id, sent_message.id, track_message.id]
            if start_response:
                messages_to_delete.append(start_response[0].id)
            await self.client.delete_messages(bot_chat_id, messages_to_delete)

            return track_message

        except Exception as e:
            try:
                messages_to_delete = [start_message.id, sent_message.id]
                if start_response:
                    messages_to_delete.append(start_response[0].id)
                await self.client.delete_messages(bot_chat_id, messages_to_delete)
            except:
                pass
            return None