# preprocessing.py
# Doel: één centrale plek die de dataset klaarmaakt voor BEIDE modellen.
# Opgesplitst in kleine functies; get_data() bundelt alles tot de eindproducten
# die de teamleden in hun notebook inladen.

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler


def load_and_clean(path="data/raw/boris_buddy_synth_dataset.csv"):
    """
    Laadt de data en doet de gedeelde opschoonstappen.
    Geeft terug: X (schone features), y (target).
    """
    # 1. Data inladen
    #    lees het csv-bestand in een dataframe
    #    BELANGRIJK: separator is ";" → pd.read_csv(path, sep=";")

    # 2. GEDEELDE opschoonstappen (voor iedereen gelijk)
    #    - behandel missende waarden (bv. invullen met mediaan of verwijderen)
    #    - (indien nodig) zet 0-en die eigenlijk "ontbrekend" betekenen eerst om
    #    - zet categorische kolommen om naar numeriek (encoding), indien aanwezig

    # 3. Features (X) en target (y) scheiden
    #    y = de doelkolom (pas de naam aan, bv. "Outcome")
    #    X = alle overige kolommen

    # 4. return X, y


def split_data(X, y, random_state=42):
    """
    Splitst in train/test. Dezelfde random_state -> iedereen dezelfde split.
    Geeft terug: X_train, X_test, y_train, y_test.
    """
    # gebruik stratify=y zodat de wel/geen-diabetes-verhouding gelijk blijft
    # X_train, X_test, y_train, y_test = train_test_split(
    #     X, y, test_size=0.2, stratify=y, random_state=random_state)
    # return X_train, X_test, y_train, y_test


def scale_data(X_train, X_test):
    """
    Maakt de genormaliseerde variant.
    BELANGRIJK: fit de scaler ALLEEN op X_train (anders lekt test-info).
    Geeft terug: X_train_scaled, X_test_scaled.
    """
    # scaler = StandardScaler()
    # X_train_scaled = scaler.fit_transform(X_train)
    # X_test_scaled  = scaler.transform(X_test)      # alleen transform!
    # return X_train_scaled, X_test_scaled


def get_data(path="data/raw/boris_buddy_synth_dataset.csv", random_state=42):
    """
    Hoofdfunctie: roept de bovenstaande functies aan en bundelt de eindproducten.
    Dit is de enige functie die de teamleden hoeven aan te roepen.

    Geeft terug (6 stuks):
        X_train, X_test               -> normale (ongeschaalde) features
        X_train_scaled, X_test_scaled -> genormaliseerde features
        y_train, y_test               -> target (voor beide varianten gelijk)

    Gebruik (in je eigen notebook):
        from preprocessing import get_data

        (X_train, X_test,
         X_train_scaled, X_test_scaled,
         y_train, y_test) = get_data()

        # Persoon C (Random Forest):        X_train, X_test
        # Persoon B (Logistic Regression):  X_train_scaled, X_test_scaled
        # y_train / y_test zijn in beide gevallen hetzelfde
    """
    # X, y = load_and_clean(path)
    # X_train, X_test, y_train, y_test = split_data(X, y, random_state)
    # X_train_scaled, X_test_scaled = scale_data(X_train, X_test)
    # return (X_train, X_test,
    #         X_train_scaled, X_test_scaled,
    #         y_train, y_test)