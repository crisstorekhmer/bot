import json
import urllib.request
import urllib.parse
import os
import time

TOKEN = "8871000948:AAHVMXrlxdXUZLR_CAXqDMEVbVeCx5bVbH0"
URL = f"https://api.telegram.org/bot{TOKEN}"

user_data = {}
message_map = {}          # កត់ត្រា message_id រវាង Admin និងអតិថិជន
pending_status_msg = {}   # កត់ត្រា message_id របស់សារទី១ (កំពុងផ្ទៀងផ្ទាត់) តាម chat_id

def send_message(chat_id, text, reply_markup=None):
    data = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    if reply_markup:
        data["reply_markup"] = reply_markup
    data = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(f"{URL}/sendMessage", data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        print("Error send_message:", e)
        return None

def delete_message(chat_id, message_id):
    data = json.dumps({"chat_id": chat_id, "message_id": message_id}).encode("utf-8")
    req = urllib.request.Request(f"{URL}/deleteMessage", data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        print("Error delete_message:", e)
        return None

def forward_message(chat_id, from_chat_id, message_id):
    data = {"chat_id": chat_id, "from_chat_id": from_chat_id, "message_id": message_id}
    data = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(f"{URL}/forwardMessage", data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            res = json.loads(response.read().decode())
            if "result" in res:
                sent_msg_id = res["result"]["message_id"]
                message_map[sent_msg_id] = from_chat_id
            return res
    except Exception as e:
        print("Error forwarding:", e)
        return None

def send_photo_local(chat_id, image_path, caption):
    if not os.path.exists(image_path):
        print(f"⚠️ អាសយដ្ឋានខុស៖ រកមិនឃើញហ្វាលរូបភាពឈ្មោះ '{image_path}' ទេ!")
        res = send_message(chat_id, caption + "\n\n⚠️ (Bot រកមិនឃើញហ្វាល QR Code ទេ!)")
        return res
    
    try:
        url = f"{URL}/sendPhoto"
        boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
        with open(image_path, "rb") as f:
            image_data = f.read()
        body = (
            f"--{boundary}\r\n" f'Content-Disposition: form-data; name="chat_id"\r\n\r\n{chat_id}\r\n'
            f"--{boundary}\r\n" f'Content-Disposition: form-data; name="caption"\r\n\r\n{caption}\r\n'
            f"--{boundary}\r\n" f'Content-Disposition: form-data; name="parse_mode"\r\n\r\nMarkdown\r\n'
            f"--{boundary}\r\n" f'Content-Disposition: form-data; name="photo"; filename="logoqrcode.jpeg"\r\n'
            f"Content-Type: image/jpeg\r\n\r\n"
        ).encode("utf-8") + image_data + f"\r\n--{boundary}--\r\n".encode("utf-8")
        req = urllib.request.Request(url, data=body, headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
        with urllib.request.urlopen(req, timeout=15) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        print("Error sending photo:", e)
        return None

def get_updates(offset=None):
    url = f"{URL}/getUpdates?timeout=30"
    if offset: url += f"&offset={offset}"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=35) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        print("Error get_updates (បណ្តាញមានបញ្ហា ឬដាច់ការតភ្ជាប់បណ្តោះអាសន្ន):", e)
        time.sleep(3)  # រង់ចាំ ៣ វិនាទីសឹមតភ្ជាប់ឡើងវិញ
        return None

print("🤖 Bot កំពុងដំណើរការ និងស្តាប់រាល់សារទាំងអស់...")
last_update_id = None
ADMIN_CHAT_ID = "8011652186"

while True:
    updates = get_updates(last_update_id)
    if updates and "result" in updates:
        for update in updates["result"]:
            last_update_id = update["update_id"] + 1
            message = update.get("message", {})
            chat_id = message.get("chat", {}).get("id")
            
            if not chat_id: continue

            # ករណី Admin Reply សារ
            if str(chat_id) == str(ADMIN_CHAT_ID) and "reply_to_message" in message:
                replied_msg = message["reply_to_message"]
                replied_msg_id = replied_msg.get("message_id")
                
                target_chat_id = message_map.get(replied_msg_id)

                if not target_chat_id:
                    for text_source in [replied_msg.get("text", ""), replied_msg.get("caption", "")]:
                        if "Telegram ID:" in text_source:
                            try:
                                line = [l for l in text_source.split("\n") if "Telegram ID:" in l][0]
                                target_chat_id = int(line.split("`")[1])
                                break
                            except:
                                pass

                if target_chat_id:
                    if target_chat_id in pending_status_msg:
                        delete_message(target_chat_id, pending_status_msg[target_chat_id])
                        del pending_status_msg[target_chat_id]

                    success_text = (
                        "🎉 *អបអរសាទរ!* ការបញ្ជាទិញរបស់អ្នកត្រូវបាន **បំពេញជោគជ័យ** រួចរាល់ហើយ!\n"
                        "អរគុណសម្រាប់ការប្រើប្រាស់សេវាកម្មយើងខ្ញុំ 🙏✨"
                    )
                    restart_menu = {
                        "keyboard": [[{"text": "🚀 Start Bot"}]],
                        "resize_keyboard": True,
                    }
                    send_message(target_chat_id, success_text, reply_markup=restart_menu)
                    send_message(ADMIN_CHAT_ID, f"✅ បានផ្ញើសារជោគជ័យ និងលុបសាររង់ចាំរបស់អតិថិជន (ID: {target_chat_id}) រួចរាល់!")
                else:
                    send_message(ADMIN_CHAT_ID, "⚠️ រកមិនឃើញ Telegram ID របស់អតិថិជនទេ សូមព្យាយាម Reply លើសារព័ត៌មានអតិថិជន។")
                continue

            # ១. ករណីអតិថិជនផ្ញើរូបភាពវិក្កយបត្រ (Receipt)
            if "photo" in message:
                print(f"📥 ទទួលបានវិក្កយបត្រពី chat_id: {chat_id}")
                message_id = message["message_id"]
                
                forward_message(ADMIN_CHAT_ID, chat_id, message_id)
                user_data.pop(chat_id, None)
                
                restart_menu = {
                    "keyboard": [[{"text": "🚀 Start Bot"}]],
                    "resize_keyboard": True,
                }
                res_status = send_message(
                    chat_id,
                    "✅ *ទទួលបានវិក្កយបត្ររបស់អ្នកហើយ!*\n⏳ ប្រព័ន្ធកំពុងផ្ទៀងផ្ទាត់ សូមរង់ចាំបន្តិច...\n\n👇 ចុចប៊ូតុងខាងក្រោមដើម្បីចាប់ផ្តើមទិញម្តងទៀត៖",
                    reply_markup=restart_menu
                )
                
                if res_status and "result" in res_status:
                    pending_status_msg[chat_id] = res_status["result"]["message_id"]

            # ២. ករណីអតិថិជនផ្ញើសារអត្ថបទធម្មតា ឬចុចប៊ូតុង
            elif "text" in message:
                text = message["text"]
                print(f"💬 សារចូលពី {chat_id}: {text}")

                main_menu = {
                    "keyboard": [
                        [{"text": "🔥 Free Fire"}, {"text": "⚡ Mobile Legends"}],
                        [{"text": "👑 Honor of Kings"}, {"text": "🎯 PUBG Mobile"}],
                        [{"text": "🩸 Blood Strike"}, {"text": "🚗 Car Parking"}],
                    ],
                    "resize_keyboard": True,
                }

                if text in ["/start", "🚀 Start Bot"]:
                    user_data.pop(chat_id, None)
                    send_message(
                        chat_id,
                        "🌟 *សួស្តី! សូមស្វាគមន៍មកកាន់ប្រព័ន្ធ Top Up អូតូម៉ាតិច* 🌟\n\n👇 សូមជ្រើសរើសហ្គេមនៅប៊ូតុងខាងក្រោម៖",
                        reply_markup=main_menu,
                    )

                # ==========================================
                # 1. កញ្ចប់តម្លៃ FREE FIRE
                # ==========================================
                elif text == "🔥 Free Fire":
                    ff_menu = {
                        "keyboard": [
                            [{"text": "💎 25 Diamonds - $0.28"}, {"text": "💎 100 Diamonds - $0.97"}],
                            [{"text": "💎 310 Diamonds - $2.95"}, {"text": "💎 520 Diamonds - $4.78"}],
                            [{"text": "💎 1060 Diamonds - $9.34"}, {"text": "💎 2180 Diamonds - $19.82"}],
                            [{"text": "💎 5600 Diamonds - $48.56"}, {"text": "💎 11500 Diamonds - $96.60"}],
                            [{"text": "👑 Monthly Pass - $7.69"}, {"text": "🔥 Weekly Pass - $1.69"}],
                            [{"text": "⚡ Weekly Lite - $0.44"}, {"text": "📦 3 កាត (3in1) - $9.79"}],
                            [{"text": "👑 Monthly Pass x2 - $15.79"}, {"text": "🔥 Weekly Pass x2 - $3.38"}],
                            [{"text": "👑 Monthly Pass x3 - $23.46"}, {"text": "🔥 Weekly Pass x3 - $5.17"}],
                            [{"text": "👑 Monthly Pass x4 - $31.18"}, {"text": "🔥 Weekly Pass x4 - $6.99"}],
                            [{"text": "👑 Monthly Pass x5 - $38.95"}, {"text": "🔥 Weekly Pass x5 - $8.65"}],
                            [{"text": "👑 Monthly Pass x10 - $77.20"}, {"text": "🔥 Weekly Pass x10 - $16.90"}],
                            [{"text": "🔙 ត្រឡប់ក្រោយ"}],
                        ],
                        "resize_keyboard": True,
                    }
                    send_message(chat_id, "🔥 *Free Fire* - សូមជ្រើសរើសកញ្ចប់ពេជ្រ ឬ Membership ខាងក្រោម៖", reply_markup=ff_menu)

                # ==========================================
                # 2. កញ្ចប់តម្លៃ MOBILE LEGENDS
                # ==========================================
                elif text == "⚡ Mobile Legends":
                    ml_menu = {
                        "keyboard": [
                            [{"text": "💎 86 Diamonds - $1.30"}, {"text": "💎 172 Diamonds - $2.55"}],
                            [{"text": "💎 257 Diamonds - $3.69"}, {"text": "💎 344 Diamonds - $4.99"}],
                            [{"text": "💎 429 Diamonds - $6.39"}, {"text": "💎 514 Diamonds - $7.44"}],
                            [{"text": "💎 600 Diamonds - $8.58"}, {"text": "💎 706 Diamonds - $9.79"}],
                            [{"text": "💎 792 Diamonds - $11.99"}, {"text": "💎 878 Diamonds - $12.46"}],
                            [{"text": "💎 963 Diamonds - $13.89"}, {"text": "💎 1050 Diamonds - $14.89"}],
                            [{"text": "💎 1136 Diamonds - $15.89"}, {"text": "💎 1222 Diamonds - $16.99"}],
                            [{"text": "💎 1412 Diamonds - $19.89"}, {"text": "💎 1584 Diamonds - $21.99"}],
                            [{"text": "💎 1756 Diamonds - $24.89"}, {"text": "💎 1928 Diamonds - $26.96"}],
                            [{"text": "💎 2195 Diamonds - $30.12"}, {"text": "💎 2539 Diamonds - $34.69"}],
                            [{"text": "💎 2901 Diamonds - $39.79"}, {"text": "💎 3688 Diamonds - $49.25"}],
                            [{"text": "💎 4394 Diamonds - $58.99"}, {"text": "💎 5532 Diamonds - $74.15"}],
                            [{"text": "💎 6238 Diamonds - $84.79"}, {"text": "💎 6944 Diamonds - $94.59"}],
                            [{"text": "💎 7727 Diamonds - $104.29"}, {"text": "💎 9288 Diamonds - $124.69"}],
                            [{"text": "💎 10080 Diamonds - $134.79"}, {"text": "💎 10700 Diamonds - $140.99"}],
                            [{"text": "📦 Weekly Pass - $1.53"}, {"text": "⭐ Elite Weekly - $0.92"}],
                            [{"text": "🌟 Epic Monthly - $4.19"}, {"text": "🛡️ Twilight Pass - $8.42"}],
                            [{"text": "📦 Weekly Pass x 2 - $3.40"}, {"text": "📦 Weekly Pass x3 - $4.79"}],
                            [{"text": "📦 Weekly Pass x4 - $6.39"}, {"text": "📦 Weekly Pass x5 - $7.85"}],
                            [{"text": "🔙 ត្រឡប់ក្រោយ"}],
                        ],
                        "resize_keyboard": True,
                    }
                    send_message(chat_id, "⚡ *Mobile Legends* - សូមជ្រើសរើសកញ្ចប់ពេជ្រ និង Pass ខាងក្រោម៖", reply_markup=ml_menu)

                # ==========================================
                # 3. កញ្ចប់តម្លៃ HONOR OF KINGS
                # ==========================================
                elif text == "👑 Honor of Kings":
                    hok_menu = {
                        "keyboard": [
                            [{"text": "🎫 Weekly Card - $1.06"}, {"text": "🔥 Weekly Card Plus - $3.37"}],
                            [{"text": "💎 16 Token - $0.23"}, {"text": "💎 80 Token - $0.98"}],
                            [{"text": "💎 240 Token - $2.76"}, {"text": "💎 400 Token - $4.60"}],
                            [{"text": "💎 560 Token - $6.39"}, {"text": "💎 830 Token - $8.89"}],
                            [{"text": "💎 1245 Token - $13.79"}, {"text": "💎 2508 Token - $26.89"}],
                            [{"text": "💎 4180 Token - $44.89"}, {"text": "💎 8360 Token - $88.69"}],
                            [{"text": "🔙 ត្រឡប់ក្រោយ"}],
                        ],
                        "resize_keyboard": True,
                    }
                    send_message(chat_id, "👑 *Honor of Kings* - សូមជ្រើសរើសកញ្ចប់ Tokens និង Cards ខាងក្រោម៖", reply_markup=hok_menu)

                # ==========================================
                # 4. កញ្ចប់តម្លៃ PUBG MOBILE
                # ==========================================
                elif text == "🎯 PUBG Mobile":
                    pubg_menu = {
                        "keyboard": [
                            [{"text": "💎 60 UC - $0.98"}, {"text": "💎 325 UC - $4.89"}],
                            [{"text": "💎 660 UC - $9.71"}, {"text": "💎 1800 UC - $23.89"}],
                            [{"text": "💎 3850 UC - $47.50"}, {"text": "💎 8100 UC - $94.99"}],
                            [{"text": "📦 First Purchase Pack - $0.95"}, {"text": "✨ Mythic Emblem Pack - $4.44"}],
                            [{"text": "🛠️ Upgradable Firearm Materials Pack - $2.79"}, {"text": "📦 Weekly Mythic Emblem Value Pack - $2.71"}],
                            [{"text": "⭐ Elite Pass LV1-50 - $5.20"}, {"text": "⭐ Elite Pass LV1-100 - $10.03"}],
                            [{"text": "👑 Elite Pass Plus LV1-100 - $24.99"}],
                            [{"text": "🔥 Prime (1 Month) - $0.96"}, {"text": "🔥 Prime Plus (1 Month) - $8.99"}],
                            [{"text": "🔥 Prime (3 Months) - $2.78"}, {"text": "🔥 Prime Plus (3 Months) - $26.89"}],
                            [{"text": "🔥 Prime (6 Months) - $5.59"}, {"text": "🔥 Prime Plus (6 Months) - $53.99"}],
                            [{"text": "🔥 Prime (12 Months) - $10.89"}, {"text": "🔥 Prime Plus (12 Months) - $108.28"}],
                            [{"text": "📦 Weekly Deal Pack 1 - $0.96"}, {"text": "📦 Weekly Deal Pack 2 - $2.89"}],
                            [{"text": "🔙 ត្រឡប់ក្រោយ"}],
                        ],
                        "resize_keyboard": True,
                    }
                    send_message(chat_id, "🎯 *PUBG Mobile* - សូមជ្រើសរើសកញ្ចប់ UC ឬ Pass ខាងក្រោម៖", reply_markup=pubg_menu)

                # ==========================================
                # 5. កញ្ចប់តម្លៃ BLOOD STRIKE
                # ==========================================
                elif text == "🩸 Blood Strike":
                    bs_menu = {
                        "keyboard": [
                            [{"text": "💎 51 Diamonds - $0.48"}, {"text": "💎 105 Diamonds - $0.96"}],
                            [{"text": "💎 320 Diamonds - $2.52"}, {"text": "💎 540 Diamonds - $4.40"}],
                            [{"text": "💎 1100 Diamonds - $8.39"}, {"text": "💎 2260 Diamonds - $16.40"}],
                            [{"text": "💎 5800 Diamonds - $41.12"}, {"text": "🔥 899deal - $7.39"}],
                            [{"text": "🔥 999deal - $8.44"}, {"text": "🔥 49deal - $0.47"}],
                            [{"text": "🔥 99deal - $0.92"}, {"text": "🔥 199deal - $1.78"}],
                            [{"text": "🔥 299deal - $2.65"}, {"text": "🔥 399deal - $3.45"}],
                            [{"text": "🔥 499deal - $4.48"}, {"text": "🔥 599deal - $5.29"}],
                            [{"text": "🔥 699deal - $5.89"}, {"text": "🔥 799deal - $7.29"}],
                            [{"text": "📦 Punch Man Upgrade Point Lucky - $1.74"}, {"text": "📦 7DS Featured Valor Voucher - $0.90"}],
                            [{"text": "📦 Enable Cornucopia - $1.74"}, {"text": "📦 One-Punch Man Collab Upgrade Point - $1.70"}],
                            [{"text": "🎫 Level Up Pass - $1.75"}, {"text": "🎒 Lucky Bag Week - $0.90"}],
                            [{"text": "📦 Maestro Featured Stash Voucher - $1.74"}, {"text": "🛡️ Season Pass - $0.90"}],
                            [{"text": "📦 Seven Deadly Sins Upgrade Point - $1.74"}, {"text": "⭐ Strike Pass Elite - $3.69"}],
                            [{"text": "👑 Strike Pass Premium - $7.69"}, {"text": "📦 Tokyo Revengers Featured Valor 1 - $0.90"}],
                            [{"text": "📦 Tokyo Revengers Featured Valor 2 - $0.92"}, {"text": "📦 Tokyo Revengers Upgrade Point - $1.74"}],
                            [{"text": "✨ Ultra Skin Lucky Chest - $0.52"}, {"text": "🎁 One-Punch Man Exclusive Lucky Bag - $0.90"}],
                            [{"text": "🎁 One-Punch Man Featured Valor Voucher - $0.90"}],
                            [{"text": "🔙 ត្រឡប់ក្រោយ"}],
                        ],
                        "resize_keyboard": True,
                    }
                    send_message(chat_id, "🩸 *Blood Strike* - សូមជ្រើសរើសកញ្ចប់ពេជ្រ ឬ Deals ខាងក្រោម៖", reply_markup=bs_menu)

                # ==========================================
                # 6. កញ្ចប់តម្លៃ CAR PARKING
                # ==========================================
                elif text == "🚗 Car Parking":
                    cpm_menu = {
                        "keyboard": [
                            [{"text": "🪙 5,500 Coins - $0.20"}, {"text": "🪙 10,000 Coins - $0.35"}],
                            [{"text": "🪙 20,000 Coins - $0.60"}, {"text": "🪙 30,000 Coins - $0.80"}],
                            [{"text": "💵 500M Money - $0.65"}, {"text": "💵 1000M Money - $1"}],
                            [{"text": "🔓 Unlock All Cars - $1"}, {"text": "👑 VIP Package - $1"}],
                            [{"text": "🔙 ត្រឡប់ក្រោយ"}],
                        ],
                        "resize_keyboard": True,
                    }
                    send_message(chat_id, "🚗 *Car Parking* - សូមជ្រើសរើសកញ្ចប់ខាងក្រោម៖", reply_markup=cpm_menu)

                elif text == "🔙 ត្រឡប់ក្រោយ":
                    send_message(chat_id, "🏠 សូមជ្រើសរើសប្រភេទហ្គេមខាងក្រោម៖", reply_markup=main_menu)

                # --- ការផ្ទៀងផ្ទាត់កញ្ចប់ Free Fire ---
                elif text in [
                    "💎 25 Diamonds - $0.28", "💎 100 Diamonds - $0.97",
                    "💎 310 Diamonds - $2.95", "💎 520 Diamonds - $4.78",
                    "💎 1060 Diamonds - $9.34", "💎 2180 Diamonds - $19.82",
                    "💎 5600 Diamonds - $48.56", "💎 11500 Diamonds - $96.60",
                    "👑 Monthly Pass - $7.69", "🔥 Weekly Pass - $1.69",
                    "⚡ Weekly Lite - $0.44", "📦 3 កាត (3in1) - $9.79",
                    "👑 Monthly Pass x2 - $15.79", "🔥 Weekly Pass x2 - $3.38",
                    "👑 Monthly Pass x3 - $23.46", "🔥 Weekly Pass x3 - $5.17",
                    "👑 Monthly Pass x4 - $31.18", "🔥 Weekly Pass x4 - $6.99",
                    "👑 Monthly Pass x5 - $38.95", "🔥 Weekly Pass x5 - $8.65",
                    "👑 Monthly Pass x10 - $77.20", "🔥 Weekly Pass x10 - $16.90"
                ]:
                    user_data[chat_id] = {"game": "Free Fire", "package": text}
                    send_message(chat_id, f"✅ អ្នកបានជ្រើសរើស៖ *{text}*\n\n👉 សូមផ្ញើលេខ *User ID នឹង NameGame* របស់ហ្គេម Free Fire មកទីនេះ៖")

                # --- ការផ្ទៀងផ្ទាត់កញ្ចប់ Mobile Legends ---
                elif text in [
                    "💎 86 Diamonds - $1.30", "💎 172 Diamonds - $2.55",
                    "💎 257 Diamonds - $3.69", "💎 344 Diamonds - $4.99",
                    "💎 429 Diamonds - $6.39", "💎 514 Diamonds - $7.44",
                    "💎 600 Diamonds - $8.58", "💎 706 Diamonds - $9.79",
                    "💎 792 Diamonds - $11.99", "💎 878 Diamonds - $12.46",
                    "💎 963 Diamonds - $13.89", "💎 1050 Diamonds - $14.89",
                    "💎 1136 Diamonds - $15.89", "💎 1222 Diamonds - $16.99",
                    "💎 1412 Diamonds - $19.89", "💎 1584 Diamonds - $21.99",
                    "💎 1756 Diamonds - $24.89", "💎 1928 Diamonds - $26.96",
                    "💎 2195 Diamonds - $30.12", "💎 2539 Diamonds - $34.69",
                    "💎 2901 Diamonds - $39.79", "💎 3688 Diamonds - $49.25",
                    "💎 4394 Diamonds - $58.99", "💎 5532 Diamonds - $74.15",
                    "💎 6238 Diamonds - $84.79", "💎 6944 Diamonds - $94.59",
                    "💎 7727 Diamonds - $104.29", "💎 9288 Diamonds - $124.69",
                    "💎 10080 Diamonds - $134.79", "💎 10700 Diamonds - $140.99",
                    "📦 Weekly Pass - $1.53", "⭐ Elite Weekly - $0.92",
                    "🌟 Epic Monthly - $4.19", "🛡️ Twilight Pass - $8.42",
                    "📦 Weekly Pass x 2 - $3.40", "📦 Weekly Pass x3 - $4.79",
                    "📦 Weekly Pass x4 - $6.39", "📦 Weekly Pass x5 - $7.85"
                ]:
                    user_data[chat_id] = {"game": "Mobile Legends", "package": text}
                    send_message(chat_id, f"✅ អ្នកបានជ្រើសរើស៖ *{text}*\n\n👉 សូមផ្ញើលេខ *User ID និង Zone ID និង NameGame* មកទីនេះ៖")

                # --- ការផ្ទៀងផ្ទាត់កញ្ចប់ Honor of Kings ---
                elif text in [
                    "🎫 Weekly Card - $1.06", "🔥 Weekly Card Plus - $3.37",
                    "💎 16 Token - $0.23", "💎 80 Token - $0.98",
                    "💎 240 Token - $2.76", "💎 400 Token - $4.60",
                    "💎 560 Token - $6.39", "💎 830 Token - $8.89",
                    "💎 1245 Token - $13.79", "💎 2508 Token - $26.89",
                    "💎 4180 Token - $44.89", "💎 8360 Token - $88.69"
                ]:
                    user_data[chat_id] = {"game": "Honor of Kings", "package": text}
                    send_message(chat_id, f"✅ អ្នកបានជ្រើសរើស៖ *{text}*\n\n👉 សូមផ្ញើលេខ *User ID និង NameGame* របស់ហ្គេម Honor of Kings មកទីនេះ៖")

                # --- ការផ្ទៀងផ្ទាត់កញ្ចប់ PUBG Mobile ---
                elif text in [
                    "💎 60 UC - $0.98", "💎 325 UC - $4.89",
                    "💎 660 UC - $9.71", "💎 1800 UC - $23.89",
                    "💎 3850 UC - $47.50", "💎 8100 UC - $94.99",
                    "📦 First Purchase Pack - $0.95", "✨ Mythic Emblem Pack - $4.44",
                    "🛠️ Upgradable Firearm Materials Pack - $2.79", "📦 Weekly Mythic Emblem Value Pack - $2.71",
                    "⭐ Elite Pass LV1-50 - $5.20", "⭐ Elite Pass LV1-100 - $10.03",
                    "👑 Elite Pass Plus LV1-100 - $24.99",
                    "🔥 Prime (1 Month) - $0.96", "🔥 Prime Plus (1 Month) - $8.99",
                    "🔥 Prime (3 Months) - $2.78", "🔥 Prime Plus (3 Months) - $26.89",
                    "🔥 Prime (6 Months) - $5.59", "🔥 Prime Plus (6 Months) - $53.99",
                    "🔥 Prime (12 Months) - $10.89", "🔥 Prime Plus (12 Months) - $108.28",
                    "📦 Weekly Deal Pack 1 - $0.96", "📦 Weekly Deal Pack 2 - $2.89"
                ]:
                    user_data[chat_id] = {"game": "PUBG Mobile", "package": text}
                    send_message(chat_id, f"✅ អ្នកបានជ្រើសរើស៖ *{text}*\n\n👉 សូមផ្ញើលេខ *Character ID និង NameGame* របស់ហ្គេម PUBG Mobile មកទីនេះ៖")
                    
                # --- ការផ្ទៀងផ្ទាត់កញ្ចប់ Blood Strike ---
                elif text in [
                    "💎 51 Diamonds - $0.48", "💎 105 Diamonds - $0.96",
                    "💎 320 Diamonds - $2.52", "💎 540 Diamonds - $4.40",
                    "💎 1100 Diamonds - $8.39", "💎 2260 Diamonds - $16.40",
                    "💎 5800 Diamonds - $41.12", "🔥 899deal - $7.39",
                    "🔥 999deal - $8.44", "🔥 49deal - $0.47",
                    "🔥 99deal - $0.92", "🔥 199deal - $1.78",
                    "🔥 299deal - $2.65", "🔥 399deal - $3.45",
                    "🔥 499deal - $4.48", "🔥 599deal - $5.29",
                    "🔥 699deal - $5.89", "🔥 799deal - $7.29",
                    "📦 Punch Man Upgrade Point Lucky - $1.74", "📦 7DS Featured Valor Voucher - $0.90",
                    "📦 Enable Cornucopia - $1.74", "📦 One-Punch Man Collab Upgrade Point - $1.70",
                    "🎫 Level Up Pass - $1.75", "🎒 Lucky Bag Week - $0.90",
                    "📦 Maestro Featured Stash Voucher - $1.74", "🛡️ Season Pass - $0.90",
                    "📦 Seven Deadly Sins Upgrade Point - $1.74", "⭐ Strike Pass Elite - $3.69",
                    "👑 Strike Pass Premium - $7.69", "📦 Tokyo Revengers Featured Valor 1 - $0.90",
                    "📦 Tokyo Revengers Featured Valor 2 - $0.92", "📦 Tokyo Revengers Upgrade Point - $1.74",
                    "✨ Ultra Skin Lucky Chest - $0.52", "🎁 One-Punch Man Exclusive Lucky Bag - $0.90",
                    "🎁 One-Punch Man Featured Valor Voucher - $0.90"
                ]:
                    user_data[chat_id] = {"game": "Blood Strike", "package": text}
                    send_message(chat_id, f"✅ អ្នកបានជ្រើសរើស៖ *{text}*\n\n👉 សូមផ្ញើលេខ *User ID និង NameGame* របស់ហ្គេម Blood Strike មកទីនេះ៖")

                # --- ការផ្ទៀងផ្ទាត់កញ្ចប់ Car Parking ---
                elif text in [
                    "🪙 5,500 Coins - $0.20", "🪙 10,000 Coins - $0.35",
                    "🪙 20,000 Coins - $0.60", "🪙 30,000 Coins - $0.80",
                    "💵 500M Money - $1", "💵 1000M Money - $1.25",
                    "🔓 Unlock All Cars - $1", "👑 VIP Package - $1"
                ]:
                    user_data[chat_id] = {"game": "Car Parking", "package": text}
                    send_message(chat_id, f"✅ អ្នកបានជ្រើសរើស៖ *{text}*\n\n👉 សូមផ្ញើរ gmail នឹង password អាខោនហ្គេមរបស់អ្នក៖")

                # ពេលអតិថិជនវាយបញ្ចូល ID ឬ Gmail & Password ផ្ញើមកកាន់ Admin
                else:
                    data = user_data.get(chat_id)
                    if data:
                        message_id = message["message_id"]
                        
                        forward_message(ADMIN_CHAT_ID, chat_id, message_id)
                        
                        admin_info = (
                            f"🔔 *មានការបញ្ជាទិញថ្មី!*\n"
                            f"👤 Telegram ID: `{chat_id}`\n"
                            f"🎮 ហ្គេម៖ *{data['game']}*\n"
                            f"🆔 Info / Account: `{text}`\n"
                            f"📦 កញ្ចប់៖ *{data['package']}*"
                        )
                        res_msg = send_message(ADMIN_CHAT_ID, admin_info)
                        
                        if res_msg and "result" in res_msg:
                            message_map[res_msg["result"]["message_id"]] = chat_id

                        caption_text = (
                            f"📥 ព័ត៌មានអតិថិជនបញ្ជាទិញ៖\n"
                            f"🎮 ហ្គេម៖ *{data['game']}*\n"
                            f"🆔 Info/Acc: `{text}`\n"
                            f"📦 កញ្ចប់៖ *{data['package']}*\n\n"
                            "💳 *សូមស្កេន QR Code ខាងលើដើម្បីទូទាត់ប្រាក់*\n"
                            "ផ្ញើសន្លឹកប័ណ្ណបញ្ជាក់ការបង់ប្រាក់ (Receipt) មកទីនេះជាការស្រេច!"
                        )
                        send_photo_local(chat_id, "images/logoqrcode.jpeg", caption_text)
                    else:
                        send_message(
                            chat_id, 
                            "⚠️ សូមជ្រើសរើសហ្គេម និងកញ្ចប់ជាមុនសិន។", 
                            reply_markup=main_menu
                        )
