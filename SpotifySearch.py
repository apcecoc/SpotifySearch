from .. import loader, utils
from telethon.tl.types import Message, InputMediaUploadedDocument
from telethon.tl.types import DocumentAttributeAudio
import requests
from urllib.parse import quote
import io

__version__ = (1, 0, 2)
#       █████  ██████   ██████ ███████  ██████  ██████   ██████ 
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
    """Spotify Track Search and Download"""

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
        "download_error": "❌ Error downloading: {error}",
        "download_success": "✅ Track successfully downloaded!",
        "download_failed": "❌ Failed to download track",
        "downloading": "⏳ Downloading track..."
    }

    strings_ru = {
        "name": "SpotifySearch",
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
        "download_error": "❌ Ошибка при скачивании: {error}",
        "download_success": "✅ Трек успешно загружен!",
        "download_failed": "❌ Не удалось скачать трек",
        "downloading": "⏳ Загрузка трека..."
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            "SEARCH_LIMIT", 50, "Максимальное количество результатов поиска"
        )
        self.search_results = {}
        self.current_search = None

    def format_duration(self, seconds: int) -> str:
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        return f"{minutes}:{remaining_seconds:02d}"

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
        """<ссылка> Скачать трек Spotify по ссылке. Можно ответить на сообщение со ссылкой или указать ссылку напрямую."""
        url = utils.get_args_raw(message)

        if not url and message.is_reply:
            reply = await message.get_reply_message()
            url = reply.raw_text

        if not url:
            await utils.answer(message, "❌ Укажите ссылку на трек Spotify или ответьте на сообщение со ссылкой")
            return

        try:
            track_id = url.split("/")[-1].split("?")[0]
            response = requests.get(f"https://api.paxsenix.biz.id/spotify/track?id={track_id}")
            response.raise_for_status()
            track = response.json()

            duration_seconds = track['duration_ms'] // 1000
            artist_name = ', '.join(a['name'] for a in track['artists'])
            track_name = track['name']

            await utils.answer(message, self.strings["downloading"])

            servers = ["spotify", "spotify2", "spotify3", "yt", "yt2", "yt3", "deezer"]
            track_downloaded = False

            for server in servers:
                await utils.answer(message, f"⏳ Пытаюсь скачать трек с сервера {server}...")

                response = requests.get(f"https://api.paxsenix.biz.id/dl/spotify?url={quote(url)}&serv={server}")
                data = response.json()

                if data.get("ok"):
                    audio_response = requests.get(data["directUrl"])
                    audio_content = io.BytesIO(audio_response.content)

                    file_extension = "m4a" if server in ["spotify", "spotify2", "spotify3"] else "mp3"
                    audio_content.name = f"{artist_name} - {track_name}.{file_extension}"

                    attributes = [
                        DocumentAttributeAudio(
                            duration=duration_seconds,
                            title=track_name,
                            performer=artist_name,
                            waveform=None
                        )
                    ]

                    mime_type = 'audio/mp4' if server in ["spotify", "spotify2", "spotify3"] else 'audio/mp3'

                    await self._client.send_file(
                        message.chat_id,
                        audio_content,
                        attributes=attributes,
                        title=track_name,
                        performer=artist_name,
                        supports_streaming=True,
                        mime_type=mime_type,
                        caption=f"🎵 {artist_name} - {track_name}"
                    )

                    await utils.answer(message, self.strings["download_success"])
                    track_downloaded = True
                    break

            if not track_downloaded:
                await utils.answer(message, self.strings["download_failed"])

        except Exception as e:
            await utils.answer(message, self.strings["download_error"].format(error=str(e)))

    async def search_and_show_tracks(self, message: Message, query: str):
        try:
            response = requests.get(
                f"https://api.paxsenix.biz.id/spotify/search?q={quote(query)}",
                headers={"Accept": "application/json"}
            )
            response.raise_for_status()
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
            track = response.json()

            duration_seconds = track['duration_ms'] // 1000
            formatted_duration = self.format_duration(duration_seconds)
            
            artist_name = ', '.join(a['name'] for a in track['artists'])
            track_name = track['name']

            text = self.strings["track_info"].format(
                title=track_name,
                artist=artist_name,
                album=track['album']['name'],
                duration=formatted_duration,
                link=track['external_urls']['spotify']
            )

            markup = [
                [{"text": "⬇️ Скачать", "callback": self.download_track, "args": (
                    track['external_urls']['spotify'],
                    track_name,
                    artist_name,
                    duration_seconds
                )}]
            ]

            await call.edit(text=text, reply_markup=markup)
        except Exception as e:
            await call.edit(text=self.strings["search_error_generic"].format(error=str(e)))

    async def download_track(self, call, track_url: str, track_name: str, artist_name: str, duration: int):
        servers = ["spotify", "spotify2", "spotify3", "yt", "yt2", "yt3", "deezer"]
        track_downloaded = False

        try:
            for server in servers:
                await call.edit(text=f"⏳ Пытаюсь скачать трек с сервера {server}...")

                response = requests.get(f"https://api.paxsenix.biz.id/dl/spotify?url={quote(track_url)}&serv={server}")
                data = response.json()

                if data.get("ok"):
                    audio_response = requests.get(data["directUrl"])
                    audio_content = io.BytesIO(audio_response.content)

                    file_extension = "m4a" if server in ["spotify", "spotify2", "spotify3"] else "mp3"
                    audio_content.name = f"{artist_name} - {track_name}.{file_extension}"

                    attributes = [
                        DocumentAttributeAudio(
                            duration=duration,
                            title=track_name,
                            performer=artist_name,
                            waveform=None
                        )
                    ]

                    mime_type = 'audio/mp4' if server in ["spotify", "spotify2", "spotify3"] else 'audio/mp3'

                    await self._client.send_file(
                        call.form["chat"],
                        audio_content,
                        attributes=attributes,
                        title=track_name,
                        performer=artist_name,
                        supports_streaming=True,
                        mime_type=mime_type,
                        caption=f"🎵 {artist_name} - {track_name}"
                    )

                    await call.edit(text=self.strings["download_success"])
                    track_downloaded = True
                    break

            if not track_downloaded:
                await call.edit(text=self.strings["download_failed"])

        except Exception as e:
            await call.edit(text=self.strings["download_error"].format(error=str(e)))
