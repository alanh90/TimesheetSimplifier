"""
Initial setup script for Timesheet Simplifier
Run this to set up the application for first use
"""

import os
import shutil
from pathlib import Path
import subprocess
import sys


def create_directories():
    """Create necessary directories"""
    directories = ['charge_codes', 'data', 'exports']

    print("Creating directories...")
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        # Replaced '✓' with '-'
        print(f"  - Created {directory}/")

    # Create .gitkeep files to ensure directories are tracked
    for directory in directories:
        gitkeep = Path(directory) / '.gitkeep'
        # Ensure .gitkeep files exist, but don't error if they do
        if not gitkeep.exists():
            gitkeep.touch()


def copy_sample_files():
    """Copy sample files if they don't exist"""
    print("\nSetting up sample files...")

    # Check if sample charge code file exists (assuming it's at the project root initially)
    if os.path.exists('sample_charge_codes.csv'):
        target_path = Path('charge_codes') / 'sample_charge_codes.csv'
        if not target_path.exists():
            shutil.copy('sample_charge_codes.csv', target_path)
            # Replaced '✓' with '-'
            print("  - Copied sample charge codes to charge_codes/")
        else:
            # Replaced '→' with '-'
            print("  - Sample charge codes already exist")
    else:
        # Replaced '!' with '-' (or could remove if desired)
        print("  - Sample charge codes file not found")


def install_requirements():
    """Install Python requirements"""
    print("\nInstalling Python packages...")

    try:
        # pip install -e . (editable install)
        # This is the key part for src/ layout projects
        # We assume requirements.txt is installed via previous 'python setup.py'
        # or separate pip install -r, but we ensure the editable install for src/
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-e', '.'])
        # Replaced '✓' with '-'
        print("  - Project installed in editable mode & dependencies verified/installed.")
    except subprocess.CalledProcessError:
        # Replaced '!' with '-'
        print("  - Error installing packages. Please ensure requirements.txt is valid and try running 'pip install -r requirements.txt' manually.")
        return False

    return True


def check_python_version():
    """Check if Python version is 3.10 or higher"""
    print("Checking Python version...")

    if sys.version_info < (3, 10):
        # Replaced '!' with '-'
        print(f"  - Python 3.10+ required. You have {sys.version.split()[0]}")
        return False

    # Replaced '✓' with '-'
    print(f"  - Python {sys.version.split()[0]} detected")
    return True


def main():
    """Main setup function"""
    print("=" * 50)
    print("Timesheet Simplifier - Setup")
    print("=" * 50)
    print()

    # Check Python version
    if not check_python_version():
        print("\nSetup failed. Please install Python 3.10 or higher.")
        return

    # Create directories
    create_directories()

    # Copy sample files
    copy_sample_files()

    # Install requirements and editable mode for src/
    # This single call now handles both the editable install and implies requirements are met
    if not install_requirements():
        print("\nSetup completed with warnings.")
        return

    print("\n" + "=" * 50)
    # Removed '✨' emoji
    print("Setup completed successfully!")
    print("=" * 50)
    print()
    print("Next steps:")
    print("1. Ask your manager for the charge codes file")
    print("2. Place it in the 'charge_codes' directory")
    print("3. Run the application:")
    # Updated command for src/ structure
    print("   - Windows: run.bat")
    print("   - macOS/Linux: ./run.sh")
    print("   - Or directly: streamlit run src/app.py")
    print()
    # Removed '🎉' emoji
    print("Happy time tracking!")


if __name__ == "__main__":
    main()