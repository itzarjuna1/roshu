# tictactoe.py
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
from collections import defaultdict

# =========================
# Storage
# =========================
games = {}  # {chat_id: game_data}
leaderboards = defaultdict(lambda: defaultdict(int))  # leaderboards[chat_id][user_id] = wins
PREFIXES = ["/", ".", "!"]

# =========================
# Start Tic Tac Toe
# =========================
@Client.on_message(filters.command("tictac", prefixes=PREFIXES) & filters.group)
async def start_tictactoe(client: Client, message: Message):
    chat_id = message.chat.id
    # Initialize game
    if chat_id in games:
        return await message.reply_text("A Tic Tac Toe game is already running!")
    games[chat_id] = {
        "players": [],
        "board": [""]*9,
        "turn": 0,
        "started": False
    }
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("✅ Join Game", callback_data="tictac_join")]]
    )
    await message.reply_text("🎮 Tic Tac Toe started! Click ✅ Join Game to participate (2 players required).", reply_markup=keyboard)

# =========================
# Handle callbacks
# =========================
@Client.on_callback_query()
async def tictactoe_callbacks(client: Client, callback_query: CallbackQuery):
    chat_id = callback_query.message.chat.id
    user = callback_query.from_user
    data = callback_query.data

    if chat_id not in games:
        return await callback_query.answer("No game running.", show_alert=True)

    game = games[chat_id]

    # === Join game ===
    if data == "tictac_join":
        if user.id in [p.id for p in game["players"]]:
            return await callback_query.answer("You already joined!", show_alert=True)
        if len(game["players"]) >= 2:
            return await callback_query.answer("Game is full!", show_alert=True)

        game["players"].append(user)
        await callback_query.answer(f"{user.mention} joined!")

        if len(game["players"]) == 2:
            game["started"] = True
            await send_tictac_board(client, chat_id, callback_query.message)
        else:
            await callback_query.message.edit_text(f"Tic Tac Toe waiting for players...\n1/2 joined.", reply_markup=callback_query.message.reply_markup)
        return

    # === Make a move ===
    if data.startswith("tictac_move:"):
        if not game["started"]:
            return await callback_query.answer("Game hasn't started yet.", show_alert=True)

        pos = int(data.split(":")[1])
        player_turn = game["players"][game["turn"] % 2]
        if user.id != player_turn.id:
            return await callback_query.answer("Not your turn!", show_alert=True)
        if game["board"][pos] != "":
            return await callback_query.answer("Cell already taken!", show_alert=True)

        mark = "❌" if game["turn"] % 2 == 0 else "⭕"
        game["board"][pos] = mark
        game["turn"] += 1

        winner = check_winner(game["board"])
        if winner:
            text = f"{winner} wins! 🏆"
            if winner == "❌":
                leaderboards[chat_id][game["players"][0].id] += 1
            else:
                leaderboards[chat_id][game["players"][1].id] += 1
            await callback_query.message.edit_text(render_board(game["board"]) + "\n\n" + text, reply_markup=None)
            del games[chat_id]
        elif "" not in game["board"]:
            await callback_query.message.edit_text(render_board(game["board"]) + "\n\nIt's a draw!", reply_markup=None)
            del games[chat_id]
        else:
            await send_tictac_board(client, chat_id, callback_query.message)
        return

# =========================
# Render board
# =========================
def render_board(board):
    return "\n".join([" | ".join(board[i:i+3]) if board[i] != "" else "▫️ | ▫️ | ▫️" for i in range(0, 9, 3)])

# =========================
# Send board with buttons
# =========================
async def send_tictac_board(client, chat_id, message):
    game = games[chat_id]
    keyboard = []
    for i in range(0, 9, 3):
        row = []
        for j in range(3):
            idx = i+j
            text = game["board"][idx] if game["board"][idx] != "" else "▫️"
            row.append(InlineKeyboardButton(text, callback_data=f"tictac_move:{idx}"))
        keyboard.append(row)
    board_markup = InlineKeyboardMarkup(keyboard)
    player_turn = game["players"][game["turn"] % 2]
    await message.edit_text(f"Tic Tac Toe - {player_turn.mention}'s turn\n\n" + render_board(game["board"]), reply_markup=board_markup)

# =========================
# Leaderboard
# =========================
@Client.on_message(filters.command("ticlead", prefixes=PREFIXES) & filters.group)
async def tictac_leaderboard(client: Client, message: Message):
    chat_id = message.chat.id
    if chat_id not in leaderboards or not leaderboards[chat_id]:
        return await message.reply_text("No games played yet!")

    text = "🏆 Tic Tac Toe Leaderboard 🏆\n\n"
    sorted_players = sorted(leaderboards[chat_id].items(), key=lambda x: x[1], reverse=True)
    for idx, (user_id, wins) in enumerate(sorted_players[:10], 1):
        text += f"{idx}. [User](tg://user?id={user_id}) - {wins} wins\n"
    await message.reply_text(text, disable_web_page_preview=True)

# =========================
# Check winner
# =========================
def check_winner(b):
    wins = [
        [0,1,2],[3,4,5],[6,7,8],
        [0,3,6],[1,4,7],[2,5,8],
        [0,4,8],[2,4,6]
    ]
    for w in wins:
        if b[w[0]] != "" and b[w[0]] == b[w[1]] == b[w[2]]:
            return b[w[0]]
    return None
