import json
import urllib.request
import urllib.parse
import os

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
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        print("Error send_message:", e)
        return None

def delete_message(chat_id, message_id):
    data = json.dumps({"chat_id": chat_id, "message_id": message_id}).encode("utf-8")
    req = urllib.request.Request(f"{URL}/deleteMessage", data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        print("Error delete_message:", e)
        return None

def forward_message(chat_id, from_chat_id, message_id):
    data = {"chat_id": chat_id, "from_chat_id": from_chat_id, "message_id": message_id}
    data = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(f"{URL}/forwardMessage", data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as response:
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
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        print("Error sending photo:", e)
        return None

def get_updates(offset=None):
    url = f"{URL}/getUpdates?timeout=100"
    if offset: url += f"&offset={offset}"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        print("Error get_updates:", e)
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
                        "🎉 *អបអរសាទរ!* ការបញ្ជាទិញពេជ្ររបស់អ្នកត្រូវបាន **បំពេញជោគជ័យ** រួចរាល់ហើយ!\n"
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
                        [{"text": "👑 Honor of Kings"}],
                    ],
                    "resize_keyboard": True,
                }

                if text in ["/start", "🚀 Start Bot"]:
                    user_data.pop(chat_id, None)
                    send_message(
                        chat_id,
                        "🌟 *សួស្តី! សូមស្វាគមន៍មកកាន់ប្រព័ន្ធ Top Up ពេជ្រអូតូម៉ាតិច* 🌟\n\n👇 សូមជ្រើសរើសហ្គេមនៅប៊ូតុងខាងក្រោម៖",
                        reply_markup=main_menu,
                    )

                elif text == "🔥 Free Fire":
                    ff_menu = {
                        "keyboard": [
                            [{"text": "💎 25 Diamonds - $0.25"}, {"text": "💎 100 Diamonds - $0.95"}],
                            [{"text": "💎 310 Diamonds - $2.89"}, {"text": "💎 520 Diamonds - $4.59"}],
                            [{"text": "💎 1060 Diamonds - $8.89"}, {"text": "💎 2180 Diamonds - $19.26"}],
                            [{"text": "💎 5600 Diamonds - $48.14"}, {"text": "💎 11500 Diamonds - $96.29"}],
                            [{"text": "👑 Monthly Pass - $7.59"}, {"text": "⚡ Weekly Pass - $1.59"}],
                            [{"text": "🔙 ត្រឡប់ក្រោយ"}],
                        ],
                        "resize_keyboard": True,
                    }
                    send_message(chat_id, "🔥 *Free Fire* - សូមជ្រើសរើសកញ្ចប់ពេជ្រ ឬ Membership ខាងក្រោម៖", reply_markup=ff_menu)

                elif text == "⚡ Mobile Legends":
                    ml_menu = {
                        "keyboard": [
                            [{"text": "💎 86 Diamonds - $1.25"}, {"text": "💎 172 Diamonds - $2.45"}],
                            [{"text": "💎 257 Diamonds - $3.59"}, {"text": "💎 344 Diamonds - $4.89"}],
                            [{"text": "💎 429 Diamonds - $6.09"}, {"text": "💎 514 Diamonds - $7.19"}],
                            [{"text": "💎 600 Diamonds - $8.49"}, {"text": "💎 706 Diamonds - $9.69"}],
                            [{"text": "💎 792 Diamonds - $10.95"}, {"text": "💎 878 Diamonds - $12.19"}],
                            [{"text": "💎 963 Diamonds - $13.29"}, {"text": "💎 1050 Diamonds - $14.59"}],
                            [{"text": "💎 1136 Diamonds - $15.79"}, {"text": "💎 1222 Diamonds - $16.89"}],
                            [{"text": "💎 1412 Diamonds - $19.19"}, {"text": "💎 1584 Diamonds - $21.89"}],
                            [{"text": "💎 1756 Diamonds - $24.39"}, {"text": "💎 1928 Diamonds - $26.59"}],
                            [{"text": "💎 2195 Diamonds - $29.99"}, {"text": "💎 2539 Diamonds - $34.29"}],
                            [{"text": "💎 2901 Diamonds - $39.09"}, {"text": "💎 3688 Diamonds - $48.69"}],
                            [{"text": "💎 4394 Diamonds - $58.69"}, {"text": "💎 5532 Diamonds - $73.49"}],
                            [{"text": "💎 6238 Diamonds - $83.69"}, {"text": "💎 6944 Diamonds - $93.39"}],
                            [{"text": "💎 7727 Diamonds - $103.29"}, {"text": "💎 9288 Diamonds - $122.89"}],
                            [{"text": "💎 10080 Diamonds - $133.79"}, {"text": "💎 10700 Diamonds - $138.99"}],
                            [{"text": "📦 Weekly Pass - $1.49"}, {"text": "⭐ Elite Weekly - $0.89"}],
                            [{"text": "🌟 Epic Monthly - $4.09"}, {"text": "🛡️ Twilight Pass - $8.19"}],
                            [{"text": "📦 Weekly Pass x 2 - $2.98"}, {"text": "📦 Weekly Pass x3 - $4.47"}],
                            [{"text": "📦 Weekly Pass x4 - $5.96"}, {"text": "📦 Weekly Pass x5 - $7.45"}],
                            [{"text": "🔙 ត្រឡប់ក្រោយ"}],
                        ],
                        "resize_keyboard": True,
                    }
                    send_message(chat_id, "⚡ *Mobile Legends* - សូមជ្រើសរើសកញ្ចប់ពេជ្រ និង Pass ខាងក្រោម៖", reply_markup=ml_menu)

                elif text == "👑 Honor of Kings":
                    hok_menu = {
                        "keyboard": [
                            [{"text": "🎫 Weekly Card - $0.99"}, {"text": "🔥 Weekly Card Plus - $3.30"}],
                            [{"text": "💎 16 Token - $0.20"}, {"text": "💎 80 Token - $0.89"}],
                            [{"text": "💎 240 Token - $2.69"}, {"text": "💎 400 Token - $4.42"}],
                            [{"text": "💎 560 Token - $6.19"}, {"text": "💎 830 Token - $8.79"}],
                            [{"text": "💎 1245 Token - $12.99"}, {"text": "💎 2508 Token - $26.19"}],
                            [{"text": "💎 4180 Token - $44.19"}, {"text": "💎 8360 Token - $87.19"}],
                            [{"text": "🔙 ត្រឡប់ក្រោយ"}],
                        ],
                        "resize_keyboard": True,
                    }
                    send_message(chat_id, "👑 *Honor of Kings* - សូមជ្រើសរើសកញ្ចប់ Tokens និង Cards ខាងក្រោម៖", reply_markup=hok_menu)

                elif text == "🔙 ត្រឡប់ក្រោយ":
                    send_message(chat_id, "🏠 សូមជ្រើសរើសប្រភេទហ្គេមខាងក្រោម៖", reply_markup=main_menu)

                # កញ្ចប់ Free Fire
                elif text in [
                    "💎 25 Diamonds - $0.25", "💎 100 Diamonds - $0.95",
                    "💎 310 Diamonds - $2.89", "💎 520 Diamonds - $4.59",
                    "💎 1060 Diamonds - $8.89", "💎 2180 Diamonds - $19.26",
                    "💎 5600 Diamonds - $48.14", "💎 11500 Diamonds - $96.29",
                    "👑 Monthly Pass - $7.59", "⚡ Weekly Pass - $1.59"
                ]:
                    user_data[chat_id] = {"game": "Free Fire", "package": text}
                    send_message(chat_id, f"✅ អ្នកបានជ្រើសរើស៖ *{text}*\n\n👉 សូមផ្ញើលេខ *User ID* របស់ហ្គេម Free Fire មកទីនេះ៖")

                # កញ្ចប់ Mobile Legends
                elif text in [
                    "💎 86 Diamonds - $1.25", "💎 172 Diamonds - $2.45",
                    "💎 257 Diamonds - $3.59", "💎 344 Diamonds - $4.89",
                    "💎 429 Diamonds - $6.09", "💎 514 Diamonds - $7.19",
                    "💎 600 Diamonds - $8.49", "💎 706 Diamonds - $9.69",
                    "💎 792 Diamonds - $10.95", "💎 878 Diamonds - $12.19",
                    "💎 963 Diamonds - $13.29", "💎 1050 Diamonds - $14.59",
                    "💎 1136 Diamonds - $15.79", "💎 1222 Diamonds - $16.89",
                    "💎 1412 Diamonds - $19.19", "💎 1584 Diamonds - $21.89",
                    "💎 1756 Diamonds - $24.39", "💎 1928 Diamonds - $26.59",
                    "💎 2195 Diamonds - $29.99", "💎 2539 Diamonds - $34.29",
                    "💎 2901 Diamonds - $39.09", "💎 3688 Diamonds - $48.69",
                    "💎 4394 Diamonds - $58.69", "💎 5532 Diamonds - $73.49",
                    "💎 6238 Diamonds - $83.69", "💎 6944 Diamonds - $93.39",
                    "💎 7727 Diamonds - $103.29", "💎 9288 Diamonds - $122.89",
                    "💎 10080 Diamonds - $133.79", "💎 10700 Diamonds - $138.99",
                    "📦 Weekly Pass - $1.49", "⭐ Elite Weekly - $0.89",
                    "🌟 Epic Monthly - $4.09", "🛡️ Twilight Pass - $8.19",
                    "📦 Weekly Pass x 2 - $2.98", "📦 Weekly Pass x3 - $4.47",
                    "📦 Weekly Pass x4 - $5.96", "📦 Weekly Pass x5 - $7.45"
                ]:
                    user_data[chat_id] = {"game": "Mobile Legends", "package": text}
                    send_message(chat_id, f"✅ អ្នកបានជ្រើសរើស៖ *{text}*\n\n👉 សូមផ្ញើលេខ *User ID និង Zone ID* មកទីនេះ៖")

                # កញ្ចប់ Honor of Kings (អាប់ដេតថ្មី)
                elif text in [
                    "🎫 Weekly Card - $0.99", "🔥 Weekly Card Plus - $3.30",
                    "💎 16 Token - $0.20", "💎 80 Token - $0.89",
                    "💎 240 Token - $2.69", "💎 400 Token - $4.42",
                    "💎 560 Token - $6.19", "💎 830 Token - $8.79",
                    "💎 1245 Token - $12.99", "💎 2508 Token - $26.19",
                    "💎 4180 Token - $44.19", "💎 8360 Token - $87.19"
                ]:
                    user_data[chat_id] = {"game": "Honor of Kings", "package": text}
                    send_message(chat_id, f"✅ អ្នកបានជ្រើសរើស៖ *{text}*\n\n👉 សូមផ្ញើលេខ *User ID* របស់ហ្គេម Honor of Kings មកទីនេះ៖")

                # ពេលអតិថិជនវាយបញ្ចូល User ID / Zone ID
                else:
                    data = user_data.get(chat_id)
                    if data:
                        message_id = message["message_id"]
                        
                        forward_message(ADMIN_CHAT_ID, chat_id, message_id)
                        
                        admin_info = (
                            f"🔔 *មានការបញ្ជាទិញថ្មី!*\n"
                            f"👤 Telegram ID: `{chat_id}`\n"
                            f"🎮 ហ្គេម៖ *{data['game']}*\n"
                            f"🆔 Game ID: `{text}`\n"
                            f"📦 កញ្ចប់៖ *{data['package']}*"
                        )
                        res_msg = send_message(ADMIN_CHAT_ID, admin_info)
                        
                        if res_msg and "result" in res_msg:
                            message_map[res_msg["result"]["message_id"]] = chat_id

                        caption_text = (
                            f"📥 ព័ត៌មានអតិថិជនបញ្ជាទិញ៖\n"
                            f"🎮 ហ្គេម៖ *{data['game']}*\n"
                            f"🆔 ID: `{text}`\n"
                            f"📦 កញ្ចប់៖ *{data['package']}*\n\n"
                            "💳 *សូមស្កេន QR Code ខាងលើដើម្បីទូទាត់ប្រាក់*\n"
                            "ផ្ញើសន្លឹកប័ណ្ណបញ្ជាក់ការបង់ប្រាក់ (Receipt) មកទីនេះជាការស្រេច!"
                        )
                        send_photo_local(chat_id, "images/logoqrcode.jpeg", caption_text)
                    else:
                        send_message(
                            chat_id, 
                            "⚠️ សូមជ្រើសរើសហ្គេម និងកញ្ចប់ពេជ្រជាមុនសិន។", 
                            reply_markup=main_menu
                        )
