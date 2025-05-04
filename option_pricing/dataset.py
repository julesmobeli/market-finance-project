import yfinance as yf
import pandas as pd
import numpy as np
# from pylab import *
from datetime import datetime

# Ticker pour les actions Google (classe C)
ticker = yf.Ticker("GOOG")
# Récupérer les dates d'expiration des options
expiration_dates = ticker.options
all_dataframes = []
# Récupérer le prix actuel du sous-jacent (Tesla)
current_price = ticker.history(period="1d")['Close'].iloc[-1]

for date in expiration_dates:
    # Obtenir les chaînes d'options (calls et puts) pour cette date
    options_chain = ticker.option_chain(date)
    calls = options_chain.calls
    puts = options_chain.puts
    merged_df = pd.merge(
            calls[['strike', 'lastTradeDate','lastPrice','volume']].rename(columns={'lastTradeDate': 'call_lastTradeDate',
                                                                 'lastPrice': 'call_lastPrice',
                                                                    'volume':'call_volume'}),
            puts[['strike', 'lastTradeDate','lastPrice']].rename(columns={'lastTradeDate': 'put_lastTradeDate',
                                                   'lastPrice': 'put_lastPrice',
                                                          'volume':'put_volume'}),
            on='strike',
            how='outer'
        )

    # Ajouter une colonne pour la date d'expiration
    merged_df['expiration_date'] = date
    # Assurez-vous que les colonnes sont converties en format datetime
    merged_df['expiration_date'] = pd.to_datetime(merged_df['expiration_date']).dt.tz_localize(None)
    merged_df['call_lastTradeDate'] = pd.to_datetime(merged_df['call_lastTradeDate']).dt.tz_localize(None)

    # Calcul de Time to Maturity (en jours)
    merged_df['Time_to_maturity'] = (merged_df['expiration_date'] - merged_df['call_lastTradeDate']).dt.days

    # Ajouter le prix actuel du sous-jacent (Tesla) à chaque ligne
    merged_df['current_price'] = current_price

    filtered_df = merged_df[merged_df["call_volume"] >= 10]

    # Ajouter le DataFrame à la liste
    all_dataframes.append(filtered_df)



    # Combiner tous les DataFrames en un seul
final_df = pd.concat(all_dataframes, ignore_index=True)


from fonctions import implied_volatility as iv  

# Exemple : taux sans risque
r = 0.02

# Fonction pour calculer la volatilité implicite avec gestion des erreurs
def safe_iv(row):
    try:
        # Calculer la volatilité implicite
        return iv(
            row["current_price"],
            row["strike"],
            row["Time_to_maturity"] / 365,  # Conversion des jours en années
            r,
            row["call_lastPrice"] if row["strike"] <= row["current_price"] else row["put_lastPrice"]
        )
    except:
        # Retourner NaN si une erreur survient
        return np.nan


final_df = final_df.dropna(subset=["put_lastPrice", "call_lastPrice"])

# Créer une copie explicite
final_df = final_df.copy()

# Calculer la volatilité implicite
final_df["implied_volatility"] = final_df.apply(safe_iv, axis=1)
