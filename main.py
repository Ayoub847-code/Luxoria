import discord
from discord.ext import commands
from discord.ui import Button, View
import json
import os

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True

# Initialisation du bot
bot = commands.Bot(command_prefix='/', intents=intents)

# Chargement de la base de données JSON
def load_data():
    if os.path.exists('database.json'):
        with open('database.json', 'r') as f:
            return json.load(f)
    else:
        return {}

def save_data(data):
    with open('database.json', 'w') as f:
        json.dump(data, f)

# Commande /boutique
@bot.command()
async def boutique(ctx):
    """Affiche la boutique avec des produits"""
    data = load_data()
    products = data.get("products", [])

    # Crée l'embed pour la boutique
    embed = discord.Embed(title="Boutique Luxoria", description="Voici nos produits disponibles à l'achat.", color=discord.Color.blue())
    
    if len(products) > 0:
        for product in products:
            embed.add_field(name=product['name'], value=f"**Prix :** {product['price']}€\n**Stock :** {product['stock']} unités\n**Description :** {product['description']}", inline=False)

        button = Button(label="Acheter", style=discord.ButtonStyle.green)
        button.callback = acheter_callback

        view = View()
        view.add_item(button)

        channel = discord.utils.get(ctx.guild.text_channels, name='commandes')
        if channel:
            await channel.send(embed=embed, view=view)
        await ctx.send("Consulte la boutique dans le salon #commandes.")
    else:
        await ctx.send("Aucun produit disponible pour le moment.")

# Commande /addproduct (ajout de produit)
@bot.command()
async def addproduct(ctx, name: str, price: float, stock: int, description: str):
    """Ajoute un produit à la boutique (admin uniquement)"""
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("Tu n'as pas la permission d'ajouter un produit.")
        return

    data = load_data()
    new_product = {
        'name': name,
        'price': price,
        'stock': stock,
        'description': description
    }
    data["products"].append(new_product)
    save_data(data)

    await ctx.send(f"Le produit **{name}** a été ajouté à la boutique.")

# Commande /deleteproduct (supprime un produit)
@bot.command()
async def deleteproduct(ctx, name: str):
    """Supprime un produit de la boutique (admin uniquement)"""
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("Tu n'as pas la permission de supprimer un produit.")
        return

    data = load_data()
    products = data.get("products", [])
    
    # Recherche du produit par nom
    product_to_remove = None
    for product in products:
        if product['name'].lower() == name.lower():
            product_to_remove = product
            break

    if product_to_remove:
        products.remove(product_to_remove)
        save_data(data)
        await ctx.send(f"Le produit **{name}** a été supprimé de la boutique.")
    else:
        await ctx.send(f"Le produit **{name}** n'a pas été trouvé dans la boutique.")

# Commande /cadis (voir son panier)
@bot.command()
async def cadis(ctx):
    """Affiche le panier de l'utilisateur"""
    data = load_data()
    user_cart = data.get(f"cart_{ctx.author.id}", [])

    if user_cart:
        embed = discord.Embed(title="Ton Panier", color=discord.Color.orange())
        for item in user_cart:
            embed.add_field(name=item['name'], value=f"**Prix :** {item['price']}€", inline=False)
        await ctx.send(embed=embed)
    else:
        await ctx.send("Ton panier est vide.")

# Commande /cmdencours (voir les commandes en cours)
@bot.command()
async def cmdencours(ctx):
    """Affiche les commandes en cours (admin uniquement)"""
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("Tu n'as pas la permission de voir les commandes en cours.")
        return

    data = load_data()
    in_progress = data.get("orders_in_progress", [])

    if in_progress:
        embed = discord.Embed(title="Commandes en Cours", color=discord.Color.green())
        for order in in_progress:
            embed.add_field(name=order['product'], value=f"Commande de {order['user']} - Statut: {order['status']}", inline=False)
        await ctx.send(embed=embed)
    else:
        await ctx.send("Aucune commande en cours.")

# Commande /cmdlivrer (livrer une commande)
@bot.command()
async def cmdlivrer(ctx, order_id: int):
    """Marque une commande comme livrée (admin uniquement)"""
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("Tu n'as pas la permission de livrer une commande.")
        return

    data = load_data()
    in_progress = data.get("orders_in_progress", [])
    order = next((o for o in in_progress if o['id'] == order_id), None)

    if order:
        order['status'] = "Livré"
        save_data(data)
        await ctx.send(f"La commande **{order['product']}** a été marquée comme livrée.")
    else:
        await ctx.send("Commande non trouvée.")

# Commande /suprcmd (supprimer une commande)
@bot.command()
async def suprcmd(ctx, order_id: int):
    """Supprime une commande (admin uniquement)"""
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("Tu n'as pas la permission de supprimer une commande.")
        return

    data = load_data()
    in_progress = data.get("orders_in_progress", [])
    order = next((o for o in in_progress if o['id'] == order_id), None)

    if order:
        in_progress.remove(order)
        save_data(data)
        await ctx.send(f"La commande **{order['product']}** a été supprimée.")
    else:
        await ctx.send("Commande non trouvée.")

# Commande /ajouterabo (ajouter un abonnement)
@bot.command()
async def ajouterabo(ctx, user: discord.User, abo_type: str, duration: int):
    """Ajoute un abonnement à un utilisateur (admin uniquement)"""
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("Tu n'as pas la permission d'ajouter un abonnement.")
        return

    data = load_data()
    subscriptions = data.get("subscriptions", {})
    subscriptions[user.id] = {
        'type': abo_type,
        'duration': duration,
        'start_date': str(ctx.message.created_at)
    }
    save_data(data)
    await ctx.send(f"Un abonnement **{abo_type}** a été ajouté pour {user.name} pour {duration} jours.")

# Commande /monprofil (affiche le profil de l'utilisateur)
@bot.command()
async def monprofil(ctx):
    """Affiche les informations du profil de l'utilisateur"""
    data = load_data()
    user_data = data.get(f"user_{ctx.author.id}", {})

    if user_data:
        embed = discord.Embed(title=f"Profil de {ctx.author.name}", color=discord.Color.purple())
        embed.add_field(name="Rôle VIP", value=user_data.get('vip', 'Non'), inline=False)
        embed.add_field(name="Achats passés", value=", ".join(user_data.get('purchases', [])), inline=False)
        await ctx.send(embed=embed)
    else:
        await ctx.send("Aucune donnée trouvée pour ton profil.")

# Commande /vip (affiche les avantages du rôle VIP)
@bot.command()
async def vip(ctx):
    """Affiche les avantages du rôle VIP"""
    await ctx.send("Les avantages du rôle VIP sont :\n- Accès aux promotions spéciales\n- Support prioritaire\n- Et bien plus !")

# Commande /vip-promos (liste des promotions pour VIP)
@bot.command()
async def vip_promos(ctx):
    """Affiche les promotions réservées aux VIP"""
    await ctx.send("Les promotions VIP actuelles :\n- 20% de réduction sur tous les produits\n- Accès à des produits exclusifs.")

# Commande /vip-support (ouvre un ticket de support pour VIP)
@bot.command()
async def vip_support(ctx):
    """Ouvre un ticket de support pour VIP"""
    await ctx.send(f"{ctx.author.mention}, un ticket de support a été créé pour toi. Un membre du staff va te répondre bientôt.")

# Démarrage du bot
@bot.event
async def on_ready():
    print(f'{bot.user} a bien démarré.')

# Lancer le bot
bot.run(os.getenv("DISCORD_TOKEN"))
