from pathlib import Path
import toml
import json
from discord.ext import commands

class toml_struct:
    """ ## toml_struct
    ------
    a simple TOML structure parser that is able to access toml sections as dictionaries with attributes\n
    ```
    # example.py

    # --- toml file contents ---
    # [example_stuff]
    # foo = "bar"
    # --------------------------

    tomlfile = toml_struct("example.toml")

    # accessing toml:
    print(tomlfile.example_stuff["foo"]) # prints 'bar'
    ```"""
    def __init__(self, file_path:str) -> None:
        with open(file_path, 'r') as file:
            self.__tomlfile = toml.load(file)

    def __getattr__(self, name):
        if name in self.__tomlfile:
            return self.__tomlfile[name]
        raise AttributeError(f"{self.__class__.__name__} object has no atribute '{name}'")

    def __getitem__(self, key):
        return self.__tomlfile[key]

class masworld:
    """structure values and key info from the Masworld SMP server"""
    channels = toml_struct("./data/channels.toml")
    serverstuff = json.load(open("./data/datafile.json"))["server"]
    bot = None

    @classmethod
    def set_bot(cls, bot_instance:commands.AutoShardedBot):
        cls.bot = bot_instance

    def __getattr__(self, name):
        if name in self.channels:
            return self.tomlsection(self.channels[name])
        elif name in self.serverstuff:
            return self.serverstuff[name]
        raise AttributeError(f"{self.__class__.__name__} object has no attribute '{name}'")
    
    def __getitem__(self, key):
        if key in self.channels:
            return self.tomlsection(self.channels[key])
        elif key in self.serverstuff:
            return self.serverstuff[key]
        
    class tomlsection:
        def __init__(self, sectiondata):
            self.sectiondata = sectiondata
    
        def __getitem__(self, key):
            if key in self.sectiondata:
                channel_id = self.sectiondata[key]
                return masworld.bot.get_channel(int(channel_id))
            raise KeyError(f"'{key}' not found in section")

class emoji:
    """masworld emoji codes available for fomatting into messages!"""
    thunking = "<:thunking:1288468167974191155>"
    kindasus = "<:kindasus:1288468138987360319>"
    masworldlogo = "<:masworld_logo:1274052167426244648>"
