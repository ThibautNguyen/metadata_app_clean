import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader


def authenticate_and_logout():
    """
    Gère l'authentification et affiche le bouton de déconnexion sur toutes les pages.
    Retourne (name, authentication_status, username, authenticator)
    """
    # Chargement de la configuration
    with open('config.yaml') as file:
        config = yaml.load(file, Loader=SafeLoader)

    authenticator = stauth.Authenticate(
        config['credentials'],
        config['cookie']['name'],
        config['cookie']['key'],
        config['cookie']['expiry_days']
    )

    name, authentication_status, username = authenticator.login('main', 'Connexion')

    if authentication_status:
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
            st.success(f"Bienvenue *{name}*", icon="👤")
            if st.button('🚪 Déconnexion', use_container_width=True):
                authenticator.logout('main')
                st.session_state.clear()
                st.rerun()
    elif authentication_status is False:
        st.error("Nom d'utilisateur/mot de passe incorrect")
        st.stop()
    elif authentication_status is None:
        st.warning("Veuillez entrer votre nom d'utilisateur et votre mot de passe")
        st.stop()

    return name, authentication_status, username, authenticator 