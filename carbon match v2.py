import random
import streamlit as st
from supabase import create_client, Client
from streamlit_autorefresh import st_autorefresh
import time

# ============================================================
# Page Setup
# ============================================================
st.set_page_config(
    page_title="Carbon Match: Carbon Showdown (Online)", layout="wide"
)

TABLE = "carbon_match_games"

# ============================================================
# Bilingual Text Dictionary
# ============================================================
LANG_TEXT = {
    "EN": {
        # Page / Header
        "page_title": "🃏 Carbon Match: Carbon Showdown (Online)",
        "room_caption": "Enter the same room code with your opponent, choose your role, and battle online.",
        "room_input_label": "Room Code (Must match opponent, e.g., abc123)",
        "you_are": "You are?",
        "join_create": "Join / Create Room",
        "room_warn": "Please enter a room code first.",
        "leave_room": "🚪 Leave Room",
        "room_header": lambda rc, mp: f"Room: {rc} ｜ You are: {mp} ｜ Rules: +1 AP, All Swap, Single Swap, Push, Steal, Destroy, Chaos Card.",
        # Deck Status
        "deck_status": "📦 Deck Status",
        "cards_remaining": lambda cnt: f"Cards Remaining: {cnt} / 50",
        # Metrics
        "current_turn": "📍 Current Turn",
        "current_ap": "⚡ Current AP",
        "score_label": "⭐ Score",
        "restart": "🔄 Restart Game",
        # Game Over
        "game_settled": "🏆 GAME SETTLED 🏆",
        "game_over_msg": lambda wt, ws: f"Congratulations! <span style='color:#ffeaa7;text-decoration:underline;'>{wt}</span> wins with <span style='color:#55efc4;'>{ws} pts</span>!",
        # Player Zone
        "p1_zone": "🔵 Player 1 Zone",
        "p2_zone": "🔴 Player 2 Zone",
        "you_suffix": " (You)",
        "your_turn": lambda ap: f"⚡ Your turn (Remaining AP: {ap})",
        "opp_turn": "⏳ Opponent's turn, please wait...",
        "current_score": lambda s: f"(Current Score: {s})",
        # Action Buttons
        "draw_card": "🎴 Draw Card (-1 AP)",
        "neutralize": "🌿 Neutralize (0 pts)",
        "end_turn": "⏭️ End Turn",
        "draw_warn": "Insufficient AP or empty deck!",
        "neutral_warn_no_pair": "No opposite-color cards available for pairing!",
        "neutral_warn_few": "Staging area has fewer than 2 cards!",
        # Hand / Staging / Scoring
        "hand_title": lambda p: f"**🎒 {p}'s Hand Cards**",
        "hand_empty": "Hand library is empty",
        "staging_title": lambda p: f"**📥 {p}'s Staging Area**",
        "staging_empty": "Staging area is empty",
        "scored_title": lambda p, s: f"**🏆 {p} Scored Area (Total Score: {s})**",
        "scored_empty": "No pairs in scored area yet",
        "pair_label": lambda i: f"Pair #{i+1}",
        # Tactical hints
        "push_hint": "👉 [Push Active] Click the card to push to opponent:",
        "single_swap_hint_own": "👉 [Single Swap Active] Select a card from your staging area:",
        "single_swap_hint_opp": "👉 [Single Swap Active] Click a card in opponent's staging area:",
        "steal_hint": "👉 [Steal Active] Click a card in opponent's staging area to steal:",
        "destroy_hint": "👉 [Destroy Active] Click a card in opponent's staging area to destroy:",
        "ap_warn": "⚠️ Insufficient AP!",
        # Card play buttons
        "play_btn": lambda i: f"Play #{i+1}",
        "push_btn": lambda i: f"Push #{i+1}",
        "select_btn": lambda i: f"Select #{i+1}",
        "swap_btn": lambda i: f"Swap #{i+1}",
        "steal_btn": lambda i: f"Steal #{i+1}",
        "destroy_btn": lambda i: f"Destroy #{i+1}",
        # Logs
        "game_start": "🎮 Game started! Carbon neutrality dual match launched. Player 1's turn.",
        "log_draw_number": lambda p, v, t: f"{p} drew number card [{v}-{t}], entered staging area.",
        "log_draw_tactical": lambda p, v: f"{p} drew tactical card [{v}].",
        "log_neutral": lambda p, v: f"🌿 {p} manually neutralized mixed pair (No.{v}): 0 pts.",
        "log_end_turn": lambda t: f"Turn passed: Current turn is {t}.",
        "log_plus_ap": lambda p: f"⚡ {p} played +1 AP card: +1 AP!",
        "log_all_swap": lambda p: f"🔄 {p} played All Swap card: swapped both staging areas!",
        "log_single_swap_prepare": lambda p: f"🎯 {p} preparing Single Swap: select own card.",
        "log_single_swap_locked": lambda p, c: f"🔄 {p} locked card {c}, click opponent's card to swap.",
        "log_single_swap_p1": lambda oc, tc: f"🔄 Player 1 swapped {oc} with Player 2's {tc}!",
        "log_single_swap_p2": lambda oc, tc: f"🔄 Player 2 swapped {oc} with Player 1's {tc}!",
        "log_push_prepare": lambda p: f"🎯 {p} preparing Push: select card to push.",
        "log_push_p1": lambda c: f"🎯 Player 1 pushed {c} to Player 2!",
        "log_push_p2": lambda c: f"🎯 Player 2 pushed {c} to Player 1!",
        "log_steal_prepare": lambda p: f"🎯 {p} preparing Steal: select a card from opponent's staging area.",
        "log_steal_p1": lambda c: f"🕵️ Player 1 stole {c} from Player 2's staging area!",
        "log_steal_p2": lambda c: f"🕵️ Player 2 stole {c} from Player 1's staging area!",
        "log_destroy_prepare": lambda p: f"🎯 {p} preparing Destroy: select opponent's staging card to destroy.",
        "log_destroy": lambda a, v, c: f"💣 Player {a} destroyed Player {v}'s card {c}!",
        "log_double_black": lambda p, v, pts: f"🚨 {p} triggered Double Black Pair (No.{v}): -{v} = {pts} pts",
        "log_double_red": lambda p, v, pts: f"💡 {p} triggered Double Red Pair (No.{v}): +{v} * 1.5 = +{pts} pts",
        "log_chaos_no_scoring": lambda p: f"🃏 {p} drew a Chaos Card, but the scoring area is empty. Chaos effect fails!",
        "log_chaos": lambda p, pair, pts, opp: f"🃏 {p} drew a Chaos Card! Highest scoring pair {pair} ({pts} pts) sent to {opp}'s staging area!",
        "log_game_over": lambda p1s, p2s, w: f"🏁 【Game Over】Final Settlement: Player 1 Score {p1s}, Player 2 Score {p2s}. Winner: [{w}]!",
        "toast_chaos": "Chaos Card drawn! Chaos is unfolding...",
        # Logs section
        "logs_title": "📋 Game Dynamic Logs",
        # Language toggle
        "lang_label": "🌐 Language / 语言",
    },
    "ZH": {
        # Page / Header
        "page_title": "🃏 碳匹配：碳对决（在线版）",
        "room_caption": "与对手输入相同的房间号，选择你的角色，开始在线对战！",
        "room_input_label": "房间号（需与对手一致，例：abc123）",
        "you_are": "你是？",
        "join_create": "加入 / 创建房间",
        "room_warn": "请先输入房间号。",
        "leave_room": "🚪 离开房间",
        "room_header": lambda rc, mp: f"房间: {rc} ｜ 你是: {mp} ｜ 规则: +1行动点, 全体交换, 单卡交换, 推送, 偷取, 销毁, 混沌卡",
        # Deck Status
        "deck_status": "📦 牌堆状态",
        "cards_remaining": lambda cnt: f"剩余卡牌: {cnt} / 50",
        # Metrics
        "current_turn": "📍 当前回合",
        "current_ap": "⚡ 当前行动点",
        "score_label": "⭐ 分数",
        "restart": "🔄 重新开始",
        # Game Over
        "game_settled": "🏆 游戏结算 / GAME SETTLED 🏆",
        "game_over_msg": lambda wt, ws: f"恭喜 <span style='color:#ffeaa7;text-decoration:underline;'>{wt}</span> 以 <span style='color:#55efc4;'>{ws} 分</span> 获得最终胜利！",
        # Player Zone
        "p1_zone": "🔵 玩家1区域",
        "p2_zone": "🔴 玩家2区域",
        "you_suffix": "（你）",
        "your_turn": lambda ap: f"⚡ 你的回合（剩余行动点: {ap}）",
        "opp_turn": "⏳ 对手回合，请稍候...",
        "current_score": lambda s: f"（当前分数: {s}）",
        # Action Buttons
        "draw_card": "🎴 抽牌（-1行动点）",
        "neutralize": "🌿 中和（0分）",
        "end_turn": "⏭️ 结束回合",
        "draw_warn": "行动点不足或牌堆为空！",
        "neutral_warn_no_pair": "暂存区没有可配对的异色牌！",
        "neutral_warn_few": "暂存区卡牌不足2张！",
        # Hand / Staging / Scoring
        "hand_title": lambda p: f"**🎒 {p} 的手牌**",
        "hand_empty": "手牌为空",
        "staging_title": lambda p: f"**📥 {p} 的暂存区**",
        "staging_empty": "暂存区为空",
        "scored_title": lambda p, s: f"**🏆 {p} 得分区（总分: {s}）**",
        "scored_empty": "得分区暂无配对",
        "pair_label": lambda i: f"配对 #{i+1}",
        # Tactical hints
        "push_hint": "👉 【推送激活】点击要推给对手的卡牌：",
        "single_swap_hint_own": "👉 【单卡交换激活】选择你暂存区的一张牌：",
        "single_swap_hint_opp": "👉 【单卡交换激活】点击对手暂存区的一张牌进行交换：",
        "steal_hint": "👉 【偷取激活】点击对手暂存区的牌来偷取：",
        "destroy_hint": "👉 【销毁激活】点击对手暂存区的牌来销毁：",
        "ap_warn": "⚠️ 行动点不足！",
        # Card play buttons
        "play_btn": lambda i: f"出牌 #{i+1}",
        "push_btn": lambda i: f"推送 #{i+1}",
        "select_btn": lambda i: f"选择 #{i+1}",
        "swap_btn": lambda i: f"交换 #{i+1}",
        "steal_btn": lambda i: f"偷取 #{i+1}",
        "destroy_btn": lambda i: f"销毁 #{i+1}",
        # Logs
        "game_start": "🎮 游戏开始！碳中和对决正式启动。玩家1先手。",
        "log_draw_number": lambda p, v, t: f"{p} 抽到数字牌 [{v}-{t}]，进入暂存区。",
        "log_draw_tactical": lambda p, v: f"{p} 抽到战术卡 [{v}]。",
        "log_neutral": lambda p, v: f"🌿 {p} 手动中和了混色配对（编号{v}）：0分。",
        "log_end_turn": lambda t: f"回合结束：当前轮到 {t}。",
        "log_plus_ap": lambda p: f"⚡ {p} 打出+1行动点卡：+1行动点！",
        "log_all_swap": lambda p: f"🔄 {p} 打出全体交换卡：双方暂存区互换！",
        "log_single_swap_prepare": lambda p: f"🎯 {p} 准备单卡交换：选择自己的牌。",
        "log_single_swap_locked": lambda p, c: f"🔄 {p} 锁定了卡牌 {c}，点击对手的牌进行交换。",
        "log_single_swap_p1": lambda oc, tc: f"🔄 玩家1将 {oc} 与玩家2的 {tc} 进行了交换！",
        "log_single_swap_p2": lambda oc, tc: f"🔄 玩家2将 {oc} 与玩家1的 {tc} 进行了交换！",
        "log_push_prepare": lambda p: f"🎯 {p} 准备推送：选择要推出的牌。",
        "log_push_p1": lambda c: f"🎯 玩家1将 {c} 推送给了玩家2！",
        "log_push_p2": lambda c: f"🎯 玩家2将 {c} 推送给了玩家1！",
        "log_steal_prepare": lambda p: f"🎯 {p} 准备偷取：选择对手暂存区的一张牌。",
        "log_steal_p1": lambda c: f"🕵️ 玩家1从玩家2暂存区偷取了 {c}！",
        "log_steal_p2": lambda c: f"🕵️ 玩家2从玩家1暂存区偷取了 {c}！",
        "log_destroy_prepare": lambda p: f"🎯 {p} 准备销毁：选择对手暂存区的牌。",
        "log_destroy": lambda a, v, c: f"💣 玩家{a} 销毁了玩家{v}的卡牌 {c}！",
        "log_double_black": lambda p, v, pts: f"🚨 {p} 触发双黑配对（编号{v}）：-{v} = {pts}分",
        "log_double_red": lambda p, v, pts: f"💡 {p} 触发双红配对（编号{v}）：+{v} * 1.5 = +{pts}分",
        "log_chaos_no_scoring": lambda p: f"🃏 {p} 抽到混沌卡，但得分区为空，混沌效果无效！",
        "log_chaos": lambda p, pair, pts, opp: f"🃏 {p} 抽到混沌卡！最高分配对 {pair}（{pts}分）被送入 {opp} 的暂存区！",
        "log_game_over": lambda p1s, p2s, w: f"🏁 【游戏结束】最终结算：玩家1得分 {p1s}，玩家2得分 {p2s}。获胜者：【{w}】！",
        "toast_chaos": "抽到混沌卡！混沌效果正在展开...",
        # Logs section
        "logs_title": "📋 游戏动态日志",
        # Language toggle
        "lang_label": "🌐 Language / 语言",
    },
}

# Player name translations
PLAYER_NAMES = {
    "EN": {"Player 1": "Player 1", "Player 2": "Player 2", "Draw": "Draw"},
    "ZH": {"Player 1": "玩家1", "Player 2": "玩家2", "Draw": "平局"},
}

# ============================================================
# Language State
# ============================================================
if "lang" not in st.session_state:
    st.session_state.lang = "EN"

# ============================================================
# Supabase Connection
# ============================================================
@st.cache_resource
def get_supabase() -> Client:
    url = st.secrets["supabase_url"]
    key = st.secrets["supabase_key"]
    return create_client(url, key)


supabase = get_supabase()


# ============================================================
# Deck Builder — 50 cards total
#   Number cards: 5 nums × 2 colors × 3 copies = 30
#   Power cards:  6 types × 3 copies            = 18
#   Chaos Cards:  2 copies                       =  2
#   Total                                        = 50
# ============================================================
def new_deck():
    deck = []
    # 1. Number cards (1-5, Black/Red) — 3 copies each
    for num in range(1, 6):
        for _ in range(3):
            deck.append([str(num), "B"])
            deck.append([str(num), "R"])

    # 2. Power / tactical cards — 3 copies each (6 types × 3 = 18)
    for _ in range(3):
        deck.append(["+1 AP", "T"])
        deck.append(["All Swap", "T"])
        deck.append(["Single Swap", "T"])
        deck.append(["Push", "T"])
        deck.append(["Steal", "T"])
        deck.append(["Destroy", "T"])

    # 3. Chaos Card — 2 copies
    for _ in range(2):
        deck.append(["Chaos Card", "C"])

    random.shuffle(deck)
    return deck


# ============================================================
# Card HTML Renderer  (design preserved)
# ============================================================
def render_card_html(val, card_type, size="normal"):
    if val == "+1 AP":
        bg, border, text_c, label = "#e3f2fd", "#2196f3", "#0d47a1", "Action Point"
    elif val == "All Swap":
        bg, border, text_c, label = "#f3e5f5", "#ab47bc", "#4a148c", "Staging Swap"
    elif val == "Single Swap":
        bg, border, text_c, label = "#e1f5fe", "#00acc1", "#006064", "Target Swap"
    elif val == "Push":
        bg, border, text_c, label = "#e8f5e9", "#4caf50", "#1b5e20", "Card Push"
    elif val == "Steal":
        bg, border, text_c, label = "#fff3cd", "#ffc107", "#856404", "Steal Card"
    elif val == "Destroy":
        bg, border, text_c, label = "#f8d7da", "#dc3545", "#721c24", "Clear Card"
    elif val == "Chaos Card":
        bg, border, text_c, label = "#fff3e0", "#ff9800", "#e65100", "Chaos Event"
    elif card_type == "B":
        bg, border, text_c, label = "#f0f2f6", "#333333", "#111111", "Emission"
    elif card_type == "R":
        bg, border, text_c, label = "#ffe6e6", "#ff4b4b", "#c62828", "Capture"
    else:
        bg, border, text_c, label = "#ffffff", "#cccccc", "#333333", ""

    if size == "large":
        w, h, fs, l_fs = "100px", "130px", "18px", "11px"
    elif size == "medium":
        w, h, fs, l_fs = "75px", "95px", "14px", "10px"
    else:
        w, h, fs, l_fs = "55px", "70px", "10px", "8px"

    return f"""
    <div style="width:{w};height:{h};border:3px solid {border};border-radius:10px;background-color:{bg};
                display:inline-flex;flex-direction:column;align-items:center;justify-content:center;
                box-shadow:2px 3px 6px rgba(0,0,0,0.15);margin:4px;text-align:center;padding:2px;">
        <span style="font-size:{fs};font-weight:bold;color:{text_c};word-break:break-all;">{val}</span>
        <span style="font-size:{l_fs};color:#444;font-weight:bold;margin-top:2px;">{label}</span>
    </div>
    """


# ============================================================
# Initial Game State
# ============================================================
def initial_state(lang="EN"):
    T = LANG_TEXT[lang]
    return {
        "deck": new_deck(),
        "ap": 2,
        "turn": "Player 1",
        "p1_staging": [],
        "p1_scoring": [],
        "p1_hand": [],
        "p1_score": 0.0,
        "p2_staging": [],
        "p2_scoring": [],
        "p2_hand": [],
        "p2_score": 0.0,
        "active_tactical": None,
        "tactical_hand_idx": None,
        "tactical_player": None,
        "q_selected_own_card": None,
        "game_over": False,
        "logs": [T["game_start"]],
    }


# ============================================================
# Supabase helpers
# ============================================================
def load_game(room_code):
    res = supabase.table(TABLE).select("*").eq("room_code", room_code).execute()
    if res.data:
        return res.data[0]["state"]
    state = initial_state(st.session_state.lang)
    supabase.table(TABLE).insert({"room_code": room_code, "state": state}).execute()
    return state


def save_game(room_code, state):
    supabase.table(TABLE).update({"state": state}).eq("room_code", room_code).execute()


def add_log(state, msg):
    state["logs"].insert(0, msg)
    if len(state["logs"]) > 2000:
        state["logs"].pop()


# ============================================================
# Game Logic
# ============================================================
def check_game_over_and_settle(state, lang="EN"):
    T = LANG_TEXT[lang]
    POWER_CARDS = ["+1 AP", "All Swap", "Single Swap", "Push", "Steal", "Destroy", "Chaos Card"]
    if len(state["deck"]) == 0 and not state["game_over"]:
        p1_has_power = any(c[0] in POWER_CARDS for c in state["p1_hand"])
        p2_has_power = any(c[0] in POWER_CARDS for c in state["p2_hand"])
        both_staging_empty = (len(state["p1_staging"]) == 0) and (len(state["p2_staging"]) == 0)

        if (not p1_has_power and not p2_has_power) or both_staging_empty:
            state["game_over"] = True
            p1_s = state["p1_score"]
            p2_s = state["p2_score"]
            if p1_s > p2_s:
                winner = PLAYER_NAMES[lang]["Player 1"]
            elif p2_s > p1_s:
                winner = PLAYER_NAMES[lang]["Player 2"]
            else:
                winner = PLAYER_NAMES[lang]["Draw"]
            add_log(state, T["log_game_over"](p1_s, p2_s, winner))


def check_auto_same_color_match(state, is_p1, lang="EN"):
    """Auto-detect and score same-color pairs in the staging area."""
    T = LANG_TEXT[lang]
    staging = state["p1_staging"] if is_p1 else state["p2_staging"]
    scoring = state["p1_scoring"] if is_p1 else state["p2_scoring"]
    p_name = PLAYER_NAMES[lang]["Player 1"] if is_p1 else PLAYER_NAMES[lang]["Player 2"]

    if len(staging) >= 2:
        vals = [c[0] for c in staging if c[1] in ["B", "R"]]
        for v in set(vals):
            mc = [c for c in staging if c[0] == v and c[1] in ["B", "R"]]
            for color in ["B", "R"]:
                color_cards = [c for c in mc if c[1] == color]
                if len(color_cards) >= 2:
                    c1, c2 = color_cards[0], color_cards[1]
                    num_v = int(v)
                    if color == "B":
                        pts = -num_v * 1.0
                        if is_p1:
                            state["p1_score"] += pts
                        else:
                            state["p2_score"] += pts
                        add_log(state, T["log_double_black"](p_name, v, pts))
                    else:
                        pts = num_v * 1.5
                        if is_p1:
                            state["p1_score"] += pts
                        else:
                            state["p2_score"] += pts
                        add_log(state, T["log_double_red"](p_name, v, pts))

                    scoring.append([c1, c2])
                    new_st = [c for c in staging if c != c1 and c != c2]
                    if is_p1:
                        state["p1_staging"] = new_st
                    else:
                        state["p2_staging"] = new_st
                    return True
    return False


def _pair_score(item):
    """Calculate the score value of a scored pair (list of 2 cards)."""
    pts = 0.0
    for card in item:
        try:
            val_num = int(card[0])
        except (ValueError, TypeError):
            continue
        if card[1] == "B":
            pts += -val_num * 1.0
        elif card[1] == "R":
            pts += val_num * 1.5
    return pts


def auto_chaos_transfer(state, is_p1, lang="EN"):
    """
    Chaos Card effect:
    - Find the highest-scoring pair in the drawing player's scoring area.
    - Remove it from their scoring area and deduct the points.
    - Place those cards into the OPPONENT's staging area.
    - Trigger auto-match check on the opponent's staging area.
    If the drawing player's scoring area is empty, the chaos effect fails harmlessly.
    """
    T = LANG_TEXT[lang]
    scoring = state["p1_scoring"] if is_p1 else state["p2_scoring"]
    p_name = PLAYER_NAMES[lang]["Player 1"] if is_p1 else PLAYER_NAMES[lang]["Player 2"]
    opp_name = PLAYER_NAMES[lang]["Player 2"] if is_p1 else PLAYER_NAMES[lang]["Player 1"]

    st.toast(T["toast_chaos"], icon="🃏")
    time.sleep(2)

    # No scored pairs → chaos fizzles
    if not scoring:
        add_log(state, T["log_chaos_no_scoring"](p_name))
        return

    # Find the pair with the HIGHEST positive point value
    best_idx = max(range(len(scoring)), key=lambda i: _pair_score(scoring[i]))
    best_pts = _pair_score(scoring[best_idx])
    removed_pair = scoring.pop(best_idx)

    # Deduct those points from the drawing player
    if is_p1:
        state["p1_score"] -= best_pts
        state["p2_staging"].extend(removed_pair)
    else:
        state["p2_score"] -= best_pts
        state["p1_staging"].extend(removed_pair)

    add_log(state, T["log_chaos"](p_name, removed_pair, best_pts, opp_name))

    # Auto-match in the opponent's newly updated staging area
    check_auto_same_color_match(state, not is_p1, lang)


# ============================================================
# Room Selection
# ============================================================
if "room_code" not in st.session_state:
    st.session_state.room_code = None
if "my_player_is_p1" not in st.session_state:
    st.session_state.my_player_is_p1 = None

# Language selector — always visible at top-right
_lang_col1, _lang_col2 = st.columns([6, 1])
with _lang_col2:
    lang_choice = st.selectbox(
        LANG_TEXT["EN"]["lang_label"],
        options=["EN", "中文"],
        index=0 if st.session_state.lang == "EN" else 1,
        label_visibility="collapsed",
    )
    new_lang = "EN" if lang_choice == "EN" else "ZH"
    if new_lang != st.session_state.lang:
        st.session_state.lang = new_lang
        st.rerun()

lang = st.session_state.lang
T = LANG_TEXT[lang]

if st.session_state.room_code is None:
    with _lang_col1:
        st.title(T["page_title"])
    st.caption(T["room_caption"])
    room_input = st.text_input(T["room_input_label"])
    player_choice = st.radio(T["you_are"], ["Player 1", "Player 2"], horizontal=True)
    if st.button(T["join_create"], type="primary"):
        if room_input.strip():
            st.session_state.room_code = room_input.strip()
            st.session_state.my_player_is_p1 = player_choice == "Player 1"
            st.rerun()
        else:
            st.warning(T["room_warn"])
    st.stop()

room_code = st.session_state.room_code
my_player_is_p1 = st.session_state.my_player_is_p1
my_player_name = "Player 1" if my_player_is_p1 else "Player 2"
my_player_display = PLAYER_NAMES[lang]["Player 1"] if my_player_is_p1 else PLAYER_NAMES[lang]["Player 2"]

st_autorefresh(interval=2500, key="auto_refresh")

state = load_game(room_code)

# ============================================================
# Header Layout
# ============================================================
top_l, top_r = st.columns([4, 1])
with top_l:
    st.title(T["page_title"])
    st.caption(T["room_header"](room_code, my_player_display))
with top_r:
    st.selectbox(
        T["lang_label"],
        options=["EN", "中文"],
        index=0 if lang == "EN" else 1,
        key="lang_header",
        label_visibility="collapsed",
        on_change=lambda: None,  # handled by top selectbox
    )
    if st.button(T["leave_room"]):
        st.session_state.room_code = None
        st.session_state.my_player_is_p1 = None
        st.rerun()

can_act = (state["turn"] == my_player_name) and not state["game_over"]

deck_count = len(state["deck"])
st.markdown(
    f"""
    <div style="background:linear-gradient(135deg,#2c3e50,#4ca1af);padding:14px;border-radius:12px;
                text-align:center;color:white;margin-bottom:20px;box-shadow:0 4px 6px rgba(0,0,0,0.1);">
        <h3 style="margin:0;font-size:22px;">{T["deck_status"]}</h3>
        <p style="margin:6px 0 0 0;font-size:26px;font-weight:bold;color:#f1c40f;">{T["cards_remaining"](deck_count)}</p>
    </div>
    """,
    unsafe_allow_html=True,
)

top1, top2, top3, top4 = st.columns(4)
top1.metric(T["current_turn"], PLAYER_NAMES[lang].get(state["turn"], state["turn"]))
top2.metric(T["current_ap"], f"{state['ap']} / 2")
top3.metric(T["score_label"], f"P1: {state['p1_score']} | P2: {state['p2_score']}")
if top4.button(T["restart"], use_container_width=True):
    save_game(room_code, initial_state(lang))
    st.rerun()

# ============================================================
# Game Over Banner
# ============================================================
if state["game_over"]:
    p1_s = state["p1_score"]
    p2_s = state["p2_score"]
    if p1_s > p2_s:
        winner_text = PLAYER_NAMES[lang]["Player 1"]
        winner_score = p1_s
    elif p2_s > p1_s:
        winner_text = PLAYER_NAMES[lang]["Player 2"]
        winner_score = p2_s
    else:
        winner_text = PLAYER_NAMES[lang]["Draw"]
        winner_score = f"P1: {p1_s} / P2: {p2_s}"

    st.markdown(
        f"""
        <div style="background:linear-gradient(135deg,#f12711,#f5af19);padding:25px;border-radius:15px;
                    text-align:center;color:white;margin-bottom:25px;box-shadow:0 8px 16px rgba(0,0,0,0.3);">
            <h1 style="margin:0;font-size:36px;text-shadow:2px 2px 4px rgba(0,0,0,0.4);">🏆 {T["game_settled"]} 🏆</h1>
            <p style="margin:15px 0 0 0;font-size:28px;font-weight:bold;text-shadow:1px 1px 3px rgba(0,0,0,0.4);">
                {T["game_over_msg"](winner_text, winner_score)}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("---")

# ============================================================
# Split Screen Layout
# ============================================================
col_p1, col_p2 = st.columns(2)


def render_player_column(target_is_p1):
    p_name_key = "Player 1" if target_is_p1 else "Player 2"
    p_name_display = PLAYER_NAMES[lang]["Player 1"] if target_is_p1 else PLAYER_NAMES[lang]["Player 2"]
    is_mine = target_is_p1 == my_player_is_p1
    turn_is_this_player = (state["turn"] == p_name_key) and not state["game_over"]
    score = state["p1_score"] if target_is_p1 else state["p2_score"]
    staging = state["p1_staging"] if target_is_p1 else state["p2_staging"]
    scoring = state["p1_scoring"] if target_is_p1 else state["p2_scoring"]
    hand = state["p1_hand"] if target_is_p1 else state["p2_hand"]

    with st.container():
        label = T["p1_zone"] if target_is_p1 else T["p2_zone"]
        if is_mine:
            label += T["you_suffix"]
        st.markdown(f"### {label}")

        if turn_is_this_player:
            if is_mine:
                st.success(T["your_turn"](state["ap"]))
            else:
                st.info(T["opp_turn"])
        else:
            st.caption(T["current_score"](score))

        # ── Action buttons (only for the active player on their turn) ──
        if is_mine and can_act:
            b1, b2, b3 = st.columns(3)
            with b1:
                if st.button(T["draw_card"], key=f"draw_{p_name_key}"):
                    if state["ap"] > 0 and len(state["deck"]) > 0:
                        card = state["deck"].pop(0)
                        state["ap"] -= 1
                        if card[1] in ["B", "R"]:
                            staging.append(card)
                            add_log(state, T["log_draw_number"](p_name_display, card[0], card[1]))
                            check_auto_same_color_match(state, target_is_p1, lang)
                        elif card[0] == "Chaos Card":
                            auto_chaos_transfer(state, target_is_p1, lang)
                        else:
                            hand.append(card)
                            add_log(state, T["log_draw_tactical"](p_name_display, card[0]))
                        check_game_over_and_settle(state, lang)
                        save_game(room_code, state)
                        st.rerun()
                    else:
                        st.warning(T["draw_warn"])

            with b2:
                if st.button(T["neutralize"], key=f"neutral_{p_name_key}"):
                    if len(staging) >= 2:
                        vals = [c[0] for c in staging if c[1] in ["B", "R"]]
                        matched = False
                        for v in set(vals):
                            mc = [c for c in staging if c[0] == v and c[1] in ["B", "R"]]
                            b_cards = [c for c in mc if c[1] == "B"]
                            r_cards = [c for c in mc if c[1] == "R"]
                            if b_cards and r_cards:
                                c1, c2 = b_cards[0], r_cards[0]
                                scoring.append([c1, c2])
                                staging.remove(c1)
                                staging.remove(c2)
                                add_log(state, T["log_neutral"](p_name_display, v))
                                matched = True
                                break
                        if matched:
                            save_game(room_code, state)
                            st.rerun()
                        else:
                            st.warning(T["neutral_warn_no_pair"])
                    else:
                        st.warning(T["neutral_warn_few"])

            with b3:
                if st.button(T["end_turn"], key=f"end_{p_name_key}"):
                    state["ap"] = 2
                    state["turn"] = "Player 2" if target_is_p1 else "Player 1"
                    next_display = PLAYER_NAMES[lang]["Player 2"] if target_is_p1 else PLAYER_NAMES[lang]["Player 1"]
                    state["active_tactical"] = None
                    state["tactical_player"] = None
                    state["q_selected_own_card"] = None
                    add_log(state, T["log_end_turn"](next_display))
                    save_game(room_code, state)
                    st.rerun()

        st.markdown("---")

        # ── 1. Hand Cards ──
        st.markdown(T["hand_title"](p_name_display))
        if hand:
            cols_num = max(1, min(len(hand), 4))
            h_cols = st.columns(cols_num)
            for h_idx, hcard in enumerate(hand):
                with h_cols[h_idx % 4]:
                    st.markdown(render_card_html(hcard[0], hcard[0], size="large"), unsafe_allow_html=True)
            
            # 判定当前手牌是否为功能卡 (Power Card)
                    is_power_card = hcard[0] in ["+1 AP", "All Swap", "Single Swap", "Push", "Steal", "Destroy", "Chaos Card"]

            # 情况 A：如果这是我自己的手牌区，且轮到我的回合，渲染「出牌」按钮
                    if is_mine and can_act:
                        if st.button(T["play_btn"](h_idx), key=f"play_{p_name_key}_{h_idx}"):
                            ctype = hcard[0]

                    # +1 AP — no AP cost, immediate effect
                            if ctype == "+1 AP":
                                hand.pop(h_idx)
                                state["ap"] += 1
                                add_log(state, T["log_plus_ap"](p_name_display))
                                check_game_over_and_settle(state, lang)
                                save_game(room_code, state)
                                st.rerun()

                    # All Swap — costs 1 AP, swaps both staging areas
                            elif ctype == "All Swap":
                                if state["ap"] > 0:
                                    hand.pop(h_idx)
                                    state["ap"] -= 1
                                    state["p1_staging"], state["p2_staging"] = (
                                        state["p2_staging"],
                                        state["p1_staging"],
                                    )
                                    add_log(state, T["log_all_swap"](p_name_display))
                                    check_auto_same_color_match(state, True, lang)
                                    check_auto_same_color_match(state, False, lang)
                                    check_game_over_and_settle(state, lang)
                                    save_game(room_code, state)
                                    st.rerun()
                                else:
                                    st.warning(T["ap_warn"])

                    # Single Swap — costs 1 AP, two-step selection
                            elif ctype == "Single Swap":
                                if state["ap"] > 0:
                                    state["active_tactical"] = "Single Swap"
                                    state["tactical_hand_idx"] = h_idx
                                    state["tactical_player"] = target_is_p1
                                    state["q_selected_own_card"] = None
                                    add_log(state, T["log_single_swap_prepare"](p_name_display))
                                    save_game(room_code, state)
                                    st.rerun()
                                else:
                                    st.warning(T["ap_warn"])

                    # Push — costs 1 AP, send own staging card to opponent
                            elif ctype == "Push":
                               if state["ap"] > 0:
                                    state["active_tactical"] = "Push"
                                    state["tactical_hand_idx"] = h_idx
                                    state["tactical_player"] = target_is_p1
                                    add_log(state, T["log_push_prepare"](p_name_display))
                                    save_game(room_code, state)
                                    st.rerun()
                                else:
                                    st.warning(T["ap_warn"])

                    # Steal — costs 1 AP
                            elif ctype == "Steal":
                                if state["ap"] > 0:
                                    state["active_tactical"] = "Steal"
                                    state["tactical_hand_idx"] = h_idx
                                    state["tactical_player"] = target_is_p1
                                    add_log(state, f"🎯 {p_name_display} preparing Steal: select a power card from opponent's hand.")
                                    save_game(room_code, state)
                                    st.rerun()
                                else:
                                    st.warning("⚠️ Insufficient AP!")

                    # Destroy — costs 1 AP
                            elif ctype == "Destroy":
                                if state["ap"] > 0:
                                    state["active_tactical"] = "Destroy"
                                    state["tactical_hand_idx"] = h_idx
                                    state["tactical_player"] = target_is_p1
                                    add_log(state, f"🎯 {p_name_display} preparing Destroy: select a power card from opponent's hand to destroy.")
                                    save_game(room_code, state)
                                    st.rerun()
                                else:
                                    st.warning("⚠️ Insufficient AP!")

            # 情况 B：如果这是【对手】的手牌区，且我是行动玩家（正处于战术结算中），且该牌是功能卡
                    elif can_act and not is_mine and is_power_card:
                
                # ── 偷取对手功能牌 ──
                        if state["active_tactical"] == "Steal" and target_is_p1 != state["tactical_player"]:
                            if st.button(T["steal_btn"](h_idx), key=f"steal_hand_{target_is_p1}_{h_idx}"):
                                thief_is_p1 = state["tactical_player"]
                        # 扣除自己手上的 Steal 卡和 1 AP
                                my_hand = state["p1_hand"] if thief_is_p1 else state["p2_hand"]
                                my_hand.pop(state["tactical_hand_idx"])
                                state["ap"] -= 1
                        
                        # 偷取对方的功能卡，放入自己的手牌
                                stolen_card = hand.pop(h_idx)
                                my_hand.append(stolen_card)
                        
                                add_log(state, f"🕵️ Player {'1' if thief_is_p1 else '2'} stole power card [{stolen_card[0]}] from opponent's hand!")
                                state["active_tactical"] = None
                                state["tactical_hand_idx"] = None
                                state["tactical_player"] = None
                                check_game_over_and_settle(state, lang)
                                save_game(room_code, state)
                                st.rerun()

                # ── 销毁对手功能牌 ──
                    elif state["active_tactical"] == "Destroy" and target_is_p1 != state["tactical_player"]:
                            if st.button(T["destroy_btn"](h_idx), key=f"destroy_hand_{target_is_p1}_{h_idx}"):
                                destroyer_is_p1 = state["tactical_player"]
                        # 扣除自己手上的 Destroy 卡和 1 AP
                                my_hand = state["p1_hand"] if destroyer_is_p1 else state["p2_hand"]
                                my_hand.pop(state["tactical_hand_idx"])
                                state["ap"] -= 1
                        
                        # 直接销毁对方手里的功能卡
                                destroyed_card = hand.pop(h_idx)
                        
                                add_log(state, f"💣 Player {'1' if destroyer_is_p1 else '2'} destroyed opponent's power card [{destroyed_card[0]}]!")
                                state["active_tactical"] = None
                                state["tactical_hand_idx"] = None
                                state["tactical_player"] = None
                                check_game_over_and_settle(state, lang)
                                save_game(room_code, state)
                                st.rerun()
            else:
                st.caption(T["hand_empty"])

        st.markdown("---")

        # ── 2. Staging Area ──
        st.markdown(T["staging_title"](p_name_display))

        # Contextual hint banners
        if state["active_tactical"] == "Push" and can_act and target_is_p1 == state["tactical_player"]:
            st.info(T["push_hint"])
        elif state["active_tactical"] == "Single Swap" and can_act:
            if state["q_selected_own_card"] is None and target_is_p1 == state["tactical_player"]:
                st.info(T["single_swap_hint_own"])
            elif state["q_selected_own_card"] is not None and target_is_p1 != state["tactical_player"]:
                st.info(T["single_swap_hint_opp"])
        elif state["active_tactical"] == "Steal" and can_act and target_is_p1 != state["tactical_player"]:
            st.info(T["steal_hint"])
        elif state["active_tactical"] == "Destroy" and can_act and target_is_p1 != state["tactical_player"]:
            st.info(T["destroy_hint"])

        if staging:
            cols_num = max(1, min(len(staging), 4))
            st_cols = st.columns(cols_num)
            for idx, card in enumerate(staging):
                with st_cols[idx % 4]:
                    st.markdown(render_card_html(card[0], card[1], size="medium"), unsafe_allow_html=True)

                    # ── Push button (own staging area) ──
                    if (
                        state["active_tactical"] == "Push"
                        and can_act
                        and target_is_p1 == state["tactical_player"]
                    ):
                        if st.button(T["push_btn"](idx), key=f"push_k_{target_is_p1}_{idx}"):
                            h_idx = state["tactical_hand_idx"]
                            (state["p1_hand"] if target_is_p1 else state["p2_hand"]).pop(h_idx)
                            state["ap"] -= 1
                            pushed_card = staging.pop(idx)
                            if target_is_p1:
                                state["p2_staging"].append(pushed_card)
                                add_log(state, T["log_push_p1"](pushed_card))
                                check_auto_same_color_match(state, False, lang)
                            else:
                                state["p1_staging"].append(pushed_card)
                                add_log(state, T["log_push_p2"](pushed_card))
                                check_auto_same_color_match(state, True, lang)
                            state["active_tactical"] = None
                            state["tactical_hand_idx"] = None
                            state["tactical_player"] = None
                            check_game_over_and_settle(state, lang)
                            save_game(room_code, state)
                            st.rerun()

                    # ── Single Swap step-1: select own card ──
                    elif (
                        state["active_tactical"] == "Single Swap"
                        and can_act
                        and state["q_selected_own_card"] is None
                        and target_is_p1 == state["tactical_player"]
                    ):
                        if st.button(T["select_btn"](idx), key=f"q_own_{target_is_p1}_{idx}"):
                            state["q_selected_own_card"] = [target_is_p1, idx, card]
                            add_log(state, T["log_single_swap_locked"](p_name_display, card))
                            save_game(room_code, state)
                            st.rerun()

                    # ── Single Swap step-2: select opponent card ──
                    elif (
                        state["active_tactical"] == "Single Swap"
                        and can_act
                        and state["q_selected_own_card"] is not None
                        and target_is_p1 != state["tactical_player"]
                    ):
                        if st.button(T["swap_btn"](idx), key=f"q_target_{target_is_p1}_{idx}"):
                            own_p_is_p1, own_idx, own_card = state["q_selected_own_card"]
                            h_idx = state["tactical_hand_idx"]
                            (state["p1_hand"] if own_p_is_p1 else state["p2_hand"]).pop(h_idx)
                            state["ap"] -= 1
                            target_card = staging[idx]
                            if own_p_is_p1:
                                state["p1_staging"][own_idx] = target_card
                                state["p2_staging"][idx] = own_card
                                add_log(state, T["log_single_swap_p1"](own_card, target_card))
                            else:
                                state["p2_staging"][own_idx] = target_card
                                state["p1_staging"][idx] = own_card
                                add_log(state, T["log_single_swap_p2"](own_card, target_card))
                            state["active_tactical"] = None
                            state["tactical_hand_idx"] = None
                            state["tactical_player"] = None
                            state["q_selected_own_card"] = None
                            check_auto_same_color_match(state, True, lang)
                            check_auto_same_color_match(state, False, lang)
                            check_game_over_and_settle(state, lang)
                            save_game(room_code, state)
                            st.rerun()
        else:
            st.caption(T["staging_empty"])

        st.markdown("---")

        # ── 3. Scored Area ──
        st.markdown(T["scored_title"](p_name_display, score))
        if scoring:
            for idx, s_item in enumerate(scoring):
                st.markdown(
                    f"<span style='font-size:14px;'>{T['pair_label'](idx)}</span>",
                    unsafe_allow_html=True,
                )
                if len(s_item) == 2:
                    sc1, sc2 = st.columns(2)
                    with sc1:
                        st.markdown(render_card_html(s_item[0][0], s_item[0][1], size="small"), unsafe_allow_html=True)
                    with sc2:
                        st.markdown(render_card_html(s_item[1][0], s_item[1][1], size="small"), unsafe_allow_html=True)
                else:
                    st.markdown(render_card_html(s_item[0][0], s_item[0][1], size="small"), unsafe_allow_html=True)
        else:
            st.caption(T["scored_empty"])


with col_p1:
    render_player_column(True)

with col_p2:
    render_player_column(False)

st.markdown("---")
st.subheader(T["logs_title"])
log_container = st.container(height=180)
with log_container:
    for lg in state["logs"]:
        st.markdown(f"- {lg}")
