import os
import json
import io
from collections import defaultdict
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload

# === CONFIG ===
SERVICE_ACCOUNT_FILE = 'credentials.json'
FOLDER_ID_REDUCED = '1Nh2_-lsQpUDY3E5vuQqgGsHV7Vgbj8AT'  # euv-data/reduced_votes
FOLDER_ID_RESULTAAT = '1cDNDyPKhSDelf2YuL-2jtjgvTXoPO0W6'  # euv-data/resultaat
FOLDER_ID_RANKING = '1Jt3o0S9crNExpYCy3H5O_d1w8AXgMcFf'   # euv-data/ranking_per_land

INPUT_DIR = os.path.expanduser("/tmp/euv_shuffle2_input")
OUTPUT_DIR = os.path.expanduser("/tmp/euv_shuffle2_output")
FINAL_RANKING_FILE = os.path.join(OUTPUT_DIR, "final_ranking.json")
WINNERS_FILE = os.path.join(OUTPUT_DIR, "winners_per_country.json")

# === SETUP GOOGLE DRIVE API ===
SCOPES = ['https://www.googleapis.com/auth/drive']
creds = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build('drive', 'v3', credentials=creds)


def upload_to_drive(filepath, drive_filename, folder_id):
    file_metadata = {
        'name': drive_filename,
        'parents': [folder_id]
    }
    media = MediaFileUpload(filepath, resumable=True)
    service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    print(f"☁️ Geüpload naar Google Drive: {drive_filename} → map ID {folder_id}")


# === DOWNLOAD STEMBESTANDEN ===
print("🔽 Downloaden van stemdata uit Google Drive...")
os.makedirs(INPUT_DIR, exist_ok=True)

results = service.files().list(
    q=f"'{FOLDER_ID_REDUCED}' in parents and trashed = false",
    fields="files(id, name)").execute()
files = results.get('files', [])

for file in files:
    if file['name'].endswith(".json") and file['name'].startswith("reduced_votes_"):
        file_id = file['id']
        file_name = file['name']
        request = service.files().get_media(fileId=file_id)
        local_path = os.path.join(INPUT_DIR, file_name)
        with io.FileIO(local_path, 'wb') as fh:
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()
        print(f"✅ Gedownload: {file_name}")


# === STEMVERWERKING ===
print("⚙️ Verwerken van stemmen...")
os.makedirs(OUTPUT_DIR, exist_ok=True)

votes_total = defaultdict(int)
winners_per_country = {}
per_country_votes = defaultdict(lambda: defaultdict(int))  # {country: {song: count}}

for filename in os.listdir(INPUT_DIR):
    if filename.endswith(".json") and filename.startswith("reduced_votes_"):
        file_path = os.path.join(INPUT_DIR, filename)
        with open(file_path, "r") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                print(f"⚠️ Ongeldig JSON-bestand: {filename}")
                continue

            if not data:
                print(f"⚠️ Leeg bestand: {filename}")
                continue

            for entry in data:
                if "country" not in entry or "votes" not in entry:
                    print(f"⚠️ Fout in structuur: {filename} → entry mist 'country' of 'votes'")
                    continue

                country = entry["country"]
                sorted_votes = sorted(entry["votes"], key=lambda v: v["count"], reverse=True)
                if sorted_votes:
                    winners_per_country[country] = {
                        "song_number": sorted_votes[0]["song_number"],
                        "votes": sorted_votes[0]["count"]
                    }

                for vote in entry["votes"]:
                    song_number = vote["song_number"]
                    count = vote["count"]
                    votes_total[song_number] += count
                    per_country_votes[country][song_number] += count

print(f"📊 Totaal aantal unieke songs geteld: {len(votes_total)}")


# === FINALE RANKING TOTAAL ===
ranking = sorted(votes_total.items(), key=lambda x: x[1], reverse=True)
final_ranking = [
    {"rank": rank + 1, "song_number": song_number, "total_votes": total_votes}
    for rank, (song_number, total_votes) in enumerate(ranking)
]

# === PER LAND: JSON RANKING ===
for country, song_counts in per_country_votes.items():
    country_ranking = sorted(song_counts.items(), key=lambda x: x[1], reverse=True)
    output_path = os.path.join(OUTPUT_DIR, f"{country}_ranking.json")
    country_result = [
        {"rank": rank + 1, "song_number": song, "votes": count}
        for rank, (song, count) in enumerate(country_ranking)
    ]
    with open(output_path, "w") as f:
        json.dump(country_result, f, indent=4)
    print(f"📁 Opgeslagen: {output_path}")
    upload_to_drive(output_path, f"{country}_ranking.json", FOLDER_ID_RANKING)

# === OPSLAAN EN UPLOADEN FINAL RANKING ===
with open(FINAL_RANKING_FILE, "w") as f:
    json.dump(final_ranking, f, indent=4)
upload_to_drive(FINAL_RANKING_FILE, "final_ranking.json", FOLDER_ID_RESULTAAT)

with open(WINNERS_FILE, "w") as f:
    json.dump(winners_per_country, f, indent=4)
upload_to_drive(WINNERS_FILE, "winners_per_country.json", FOLDER_ID_RESULTAAT)


# === VALIDATIE ===
if final_ranking:
    max_votes = final_ranking[0]["total_votes"]
    assert all(tv <= max_votes for _, tv in ranking), "Winnaar validatie mislukt!"
    winning_song = final_ranking[0]['song_number']
    winning_country = None
    for country, winner_info in winners_per_country.items():
        if winner_info["song_number"] == winning_song:
            winning_country = country
            break
    print(f"🏆 Validatie geslaagd. Winnaar is lied {winning_song} met {max_votes} stemmen van land {winning_country}.")
else:
    print("⚠️ Geen geldige stemdata gevonden.")
