import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import os


def authenticate_and_logout():
    """
    Gère l'authentification et affiche le bouton de déconnexion sur toutes les pages.
    Retourne (name, authentication_status, username, authenticator)
    """
    # Chemin vers le fichier de configuration (relatif au script principal)
    config_path = 'config.yaml'
    if not os.path.exists(config_path):
        st.error(f"Le fichier de configuration '{config_path}' est introuvable.")
        st.stop()
        
    with open(config_path) as file:
        config = yaml.load(file, Loader=SafeLoader)

    authenticator = stauth.Authenticate(
        config['credentials'],
        config['cookie']['name'],
        config['cookie']['key'],
        config['cookie']['expiry_days']
    )

    # La méthode login() gère maintenant l'affichage du formulaire et la logique
    authenticator.login()

    if st.session_state["authentication_status"]:
        with st.sidebar:
            # CSS pour forcer la couleur blanche sur tous les boutons de la sidebar
            st.markdown(
                '''
                <style>
                section[data-testid="stSidebar"] button {
                    background-color: #fff !important;
                    color: #333 !important;
                    border: 1px solid #ddd !important;
                    font-weight: 600;
                }
                section[data-testid="stSidebar"] button:hover {
                    background-color: #f5f5f5 !important;
                    color: #111 !important;
                }
                </style>
                ''',
                unsafe_allow_html=True
            )
            st.markdown('---')
            st.markdown('#### Session')
            st.success(f'Bienvenue *{st.session_state["name"]}*', icon="👤")
            if st.button('🚪 Déconnexion', use_container_width=True):
                authenticator.logout('Déconnexion', 'main')
                st.session_state.clear()
                st.rerun()
    elif st.session_state["authentication_status"] is False:
        st.error("Nom d'utilisateur/mot de passe incorrect")
    elif st.session_state["authentication_status"] is None:
        st.warning("Veuillez entrer votre nom d'utilisateur et votre mot de passe")

    # Si l'utilisateur n'est pas authentifié, on arrête l'exécution de la page
    if not st.session_state["authentication_status"]:
        st.stop()

    return st.session_state["name"], st.session_state["authentication_status"], st.session_state["username"], authenticator 