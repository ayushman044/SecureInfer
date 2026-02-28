import pickle, numpy as np, time, sys, os
import pandas as pd
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.explainer import ThreatExplainer

SEVERITY_MAP = {
    'BENIGN': 'SAFE',
    'Bot': 'CRITICAL',              'DDoS': 'CRITICAL',
    'DoS GoldenEye': 'HIGH',        'DoS Hulk': 'CRITICAL',
    'DoS Slowhttptest': 'HIGH',     'DoS slowloris': 'HIGH',
    'FTP-Patator': 'HIGH',          'Heartbleed': 'CRITICAL',
    'Infiltration': 'CRITICAL',     'PortScan': 'HIGH',
    'SSH-Patator': 'HIGH',
    'Web Attack - Brute Force':     'HIGH',
    'Web Attack - Sql Injection':   'CRITICAL',
    'Web Attack - XSS':             'HIGH',
}

class SecureInferPipeline:
    def __init__(self):
        print("🛡️  Initializing SecureInfer pipeline...")
        self.classifier   = pickle.load(open("models/classifier.pkl",    "rb"))
        self.le           = pickle.load(open("models/label_encoder.pkl", "rb"))
        self.scaler       = pickle.load(open("models/scaler.pkl",        "rb"))
        self.feature_cols = pickle.load(open("models/feature_cols.pkl",  "rb"))
        self.explainer    = ThreatExplainer()
        print("✅ SecureInfer ready — zero data egress mode active.\n")

    def analyze(self, raw_log: dict) -> dict:
        t0 = time.time()

        # Fix 1: Use DataFrame with column names → silences StandardScaler warning
        row        = pd.DataFrame([{col: raw_log.get(col, 0) for col in self.feature_cols}])
        row_scaled = self.scaler.transform(row)

        # Fix 2: Pass DataFrame to XGBoost directly → stays on correct device
        row_scaled_df = pd.DataFrame(row_scaled, columns=self.feature_cols)

        pred_enc      = self.classifier.predict(row_scaled_df)[0]
        proba         = self.classifier.predict_proba(row_scaled_df)[0]
        confidence    = float(proba.max() * 100)
        attack_type   = self.le.inverse_transform([pred_enc])[0]
        severity      = SEVERITY_MAP.get(attack_type, 'MEDIUM')
        classifier_ms = int((time.time() - t0) * 1000)

        # Stage 2 — LLM briefing (only for non-BENIGN)
        if attack_type == 'BENIGN':
            briefing = {
                "summary":      "Traffic is normal. No threat detected.",
                "severity":     "SAFE",
                "impact":       "None.",
                "action":       "No action required.",
                "inference_ms": 0
            }
        else:
            briefing = self.explainer.explain(attack_type, raw_log, confidence)

        total_ms = int((time.time() - t0) * 1000)
        return {
            "attack_type":   attack_type,
            "severity":      severity,
            "confidence":    round(confidence, 1),
            "briefing":      briefing,
            "is_threat":     attack_type != 'BENIGN',
            "classifier_ms": classifier_ms,
            "llm_ms":        briefing.get("inference_ms", 0),
            "total_ms":      total_ms,
        }
