#!/usr/bin/env python
"""
Test si Flask funciona correctamente
"""

import sys

print("🔍 Diagnostic - Testing Flask Stack\n")
print("="*60)

# Test 1: Python version
print(f"✓ Python: {sys.version}")
print(f"✓ Executable: {sys.executable}")

# Test 2: Imports básicos
try:
    import flask
    print(f"✓ Flask: {flask.__version__}")
except Exception as e:
    print(f"✗ Flask: {e}")
    sys.exit(1)

try:
    import librosa
    print(f"✓ Librosa: {librosa.__version__}")
except Exception as e:
    print(f"✗ Librosa: {e}")
    sys.exit(1)

try:
    from sklearn.decomposition import FastICA
    print(f"✓ Scikit-learn: OK")
except Exception as e:
    print(f"✗ Scikit-learn: {e}")
    sys.exit(1)

try:
    from flask_cors import CORS
    print(f"✓ Flask-CORS: OK")
except Exception as e:
    print(f"✗ Flask-CORS: {e}")
    sys.exit(1)

# Test 3: Importar app
try:
    from audio_editor_web import app
    print(f"✓ audio_editor_web: Importado correctamente")
except Exception as e:
    print(f"✗ audio_editor_web: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Verificar rutas
print(f"\n✓ Rutas Flask registradas:")
for rule in app.url_map.iter_rules():
    print(f"   {rule.methods - {'OPTIONS', 'HEAD'}} -> {rule.rule}")

# Test 5: Intentar iniciar Flask brevemente
print(f"\n🖇️  Intentando iniciar Flask en puerto 5000...")
print("="*60 + "\n")

try:
    import threading
    import requests
    import time
    
    # Iniciar Flask en thread
    def run_flask():
        app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False, threaded=True)
    
    server_thread = threading.Thread(target=run_flask, daemon=True)
    server_thread.start()
    
    # Esperar e intentar conectar
    time.sleep(2)
    
    try:
        response = requests.get("http://127.0.0.1:5000/api/health", timeout=2)
        print(f"✓ GET /api/health: {response.status_code}")
        print(f"  Response: {response.json()}\n")
        print("✅ ¡ÉXITO! Flask funciona correctamente")
    except Exception as e:
        print(f"✗ No se pudo conectar: {e}")
        
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
