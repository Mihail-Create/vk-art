# -*- coding: utf-8 -*-
import sys
import os
import json
import asyncio
from datetime import datetime, timedelta

sys.path.insert(0, r"C:\Users\user\Desktop\vk-art-bot")

import bot

passed = 0
failed = 0

def assert_eq(cond, desc):
    global passed, failed
    if cond:
        passed += 1
        print(f"  ✅ PASS: {desc}")
    else:
        failed += 1
        print(f"  ❌ FAIL: {desc}")

print("====================================================")
print("🚀 FULL INTEGRATED PIPELINE TEST SUITE (VK ART BOT)")
print("====================================================")

# TEST 1: Tariffs
print("\n--- TEST SUITE 1: Guild Tariffs & Discounts ---")
t_dhatelle = bot.get_customer_tariff("Dha't'elle")
assert_eq(t_dhatelle["type"] == "free" and t_dhatelle["price"] == 0, "Dha't'elle gets 100% free tariff (0 RUB)")

t_7rota1 = bot.get_customer_tariff("7-я рота")
assert_eq(t_7rota1["type"] == "free" and t_7rota1["price"] == 0, "7-я рота gets 100% free tariff (0 RUB)")

t_7rota2 = bot.get_customer_tariff("Седьмая рота")
assert_eq(t_7rota2["type"] == "free" and t_7rota2["price"] == 0, "Седьмая рота gets 100% free tariff (0 RUB)")

t_zakat1 = bot.get_customer_tariff("Zакат")
assert_eq(t_zakat1["type"] == "ally" and t_zakat1["price"] == 250, "Zакат gets 50% ally discount (250 RUB)")

t_zakat2 = bot.get_customer_tariff("Закат")
assert_eq(t_zakat2["type"] == "ally" and t_zakat2["price"] == 250, "Закат gets 50% ally discount (250 RUB)")

t_defenders = bot.get_customer_tariff("Zащитники")
assert_eq(t_defenders["type"] == "ally" and t_defenders["price"] == 250, "Zащитники gets 50% ally discount (250 RUB)")

t_kb = bot.get_customer_tariff("Красное&Белое")
assert_eq(t_kb["type"] == "ally" and t_kb["price"] == 250, "Красное&Белое gets 50% ally discount (250 RUB)")

t_scavengers = bot.get_customer_tariff("Донные Падальщики")
assert_eq(t_scavengers["type"] == "ally" and t_scavengers["price"] == 250, "Донные Падальщики gets 50% ally discount (250 RUB)")

t_enemy = bot.get_customer_tariff("Carpe Diem")
assert_eq(t_enemy["blocked"] is True, "Carpe Diem enemy guild is blocked")

t_neutral = bot.get_customer_tariff("Любая Другая")
assert_eq(t_neutral["type"] == "standard" and t_neutral["price"] == 500, "Neutral guild gets standard price (500 RUB)")

# TEST 2: Nickname & Guild extraction from ToR profiles
print("\n--- TEST SUITE 2: Nickname & Guild Extraction ---")
profile_sample_1 = """
📜 Статус
Тазир
🏰 Dha't'elle | ур. 45 | Боец
[id12345678|Тазир]
"""
extracted_nick1 = bot.extract_nickname_from_profile(profile_sample_1, 12345678)
assert_eq(extracted_nick1 == "Тазир", f"Extracted nickname from [id12345678|Тазир]: got {extracted_nick1}")

profile_sample_2 = """
📜 Статус
🔹 Ярость всегда рядом
🏰 Dha't'elle | ур. 80 | Мастер
"""
extracted_nick2 = bot.extract_nickname_from_profile(profile_sample_2, 208825850)
assert_eq(extracted_nick2 == "Ярость всегда рядом", f"Extracted nickname from header: got {extracted_nick2}")

# Mock Classes
class MockForwarded:
    def __init__(self, from_id, text, date_offset_sec=0):
        self.from_id = from_id
        self.text = text
        self.date = int((datetime.now() - timedelta(seconds=date_offset_sec)).timestamp())

class MockMessage:
    def __init__(self, from_id, text, fwd_messages=None, reply_message=None):
        self.from_id = from_id
        self.peer_id = from_id
        self.text = text
        self.fwd_messages = fwd_messages or []
        self.reply_message = reply_message
        self.attachments = []
        self.answers = []

    async def answer(self, text, keyboard=None):
        self.answers.append(text)

# TEST 3: ToR Storefront Payment Verification
print("\n--- TEST SUITE 3: ToR Payment Log Verification ---")

valid_tor_log = "Вы успешно передали 27000 ядер игроку [id208825850|Ярость всегда рядом]."
fwd_valid = MockForwarded(from_id=-bot.TOR_BOT_GROUP_ID, text=valid_tor_log)
msg_with_valid_fwd = MockMessage(from_id=777123, text="", fwd_messages=[fwd_valid])

trans_msg, trans_match = bot.get_customer_tor_transfer_log(msg_with_valid_fwd)
assert_eq(trans_msg is not None and trans_match is not None, "Valid forwarded ToR log recognized from -TOR_BOT_GROUP_ID")

msg_spoofed = MockMessage(from_id=777123, text="Вы успешно передали 27000 ядер игроку [id208825850|Ярость всегда рядом].")
trans_spoof_msg, trans_spoof_match = bot.get_customer_tor_transfer_log(msg_spoofed)
assert_eq(trans_spoof_msg is None, "Spoofed direct message without ToR bot forward is rejected")

wrong_recip_log = "Вы успешно передали 27000 ядер игроку [id999999|Другой Игрок]."
fwd_wrong = MockForwarded(from_id=-bot.TOR_BOT_GROUP_ID, text=wrong_recip_log)
msg_wrong = MockMessage(from_id=777123, text="", fwd_messages=[fwd_wrong])
w_msg, w_match = bot.get_customer_tor_transfer_log(msg_wrong)

async def test_payment_execution():
    payer_id = 998877
    payer_msg = MockMessage(from_id=payer_id, text="", fwd_messages=[fwd_valid])
    await bot.handle_tor_store_payment(payer_msg, fwd_valid, trans_match)
    assert_eq(any("успешно активирована" in ans for ans in payer_msg.answers), "Payment handler activated 30-day storefront in bot")

    # Check store_subscriptions.json
    sub_path = os.path.join(r"C:\Users\user\Desktop\vk-art-bot\miniapp", "store_subscriptions.json")
    with open(sub_path, "r", encoding="utf-8") as f:
        subs = json.load(f)
    found_sub = any(s.get("userId") == payer_id for s in subs)
    assert_eq(found_sub, "Storefront subscription written and synced to miniapp/store_subscriptions.json")

    # Replay protection
    payer_msg_replay = MockMessage(from_id=payer_id, text="", fwd_messages=[fwd_valid])
    await bot.handle_tor_store_payment(payer_msg_replay, fwd_valid, trans_match)
    assert_eq(any("уже был активирован" in ans for ans in payer_msg_replay.answers), "Anti-replay protection rejected used payment transfer log")

# TEST 4: Clan Chat Status Registration
async def test_clan_status_sync():
    print("\n--- TEST SUITE 4: Clan Chat Status Auto-Registration ---")
    status_card_text = (
        "📜 Статус\n"
        "[id554433|СеверныйВолк]\n"
        "🏰 Dha't'elle | Ур. 65 | Ветеран"
    )
    clan_msg = MockMessage(
        from_id=554433,
        text=status_card_text,
    )
    clan_msg.peer_id = 2000000001

    await bot.handle_clan_chat(clan_msg)
    user_key = "554433"
    assert_eq(user_key in bot.clan_members, "Clan member saved to clan_members from status card")
    assert_eq(bot.clan_members[user_key]["nickname"] == "СеверныйВолк", "Clan member nickname saved accurately")
    assert_eq(user_key in bot.customer_profiles, "Clan member automatically registered in customer_profiles")
    assert_eq(bot.customer_profiles[user_key]["payment_type"] == "free", "Clan member granted 100% free art tariff")

# TEST 5: Mini App Art Order Pipeline
async def test_art_order_pipeline():
    print("\n--- TEST SUITE 5: Art Order Dispatch & Completion ---")
    order_data = {
        "race": "Эльф",
        "gender": "Мужской",
        "style": "Аниме",
        "mood": "Боевой",
        "description": "Герой в сияющих доспехах с мечом",
        "guild": "Dha't'elle",
        "payment_type": "free",
        "price": 0,
        "references": []
    }
    customer_id = 554433
    order_id = "test_art_ord_123456"
    bot.order_records[order_id] = {
        "customer_id": customer_id,
        "status": "waiting",
        "race": order_data["race"],
        "style": order_data["style"],
        "guild": order_data["guild"],
        "payment_type": "free",
        "price": 0,
        "description": order_data["description"],
        "references": [],
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "result_sent": False
    }

    # Artist accepts order
    artist_id = 888999
    bot.order_records[order_id]["status"] = "in_progress"
    bot.order_records[order_id]["artist_id"] = artist_id

    # Artist delivers result
    artist_msg = MockMessage(
        from_id=artist_id,
        text=f"Готово! Результат заказа {order_id[:8]} выполнен в лучшем виде."
    )
    artist_msg.peer_id = bot.ARTIST_CHAT_ID
    artist_msg.attachments = []

    # Mock API request for customer delivery verification
    sent_to_customer = []
    orig_request = bot.bot.api.request
    async def mock_request(method, data=None):
        if method == "messages.send":
            sent_to_customer.append(data)
            return {"response": 12345}
        if method == "users.get":
            return {"response": [{"id": 888999, "first_name": "Тест", "last_name": "Художник"}]}
        return await orig_request(method, data)
    bot.bot.api.request = mock_request

    try:
        await bot.forward_artist_result(artist_msg)
        assert_eq(bot.order_records[order_id]["status"] == "completed", "Order status transitioned to completed")
        assert_eq(bot.order_records[order_id]["result_sent"] is True, "Order marked as result_sent")
        assert_eq(len(sent_to_customer) > 0, "Completed art result successfully delivered to customer PM")
    finally:
        bot.bot.api.request = orig_request

asyncio.run(test_payment_execution())
asyncio.run(test_clan_status_sync())
asyncio.run(test_art_order_pipeline())

print(f"\n====================================================")
print(f"INTEGRATION TEST RESULTS: {passed} PASSED, {failed} FAILED")
print(f"====================================================")
if failed > 0:
    sys.exit(1)
