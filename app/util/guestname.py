import random

from models.user import UserModel

adjectives = [
    "Schnell", "Klug", "Stark", "Mutig", "Flink", "Leis", "Tapfer", "Freundlich", "Witzig", "Weis",
    "Kreativ", "Neugierig", "Laut", "Energetisch", "Entschlossen", "Gewitzt", "Verspielt", "Sanft",
    "Ruhig", "Schlau", "Frech", "Zäh", "Listig", "Wachsam", "Glücklich", "Hartnäckig", "Lieb", "Achtsam",
    "Bescheiden", "Eifrig", "Geduldig", "Zuverlässig", "Charmant", "Treu", "Fröhlich", "Optimistisch",
    "Hilfsbereit", "Einfühlsam", "Beharrlich", "Gelassen", "Besonnen", "Ausdauernd", "Anpassungsfähig",
    "Vorsichtig", "Humorvoll", "Erfinderisch", "Respektvoll", "Aufmerksam", "Ordentlich", "Selbstbewusst",
    "Gerecht", "Warmherzig", "Großzügig", "Leidenschaftlich", "Aufrichtig", "Gedankenvoll", "Fantasievoll",
    "Dankbar", "Schlagfertig", "Unerschrocken", "Herzlich"
]

animals = {
    "Tiger":      "der", "Fuchs": "der", "Adler": "der", "Loewe": "der", "Wolf": "der", "Panda": "der",
    "Koala":      "der", "Oktopus": "der", "Chamäleon": "das", "Alpaka": "das", "Kranich": "der",
    "Delfin":     "der", "Nashorn": "das", "Pfau": "der", "Erdmännchen": "das", "Falke": "der",
    "Zebra":      "das", "Wombat": "der", "Flamingo": "der", "Leguan": "der", "Koboldmaki": "der",
    "Pinguin":    "der", "Schakal": "der", "Wal": "der", "Vielfraß": "der", "Mungo": "der",
    "Faultier":   "das", "Tapir": "der", "Eule": "die", "Seepferdchen": "das",
    "Giraffe":    "die", "Nashornvogel": "der", "Dachs": "der", "Elch": "der", "Murmeltier": "das",
    "Känguru":    "das", "Seehund": "der", "Kojote": "der", "Kakadu": "der", "Ameisenbär": "der",
    "Luchs":      "der", "Schildkröte": "die", "Hyäne": "die", "Otter": "der", "Orang-Utan": "der",
    "Papagei":    "der", "Warzenschwein": "das", "Bär": "der", "Möwe": "die", "Schneeleopard": "der",
    "Fledermaus": "die", "Eisbär": "der", "Kormoran": "der", "Manta": "der", "Rentier": "das",
    "Wisent":     "der", "Marder": "der", "Gepard": "der", "Stachelschwein": "das", "Igel": "der",
    "Phillip":    "der", "Robin": "der", "Annabelle": "die", "Felix": "der", "Lars": "der",
    "Xaver":      "der", "JanL": "der", "JanR": "der", "JanW": "der", "Niklas": "der", "Max": "der",
}


def adjust_adjective(adj, gender):
    if gender == "der":
        return adj + "er"
    elif gender == "die":
        return adj + "e"
    elif gender == "das":
        return adj + "es"
    else:
        return adj


def generate_guestname():
    adj = random.choice(adjectives)
    animal, article = random.choice(list(animals.items()))
    adj_corrected = adjust_adjective(adj, article)
    return f"{adj_corrected}{animal}"


def generate_random_name_and_check_if_exists(db):
    max_tries = 1000
    for _ in range(max_tries):
        name = generate_guestname()
        if not db.query(UserModel.username).filter_by(username=name).first():
            return name
    raise ValueError("Max tries exceeded while generating a unique guestname")
