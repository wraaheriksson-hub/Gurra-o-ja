import os
import time
import smtplib
from email.mime.text import MIMEText
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import requests

# --- KONFIGURATION ---

LOGIN_URL = "https://bariumapp.vgregion.se/Spaces/1/Lists/List/46ac6a3f-d9f7-4aaa-bd31-c5ec3836299f?sort=ambulans%E9%A6%99datum&dir=ASC"
USERNAME = os.environ.get("MONITOR_USER")      # sätts som miljövariabel
PASSWORD = os.environ.get("MONITOR_PASS")      # sätts som miljövariabel
DISCORD_WEBHOOK = "https://discord.com/api/webhooks/1404430359545905194/oD-2sm8psoUNM4pi9Vke8aJyVrB3dcssfDzptQevdcVq8l2A3L-UzBG0Rdpm0-Lc4c1l"

EMAIL_SENDER = os.environ.get("EMAIL_SENDER")     # Gmail-adress som skickar
EMAIL_PASS = os.environ.get("EMAIL_PASS")         # Gmail app-lösenord
EMAIL_RECEIVERS = ["Wraaheriksson@gmail.com", "Annaengstrom90@hotmail.com", "tredje@email.se"]  # Byt ut tredje adressen!

POLL_INTERVAL = 20  # sekunder

# --- FUNKTIONER ---

def send_discord(msg):
    if not DISCORD_WEBHOOK:
        print("Discord webhook saknas")
        return
    data = {"content": msg}
    resp = requests.post(DISCORD_WEBHOOK, json=data)
    if resp.status_code != 204:
        print("Misslyckades skicka Discord-notis:", resp.text)

def send_email(subject, body):
    if not EMAIL_SENDER or not EMAIL_PASS:
        print("E-postuppgifter saknas")
        return
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_SENDER
    msg["To"] = ", ".join(EMAIL_RECEIVERS)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_SENDER, EMAIL_PASS)
            server.sendmail(EMAIL_SENDER, EMAIL_RECEIVERS, msg.as_string())
        print("E-post skickad")
    except Exception as e:
        print("Fel vid e-postskick:", e)

def get_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def main():
    seen_passes = set()
    driver = get_driver()
    try:
        print("Öppnar inloggningssida...")
        driver.get(LOGIN_URL)
        time.sleep(2)

        driver.find_element(By.CSS_SELECTOR,"input.button:nth-child(8)").click()
        time.sleep(2)

        print("Fyller i användarnamn och lösenord...")
        driver.find_element(By.NAME, "USER").send_keys(USERNAME)
        driver.find_element(By.NAME, "PASSWORD").send_keys(PASSWORD)
        driver.find_element(By.CSS_SELECTOR,"div.form-field:nth-child(5) > input:nth-child(1)").click()  # Om det finns en knapp med id "submit", annars ändra!

        time.sleep(5)  # Vänta på att sidan laddas efter inloggning

        print("Startar övervakning av passen...")
        while True:
            # Om sidan måste laddas om för att uppdatera pass, använd driver.refresh()
            driver.refresh()
            time.sleep(5)  # Vänta på att tabellen laddas

            # Hitta tabellraderna - OBS: byt ut CSS-selector till rätt tabell!
            rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")

            for row in rows:
                text = row.text.strip()
                if text and text not in seen_passes:
                    print("Nytt pass hittat:", text)
                    seen_passes.add(text)
                    # Skicka notis
                    send_discord(f"Nytt pass tillgängligt: {text}")
                    send_email("Nytt pass tillgängligt", text)

            time.sleep(POLL_INTERVAL)

    finally:
       # driver.quit()
       print(" hej")

if __name__ == "__main__":
    main()
