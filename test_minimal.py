import streamlit as st

st.title("Test de débogage Streamlit Cloud")

st.write("## 1. Test de l'environnement")
st.write("✅ Streamlit fonctionne !")

st.write("## 2. Test des secrets")
try:
    if hasattr(st, 'secrets'):
        st.write("✅ st.secrets est disponible")
        if 'NEON_HOST' in st.secrets:
            st.write(f"✅ NEON_HOST trouvé : {st.secrets['NEON_HOST'][:20]}...")
        else:
            st.write("❌ NEON_HOST non trouvé dans les secrets")
    else:
        st.write("❌ st.secrets n'est pas disponible")
except Exception as e:
    st.write(f"❌ Erreur avec les secrets : {e}")

st.write("## 3. Test des imports")
try:
    import pandas as pd
    st.write("✅ pandas importé")
except Exception as e:
    st.write(f"❌ Erreur pandas : {e}")

try:
    import plotly
    st.write("✅ plotly importé")
except Exception as e:
    st.write(f"❌ Erreur plotly : {e}")

try:
    import psycopg2
    st.write("✅ psycopg2 importé")
except Exception as e:
    st.write(f"❌ Erreur psycopg2 : {e}")

try:
    import streamlit_authenticator as stauth
    st.write("✅ streamlit_authenticator importé")
except Exception as e:
    st.write(f"❌ Erreur streamlit_authenticator : {e}")

st.write("## 4. Test de connexion DB")
try:
    # Essayer une connexion simple
    db_params = {
        'host': st.secrets.get('NEON_HOST', 'ep-wispy-queen-abzi1lne-pooler.eu-west-2.aws.neon.tech'),
        'database': st.secrets.get('NEON_DATABASE', 'neondb'),
        'user': st.secrets.get('NEON_USER', 'neondb_owner'),
        'password': st.secrets.get('NEON_PASSWORD', 'npg_XsA4wfvHy2Rn'),
        'sslmode': 'require'
    }
    
    import psycopg2
    conn = psycopg2.connect(**db_params)
    with conn.cursor() as cur:
        cur.execute("SELECT 1")
        result = cur.fetchone()
        conn.close()
        st.write("✅ Connexion DB réussie !")
except Exception as e:
    st.write(f"❌ Erreur DB : {e}")

st.write("## 5. Test config.yaml")
try:
    import yaml
    with open('config.yaml') as file:
        config = yaml.load(file, Loader=yaml.SafeLoader)
        st.write("✅ config.yaml chargé")
except Exception as e:
    st.write(f"❌ Erreur config.yaml : {e}") 