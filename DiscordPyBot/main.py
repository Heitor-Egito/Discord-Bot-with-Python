import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os
import random
import asyncio

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
painel_cargos_id = None

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
    
    # Isso daqui é para impossibilitar que o usuário reaja com um emoji que está no dicionário, mas está em outra mensagem, e mesmo assim pegue o cargo
    global painel_cargos_id # Puxa a variável global
    painel_cargos_id = msg.id # Coloca ela como o ID da mensagem respectiva

    for emoji in cargo_por_emoji.keys():
        await msg.add_reaction(emoji) # Adiciona os emojis

@bot.event # O @bot.event é algo mais passivo, ele funciona meio que em plano de fundo
async def on_raw_reaction_add(payload): # Checa se reagiram a mensagem e dá o cargo
    if payload.member is None or payload.member.bot: # Ignora se a reação for de um bot
        return

    emoji = payload.emoji.name # Pega o emoji que foi reagido

    if emoji not in cargo_por_emoji: # Se o emoji reagido não tiver relacionado a um cargo, só ignora ele
        return

    if payload.message_id != painel_cargos_id: # Verifica o ID da mensagem
        return
    if painel_cargos_id is None: # Se não tiver mensagem definida só ignora
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

    if member is None:
        return
        
    if emoji not in cargo_por_emoji:
        return

    if payload.message_id != painel_cargos_id:
        return
    if painel_cargos_id is None:
        return
    
    role = cargo_por_emoji[emoji]
    await member.remove_roles(role) 


@bot.command()
async def blackjack(ctx): # Cria o comando +blackjack
    card_categories = [':hearts:', ':diamonds:', ':spades:', ':clubs:'] # Lista dos emojis referentes a cada naipe
    cards_list = ['Ace','2','3','4','5','6','7','8','9','10','Jack','Queen','King'] # Lista com todas as cartas (Ás até o Rei)
    deck = [(card, category) for category in card_categories for card in cards_list] # Cria um deck, que é uma lista de tuplas com todas as cartas disponíveis

    def card_value(card, current_score): # Cria a função pra definir o valor das cartas
        if card[0] in ['Jack','Queen','King']:
            return 10
        elif card[0] == 'Ace':
            return 11 if current_score + 11 <= 21 else 1 # Isso daqui é para não explodir injustamente
        else:
            return int(card[0])

    random.shuffle(deck) # Embaralha o deck

    player_card = [deck.pop(), deck.pop()] # puxa duas cartas
    dealer_card = [deck.pop(), deck.pop()] # puxa duas cartas
    
    def format_hand(hand):
        return " | ".join([f"{card} {suit}" for card, suit in hand])
        
    def score(hand): # Cria uma função para calcular os pontos
        total = 0
        for c in hand: # Pega a mão e contabiliza os pontos
            total += card_value(c, total)
        return total
    
    def check(msg): # Função só para checar se a mensagem que respondeu foi a do mesmo usuário
        return msg.author == ctx.author and msg.channel == ctx.channel
        
    while True: # Loop do turno do JOGADOR
        player_score = score(player_card) # Pontuação do Jogador
        dealer_score = score(dealer_card) # Pontuação do Dealer

        await ctx.send( # Mensagem do turno do jogador
            f"🃏 **Suas cartas:** {format_hand(player_card)}\n"
            f"📊 **Seu score:** {player_score}\n\n"
            f"Digite **play** para comprar ou **stop** para parar."
        )

        if player_score > 21: # Se o jogador estourar
            await ctx.send("💥 Você estourou! Dealer venceu.")
            return

        try:
            choice = await bot.wait_for("message", check=check, timeout=30) # Espera a mensagem do player por 30 segundos, caso passe desse tempo, ele cancela o jogo
        except asyncio.TimeoutError:
            await ctx.send("⏱️ Tempo esgotado. Jogo cancelado.")
            return

        if choice.content.lower() == "play": # Caso o jogador queira pegar mais uma carta
            player_card.append(deck.pop()) # Adiciona +1 carta na mão do jogador
        elif choice.content.lower() == "stop": # Caso o jogador queira parar
            break
        else:
            await ctx.send("Escolha inválida.") # Caso ele escolha algo fora do aceitável
            continue

    while dealer_score < 17: # Turno do dealer é bem básico, ele só puxa se tiver com -17 pontos
        dealer_card.append(deck.pop())
        dealer_score = score(dealer_card)

    # Atualiza uma última vez as pontuações
    player_score = score(player_card)
    dealer_score = score(dealer_card)

    await ctx.send( # Mensagem de Resultado
        f"🂠 **Dealer:** {format_hand(dealer_card)} ({dealer_score})\n"
        f"🃏 **Você:** {format_hand(player_card)} ({player_score})"
    )
    # Cada um dos finais aí
    if dealer_score > 21 or player_score > dealer_score:
        await ctx.send("🎉 **Você venceu!**")
    elif dealer_score > player_score:
        await ctx.send("😈 **Dealer venceu!**")
    else:
        await ctx.send("🤝 **Empate!**")


bot.run(token, log_handler=handler, log_level=logging.DEBUG)
