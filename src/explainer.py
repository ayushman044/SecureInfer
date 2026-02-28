import requests, json, re, time

class ThreatExplainer:
    def __init__(self):
        self.url   = "http://localhost:11434/api/generate"
        self.model = "phi3:mini"

        print("🔥 Connecting to Ollama (phi3:mini)...")
        try:
            r      = requests.get("http://localhost:11434/api/tags", timeout=5)
            models = [m['name'] for m in r.json().get('models', [])]
            print(f"✅ Ollama connected.")
            print(f"   Available models: {models}")
            if not any("phi3" in m for m in models):
                print("⚠️  phi3:mini not found. Run: ollama pull phi3:mini")
        except Exception as e:
            print(f"❌ Ollama not reachable: {e}")
            print("   Fix: open a new terminal and run: ollama serve")

    def explain(self, attack_type: str, features: dict, confidence: float) -> dict:
        prompt = f"""You are SecureInfer, an on-device cybersecurity AI analyst.
Respond ONLY with a valid JSON object. No markdown. No text outside JSON.
Required keys: "summary", "severity", "impact", "action"
Severity must be exactly one of: SAFE, LOW, MEDIUM, HIGH, CRITICAL
Keep all values under 80 words total.

Network attack detected:
Type: {attack_type}
Confidence: {confidence:.1f}%
Destination Port: {features.get('Destination Port', 'N/A')}
Flow Duration: {features.get('Flow Duration', 'N/A')} ms
Forward Packets: {features.get('Total Fwd Packets', 'N/A')}
Backward Packets: {features.get('Total Backward Packets', 'N/A')}
Packet Length Mean: {features.get('Packet Length Mean', 'N/A')}
Flow Bytes/s: {features.get('Flow Bytes/s', 'N/A')}

Respond with JSON only:"""

        t0 = time.time()
        try:
            response = requests.post(
                self.url,
                json={
                    "model":  self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.2,
                        "num_predict": 250,
                        "stop": ["\n\n", "```"]
                    }
                },
                timeout=120
            )
            raw = response.json().get("response", "")
        except Exception as e:
            print(f"⚠️  Ollama request failed: {e}")
            raw = ""

        inference_ms = int((time.time() - t0) * 1000)

        # Parse JSON from response
        result = {}
        try:
            # Try direct parse first
            result = json.loads(raw.strip())
        except Exception:
            try:
                # Extract JSON block if wrapped in text
                match = re.search(r'\{.*?\}', raw, re.DOTALL)
                if match:
                    result = json.loads(match.group())
            except Exception:
                pass

        # Fallback if parsing failed
        if not all(k in result for k in ("summary", "severity", "impact", "action")):
            result = {
                "summary":  f"{attack_type} attack detected with {confidence:.0f}% confidence.",
                "severity": "HIGH",
                "impact":   "Potential unauthorized access or service disruption.",
                "action":   "Isolate the affected endpoint and review logs immediately."
            }

        result["inference_ms"] = inference_ms
        return result
