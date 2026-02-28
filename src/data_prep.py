import pandas as pd
import numpy as np
import glob, os, pickle
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split

def load_data():
    csv_files = glob.glob("data/**/*.csv", recursive=True)
    if not csv_files:
        print("❌ No CSV files found in data/")
        print("   Run the dataset download step first.")
        return None
    dfs = []
    for f in sorted(csv_files):
        print(f"  📂 Loading {os.path.basename(f)}...")
        df = pd.read_csv(f, encoding='utf-8', low_memory=False)
        df.columns = df.columns.str.strip()
        dfs.append(df)
    df = pd.concat(dfs, ignore_index=True)
    print(f"\n✅ Total records: {len(df):,}")
    print(f"📊 Label distribution:\n{df['Label'].value_counts().to_string()}\n")
    return df

def preprocess(df):
    df = df.copy()
    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    df.dropna(inplace=True)

    le = LabelEncoder()
    df['Label_enc'] = le.fit_transform(df['Label'])

    key_features = [
        'Destination Port', 'Flow Duration', 'Total Fwd Packets',
        'Total Backward Packets', 'Total Length of Fwd Packets',
        'Fwd Packet Length Max', 'Fwd Packet Length Mean',
        'Bwd Packet Length Max', 'Bwd Packet Length Mean',
        'Flow Bytes/s', 'Flow Packets/s', 'Flow IAT Mean',
        'Flow IAT Std', 'Fwd IAT Total', 'Bwd IAT Total',
        'Fwd PSH Flags', 'Bwd Packets/s', 'Packet Length Mean',
        'Packet Length Std', 'Average Packet Size'
    ]
    available = [f for f in key_features if f in df.columns]
    print(f"✅ Using {len(available)} features")

    X = df[available].astype(float)
    y = df['Label_enc']

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    os.makedirs("models", exist_ok=True)
    pickle.dump(le,        open("models/label_encoder.pkl", "wb"))
    pickle.dump(scaler,    open("models/scaler.pkl",        "wb"))
    pickle.dump(available, open("models/feature_cols.pkl",  "wb"))
    print("✅ Preprocessors saved to models/")
    return X_scaled, y, le, available

def main():
    df = load_data()
    if df is None:
        return
    X, y, le, _ = preprocess(df)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    np.save("models/X_train.npy", X_train)
    np.save("models/X_test.npy",  X_test)
    np.save("models/y_train.npy", y_train)
    np.save("models/y_test.npy",  y_test)
    print(f"✅ Train: {X_train.shape[0]:,} | Test: {X_test.shape[0]:,}")
    print("🚀 Run next: python3 src/train_classifier.py")

if __name__ == "__main__":
    main()
