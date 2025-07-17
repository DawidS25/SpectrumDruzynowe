import streamlit as st
import random
import pandas as pd
import os
import io
import base64
import requests
from datetime import datetime


# ------------------------------
# PYTANIA
# ------------------------------
df = pd.read_csv('questions.csv', sep=';')

def filter_by_category(cat):
    return df[df['categories'] == cat].to_dict(orient='records')

funny_questions = filter_by_category('Śmieszne')
worldview_questions = filter_by_category('Światopoglądowe')
relationship_questions = filter_by_category('Związkowe')
spicy_questions = filter_by_category('Pikantne')
casual_questions = filter_by_category('Luźne')
past_questions = filter_by_category('Przeszłość')
would_you_rather_questions = filter_by_category('Wolisz')
dylema_questions = filter_by_category('Dylematy')

CATEGORIES = {
    "Śmieszne": funny_questions,
    "Światopoglądowe": worldview_questions,
    "Związkowe": relationship_questions,
    "Pikantne": spicy_questions,
    "Luźne": casual_questions,
    "Przeszłość": past_questions,
    "Wolisz": would_you_rather_questions,
    "Dylematy": dylema_questions
}

CATEGORY_EMOJIS = {
    "Śmieszne": "😂",
    "Światopoglądowe": "🌍",
    "Związkowe": "❤️",
    "Pikantne": "🌶️",
    "Luźne": "😎",
    "Przeszłość": "📜",
    "Wolisz": "🤔",
    "Dylematy": "⚖️"
}

# ------------------------------
# SESJA
# ------------------------------
defaults = {
    "team_names": ["Niebiescy", "Czerwoni"],
    "team_players": {"Niebiescy": [], "Czerwoni": []},
    "use_players": True,  # zawsze True, bo nie ma opcji bez imion
    "chosen_categories": [],
    "used_ids": set(),
    "current_question": None,
    "scores": {},
    "step": "setup",
    "questions_asked": 0,
    "ask_continue": False,
    "guesser_points": None,
    "extra_point": None,
    "results_data": []
}

for key, value in defaults.items():
    if key not in st.session_state:
        if isinstance(value, set):
            st.session_state[key] = value.copy()
        elif isinstance(value, list):
            st.session_state[key] = value[:] if not isinstance(value, dict) else value.copy()
        else:
            st.session_state[key] = value

# ------------------------------
# UPLOAD DO GITHUB (zmieniony fragment)
# ------------------------------

def upload_to_github(file_path, repo, path_in_repo, token, commit_message):
    with open(file_path, "rb") as f:
        content = f.read()
    b64_content = base64.b64encode(content).decode("utf-8")

    url = f"https://api.github.com/repos/{repo}/contents/{path_in_repo}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }

    data = {
        "message": commit_message,
        "content": b64_content,
        "branch": "main"
    }

    response = requests.put(url, headers=headers, json=data)
    return response

def get_next_game_number(repo, token, folder="wyniki"):
    url = f"https://api.github.com/repos/{repo}/contents/{folder}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return 1

    files = response.json()
    today_str = datetime.today().strftime("%Y-%m-%d")
    max_num = 0
    for file in files:
        name = file["name"]
        if name.startswith("gra") and name.endswith(".xlsx") and today_str in name:
            try:
                num_part = name[3:6]
                num = int(num_part)
                if num > max_num:
                    max_num = num
            except:
                pass
    return max_num + 1

# ------------------------------
# FUNKCJA LOSUJĄCA PYTANIA
# ------------------------------
def draw_question():
    all_qs = []
    for cat in st.session_state.chosen_categories:
        all_qs.extend(CATEGORIES[cat])
    available = [q for q in all_qs if q["id"] not in st.session_state.used_ids]
    if not available:
        return None
    question = random.choice(available)
    st.session_state.used_ids.add(question["id"])
    return question

# ------------------------------
# SETUP - wybór drużyn i graczy (TYLKO IMIONA, bez opcji bez imion)
# ------------------------------
if st.session_state.step in ["setup", "categories", "end"]:
    st.title("🎲 Spectrum")

if st.session_state.step == "setup":
    st.header("🎭 Wprowadź nazwy drużyn i imiona graczy")

    if "team_names" not in st.session_state:
        st.session_state.team_names = ["Niebiescy", "Czerwoni"]

    if "players_team_0" not in st.session_state:
        st.session_state.players_team_0 = ["", ""]  # start z 2 polami
    if "players_team_1" not in st.session_state:
        st.session_state.players_team_1 = ["", ""]

    # Nazwy drużyn
    col1, col2 = st.columns(2)
    with col1:
        st.session_state.team_names[0] = st.text_input("👫 Nazwa drużyny 1", value=st.session_state.team_names[0])
    with col2:
        st.session_state.team_names[1] = st.text_input("👫 Nazwa drużyny 2", value=st.session_state.team_names[1])

    # Funkcja renderująca pola z imionami i przyciskiem dodaj
    def render_players_inputs(team_index):
        st.write(f"**Imiona graczy drużyny {st.session_state.team_names[team_index]}:**")
        players_key = f"players_team_{team_index}"
        players_list = st.session_state[players_key]

        # Wyświetl pola tekstowe
        for i, player_name in enumerate(players_list):
            new_name = st.text_input(f"🙋‍♂️ Imię {i + 1}. osoby z drużyny {st.session_state.team_names[team_index]}",
                                    value=player_name, key=f"player_{team_index}_{i}")
            st.session_state[players_key][i] = new_name.strip()

        # Przycisk dodawania kolejnego gracza (max 7)
        if len(players_list) < 7:
            if st.button(f"➕ Dodaj kolejnego gracza do drużyny {st.session_state.team_names[team_index]}",
                         key=f"add_player_{team_index}"):
                st.session_state[players_key].append("")
                st.rerun()

    col1, col2 = st.columns(2)
    with col1:
        render_players_inputs(0)
    with col2:
        render_players_inputs(1)

    # Walidacja - wymuszamy min 2 graczy na drużynę, max 7
    def valid_players_count():
        len0 = len([p for p in st.session_state.players_team_0 if p.strip()])
        len1 = len([p for p in st.session_state.players_team_1 if p.strip()])
        if len0 < 2 or len1 < 2:
            return False
        if len0 > 7 or len1 > 7:
            return False
        return True

    if not valid_players_count():
        st.warning("⚠️ Każda drużyna musi mieć od 2 do 7 graczy (łącznie minimum 4, maksimum 14 imion).")

    # Przycisk Dalej tylko jeśli valid
    if valid_players_count():
        if st.button("✅ Dalej"):
            # Zapisz nazw drużyn i graczy
            st.session_state.scores = {}
            st.session_state.results_data = []
            st.session_state.team_names = [st.session_state.team_names[0], st.session_state.team_names[1]]

            # Lista wszystkich graczy, żeby ułatwić dalszą obsługę
            all_players = []
            for p in st.session_state.players_team_0:
                if p.strip():
                    all_players.append(p.strip() + "_niebiescy")
            for p in st.session_state.players_team_1:
                if p.strip():
                    all_players.append(p.strip() + "_czerwoni")
            st.session_state.all_players = all_players

            # Punktacja dla drużyn i graczy
            for p in all_players:
                st.session_state.scores[p] = 0

            # Punktacja dla drużyn (klucze nazwy drużyn)
            for t in st.session_state.team_names:
                st.session_state.scores[t] = 0

            # Przypisujemy listy graczy do team_players
            st.session_state.team_players = {
                st.session_state.team_names[0]: [p for p in st.session_state.players_team_0 if p.strip()],
                st.session_state.team_names[1]: [p for p in st.session_state.players_team_1 if p.strip()]
            }

            st.session_state.step = "categories"
            st.rerun()

# ------------------------------
# KATEGORIE - bez zmian
# ------------------------------
if st.session_state.step == "categories":
    st.header("📚 Wybierz kategorie pytań")

    if "category_selection" not in st.session_state:
        st.session_state.category_selection = set()

    cols = st.columns(4)
    for i, cat in enumerate(CATEGORIES.keys()):
        col = cols[i % 4]
        display_name = f"{CATEGORY_EMOJIS.get(cat, '')} {cat}"
        if cat in st.session_state.category_selection:
            if col.button(f"✅ {display_name}", key=f"cat_{cat}"):
                st.session_state.category_selection.remove(cat)
                st.rerun()
        else:
            if col.button(display_name, key=f"cat_{cat}"):
                st.session_state.category_selection.add(cat)
                st.rerun()
    selected_display = [f"{CATEGORY_EMOJIS.get(cat, '')} {cat}" for cat in st.session_state.category_selection]
    st.markdown(f"**Wybrane kategorie:** {', '.join(selected_display) or 'Brak'}")

    if st.session_state.category_selection:
        if st.button("🎯 Rozpocznij grę"):
            st.session_state.chosen_categories = list(st.session_state.category_selection)
            st.session_state.step = "game"
            st.rerun()

# ------------------------------
# LOGIKA GRY
# ------------------------------
if st.session_state.step == "game":
    team1 = st.session_state.team_names[0]
    team2 = st.session_state.team_names[1]
    team1_players = st.session_state.team_players.get(team1, [])
    team2_players = st.session_state.team_players.get(team2, [])
    use_players = st.session_state.use_players  # zawsze True teraz

    max_players = max(len(team1_players), len(team2_players))
    questions_per_round = max_players * 2  # każde pytanie dla jednej z drużyn, razem na rundę tyle pytań

    current_q_num = st.session_state.questions_asked
    current_round = (current_q_num // questions_per_round) + 1
    question_in_round = (current_q_num % questions_per_round) + 1

    # --- EKRAN POTWIERDZENIA KONTYNUACJI PO RUNDZIE ---
    if st.session_state.ask_continue:
        st.markdown(f"### 🥊 Koniec rundy {current_round - 1}")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("▶️ Kontynuuj do kolejnej rundy"):
                st.session_state.ask_continue = False
                st.session_state.current_question = draw_question()
                st.rerun()
        with col2:
            if st.button("⏹️ Zakończ grę"):
                st.session_state.step = "end"
                st.rerun()
        st.stop()


    if not st.session_state.current_question:
        q = draw_question()
        if not q:
            st.success("🎉 Pytania się skończyły! Gratulacje.")
            st.session_state.step = "end"
            st.rerun()
        else:
            st.session_state.current_question = q

    q = st.session_state.current_question

    st.markdown(f"### 🥊 Runda {current_round}")
    st.subheader(f"🧠 Pytanie {current_q_num + 1} – kategoria: *{q['categories']}*")
    st.write(q["text"])
    st.markdown(f"<small>id: {q['id']}</small>", unsafe_allow_html=True)

    if st.button("🔄 Zmień pytanie"):
        new_q = draw_question()
        if new_q:
            st.session_state.current_question = new_q
        st.rerun()

    # Odpowiadający i zgadujący — zgaduje ta sama drużyna co odpowiadający
    if current_q_num % 2 == 0:
        responding_team = team1
        guessing_team = team1  # zgaduje ta sama drużyna co odpowiadający
        other_team = team2    # przeciwnik, który może dostać punkty dodatkowe
        responder_idx = (current_q_num // 2) % len(team1_players)
        responder = team1_players[responder_idx]
    else:
        responding_team = team2
        guessing_team = team2
        other_team = team1
        responder_idx = (current_q_num // 2) % len(team2_players)
        responder = team2_players[responder_idx]

    st.markdown(f"Odpowiada: **{responder}** ({responding_team})")
    st.markdown(f"Zgadują: **{guessing_team}**")

    # Punkty dla zgadującej drużyny (tej samej co odpowiadający)
    st.markdown(f"**Ile punktów zdobywają {guessing_team}?**")
    if "guesser_points" not in st.session_state:
        st.session_state.guesser_points = None

    cols = st.columns(4)
    for i, val in enumerate([0, 2, 3, 4]):
        label = f"✅ {val}" if st.session_state.guesser_points == val else f"{val}"
        if cols[i].button(label, key=f"gp_{val}_{st.session_state.questions_asked}"):
            st.session_state.guesser_points = val
            st.rerun()

    # Punkty dodatkowe dla drużyny przeciwnika
    st.markdown(f"**Dodatkowe punkty dla drużyny {other_team}?**")
    extra_points_options = [0, 1]

    if "extra_point" not in st.session_state:
        st.session_state.extra_point = None

    cols2 = st.columns(len(extra_points_options))
    for i, val in enumerate(extra_points_options):
        label = f"✅ {val}" if st.session_state.extra_point == val else f"{val}"
        if cols2[i].button(label, key=f"ep_{val}_{st.session_state.questions_asked}"):
            st.session_state.extra_point = val
            st.rerun()

    if st.session_state.guesser_points is not None and st.session_state.extra_point is not None:
        if st.button("💾 Zapisz i dalej"):

            guesser_points = st.session_state.guesser_points
            extra_point = st.session_state.extra_point

            # Reset wyborów
            st.session_state.guesser_points = None
            st.session_state.extra_point = None

            # Przydziel punkty:
            # - zgadująca drużyna (ta sama co odpowiadający) dostaje punkty za zgadywanie
            st.session_state.scores[guessing_team] += guesser_points
            # - drużyna przeciwna dostaje punkty dodatkowe
            st.session_state.scores[other_team] += extra_point

            # Punkty dla gracza odpowiadającego:
            responder_points = 0
            responder_points += guesser_points

            def player_key(player_name, team_name):
                return f"{player_name}_{team_name.lower()}"

            st.session_state.scores[player_key(responder, responding_team)] += responder_points

            # Zapis wyników rundy
            data_to_save = {
                "runda": current_round,
                "pytanie_nr": current_q_num + 1,
                "kategoria": q['categories'],
                "pytanie": q['text'],
                "odpowiada_drużyna": responding_team,
                "zgaduje_drużyna": guessing_team,
                "punkty_zgaduje": guesser_points,
                "punkty_odpowiada": extra_point,
                "odpowiada_gracz": responder,
                "punkty_odpowiada_gracz": responder_points
            }
            if "results_data" not in st.session_state:
                st.session_state.results_data = []
            st.session_state.results_data.append(data_to_save)

            # Aktualizuj licznik pytań
            st.session_state.questions_asked += 1

            # Po zakończeniu rundy pytaj o kontynuację
            if st.session_state.questions_asked % questions_per_round == 0:
                st.session_state.ask_continue = True
                st.session_state.current_question = None
            else:
                st.session_state.current_question = draw_question()

            st.rerun()



# ------------------------------
# EKRAN KOŃCOWY
# ------------------------------
if st.session_state.step == "end":
    total_questions = st.session_state.questions_asked
    max_players = max(len(st.session_state.team_players[st.session_state.team_names[0]]),
                      len(st.session_state.team_players[st.session_state.team_names[1]]))
    total_rounds = total_questions // (max_players * 2) if max_players > 0 else 0

    st.success(f"🎉 Gra zakończona! Oto wyniki końcowe:\n\n🥊 Liczba rund: **{total_rounds}** → **{total_questions}** pytań 🧠")

    # --- WYNIKI DRUŻYN ---
    teams_scores = [(team, st.session_state.scores.get(team, 0)) for team in st.session_state.team_names]
    teams_scores.sort(key=lambda x: x[1], reverse=True)

    points_by_team = {team: {"odpowiadanie": 0, "zgadywanie": 0} for team in st.session_state.team_names}
    for row in st.session_state.results_data:
        points_by_team[row["odpowiada_drużyna"]]["odpowiadanie"] += row.get("punkty_odpowiada", 0)
        points_by_team[row["zgaduje_drużyna"]]["zgadywanie"] += row.get("punkty_zgaduje", 0)

    trophies = ["🏆", "🥈"]

    for i, (team, score) in enumerate(teams_scores):
        trophy = trophies[i] if i < len(trophies) else ""
        odp = points_by_team[team]["odpowiadanie"]
        zgad = points_by_team[team]["zgadywanie"]
        st.write(f"{trophy} {team} - {score} punktów ({zgad} za zgadywanie + {odp} dodatkowo)")

    # --- RANKING GRACZY ---
    st.markdown("---")
    st.header("🏅 Ranking graczy")

    # Mapa gracz -> drużyna
    player_to_team = {}
    for team, players in st.session_state.team_players.items():
        for p in players:
            player_to_team[p] = team

    # Sumujemy punkty dla każdego gracza
    player_points = {}
    for row in st.session_state.results_data:
        player = row.get("odpowiada_gracz")
        points = row.get("punkty_odpowiada_gracz", 0)
        if player:
            player_points[player] = player_points.get(player, 0) + points

    if player_points:
        sorted_players = sorted(player_points.items(), key=lambda x: x[1], reverse=True)

        for idx, (player, score) in enumerate(sorted_players, start=1):
            team = player_to_team.get(player)
            # Puchar wg drużyny: pierwsza drużyna 🏆, druga 🥈
            if team == st.session_state.team_names[0]:
                player_trophy = "🏆"
            elif team == st.session_state.team_names[1]:
                player_trophy = "🥈"
            else:
                player_trophy = ""

            st.write(f"{idx}. {player_trophy} **{player}** - {score} punktów")

    else:
        st.write("Brak danych o graczach odpowiadających na pytania.")

    # --- PRZYCISKI KOŃCOWE ---
    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        if st.button("🔁 Jeszcze nie kończymy!"):
            st.session_state.ask_continue = False
            st.session_state.current_question = draw_question()
            st.session_state.step = "game"
            st.rerun()

    with col2:
        if st.button("🎮 Zagraj ponownie"):
            for key, value in defaults.items():
                if isinstance(value, set):
                    st.session_state[key] = value.copy()
                elif isinstance(value, list):
                    st.session_state[key] = value[:] if not isinstance(value, dict) else value.copy()
                else:
                    st.session_state[key] = value
            if "all_players" in st.session_state:
                del st.session_state["all_players"]
            st.rerun()

    # --- Generowanie pliku Excel z wynikami w pamięci ---
    if "results_data" in st.session_state and st.session_state.results_data:

        if "results_uploaded" not in st.session_state:
            st.session_state.results_uploaded = False

        # Przygotuj dane do pliku xlsx wg Twojej struktury
        data_for_xlsx = []
        for row in st.session_state.results_data:
            data_for_xlsx.append({
                "Nr pytania": row.get("pytanie_nr", ""),
                "Treść pytania": row.get("pytanie", ""),
                "Drużyna odpowiadająca": row.get("odpowiada_drużyna", ""),
                "Gracz odpowiadający": row.get("odpowiada_gracz", ""),
                "Punkty drużyny odpowiadającej": row.get("punkty_zgaduje", 0),
                "Dodatkowe punkty dla drugiej drużyny": row.get("punkty_odpowiada", 0),
            })

        import io
        import pandas as pd
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            pd.DataFrame(data_for_xlsx).to_excel(writer, index=False, sheet_name='Wyniki')
        data = output.getvalue()

        # Przycisk do pobrania pliku XLSX
        st.download_button(
            label="💾 Pobierz wyniki gry (XLSX)",
            data=data,
            file_name="wyniki_gry.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        # --- Upload na GitHub tylko raz ---
        if not st.session_state.results_uploaded:
            temp_filename = "wyniki_temp.xlsx"
            with open(temp_filename, "wb") as f:
                f.write(data)

            repo = "DawidS25/SpectrumDruzynowe"
            try:
                token = st.secrets["GITHUB_TOKEN"]
            except Exception:
                token = None

            if token:
                from datetime import datetime
                next_num = get_next_game_number(repo, token)
                today_str = datetime.today().strftime("%Y-%m-%d")
                file_name = f"gra{next_num:03d}_{today_str}.xlsx"
                path_in_repo = f"wyniki/{file_name}"
                commit_message = f"🎉 Wyniki gry {file_name}"

                response = upload_to_github(temp_filename, repo, path_in_repo, token, commit_message)
                if response.status_code == 201:
                    st.success(f"✅ Wyniki zapisane online.")
                    st.session_state.results_uploaded = True
                else:
                    st.error(f"❌ Błąd zapisu: {response.status_code} – {response.json()}")
            else:
                st.warning("⚠️ Nie udało się zapisać wyników online.")

# git pull origin main --rebase
# git add .
# git commit -m ""
# git push