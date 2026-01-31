print("file loaded")# rps.py
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
from collections import defaultdict
import random

# =======================
# Game storage
# =======================
games = {}  # {chat_id: game_data}
leaderboard = defaultdict(lambda: defaultdict(int))  # {chat_id: {user_id: wins}}

CHOICES = ["Rock", "Paper", "Scissors"]
EMOJI = {"Rock": "✊", "Paper": "✋", "Scissors": "✌"}

# =======================
# Start RPS Game
# =======================
@Client.on_message(filters.command("rps") & filters.group)
async def start_rps(client: Client, message: Message):
    chat_id = message.chat.id
    if chat_id in games:
        return await message.reply_text("A Rock Paper Scissors game is already running! Click ✅ Join Game to play.")

    games[chat_id] = {
        "players": [],
        "choices": {},
        "started": False
    }

    join_button = InlineKeyboardMarkup(
        [[InlineKeyboardButton("✅ Join Game", callback_data="rps_join")]]
    )

    await message.reply_text(
        "Rock Paper Scissors started! Click ✅ Join Game to participate (2 players required).",
        reply_markup=join_button
    )

# =======================
# Handle button clicks
# =======================
@Client.on_callback_query()
async def rps_buttons(client: Client, callback_query: CallbackQuery):
    chat_id = callback_query.message.chat.id
    game = games.get(chat_id)
    user = callback_query.from_user

    if not game:
        return await callback_query.answer("No game in progress.", show_alert=True)

    # ===== Join Game =====
    if callback_query.data == "rps_join":
        if user.id in [p.id for p in game["players"]]:
            return await callback_query.answer("You already joined!", show_alert=True)
        if len(game["players"]) >= 2:
            return await callback_query.answer("Game already has 2 players!", show_alert=True)

        game["players"].append(user)
        if len(game["players"]) < 2:
            await callback_query.answer(f"{user.mention} joined! Waiting for another player...")
            await callback_query.message.edit_text(
                f"Rock Paper Scissors waiting for players...\n"
                f"{len(game['players'])}/2 joined.",
                reply_markup=callback_query.message.reply_markup
            )
            return
        else:
            game["started"] = True
            # Show buttons to pick choice
            choices_buttons = InlineKeyboardMarkup([
                [InlineKeyboardButton(f"{EMOJI[c]} {c}", callback_data=f"rps_choice:{c}") for c in CHOICES]
            ])
            await callback_query.message.edit_text(
                f"Game started!\n{game['players'][0].mention} vs {game['players'][1].mention}\n"
                f"Each player pick Rock, Paper, or Scissors:",
                reply_markup=choices_buttons
            )
            return await callback_query.answer("Game started!")

    # ===== Player makes choice =====
    if callback_query.data.startswith("rps_choice:") and game["started"]:
        choice = callback_query.data.split(":")[1]
        if user.id not in [p.id for p in game["players"]]:
            return await callback_query.answer("You are not in this game!", show_alert=True)
        if user.id in game["choices"]:
            return await callback_query.answer("You already chose!", show_alert=True)

        game["choices"][user.id] = choice
        await callback_query.answer(f"You chose {EMOJI[choice]} {choice}")

        # Check if both players made a choice
        if len(game["choices"]) < 2:
            return

        # Both players chose → determine winner
        p1, p2 = game["players"]
        c1 = game["choices"][p1.id]
        c2 = game["choices"][p2.id]

        if c1 == c2:
            result_text = f"🤝 Draw!\n{p1.mention} chose {EMOJI[c1]} {c1}\n{p2.mention} chose {EMOJI[c2]} {c2}"
        else:
            # Determine winner
            wins = {
                "Rock": "Scissors",
                "Scissors": "Paper",
                "Paper": "Rock"
            }
            if wins[c1] == c2:
                winner = p1
                winner_choice = c1
            else:
                winner = p2
                winner_choice = c2
            leaderboard[chat_id][winner.id] += 1
            result_text = (
                f"🏆 {winner.mention} wins!\n"
                f"{p1.mention} chose {EMOJI[c1]} {c1}\n"
                f"{p2.mention} chose {EMOJI[c2]} {c2}"
            )

        await callback_query.message.edit_text(result_text)
        del games[chat_id]  # reset game

# =======================
# RPS Leaderboard
# =======================
@Client.on_message(filters.command("rpslead") & filters.group)
async def show_rps_leaderboard(client: Client, message: Message):
    chat_id = message.chat.id
    if chat_id not in leaderboard or not leaderboard[chat_id]:
        return await message.reply_text("No games played yet!")

    sorted_board = sorted(leaderboard[chat_id].items(), key=lambda x: x[1], reverse=True)
    text = "🏆 Rock Paper Scissors Leaderboard 🏆\n\n"
    for idx, (user_id, wins) in enumerate(sorted_board[:10], 1):  # top 10
        text += f"{idx}. [User](tg://user?id={user_id}) - {wins} wins\n"

    await message.reply_text(text, disable_web_page_preview=True)
