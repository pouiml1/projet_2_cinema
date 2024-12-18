import streamlit as st
import json
from datetime import datetime
import zipfile

import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io

# Définir les scopes nécessaires pour accéder à Google Drive
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

# Fonction pour récupérer les identifiants d'authentification
def authenticate_google_drive():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

# Fonction pour télécharger un fichier depuis Google Drive
def download_file_from_drive(file_id):
    creds = authenticate_google_drive()
    service = build('drive', 'v3', credentials=creds)
    request = service.files().get_media(fileId=file_id)
    fh = io.FileIO('downloaded_file.zip', 'wb')
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
    return 'downloaded_file.zip'

# Fonction pour extraire le fichier ZIP
def extract_zip(zip_file_path, extract_to_folder='data_folder'):
    # Créer le dossier d'extraction s'il n'existe pas
    if not os.path.exists(extract_to_folder):
        os.makedirs(extract_to_folder)
    
    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to_folder)
        return extract_to_folder  # Retourner le chemin du dossier d'extraction

# Fonction pour charger les données JSON
def load_data_from_json(json_file_path):
    with open(json_file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    return data

# Utilisation dans Streamlit
zip_file_path = 'data_ml_final.zip'  # Le chemin vers votre fichier ZIP téléchargé
extracted_folder = extract_zip(zip_file_path)

# Charger le fichier JSON extrait
json_file_path = os.path.join(extracted_folder, 'data_ml_final.json')  # Remplacez par le nom exact de votre fichier JSON
data = load_data_from_json(json_file_path)

############ CSS ###############

# Charger le CSS
css_file_path = 'css/style.css'
with open(css_file_path, "r", encoding="utf-8") as f:
    css = f.read()

# Injecter le CSS dans l'application
st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

#################################

# Titre de l'application
st.title("Qu'est-ce qu'on regarde ce soir ?")
st.write("Chercher un film que vous avez aimé, on se charge de vous trouver quelques recommandations ✨")

# Fonction pour obtenir les titres de films
def get_movie_titles():
    titles = []
    for item in data:
        titles.append(item["Film recherché"]["caracteristique"]["title_fr"])
    return titles

# Fonction pour récupérer les films recommandés
def get_movie_details(movie_title):
    for item in data:
        if item["Film recherché"]["caracteristique"]["title_fr"].lower() == movie_title.lower():
            # Vérification que les détails sont bien un dictionnaire
            film_details = item["Film recherché"]["caracteristique"]
            if isinstance(film_details, dict):
                return item["Titres recommandés"], film_details
    return [], None

# Formater la date de sortie au format JJ/MM/AAAA
def format_release_date(date_string):
    date_obj = datetime.fromisoformat(date_string)  # Convertir la chaîne ISO en objet datetime
    return date_obj.strftime("%d/%m/%Y")  # Formater au format français JJ/MM/AAAA

# Barre de recherche intelligente (avec auto-suggestions)
movie_titles = get_movie_titles()

search_title = st.selectbox(
    "",
    options=["🔍 Quel film avez-vous aimé ?"] + sorted(movie_titles),  # Une option vide par défaut
    format_func=lambda x: '' if x == "" else x
)

# Si un film est sélectionné
st.info("ℹ️ La recherche se base sur le titre du film uniquement")
if search_title:
    # Recherche du film et de ses recommandations
    if search_title and search_title != "🔍 Quel film avez-vous aimé ?":
        recommendations, movie_details = get_movie_details(search_title)

        # Initialiser l'état dans st.session_state
        if "show_details" not in st.session_state:
            st.session_state.show_details = False  # Les détails sont masqués par défaut

        # Affichage du film recherché
        if movie_details:
            st.subheader('💖 Vous avez aimé')
            backdrop_url = movie_details.get("backdrop_path", "")
            full_backdrop_url = f"https://image.tmdb.org/t/p/w1280{backdrop_url}" if backdrop_url else None

            # Vérification de l'image de fond (backdrop)
            if full_backdrop_url:
                # Ajouter le backdrop en utilisant le CSS depuis le fichier
                st.markdown(
                    f"""
                    <div class="film-background">
                        <div class="background-opacity" style="background-image: url({full_backdrop_url});"></div>
                        <div class="film-title">{movie_details['title_fr']}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(f"## {movie_details['title_fr']}")

            # Créer une seule colonne pour centrer le bouton
            col = st.columns(1)[0]
            with col:
                st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
                if st.button("Voir les détails du film"):
                    st.session_state.show_details = not st.session_state.show_details
                st.markdown("</div>", unsafe_allow_html=True)

            # Afficher ou masquer les colonnes en fonction de l'état
            if st.session_state.show_details:
                # Afficher les détails du film
                col1, col2 = st.columns([1, 2])  # Deux colonnes pour les détails

                # Affiche du film (à gauche)
                poster_url = movie_details.get("poster_path", "")
                if poster_url:
                    full_poster_url = f"https://image.tmdb.org/t/p/w500{poster_url}"
                    with col1:
                        # Affiche l'image et ajoute un effet de zoom au clic
                        st.markdown(
                            f'<div style="text-align:center;">'
                            f'<a href="{full_poster_url}" target="_blank">'
                            f'<img src="{full_poster_url}" alt="{search_title}" class="movie-poster" style="width:100%; cursor:pointer;"/>'
                            f'</a>'
                            f'</div>',
                            unsafe_allow_html=True
                        )
                # Informations du film (à droite)
                with col2:
                    st.write(f"**🕔 Durée :** {movie_details.get('runtime', 'Inconnue')} minutes")
                    st.write(f"**⭐ Note :** {movie_details.get('vote_average', 'Non noté')}")
                    st.write(f"**🎭 Genres :** {movie_details.get('genres', 'Non spécifié')}")
                    release_date = movie_details.get("release_date", None)
                    if release_date:
                        formatted_date = format_release_date(release_date)
                    else:
                        formatted_date = "Non spécifiée"
                    st.write(f"**📅 Date de sortie :** {formatted_date}")
                    st.write(f"**🎬 Réalisateur(s) :** {movie_details.get('directors', 'Inconnu')}")
                    st.write(f"**🧑‍🎤 Acteurs :** {movie_details.get('actors', 'Non spécifié')}")
                    st.write(f"**📖 Résumé :** {movie_details.get('overview', 'Pas de résumé disponible')}")

        else:
            st.warning("Aucune information trouvée pour ce film.")
        
        # Afficher les films recommandés en 5 colonnes
        if recommendations:
            st.subheader("✨ Nos recommandations")

            cols = st.columns(5)  # Crée 5 colonnes pour afficher les films recommandés
            for i, movie in enumerate(recommendations[:5]):  # Limite à 5 films
                movie_title = movie["caracteristique"]["title_fr"]
                poster_url = movie["caracteristique"].get("poster_path", "")

                with cols[i]:
                    if poster_url:
                        img_html = f"""
                        <div style="text-align:center;">
                            <a href="https://image.tmdb.org/t/p/w500{poster_url}" target="_blank">
                                <img src="https://image.tmdb.org/t/p/w200{poster_url}" alt="{movie_title}" class="movie-poster" style="width:100%; cursor:pointer;"/>
                            </a>
                        </div>
                        """
                        # Afficher l'image avec l'effet hover
                        st.markdown(img_html, unsafe_allow_html=True)

                        # Ajouter un peu d'espace avant le bouton (par exemple 10px)
                        st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)

                        # Affichage du bouton pour voir les détails
                        if st.button(f"Voir les détails", key=f"btn_{movie_title}"):
                            st.session_state.selected_movie = movie  # Sauvegarder le film sélectionné dans la session
                            st.rerun()  # Rafraîchir pour afficher les détails
                    else:
                        st.write("Aucune affiche disponible")

        # Affichage des détails du film sélectionné
        if 'selected_movie' in st.session_state:
            movie_details = st.session_state.selected_movie["caracteristique"]
            st.subheader(f"{movie_details['title_fr']}")

            # Afficher les détails du film sélectionné
            col1, col2 = st.columns([1, 2])  # Crée 2 colonnes pour l'affiche et les détails
            with col1:
                poster_url = movie_details.get("poster_path", "")
                if poster_url:
                    full_poster_url = f"https://image.tmdb.org/t/p/w500{poster_url}"
                    img_html = f"""
                    <div style="text-align:center;">
                        <a href="{full_poster_url}" target="_blank">  <!-- Ouvre la source de l'image dans un nouvel onglet -->
                            <img src="https://image.tmdb.org/t/p/w200{poster_url}" alt="{movie_title}" class="movie-poster" style="width:100%; cursor:pointer;"/>
                        </a>
                    </div>
                    """
                    # Afficher l'image avec le lien
                    st.markdown(img_html, unsafe_allow_html=True)
            with col2:
                st.write(f"**🕔 Durée :** {movie_details.get('runtime', 'Inconnue')} minutes")
                st.write(f"**⭐ Note :** {movie_details.get('vote_average', 'Non noté')}")
                st.write(f"**🎭 Genres :** {movie_details.get('genres', 'Non spécifié')}")
                release_date = movie_details.get("release_date", None)
                if release_date:
                    formatted_date = format_release_date(release_date)
                else:
                    formatted_date = "Non spécifiée"
                st.write(f"**📅 Date de sortie :** {formatted_date}")
                st.write(f"**🎬 Réalisateur(s) :** {movie_details.get('directors', 'Inconnu')}")
                st.write(f"**🧑‍🎤 Acteurs :** {movie_details.get('actors', 'Non spécifié')}")
                st.write(f"**📖 Résumé :** {movie_details.get('overview', 'Pas de résumé disponible')}")

            # Bouton pour revenir à la liste des films recommandés
            if st.button("Fermer les détails"):
                del st.session_state.selected_movie  # Supprimer l'état du film sélectionné
                st.rerun()  # Rafraîchir la page pour revenir à l'affichage initial
