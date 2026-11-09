"""Flask backend para MC Editor Pro - Script ejecutable."""

from audio_editor_web import app

if __name__ == '__main__':
    print("🎵 MC Editor Pro - Backend")
    print("="*50)
    print("🚀 Servidor iniciado: http://127.0.0.1:5000")
    print("="*50)
    
    app.run(
        host='127.0.0.1',
        port=5000,
        debug=False,
        use_reloader=False,
        threaded=True
    )
