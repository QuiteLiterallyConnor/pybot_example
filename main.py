import os
import sys
import discord
import json
from discord.ext import commands
from dotenv import load_dotenv
from datetime import datetime, timedelta

class XPBot(commands.Cog):

    BASE_XP_PER_MESSAGE = 50

    def __init__(self, bot):
        self.bot = bot
        self.xp_data = {}
        self.last_message_time = {}
        try:
            with open("xp.json", "r") as file:
                self.xp_data = json.load(file)
        except FileNotFoundError:
            pass

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Logged in as {self.bot.user.name}")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        user_id = str(message.author.id)
        current_time = datetime.now()

        await self.bot.process_commands(message)

        if user_id not in self.last_message_time:
            self.last_message_time[user_id] = current_time

        time_diff = (current_time - self.last_message_time[user_id]).total_seconds()

        if time_diff >= 60:
            if user_id not in self.xp_data:
                self.xp_data[user_id] = 0

            level, _ = self.calculate_level_and_xp(user_id)
            if level < len(level_xp_requirements):
                self.xp_data[user_id] += self.BASE_XP_PER_MESSAGE
                self.last_message_time[user_id] = current_time
                self.save_xp_data()

                new_level, _ = self.calculate_level_and_xp(user_id)
                if new_level > level:
                    await self.notify_level_up(message.author, new_level)

    @commands.command()
    async def level(self, ctx, user: discord.User = None):
        user = user or ctx.author
        user_id = str(user.id)

        if user_id in self.xp_data:
            current_xp = self.xp_data[user_id]
            level, _ = self.calculate_level_and_xp(user_id)

            if level < len(level_xp_requirements):
                xp_needed_for_next_level = level_xp_requirements[level]
                response = f"{user.name} is level {level}, and needs {xp_needed_for_next_level - current_xp} more XP to reach the next level."
                await ctx.send(response)
            else:
                await ctx.send(f"{user.name} is at the maximum level!")
        else:
            await ctx.send("User not found or has no XP.")

    @commands.command()
    async def leaderboard(self, ctx):
        sorted_xp = sorted(self.xp_data.items(), key=lambda x: x[1], reverse=True)
        leaderboard_text = "Leaderboard:\n"
        for index, (user_id, xp) in enumerate(sorted_xp[:10], start=1):
            user = self.bot.get_user(int(user_id))
            if user:
                leaderboard_text += f"{index}. {user.name}: {xp} XP\n"
            else:
                leaderboard_text += f"{index}. Unknown User: {xp} XP (User not found)\n"
        await ctx.send(leaderboard_text)

    @commands.command()
    async def hello(self, ctx):
        await ctx.send("Hello, world!")

    @commands.command()
    async def ping(self, ctx):
        await ctx.send("Pong!")

    def save_xp_data(self):
        with open("xp.json", "w") as file:
            json.dump(self.xp_data, file)

    def calculate_level_and_xp(self, user_id):
        if user_id in self.xp_data:
            total_xp = self.xp_data[user_id]

            level = 0
            xp_remaining = total_xp
            while level < len(level_xp_requirements) and xp_remaining >= level_xp_requirements[level]:
                xp_remaining -= level_xp_requirements[level]
                level += 1

            return level, xp_remaining
        return 0, 0

    async def notify_level_up(self, user, new_level):
        await user.send(f"Congratulations! You've reached level {new_level}.")


if __name__ == "__main__":
    load_dotenv()
    TOKEN = os.getenv('DISCORD_TOKEN')

    if TOKEN is None:
        print("Error: Discord bot token not found. Set DISCORD_TOKEN in the .env file")
        sys.exit(1)

    intents = discord.Intents.default()
    intents.messages = True
    intents.message_content = True

    bot = commands.Bot(command_prefix="$", intents=intents)

    bot.add_cog(XPBot(bot))

    bot.run(TOKEN)
