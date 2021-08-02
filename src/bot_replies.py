import pasta


GENERAL_M_MISTAKE_REPLY = "Murteista johtuen 'niinpä', 'kunpa', 'onpa' kirjoitetaan usein virheellisesti käyttäen " \
                          "M-kirjainta N-kirjaimen sijaan."

REPLIES_BY_WORD = {
    'rokot': "Heh heh, kohta voidaankin taas kätellä, kun on nämä rokotteet.",
    'orona': "Heh heh, nyt ei voidakaan kätellä, kun on tämä korona.",
    'enään': "Yleiskielessä käytetään muotoa enää eikä länsimurteissa tavallista muotoa enään.",
    'mielummin': "Tarkoittanette 'mieluummin', joka on 'mielummin' -sanan oikeinkirjoitettu muoto.",
    'niimpä': GENERAL_M_MISTAKE_REPLY,
    'kumpa': GENERAL_M_MISTAKE_REPLY,
    'ompa': GENERAL_M_MISTAKE_REPLY,
    'kuullostaa': 'Yleiskielessä käymättömään kuullostaa-muotoon on ehkä päädytty kuulla-sanan mukaan. Sen taivutusmuodoissa ei kuitenkaan ole kahta ällää. Oikea kirjoitusmuoto on siis kuulostaa.',
    'sydämm': "Joissakin sanoissa tai sanojen taivutusmuodoissa voi puheessa kuulua pitkä m-äänne, vaikka kirjoitettaisiinkin vain yksi m, esimerkiksi: 'sydämellä', 'morsiamella', 'avoimuus'."
              "Sana sydän taipuu siis sydän : sydämen (vrt. avain : avaimen). Yksi m-kirjain on myös sydän-sanan johdoksissa, esim. sydämellinen, sydämellisin terveisin."
}


def replies_by_content(content: str) -> list:
    replies = []
    if len(content) > 1000 and "suihkuun" in pasta.pastas:
        replies.append(pasta.pastas.get("suihkuun"))

    for matched_word in REPLIES_BY_WORD.keys():
        for word in content.lower().split():
            if word.startswith(matched_word) or word.endswith(matched_word):
                replies.append(REPLIES_BY_WORD[matched_word])
                break
    return replies
