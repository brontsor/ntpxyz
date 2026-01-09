# Setting Up Telegram Integration with ntpxyz

`ntpxyz` can automatically send your NTP statistics plots to a private Telegram chat or group — perfect for scheduled runs on air-gapped or DMZ servers.

To enable this feature you need two pieces of information:

- `telegram_token` — your Bot API token (from BotFather)
- `chat_id` — the numeric ID of the chat where plots will be sent

Follow this guide to obtain both in under 5 minutes.

### Step 1: Create a Telegram Bot (obtain the `telegram_token`)

1. Open Telegram and search for **@BotFather** (official bot manager, blue checkmark).
2. Start a chat and send the command:

   ```
   /newbot
   ```

3. Follow the prompts:
   - Choose a **display name** for your bot (e.g., “NTP Monitor Bot”)
   - Choose a **username** that ends with `bot` (e.g., `@my_ntp_reporter_bot`)

4. BotFather will reply with a message containing your **bot token**. It looks like:

   ```
   123456789:AAFExampleTokenHere1234567890
   ```

   **Copy this entire string** — this is your `telegram_token`.

   > **Security note:** Treat this token like a password. Anyone who has it can control your bot.

### Step 2: Obtain Your `chat_id`

You have two options: send plots to a **private chat with the bot** (simplest) or to a **group/supergroup**.

#### Option A: Private Chat (recommended for personal alerts)

1. Open a direct message with your new bot (search its username or click the link BotFather provided).
2. Send any message (e.g., `hi`).
3. In a browser, open this URL (replace `YOUR_TOKEN` with the token you copied):

   ```
   https://api.telegram.org/botYOUR_TOKEN/getUpdates
   ```

   Example:

   ```
   https://api.telegram.org/bot123456789:AAFExampleTokenHere1234567890/getUpdates
   ```

4. Look for the `"chat":{"id":` field in the JSON response. The number after it is your `chat_id`.

   Example snippet:

   ```json
   "chat": {
     "id": 987654321,
     "first_name": "David",
     "type": "private"
   }
   ```

   Your `chat_id` is `987654321`.

#### Option B: Group or Supergroup (for team monitoring)

1. Create a new group (or use an existing one).
2. Add your bot to the group.
3. Promote the bot to **admin** (required for sending messages in many groups).
4. Send any message in the group.
5. Visit the same `getUpdates` URL as above.
6. Find a `"chat"` object where `"type"` is `"group"` or `"supergroup"`.
7. Copy the `"id"` — it will be a **negative number**, often starting with `-100`, e.g., `-1001234567890`.

   > Group chat IDs are always negative and frequently begin with `-100`. This is normal.

### Step 3: Add the Values to Your ntpxyz Config File

Edit (or create) the config file — default location is `~/.config/ntpxyz/config.json`:

```json
{
  "telegram_token": "123456789:AAFExampleTokenHere1234567890",
  "chat_id": "987654321"
}
```

For a group:

```json
{
  "telegram_token": "123456789:AAFExampleTokenHere1234567890",
  "chat_id": "-1001234567890"
}
```

> **Tip:** Even though `chat_id` is numeric, quoting it (as shown) works reliably for both positive and negative IDs.

### Test It

Run ntpxyz with the `--telegram` flag:

```bash
ntpxyz --scandir /var/log/ntpstats --period rolling-week --telegram
```

You should receive your plots directly in the chosen Telegram chat!

### Troubleshooting

| Symptom                          | Likely Cause & Fix                                                                 |
|----------------------------------|------------------------------------------------------------------------------------|
| “Unauthorized” error             | Token copied incorrectly — no extra spaces or line breaks                           |
| Nothing sent, no error logged    | Bot has never received a message in that chat — send a message first               |
| “Forbidden: bot was blocked”     | Unblock the bot in the private chat                                                |
| “Bad Request: chat not found”    | Wrong `chat_id` — re-run `getUpdates` after sending a new message                  |
| Group receives no messages       | Bot not admin or Privacy Mode enabled — use `/setprivacy` in BotFather and disable |

You’re all set! Your NTP server now has a direct line to your phone (or team chat).
