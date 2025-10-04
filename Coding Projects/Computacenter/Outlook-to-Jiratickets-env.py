import win32com.client
from jira import JIRA
import os
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Lade Umgebungsvariablen aus .env-Datei
load_dotenv()

# Logging einrichten für Debugging
logging.basicConfig(filename='email_to_jira.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Jira-Konfiguration aus Umgebungsvariablen
JIRA_SERVER = os.getenv('JIRA_SERVER')
JIRA_EMAIL = os.getenv('JIRA_EMAIL')
JIRA_API_TOKEN = os.getenv('JIRA_API_TOKEN')
JIRA_PROJECT_KEY = os.getenv('JIRA_PROJECT_KEY')
JIRA_ISSUE_TYPE = os.getenv('JIRA_ISSUE_TYPE', 'Task')  # Standardwert: 'Task'

# Outlook-Konfiguration aus Umgebungsvariablen
OUTLOOK_FOLDER_NAME = os.getenv('OUTLOOK_FOLDER_NAME', 'Inbox')  # Standardwert: 'Inbox'
LOOKBACK_DAYS = int(os.getenv('LOOKBACK_DAYS', '1'))  # Standardwert: 1 Tag

# Komplexe Regeln: Definiere Regeln als Liste von Dictionaries
RULES = [
    {
        'name': 'Hohe Priorität - Support-Anfragen',
        'filters': {
            'subject_contains': ['Support', 'Hilfe'],  # Betreff enthält eines dieser Wörter (OR)
            'sender_contains': ['support@domain.com'],  # Absender enthält (OR)
            'body_contains': ['dringend'],  # Body enthält (AND zu anderen)
            'has_attachments': True  # Muss Anhänge haben
        },
        'jira_mapping': {
            'priority': 'High',
            'labels': ['Support', 'Urgent'],
            'custom_fields': {
                'customfield_10010': 'Support-Team'  # Beispiel für ein Custom Field
            }
        }
    },
    {
        'name': 'Niedrige Priorität - Info-Mails',
        'filters': {
            'subject_contains': ['Info', 'Newsletter'],
            'sender_contains': [],
            'body_contains': [],
            'has_attachments': False
        },
        'jira_mapping': {
            'priority': 'Low',
            'labels': ['Info'],
            'custom_fields': {}
        }
    }
]

# Funktion zum Überprüfen, ob eine E-Mail einer Regel entspricht
def matches_rule(email, rule_filters):
    subject = email.Subject.lower()
    sender = email.SenderEmailAddress.lower()
    body = email.Body.lower()
    attachments = email.Attachments.Count > 0 if rule_filters.get('has_attachments') is not None else True
    
    if rule_filters.get('subject_contains'):
        if not any(word.lower() in subject for word in rule_filters['subject_contains']):
            return False
    
    if rule_filters.get('sender_contains'):
        if not any(word.lower() in sender for word in rule_filters['sender_contains']):
            return False
    
    if rule_filters.get('body_contains'):
        if not all(word.lower() in body for word in rule_filters['body_contains']):
            return False
    
    if 'has_attachments' in rule_filters and attachments != rule_filters['has_attachments']:
        return False
    
    return True

# Funktion zum Erstellen eines Jira-Tickets aus einer E-Mail
def create_jira_issue(jira_client, email, rule_mapping):
    summary = email.Subject
    description = f"From: {email.SenderEmailAddress}\nReceived: {email.ReceivedTime}\n\n{email.Body}"
    
    issue_dict = {
        'project': {'key': JIRA_PROJECT_KEY},
        'summary': summary,
        'description': description,
        'issuetype': {'name': JIRA_ISSUE_TYPE},
        'priority': {'name': rule_mapping.get('priority', 'Medium')},
        'labels': rule_mapping.get('labels', [])
    }
    
    custom_fields = rule_mapping.get('custom_fields', {})
    issue_dict.update(custom_fields)
    
    try:
        new_issue = jira_client.create_issue(fields=issue_dict)
        logging.info(f"Jira-Issue erstellt: {new_issue.key}")
        
        if email.Attachments.Count > 0:
            temp_dir = os.path.join(os.getcwd(), 'temp_attachments')
            os.makedirs(temp_dir, exist_ok=True)
            for attachment in email.Attachments:
                temp_path = os.path.join(temp_dir, attachment.FileName)
                attachment.SaveAsFile(temp_path)
                jira_client.add_attachment(new_issue, temp_path)
                os.remove(temp_path)
            logging.info(f"Anhänge zu {new_issue.key} hinzugefügt")
        
        return new_issue.key
    except Exception as e:
        logging.error(f"Fehler beim Erstellen des Issues: {str(e)}")
        return None

# Hauptfunktion
def main():
    try:
        # Jira-Client initialisieren
        jira_options = {'server': JIRA_SERVER}
        jira_client = JIRA(options=jira_options, basic_auth=(JIRA_EMAIL, JIRA_API_TOKEN))
        
        # Outlook initialisieren
        outlook = win32com.client.Dispatch("Outlook.Application")
        namespace = outlook.GetNamespace("MAPI")
        
        for store in namespace.Stores:
            if store.ExchangeStoreType == 3:
                try:
                    inbox = store.GetRootFolder().Folders[OUTLOOK_FOLDER_NAME]
                    logging.info(f"Verarbeite Postfach: {store.DisplayName}")
                    
                    cutoff_date = datetime.now() - timedelta(days=LOOKBACK_DAYS)
                    emails = inbox.Items
 emails.Sort("[ReceivedTime]", True)
                    
                    for email in emails:
                        if email.Class == 43:
                            received_time = email.ReceivedTime
                            if received_time < cutoff_date:
                                break
                            
                            for rule in RULES:
                                if matches_rule(email, rule['filters']):
                                    issue_key = create_jira_issue(jira_client, email, rule['jira_mapping'])
                                    if issue_key:
                                        logging.info(f"E-Mail '{email.Subject}' in Issue {issue_key} umgewandelt (Regel: {rule['name']})")
                                    break
                except Exception as e:
                    logging.error(f"Fehler beim Verarbeiten von Postfach {store.DisplayName}: {str(e)}")
    except Exception as e:
        logging.error(f"Globaler Fehler: {str(e)}")

if __name__ == "__main__":
    main()