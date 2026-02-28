import numpy as np, pickle, time
from xgboost import XGBClassifier
from sklearn.metrics import classification_report, accuracy_score

def main():
    print("📂 Loading preprocessed data...")
    X_train = np.load("models/X_train.npy")
    X_test  = np.load("models/X_test.npy")
    y_train = np.load("models/y_train.npy")
    y_test  = np.load("models/y_test.npy")
    le      = pickle.load(open("models/label_encoder.pkl", "rb"))
    print(f"✅ {X_train.shape[0]:,} train | {X_test.shape[0]:,} test | {len(le.classes_)} classes")

    print("\n🚀 Training XGBoost on GPU...")
    print("   (Same code runs on AMD ROCm unchanged — PyTorch-portable)")
    t0 = time.time()

    model = XGBClassifier(
        n_estimators=200,
        max_depth=8,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        eval_metric='mlogloss',
        tree_method='hist',
        device='cuda',
        n_jobs=-1,
        random_state=42
    )
    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        verbose=25
    )

    elapsed = round(time.time() - t0, 1)
    y_pred  = model.predict(X_test)
    acc     = accuracy_score(y_test, y_pred) * 100

    print(f"\n⏱️  Training time : {elapsed}s")
    print(f"🎯 Accuracy      : {acc:.2f}%")
    print("\n📊 Classification Report:")
    print(classification_report(y_test, y_pred, target_names=le.classes_))

    pickle.dump(model, open("models/classifier.pkl", "wb"))
    print("✅ Saved: models/classifier.pkl")
    print("🚀 Run next: streamlit run app.py")

if __name__ == "__main__":
    main()
