import sys
import logging
import os
from .authentication.auth_manager import AuthManager
from .cli.commands import app
from .cli.interactive import interactive_main
from .config import config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('passport.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def check_initialization():
    key_file = config.default_key_file
    password_file = config.default_password_file
    
    if not os.path.exists(key_file) or not os.path.exists(password_file):
        return False
    return True

def main():
    try:
        auth_manager = AuthManager()
        
        if not auth_manager.authenticate():
            print("\n Authentication failed. Exiting...")
            sys.exit(1)
        
        if not check_initialization():
            print("\n PassPort is not initialized yet!")
            print("Running initialization wizard...\n")
            
            sys.argv = ['passport', 'init']
            app()
            return
        
        if len(sys.argv) <= 1:
            interactive_main()
        else:
            app()
            
    except KeyboardInterrupt:
        print("\n Goodbye, Stay secure!")
        sys.exit(0)
    except Exception as e:
        print(f"Unexpected error: {e}")
        logger.exception("Unexpected error in main")
        sys.exit(1)

if __name__ == "__main__":
    main()