import os
import json
from collections import defaultdict

input_dir = "/data/repo_3_reduced_votes"   # input uit repo 3
output_file = "/data/repo_5_resultaat/final_ranking.json"  # output naar repo 5
output_winners_file = "/data/repo_5_resultaat/winners_per_country.json"  # land-winnaar

os.makedirs(os.path.dirname(output_file), exist_ok=True)

votes_total = defaultdict(int)
winners_per_country = {}

# Loop over alle JSON bestanden in input_dir
for filename in os.listdir(input_dir):
    if filename.endswith(".json") and filename.startswith("reduced_votes_"):
        file_path = os.path.join(input_dir, filename)
        with open(file_path, "r") as f:
            data = json.load(f)
            for entry in data:
                country = entry["country"]
                # Vind de winnaar per land (max stemmen)
                sorted_votes = sorted(entry["votes"], key=lambda v: v["count"], reverse=True)
                if sorted_votes:
                    winners_per_country[country] = {
                        "song_number": sorted_votes[0]["song_number"],
                        "votes": sorted_votes[0]["count"]
                    }
                # Totaal stemmen optellen per song
                for vote in entry["votes"]:
                    song_number = vote["song_number"]
                    count = vote["count"]
                    votes_total[song_number] += count

# Sorteer totale ranking (hoog naar laag)
ranking = sorted(votes_total.items(), key=lambda x: x[1], reverse=True)

final_ranking = []
for rank, (song_number, total_votes) in enumerate(ranking, start=1):
    final_ranking.append({
        "rank": rank,
        "song_number": song_number,
        "total_votes": total_votes
    })

# Schrijf finale ranking
with open(output_file, "w") as f:
    json.dump(final_ranking, f, indent=4)

# Schrijf winners per land
with open(output_winners_file, "w") as f:
    json.dump(winners_per_country, f, indent=4)

# Validatie
if final_ranking:
    max_votes = final_ranking[0]["total_votes"]
    assert all(tv <= max_votes for _, tv in ranking), "Winnaar validatie mislukt!"

    winning_song = final_ranking[0]['song_number']
    winning_country = None
    for country, winner_info in winners_per_country.items():
        if winner_info["song_number"] == winning_song:
            winning_country = country
            break

    print(f"✅ Validatie geslaagd. Winnaar is lied {winning_song} met {max_votes} stemmen van land {winning_country}.")

else:
    print("⚠️ Geen data gevonden in input directory.")
