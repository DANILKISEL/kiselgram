#!/usr/bin/env python3
"""
Kiselgram Management Script
Complete Messaging Platform with Groups, Channels & File Support
"""

import os
import sys
import argparse
import platform
import time
import webbrowser
import socket
import subprocess
import threading
import signal
import atexit
import json
from pathlib import Path
from datetime import datetime

# Global variables for managing the Flask process
flask_process = None
is_running = False
process_pid = None
STATUS_FILE = '.kiselgram_status.json'


def print_header():
    """Print fancy header for Kiselgram"""
    print("\n" + "=" * 60)
    print("""
  _  __ ___ _____ _____ ____ ____ ___  ____  __  __ 
 | |/ // _ \_   _| ____/ ___/ ___/ _ \|  _ \|  \/  |
 | ' /| | | || | |  _| \___ \___ \ | | | |_) | |\/| |
 | . \| |_| || | | |___ ___) |__) | |_| |  _ <| |  | |
 |_|\_\\___/ |_| |_____|____/____/ \___/|_| \_\_|  |_|
    """)
    print("=" * 60)
    print("📱 Complete Messaging Platform v2.0")
    print("👥 Groups | 📢 Channels | 📁 File Support | 🤖 Bots")
    print("=" * 60)


def check_python_version():
    """Check if Python version is compatible"""
    print("🔍 Checking Python version...")
    if sys.version_info < (3, 7):
        print(f"❌ Python 3.7+ required. Current: {platform.python_version()}")
        return False
    print(f"✅ Python {platform.python_version()}")
    return True


def check_dependencies():
    """Check if required dependencies are installed"""
    print("\n📦 Checking dependencies...")

    required = [
        'flask',
        'flask_sqlalchemy',
        'dotenv',
        'PIL'
    ]

    optional = ['pyTelegramBotAPI', 'pyfiglet']

    try:
        import importlib

        for dep in required:
            try:
                importlib.import_module(dep.replace('-', '_'))
                print(f"✅ {dep}")
            except ImportError:
                print(f"❌ {dep} - Install with: pip install {dep}")
                return False

        for dep in optional:
            try:
                importlib.import_module(dep.replace('-', '_'))
                print(f"✅ {dep} (optional)")
            except ImportError:
                print(f"⚠️  {dep} (optional - not installed)")

        return True
    except Exception as e:
        print(f"❌ Error checking dependencies: {e}")
        return False


def check_port_available(port):
    """Check if a port is available"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('127.0.0.1', port))
        sock.close()
        return result != 0
    except:
        return True


def save_status(port, pid):
    """Save application status to file"""
    status = {
        'running': True,
        'port': port,
        'pid': pid,
        'started_at': datetime.now().isoformat()
    }
    with open(STATUS_FILE, 'w') as f:
        json.dump(status, f)


def load_status():
    """Load application status from file"""
    if os.path.exists(STATUS_FILE):
        with open(STATUS_FILE, 'r') as f:
            return json.load(f)
    return None


def clear_status():
    """Clear status file"""
    if os.path.exists(STATUS_FILE):
        os.remove(STATUS_FILE)


def run_flask_app(host, port, debug):
    """Run Flask application in a subprocess"""
    global flask_process, process_pid, is_running

    try:
        # Set environment variables
        env = os.environ.copy()
        env['FLASK_ENV'] = 'development' if debug else 'production'

        # Build command based on what files exist
        if os.path.exists('run_modular.py'):
            cmd = [sys.executable, 'run_modular.py']
        elif os.path.exists('app'):
            # Create a temporary runner for modular app
            # FIXED: Use 'True' instead of 'true' for Python boolean
            runner_content = f'''#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.utils import setup_bots
import threading

app = create_app()

def init_database():
    with app.app_context():
        db.create_all()
        setup_bots()
        print("✓ Database initialized")

def start_bot_simulation(app):
    from app.utils import simulate_bot_interaction
    bot_thread = threading.Thread(target=simulate_bot_interaction, args=(app,), daemon=True)
    bot_thread.start()

if __name__ == '__main__':
    init_database()
    start_bot_simulation(app)
    app.run(host='{host}', port={port}, debug={debug})
'''

            with open('tmp_runner.py', 'w') as f:
                f.write(runner_content)
            cmd = [sys.executable, 'tmp_runner.py']
        else:
            print("❌ No Flask application found!")
            return False

        # Start Flask process
        print(f"🚀 Starting Flask on http://{host if host != '0.0.0.0' else 'localhost'}:{port}")
        flask_process = subprocess.Popen(
            cmd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )

        process_pid = flask_process.pid
        is_running = True
        save_status(port, process_pid)

        # Monitor output in a separate thread
        def monitor_output():
            for line in flask_process.stdout:
                print(f"[Flask] {line}", end='')
                if "Running on" in line and "http://" in line:
                    # Try to open browser
                    try:
                        time.sleep(1)
                        url = f"http://localhost:{port}"
                        webbrowser.open(url)
                        print(f"\n🌐 Opened browser at: {url}")
                    except:
                        pass

        monitor_thread = threading.Thread(target=monitor_output, daemon=True)
        monitor_thread.start()

        # Wait for process to complete
        flask_process.wait()
        is_running = False
        clear_status()

        return True

    except Exception as e:
        print(f"❌ Error starting Flask: {e}")
        return False

def stop_application():
    """Stop the running application"""
    global flask_process, is_running

    status = load_status()
    if not status or not status.get('running'):
        print("❌ No running application found")
        return False

    pid = status.get('pid')
    port = status.get('port', 5000)

    print(f"🛑 Stopping Kiselgram (PID: {pid}, Port: {port})...")

    try:
        # Try to kill by PID
        if pid:
            if platform.system() == 'Windows':
                subprocess.run(['taskkill', '/F', '/PID', str(pid)],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                os.kill(pid, signal.SIGTERM)

        # Also try to kill any process on the port
        if check_port_available(port):
            print("✅ Application stopped")
        else:
            # Port still in use, try harder
            if platform.system() == 'Windows':
                subprocess.run(['netstat', '-ano'], capture_output=True, text=True)
                # Find and kill process using the port
                result = subprocess.run(['netstat', '-ano'], capture_output=True, text=True)
                for line in result.stdout.split('\n'):
                    if f':{port}' in line:
                        parts = line.strip().split()
                        if len(parts) >= 5:
                            pid = parts[-1]
                            subprocess.run(['taskkill', '/F', '/PID', pid],
                                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                # For Linux/Mac
                subprocess.run(['lsof', '-ti', f':{port}'], capture_output=True, text=True)
                result = subprocess.run(['lsof', '-ti', f':{port}'], capture_output=True, text=True)
                if result.stdout.strip():
                    pids = result.stdout.strip().split()
                    for pid in pids:
                        os.kill(int(pid), signal.SIGKILL)

        clear_status()

        # Clean up temporary files
        for tmp_file in ['tmp_runner.py', 'init_db.py']:
            if os.path.exists(tmp_file):
                os.remove(tmp_file)

        print("✅ Application stopped successfully")
        return True

    except Exception as e:
        print(f"❌ Error stopping application: {e}")
        return False


def check_application():
    """Check application status"""
    status = load_status()
    if status and status.get('running'):
        pid = status.get('pid')
        port = status.get('port', 5000)
        started = status.get('started_at', 'unknown')

        print(f"✅ Kiselgram is RUNNING")
        print(f"   PID: {pid}")
        print(f"   Port: {port}")
        print(f"   Started: {started}")
        print(f"   URL: http://localhost:{port}")

        # Check if port is actually responding
        if check_port_available(port):
            print(f"⚠️  Warning: Port {port} appears to be free (process may have crashed)")
        else:
            print(f"✓ Port {port} is active")

        return True
    else:
        print("❌ Kiselgram is NOT running")
        return False


def setup_environment():
    """Setup the Kiselgram environment"""
    print("\n🔧 Setting up Kiselgram environment...")

    # Create necessary directories
    directories = [
        'uploads/images',
        'uploads/documents',
        'uploads/media',
        'static/css',
        'static/js',
        'static/images',
        'templates'
    ]

    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✓ Created: {directory}")

    # Create .env file if it doesn't exist
    if not os.path.exists('.env'):
        env_content = """# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN_HERE

# Flask Configuration
SECRET_KEY=your-secret-key-change-in-production
DATABASE_URL=sqlite:///kiselgram.db

# Server Configuration
HOST=0.0.0.0
PORT=5000
DEBUG=True

# File Uploads
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=16777216  # 16MB
"""
        with open('.env', 'w') as f:
            f.write(env_content)
        print("✓ Created .env file")

    # Create requirements.txt if it doesn't exist
    if not os.path.exists('requirements.txt'):
        req_content = """Flask>=2.3.0
Flask-SQLAlchemy>=3.0.0
python-dotenv>=1.0.0
Pillow>=10.0.0
pyTelegramBotAPI>=4.12.0
"""
        with open('requirements.txt', 'w') as f:
            f.write(req_content)
        print("✓ Created requirements.txt")

    print("\n✅ Setup completed!")
    print("\nNext steps:")
    print("1. Install dependencies: pip install -r requirements.txt")
    print("2. Configure Telegram bot in .env (optional)")
    print("3. Run: python manage.py start")

    return True


def show_help():
    """Show help information"""
    print_header()
    print("\n📚 Kiselgram Management Commands:")
    print("=" * 40)
    print("\nBasic Commands:")
    print("  python manage.py start       Start the application")
    print("  python manage.py stop        Stop the application")
    print("  python manage.py restart     Restart the application")
    print("  python manage.py status      Check application status")
    print("  python manage.py setup       Setup environment")

    print("\nAdvanced Commands:")
    print("  python manage.py start --port 8080    Use specific port")
    print("  python manage.py start --no-browser   Don't open browser")
    print("  python manage.py start --host 0.0.0.0 Bind to all interfaces")
    print("  python manage.py start --debug        Enable debug mode")
    print("  python manage.py start --no-debug     Disable debug mode")

    print("\nUtility Commands:")
    print("  python manage.py clean       Clean temporary files")
    print("  python manage.py reset-db    Reset database (⚠️ deletes data)")
    print("  python manage.py test        Run basic tests")

    print("\nExamples:")
    print("  # Start on port 8080")
    print("  python manage.py start --port 8080")
    print("")
    print("  # Start without opening browser")
    print("  python manage.py start --no-browser")
    print("")
    print("  # Check if app is running")
    print("  python manage.py status")

    return True


def clean_temporary_files():
    """Clean temporary files"""
    print("\n🧹 Cleaning temporary files...")

    files_to_remove = [
        'tmp_runner.py',
        'init_db.py',
        '__pycache__',
        'app/__pycache__',
        'app/routes/__pycache__',
        'app/utils/__pycache__',
        'instance',
        '.kiselgram_status.json'
    ]

    for item in files_to_remove:
        if os.path.exists(item):
            if os.path.isdir(item):
                import shutil
                shutil.rmtree(item)
                print(f"✓ Removed directory: {item}")
            else:
                os.remove(item)
                print(f"✓ Removed file: {item}")

    # Clean .pyc files
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.pyc'):
                filepath = os.path.join(root, file)
                os.remove(filepath)
                print(f"✓ Removed: {filepath}")

    print("✅ Cleanup completed")
    return True


def reset_database():
    """Reset the database (WARNING: deletes all data)"""
    print("\n⚠️  WARNING: This will DELETE ALL DATA!")
    confirm = input("Are you sure? Type 'yes' to continue: ")

    if confirm.lower() != 'yes':
        print("❌ Database reset cancelled")
        return False

    print("\n🗑️  Resetting database...")

    # Stop application if running
    stop_application()

    # Remove database files
    db_files = [
        'kiselgram.db',
        'instance/kiselgram.db',
        'test.db'
    ]

    for db_file in db_files:
        if os.path.exists(db_file):
            os.remove(db_file)
            print(f"✓ Removed: {db_file}")

    # Remove uploads
    if os.path.exists('uploads'):
        import shutil
        shutil.rmtree('uploads')
        os.makedirs('uploads/images', exist_ok=True)
        os.makedirs('uploads/documents', exist_ok=True)
        os.makedirs('uploads/media', exist_ok=True)
        print("✓ Cleared uploads directory")

    print("\n✅ Database reset complete")
    print("Next: Run 'python manage.py start' to recreate database")

    return True


def run_tests():
    """Run basic tests"""
    print("\n🧪 Running basic tests...")

    tests_passed = 0
    tests_failed = 0

    # Test 1: Check Python version
    try:
        if sys.version_info >= (3, 7):
            print("✓ Python version OK")
            tests_passed += 1
        else:
            print("✗ Python version too old")
            tests_failed += 1
    except:
        tests_failed += 1

    # Test 2: Check dependencies
    try:
        if check_dependencies():
            print("✓ Dependencies OK")
            tests_passed += 1
        else:
            print("✗ Missing dependencies")
            tests_failed += 1
    except:
        tests_failed += 1

    # Test 3: Check directory structure
    try:
        required_dirs = ['app', 'templates', 'static', 'uploads']
        all_exist = all(os.path.exists(d) for d in required_dirs)
        if all_exist:
            print("✓ Directory structure OK")
            tests_passed += 1
        else:
            print("✗ Missing directories")
            tests_failed += 1
    except:
        tests_failed += 1

    # Test 4: Check database
    try:
        if os.path.exists('kiselgram.db') or os.path.exists('instance/kiselgram.db'):
            print("✓ Database file exists")
            tests_passed += 1
        else:
            print("⚠️ No database file (this is OK for first run)")
            tests_passed += 1
    except:
        tests_failed += 1

    print(f"\n📊 Test Results: {tests_passed} passed, {tests_failed} failed")

    if tests_failed == 0:
        print("✅ All tests passed!")
        return True
    else:
        print("⚠️ Some tests failed. Run 'python manage.py setup' to fix issues.")
        return False


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Kiselgram Management Script')
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # Start command
    start_parser = subparsers.add_parser('start', help='Start the application')
    start_parser.add_argument('--port', type=int, default=5000, help='Port to run on')
    start_parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    start_parser.add_argument('--debug', action='store_true', default=True, help='Enable debug mode')
    start_parser.add_argument('--no-debug', action='store_false', dest='debug', help='Disable debug mode')
    start_parser.add_argument('--no-browser', action='store_true', help="Don't open browser")

    # Stop command
    subparsers.add_parser('stop', help='Stop the application')

    # Restart command
    restart_parser = subparsers.add_parser('restart', help='Restart the application')
    restart_parser.add_argument('--port', type=int, help='Port to run on')
    restart_parser.add_argument('--host', help='Host to bind to')
    restart_parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    restart_parser.add_argument('--no-debug', action='store_false', dest='debug', help='Disable debug mode')

    # Status command
    subparsers.add_parser('status', help='Check application status')

    # Setup command
    subparsers.add_parser('setup', help='Setup environment')

    # Clean command
    subparsers.add_parser('clean', help='Clean temporary files')

    # Reset DB command
    subparsers.add_parser('reset-db', help='Reset database (⚠️ deletes all data)')

    # Test command
    subparsers.add_parser('test', help='Run basic tests')

    # Help command
    subparsers.add_parser('help', help='Show help')

    args = parser.parse_args()

    if not args.command:
        print_header()
        print("\n❌ No command specified. Use 'python manage.py help' for usage.")
        return

    if args.command == 'start':
        print_header()

        # Check dependencies
        if not check_dependencies():
            print("\n❌ Missing dependencies. Install with: pip install -r requirements.txt")
            return

        # Check port
        if not check_port_available(args.port):
            print(f"\n❌ Port {args.port} is already in use!")
            choice = input(f"Try another port? (y/n): ")
            if choice.lower() == 'y':
                new_port = int(input("Enter port number: "))
                args.port = new_port
                if not check_port_available(args.port):
                    print(f"❌ Port {args.port} is also in use.")
                    return
            else:
                return

        # Check if already running
        status = load_status()
        if status and status.get('running'):
            print(f"\n⚠️  Application is already running on port {status.get('port')}")
            choice = input("Stop and restart? (y/n): ")
            if choice.lower() == 'y':
                stop_application()
            else:
                return

        print(f"\n🚀 Starting Kiselgram...")
        print(f"   Port: {args.port}")
        print(f"   Host: {args.host}")
        print(f"   Debug: {args.debug}")
        print(f"   Open Browser: {not args.no_browser}")
        print("-" * 40)

        # Start Flask in a separate thread
        flask_thread = threading.Thread(
            target=run_flask_app,
            args=(args.host, args.port, args.debug),
            daemon=True
        )
        flask_thread.start()

        # Wait a bit and check if started
        time.sleep(2)
        if not args.no_browser and check_port_available(args.port):
            # Port is free, so Flask didn't start properly
            print("\n⚠️  Flask may not have started properly. Check logs above.")
        else:
            print("\n✅ Application started!")
            print(f"🌐 Open your browser to: http://localhost:{args.port}")
            print("🛑 To stop: python manage.py stop")
            print("Press Ctrl+C to exit this script (app will continue running)")

            try:
                # Keep script alive
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n👋 Management script stopped. App continues running.")

    elif args.command == 'stop':
        print_header()
        stop_application()

    elif args.command == 'restart':
        print_header()
        print("\n🔄 Restarting Kiselgram...")

        # Get current status for defaults
        status = load_status()
        current_port = args.port if args.port else (status.get('port') if status else 5000)
        current_host = args.host if args.host else (status.get('host') if status else '0.0.0.0')

        # Stop if running
        if status and status.get('running'):
            stop_application()
            time.sleep(2)

        # Start again
        import subprocess
        cmd = [sys.executable, __file__, 'start', '--port', str(current_port), '--host', current_host]
        if args.debug:
            cmd.append('--debug')
        subprocess.run(cmd)

    elif args.command == 'status':
        print_header()
        check_application()

    elif args.command == 'setup':
        print_header()
        setup_environment()

    elif args.command == 'clean':
        print_header()
        clean_temporary_files()

    elif args.command == 'reset-db':
        print_header()
        reset_database()

    elif args.command == 'test':
        print_header()
        run_tests()

    elif args.command == 'help':
        show_help()

    else:
        print(f"❌ Unknown command: {args.command}")
        show_help()


# Cleanup on exit
def cleanup():
    """Cleanup function called on exit"""
    if os.path.exists('tmp_runner.py'):
        os.remove('tmp_runner.py')


atexit.register(cleanup)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)