![Pop Mart Bot](https://github.com/abu-sinan/popmart_bot/blob/main/assets/thumbnail.png)
# 🛒 Pop Mart Auto Purchase Bot

A fast, stealthy, and automated checkout bot for [PopMart.com](https://www.popmart.com/us), built with Python + Playwright.

---

## ✅ Features:

- Full browser automation using [Playwright](https://playwright.dev/)

- Stealth mode to bypass anti-bot detection

- Smart login check (only logs in if needed)

- Fresh session on every run (no cookie reuse)

- Detects product stock status

- Automatically adds to bag, checks out, and pays

- Telegram alerts for every action (stock, success, failure, etc.)

- Log rotation support

- Supports unlimited product links

- Runs 24/7 with optional systemd service

---

## 📁 Project Structure

```
popmart_bot/
├── bot.py                   # Main automation script
├── config.json              # Product list & settings
├── .env                     # Secrets (email, password, Telegram)
├── requirements.txt         # Python dependencies
├── run_forever.sh           # (Optional) restart loop for manual runs
├── log.txt                  # Logs (auto-rotating)
├── .gitignore               # Git exclusions
└── systemd/
    └── popmart-bot.service  # systemd service file for auto-start
```

---

⚙️ Installation

### 1. Clone the Repo or Upload Your Files

```bash
git clone https://github.com/abu-sinan/popmart_bot.git
cd popmart_bot
```

### 2. Install Python and Playwright

```bash
sudo apt update
sudo apt install python3 python3-pip -y
pip install -r requirements.txt
playwright install
```

### 3. Configure Environment Variables

Create a `.env` file:

```env
EMAIL=your_email@example.com
PASSWORD=your_password
TELEGRAM_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

### 4. Configure Products

Edit `config.json` to list products:

```json
{
  "headless": true,
  "max_retries": 5,
  "products": [
    {
      "url": "https://www.popmart.com/us/product/labubu-xxx",
      "size": "Single box",
      "quantity": 1
    }
  ]
}
```

---

## 🚀 Usage

### Manual Run (Headless or Headful)

```bash
python3 bot.py
```

### Auto-Restart Loop (Optional)

```bash
chmod +x run_forever.sh
./run_forever.sh
```

---

## 🔁 Auto-Start with systemd (Linux)

### 1. Move service file

```bash
sudo cp systemd/popmart-bot.service /etc/systemd/system/
```

### 2. Edit the service file

Update:

- `User=your_linux_user`

- `WorkingDirectory=/absolute/path/to/popmart-bot`

- `ExecStart=/usr/bin/python3 /absolute/path/to/popmart-bot/bot.py`


### 3. Enable and start the service

```bash
sudo systemctl daemon-reexec
sudo systemctl daemon-reload
sudo systemctl enable popmart-bot
sudo systemctl start popmart-bot
```

Check status:

```bash
sudo systemctl status popmart-bot
```

Logs:

```bash
journalctl -u popmart-bot -f
```

---

## 📬 Telegram Alerts

The bot will notify you on Telegram for:

- Product in stock

- Adding to bag

- Added to bag

- Checkout progress

- Payment initiated

- Purchase success

- Failures or errors

---

## 🛡️ Notes

- Stealth mode uses `playwright-stealth`

- No session persistence: each run is fresh

- Works in both headless and headful mode

- Rotate logs after 500 KB (max 3 backups)

---

## 📄 License

MIT [License](https://github.com/abu-sinan/popmart_bot/blob/main/LICENSE).