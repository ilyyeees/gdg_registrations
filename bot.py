import discord
from discord.ext import commands
import sqlite3
import asyncio
import os

# --- Load Configuration ---
try:
    from config import BOT_TOKEN, DB_NAME, VERIFICATION_CHANNEL_ID
except ImportError:
    print("Error: config.py not found.")
    print("Please create config.py with BOT_TOKEN, DB_NAME, and VERIFICATION_CHANNEL_ID.")
    exit()

# --- Bot Setup ---
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.guilds = True
intents.members = True  # Make sure this is enabled in the Discord Developer Portal

bot = commands.Bot(command_prefix='!', intents=intents)

# --- Database Check ---
if not os.path.exists(DB_NAME):
    print(f"Database file '{DB_NAME}' not found.")
    print("Please run the send_invites.py script first to create and populate the database.")
    exit()

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} ({bot.user.id})')
    print('Bot is online and ready to verify members.')
    print('------')

@bot.command(name='verify')
async def verify(ctx, *, token: str = None):
    """
    Verifies a new member using their unique token and assigns the corresponding role.
    """
    # 1. Check if the command is in the correct channel
    if ctx.channel.id != VERIFICATION_CHANNEL_ID:
        try:
            # Delete the user's message to keep the channel clean
            await ctx.message.delete()
        except discord.Forbidden:
            print(f"Bot lacks permission to delete messages in {ctx.channel.name}")
        except Exception as e:
            print(f"Error deleting message: {e}")

        # Send a private message to the user
        try:
            await ctx.author.send(f"Hi! Please use the !verify command in the designated verification channel.")
        except discord.Forbidden:
            print(f"Could not send DM to {ctx.author.name}. They might have DMs disabled.")
        return

    # 2. Check if token was provided
    if token is None:
        await ctx.send(f"Please provide your verification token, {ctx.author.mention}. Usage: !verify YOUR_TOKEN", delete_after=10)
        await asyncio.sleep(10)
        await ctx.message.delete()
        return

    conn = None
    try:
        # 3. Connect to the database
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        # 4. Find the token in the database
        cursor.execute("SELECT role_id, verified, first_name, email FROM members WHERE token = ?", (token,))
        result = cursor.fetchone()

        # 5. Handle cases: Invalid token, token already used
        if result is None:
            await ctx.send(f"Sorry {ctx.author.mention}, that token is invalid. Please check your email again or contact an admin.", delete_after=15)
            await asyncio.sleep(15)
            await ctx.message.delete()
            return

        role_id, verified, first_name, email = result

        if verified == 1:
            await ctx.send(f"Hi {ctx.author.mention}, this token has already been used. If you believe this is an error, please contact an admin.", delete_after=15)
            await asyncio.sleep(15)
            await ctx.message.delete()
            return

        # 6. Assign the role
        role = ctx.guild.get_role(role_id)
        if role is None:
            print(f"ERROR: Role with ID {role_id} not found on this server.")
            await ctx.send(f"An internal error occurred. Please contact an admin (Error: Role ID {role_id} not found).", delete_after=15)
            await asyncio.sleep(15)
            await ctx.message.delete()
            return

        await ctx.author.add_roles(role)

        # 7. Update the database to mark as verified and store user ID
        discord_id = str(ctx.author.id)
        cursor.execute("UPDATE members SET verified = 1, discord_id = ? WHERE token = ?", (discord_id, token))
        conn.commit()

        # 8. Send confirmation and clean up
        print(f"SUCCESS: Verified {first_name} ({email}) and assigned role '{role.name}'.")
        await ctx.send(f"Welcome, {ctx.author.mention}! You have been verified and assigned the **{role.name}** role. Welcome to the GDG ENSIA community!", delete_after=20)

        # Try to set their nickname to their real first name
        try:
            await ctx.author.edit(nick=first_name)
        except discord.Forbidden:
            print(f"Could not change nickname for {ctx.author.name}. Bot role is likely not high enough.")
        except Exception as e:
            print(f"Error changing nickname: {e}")

    except sqlite3.Error as e:
        print(f"An error occurred during database operation: {e}")
        await ctx.send(f"A database error occurred. Please contact an admin.", delete_after=10)
    except discord.Forbidden:
        print(f"Bot lacks permissions to assign roles or delete messages.")
        await ctx.send(f"Error: I don't have permission to assign roles. Please ensure my role is above the roles I need to assign.", delete_after=15)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        await ctx.send(f"An unexpected error occurred. Please contact an admin.", delete_after=10)
    finally:
        if conn:
            conn.close()

        try:
            # Delete the user's message containing the token for privacy
            await ctx.message.delete()
        except Exception as e:
            print(f"Could not delete user's verification message: {e}")

# Run the bot
print("Starting bot...")
bot.run(BOT_TOKEN)
