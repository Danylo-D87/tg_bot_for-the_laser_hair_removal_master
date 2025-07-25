# 🤖 LaserHouse Telegram Booking Bot

This bot is an AI-powered assistant designed to automate client bookings for laser hair removal services. It leverages a language model (LLM) to interact naturally with users, recognize booking intents, and manage appointment scheduling via Google Calendar.

### Project Structure (simplified)
```bash
.
├── main.py
├── .env
├── env.simple
├── prompts/
│   └── prompt.txt
├── booking/
│   └── calendar_api.py
├── bot/
│   ├── bot.py
│   └── bot_utils.py
├── working_hours.py
└── service-account.json
```

## 🔍 Features:
- Converses politely and helpfully with clients
- Detects when a user wants to book an appointment
- Shows available time slots based on Google Calendar events
- Creates calendar events including user email invitations
- Enforces working hours to prevent bookings outside business time


## ⚙️ How to Run

1. **Clone the repo and install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
2. **Create a .env file from env.simple template:**

   Fill in your bot token, OpenAI API key, Google Calendar ID, and other required variables.


3. **Add Google service account JSON file to the project root:**

   Download this from Google Cloud Console when setting up your service account.


4. **Configure working hours:**

   Adjust working_hours.py to set the business hours during which bookings are allowed.


5. **Start the bot:**
   ```bash
   python main.py
   ```
   
### ✅ Notes
- Events are created in the specified Google Calendar; ensure the service account has proper access.

- User email is used to send event invitations.

- If you get permission errors, double-check your CALENDAR_ID and calendar sharing settings.