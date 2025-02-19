import time
import requests as req
import os
import random
from Plugins.logger import Logger
from colorama import Fore
from pystyle import Col
from typing import Optional, Dict, List


class Tools:
    @staticmethod
    def check_token(token: str) -> bool:
        """Validate Discord bot token"""
        try:
            response = req.get(
                "https://discord.com/api/v10/users/@me",
                headers={"Authorization": f"Bot {token}"}
            )
            return response.status_code == 200
        except Exception as e:
            Logger.Error.error(f"Token validation error: {str(e)}")
            return False

    @staticmethod
    def get_guilds(token: str) -> List[List[str]]:
        """Get list of guilds the bot is in"""
        headers = {
            "Authorization": f"Bot {token}",
            "Content-Type": 'application/json'
        }
        url = Tools.api("users/@me/guilds")

        try:
            response = req.get(url, headers=headers)

            if response.status_code == 200:
                guilds = response.json()

                if guilds:
                    return [[guild["id"], guild["name"]] for guild in guilds]

                print(
                    f"\n{Col.red}[-]{Fore.RED + Fore.YELLOW} The bot is not in any server! Please invite it to a server first.")
                print(f"{Col.light_blue}Follow these steps:")
                print(f"{Col.purple}1. Go to {Col.blue}https://discord.com/developers/applications")
                print(f"{Col.purple}2. Select your application")
                print(f"{Col.purple}3. Go to OAuth2 -> URL Generator")
                print(f"{Col.purple}4. Select 'bot' and 'applications.commands' in Scopes")
                print(f"{Col.purple}5. Select 'Administrator' in Bot Permissions")
                print(f"{Col.purple}6. Copy and open the generated URL to invite the bot")
                print(f"{Col.light_blue}7. Select a server and authorize the bot{Col.white}")

                input(f"\n{Col.green}Press Enter to retry...{Col.white}")
                return Tools.get_guilds(token)  # Retry

            Logger.Error.error(f"Failed to fetch guilds (Status: {response.status_code})")
            input(f"\n{Col.green}Press Enter to retry...{Col.white}")
            return Tools.get_guilds(token)  # Retry

        except Exception as e:
            Logger.Error.error(f"Error fetching guilds: {str(e)}")
            input(f"\n{Col.green}Press Enter to retry...{Col.white}")
            return Tools.get_guilds(token)  # Retry

    @staticmethod
    def proxy() -> Optional[Dict[str, str]]:
        """Get random proxy from proxies.txt if exists"""
        if not os.path.exists("./proxies.txt"):
            return None

        try:
            with open("./proxies.txt", "r") as file:
                lines = [line.strip() for line in file if line.strip()]
                if lines:
                    proxy = random.choice(lines)
                    return {"http": proxy, "https": proxy}
        except Exception as e:
            Logger.Error.error(f"Error reading proxies: {str(e)}")
        return None

    @staticmethod
    def api(endpoint: str) -> str:
        """Create Discord API URL"""
        base_api = "https://discord.com/api/v10/"
        return base_api + endpoint.lstrip('/')

    @staticmethod
    async def break_limit(base_api: str, token: str) -> List[str]:
        """Handle paginated requests"""
        chunk_size = 1000
        users = []
        headers = {"Authorization": f"Bot {token}"}

        try:
            while True:
                params = {"limit": chunk_size}
                if users:
                    params["after"] = users[-1]

                response = req.get(base_api, headers=headers, params=params)

                if response.status_code != 200:
                    Logger.Error.error(f"API request failed (Status: {response.status_code})")
                    break

                data = response.json()
                if not data:
                    break

                try:
                    ids = [item["user"]["id"] for item in data]
                except KeyError:
                    ids = [item["id"] for item in data]

                users.extend(ids)

                if len(ids) < chunk_size:
                    break

                time.sleep(0.5)  # Rate limit prevention

        except Exception as e:
            Logger.Error.error(f"Error in pagination: {str(e)}")

        return users

    @staticmethod
    def chunker(text: list, chunk_size: int) -> List[list]:
        """Split text into chunks of specified size"""
        return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]

    @staticmethod
    def information(guild_id: str, token: str) -> Dict[str, Dict[str, str]]:
        """Get information about guild and bot user"""
        headers = {"Authorization": f"Bot {token}"}
        default_response = {
            "user": {"username": "Unknown"},
            "guild": {"name": "Unknown"}
        }

        try:
            user_url = Tools.api("users/@me")
            user_response = req.get(user_url, headers=headers)

            guild_url = Tools.api(f"guilds/{guild_id}")
            guild_response = req.get(guild_url, headers=headers)

            if user_response.status_code != 200 or guild_response.status_code != 200:
                Logger.Error.error("Failed to fetch information")
                return default_response

            return {
                "user": user_response.json(),
                "guild": guild_response.json()
            }

        except Exception as e:
            Logger.Error.error(f"Error fetching information: {str(e)}")
            return default_response