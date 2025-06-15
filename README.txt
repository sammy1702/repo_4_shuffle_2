shuffle 2: run lukt. maar met -v en mount krijg ik bestanden locaal in repo 5 terecht
docker run \
  -v /home/devasc/EUV_TEST/euv-pipeline/repo_5_resultaat/resultaat:/app/resultaat \
  -v /home/devasc/EUV_TEST/euv-pipeline/repo_5_resultaat/ranking_per_land:/app/ranking_per_land \
  -v /home/devasc/EUV_TEST/euv-pipeline/repo_5_resultaat/reduced_votes:/app/reduced_votes \
  shuffle_2_app
