import os
import discord
import google.auth
import googleapiclient.discovery
from google.cloud import firestore
import requests

env_spreadsheet = os.environ.get('SPREADSHEET', '')
env_range = os.environ.get('RANGE', '')
env_client = os.environ.get('CLIENT', '')
env_bireyselgelenler = int(os.environ.get('BIREYSELGELENLER', ''))
env_aramayagelenler = int(os.environ.get('ARAMAYAGELENLER', ''))
env_ekiplegelenler = int(os.environ.get('EKIPLEGELENLER', ''))
env_mailgun = os.environ.get('MAILGUN', '')
env_mailgunapi = os.environ.get('MAILGUNAPI', '')
env_mail = os.environ.get('MAIL', '')
env_firestore = os.environ.get('FIRESTORE', '')
scopes = ['https://www.googleapis.com/auth/spreadsheets.readonly']


def hello_pubsub(event, context):
    """Triggered from a message on a Cloud Pub/Sub topic.
    Args:
         event (dict): Event payload.
         context (google.cloud.functions.Context): Metadata for the event.
    """
    class MyClient(discord.Client):
        async def on_ready(self):
            bireyselgelenler = self.get_channel(env_bireyselgelenler)
            aramayagelenler = self.get_channel(env_aramayagelenler)
            ekiplegelenler = self.get_channel(env_ekiplegelenler)

            credentials, project = google.auth.default(scopes=scopes)
            service = googleapiclient.discovery.build(
                'sheets', 'v4', credentials=credentials)

            # Call the Sheets API
            sheet = service.spreadsheets()
            result = sheet.values().get(spreadsheetId=env_spreadsheet,
                                        range=env_range).execute()
            values = result.get('values', [])[1:]

            db = firestore.Client()
            doc_ref = db.collection(env_firestore).document('sent')

            oldmails = doc_ref.get().get('email')
            newmails = []

            dispatches = 0

            for applicant in values:
                mail = applicant[3].strip()
                newmails.append(mail)
                join = applicant[8].lower()
                if mail not in oldmails:
                    invite = ""
                    if "ev" in join:  # Team
                        invite = await ekiplegelenler.create_invite(max_uses=1, unique=True)
                    elif "ol" in join:  # Matching
                        invite = await aramayagelenler.create_invite(max_uses=1, unique=True)
                    elif "ba" in join:  # Single
                        invite = await bireyselgelenler.create_invite(max_uses=1, unique=True)

                    requests.post(
                        env_mailgun,
                        auth=("api", env_mailgunapi),
                        data={"from": env_mail,
                              "to": [mail],
                              "subject": "Discord Sunucusu!",
                              "html": f'<div style="font-family: system-ui; justify-content: center; align-items: center; width: 100%; height:100%; text-align: center;"><table><tr><h1>Solution Marathon 2020 burada!</h1></tr><tr><p>Discord kanalına katılmak için aşağıdaki butona tıklayabilirsin.</p></tr><tr><div style="background-color: rgb(114, 137, 218); border-radius: 1em; padding: 0.1em 1.0em;"><h1><a href="{invite}" style="color: white;">BURAYA TIKLA!</a></h1></div></tr><tr><a href="https://forms.gle/VCgcTURTaoj1H4ax7">Sıkıntı yaşıyorsan buraya tıkla</a></tr></table></div>'})

                    dispatches = dispatches + 1

            print(dispatches)

            doc_ref.set({"email": newmails})

            self.result = oldmails
            await self.logout()

    client = MyClient()
    client.run(env_client)
    print(str(client.result))
