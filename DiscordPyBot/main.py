import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os   

load_dotenv()
token = os.getenv('DISCORD_TOKEN') # --> DON'T PUT YOUR DISCORD TOKEN HERE, PUT IN THE .ENV FILE

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w') # Create a log file to storage all that is happening in the bot "mind" IDK how to explain it properly, mode W is to overwrite the file everytime that the bot runs
intents = discord.Intents.default() # Intents is like the permissions that the bot receives
intents.message_content = True # All the message related things
intents.members = True # Detects new members, work with roles, the members related things

bot = commands.Bot(command_prefix='+', intents=intents) # If you want to change the prefix you only need to change the '+' for the one that you want. Ex.: '!'

# Variables
roles_configurados = []
cargo_por_emoji = {}

# I will be explaining the lines in portuguese now, but maybe in the future I explain it in english
@bot.command() # Esse @bot.command serve para configurar um comando propriamente dito
@commands.has_permissions(administrator=True) # Só permite o uso desse comando se for um administrador
async def defcargos(ctx): # Define o comando +defcargos, o parâmetro dele é CTX que é o contexto da mensagem
    global cargo_por_emoji # Chama a variável global cargo_por_emoji
    cargo_por_emoji.clear() # Limpa o que foi armazenado anteriormente

    args = ctx.message.content.split()[1:]  # Pega toda a mensagem e o [1:] faz ele ignorar a primeira parte da mensagem que é o comando +defcargos, então só pega os cargos mencionados
    roles = ctx.message.role_mentions # Lista com todas os cargos mencionados

    if len(args) < 2 or not roles: # Ensina o usuário a como usar o comando -- Ele identifica se no comando não foi mencionado cargos suficiente ou se não foi mencionado cargos no geral
        await ctx.send("Use no formato: +defcargos 😀 @Cargo1 🎮 @Cargo2")
        return

    role_index = 0 # Só para sincronizar os emojis com os cargos

    for arg in args: # Lê em ordem o que foi digitado pelo usuário
        if arg.startswith("<@&"):  # Vê se o que foi escrito é um cargo
            continue
        else:
            if role_index >= len(roles):
                break

            emoji = arg
            role = roles[role_index]
            # Associa o emoji com um cargo
            cargo_por_emoji[emoji] = role # Salva no dicionário
            role_index += 1

    if not cargo_por_emoji:
        await ctx.send("Nenhum cargo configurado.")
        return

    descricao = "\n".join([f"{emoji} → {role.name}" for emoji, role in cargo_por_emoji.items()]) # Cria a lista que vai ser mostrada no final

    await ctx.send(f"Cargos configurados:\n{descricao}")

@bot.command()
async def cargos(ctx): # Cria a mensagem que vai ter as reações que dão cargo
    if not cargo_por_emoji: # Checa se tem algo no dicionário
        await ctx.send("Nenhum cargo foi configurado ainda.")
        return

    descricao = "\n".join([f"{emoji} → {role.name}" for emoji, role in cargo_por_emoji.items()])

    msg = await ctx.send("**Reaja para pegar seu cargo:**\n" + descricao) # Mensagem que vai ter reações adicionadas

    for emoji in cargo_por_emoji.keys():
        await msg.add_reaction(emoji) # Adiciona os emojis

@bot.event # O @bot.event é algo mais passivo, ele funciona meio que em plano de fundo
async def on_raw_reaction_add(payload): # Checa se reagiram a mensagem e dá o cargo
    if payload.member.bot: # Ignora se a reação for de um bot
        return

    emoji = payload.emoji.name # Pega o emoji que foi reagido

    if emoji not in cargo_por_emoji: # Se o emoji reagido não tiver relacionado a um cargo, só ignora ele
        return

    guild = bot.get_guild(payload.guild_id)
    member = payload.member
    role = cargo_por_emoji[emoji]

    await member.add_roles(role) # Dá o cargo correspondente a reação

@bot.event
async def on_raw_reaction_remove(payload): # Chega se reagiram a mensagem e remove o cargo -- Mesma lógica do on_raw_reaction_add
    guild = bot.get_guild(payload.guild_id)
    member = guild.get_member(payload.user_id)

    emoji = payload.emoji.name

    if emoji not in cargo_por_emoji:
        return

    role = cargo_por_emoji[emoji]
    await member.remove_roles(role) 
  
bot.run(token, log_handler=handler, log_level=logging.DEBUG)
