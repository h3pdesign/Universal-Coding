# Dieses Skript automatisiert die Umwandlung von E-Mails aus Microsoft Outlook in Jira-Tickets.
# Es unterstützt mehrere Postfächer, komplexe Regeln, Anhänge, Labels und zusätzliche Felder.
# Voraussetzungen:
# - Python 3.x installiert (getestet mit Python 3.12)
# - pywin32-Bibliothek: pip install pywin32 (für Outlook-Zugriff auf Windows)
# - jira-Bibliothek: pip install jira (für Jira-API)
# - Jira-Zugangsdaten: Ersetze die Platzhalter mit deinen Jira-URL, API-Token usw.
# - Outlook muss auf dem System installiert und konfiguriert sein.
# - Das Skript läuft auf Windows 11.
# - Für Automatisierung: Verwende den Windows Task Scheduler, um das Skript periodisch auszuführen.

import win32com.client
from jira import JIRA
import os
import logging
from datetime import datetime, timedelta

# Logging einrichten für Debugging
logging.basicConfig(
    filename="email_to_jira.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# Jira-Konfiguration (ersetze mit deinen Daten)
JIRA_SERVER = "https://your-jira-instance.atlassian.net"  # Deine Jira-URL
JIRA_EMAIL = "your.email@example.com"  # Deine Jira-E-Mail
JIRA_API_TOKEN = "your_api_token"  # Dein Jira-API-Token (erstellen unter https://id.atlassian.com/manage-profile/security/api-tokens)
JIRA_PROJECT_KEY = "PROJ"  # Schlüssel deines Jira-Projekts, z.B. 'BUG'
JIRA_ISSUE_TYPE = "Task"  # Issue-Typ, z.B. 'Bug', 'Task'

# Outlook-Konfiguration
OUTLOOK_FOLDER_NAME = "Inbox"  # Ordner, der überwacht werden soll (z.B. 'Inbox')
LOOKBACK_DAYS = 1  # Nur E-Mails der letzten X Tage prüfen, um Duplikate zu vermeiden

# Komplexe Regeln: Definiere Regeln als Liste von Dictionaries
# Jede Regel enthält Filterkriterien und Jira-spezifische Mapping
RULES = [
    {
        "name": "Hohe Priorität - Support-Anfragen",
        "filters": {
            "subject_contains": [
                "Support",
                "Hilfe",
            ],  # Betreff enthält eines dieser Wörter (OR)
            "sender_contains": ["support@domain.com"],  # Absender enthält (OR)
            "body_contains": ["dringend"],  # Body enthält (AND zu anderen)
            "has_attachments": True,  # Muss Anhänge haben
        },
        "jira_mapping": {
            "priority": "High",
            "labels": ["Support", "Urgent"],
            "custom_fields": {
                "customfield_10010": "Support-Team"  # Beispiel für ein Custom Field (ID aus Jira holen)
            },
        },
    },
    {
        "name": "Niedrige Priorität - Info-Mails",
        "filters": {
            "subject_contains": ["Info", "Newsletter"],
            "sender_contains": [],
            "body_contains": [],
            "has_attachments": False,
        },
        "jira_mapping": {"priority": "Low", "labels": ["Info"], "custom_fields": {}},
    },
    # Füge weitere Regeln hinzu, z.B. basierend auf Absender, Betreff usw.
]


# Funktion zum Überprüfen, ob eine E-Mail einer Regel entspricht
def matches_rule(email, rule_filters):
    subject = email.Subject.lower()
    sender = email.SenderEmailAddress.lower()
    body = email.Body.lower()
    attachments = (
        email.Attachments.Count > 0
        if rule_filters.get("has_attachments") is not None
        else True
    )

    # Überprüfe subject_contains (OR)
    if rule_filters.get("subject_contains"):
        if not any(
            word.lower() in subject for word in rule_filters["subject_contains"]
        ):
            return False

    # Überprüfe sender_contains (OR)
    if rule_filters.get("sender_contains"):
        if not any(word.lower() in sender for word in rule_filters["sender_contains"]):
            return False

    # Überprüfe body_contains (AND)
    if rule_filters.get("body_contains"):
        if not all(word.lower() in body for word in rule_filters["body_contains"]):
            return False

    # Überprüfe has_attachments
    if (
        "has_attachments" in rule_filters
        and attachments != rule_filters["has_attachments"]
    ):
        return False

    return True


# Funktion zum Erstellen eines Jira-Tickets aus einer E-Mail
def create_jira_issue(jira_client, email, rule_mapping):
    summary = email.Subject
    description = f"From: {email.SenderEmailAddress}\nReceived: {email.ReceivedTime}\n\n{email.Body}"

    issue_dict = {
        "project": {"key": JIRA_PROJECT_KEY},
        "summary": summary,
        "description": description,
        "issuetype": {"name": JIRA_ISSUE_TYPE},
        "priority": {"name": rule_mapping.get("priority", "Medium")},
        "labels": rule_mapping.get("labels", []),
    }

    # Füge Custom Fields hinzu
    custom_fields = rule_mapping.get("custom_fields", {})
    issue_dict.update(custom_fields)

    try:
        new_issue = jira_client.create_issue(fields=issue_dict)
        logging.info(f"Jira-Issue erstellt: {new_issue.key}")

        # Anhänge hinzufügen
        if email.Attachments.Count > 0:
            temp_dir = os.path.join(os.getcwd(), "temp_attachments")
            os.makedirs(temp_dir, exist_ok=True)
            for attachment in email.Attachments:
                temp_path = os.path.join(temp_dir, attachment.FileName)
                attachment.SaveAsFile(temp_path)
                jira_client.add_attachment(new_issue, temp_path)
                os.remove(temp_path)  # Aufräumen
            logging.info(f"Anhänge zu {new_issue.key} hinzugefügt")

        return new_issue.key
    except Exception as e:
        logging.error(f"Fehler beim Erstellen des Issues: {str(e)}")
        return None


# Hauptfunktion
def main():
    try:
        # Jira-Client initialisieren
        jira_options = {"server": JIRA_SERVER}
        jira_client = JIRA(
            options=jira_options, basic_auth=(JIRA_EMAIL, JIRA_API_TOKEN)
        )

        # Outlook initialisieren
        outlook = win32com.client.Dispatch("Outlook.Application")
        namespace = outlook.GetNamespace("MAPI")

        # Mehrere Postfächer handhaben: Alle Accounts durchlaufen
        for store in namespace.Stores:
            if store.ExchangeStoreType == 3:  # Nur E-Mail-Stores (nicht PST usw.)
                try:
                    inbox = store.GetRootFolder().Folders[OUTLOOK_FOLDER_NAME]
                    logging.info(f"Verarbeite Postfach: {store.DisplayName}")

                    # E-Mails der letzten LOOKBACK_DAYS Tage filtern
                    cutoff_date = datetime.now() - timedelta(days=LOOKBACK_DAYS)
                    emails = inbox.Items
                    emails.Sort("[ReceivedTime]", True)  # Neueste zuerst

                    for email in emails:
                        if email.Class == 43:  # Nur E-Mail-Items
                            received_time = email.ReceivedTime
                            if received_time < cutoff_date:
                                break  # Ältere E-Mails überspringen

                            # Regeln anwenden
                            for rule in RULES:
                                if matches_rule(email, rule["filters"]):
                                    issue_key = create_jira_issue(
                                        jira_client, email, rule["jira_mapping"]
                                    )
                                    if issue_key:
                                        # Optional: E-Mail als verarbeitet markieren (z.B. verschieben oder Flag setzen)
                                        # email.Move(some_processed_folder)
                                        logging.info(
                                            f"E-Mail '{email.Subject}' in Issue {issue_key} umgewandelt (Regel: {rule['name']})"
                                        )
                                    break  # Nur eine Regel pro E-Mail anwenden
                except Exception as e:
                    logging.error(
                        f"Fehler beim Verarbeiten von Postfach {store.DisplayName}: {str(e)}"
                    )
    except Exception as e:
        logging.error(f"Globaler Fehler: {str(e)}")


if __name__ == "__main__":
    main()
