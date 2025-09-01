#!/usr/bin/env python3
"""Build script for creating executable from Sermon Slides Generator GUI."""

import os
import shutil
import subprocess
import sys
from pathlib import Path

def clean_build():
    """Clean previous build artifacts."""
    print("🧹 Cleaning previous builds...")
    
    build_dir = Path("build")
    dist_dir = Path("dist")
    
    if build_dir.exists():
        shutil.rmtree(build_dir)
        print("   ✓ Removed build/")
    
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
        print("   ✓ Removed dist/")

def build_executable():
    """Build the executable using PyInstaller."""
    print("🔨 Building executable...")
    
    # Ensure we're in the right directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # Run PyInstaller with our spec file
    try:
        result = subprocess.run([
            sys.executable, "-m", "PyInstaller",
            "sermon_slides.spec",
            "--clean",
            "--noconfirm"
        ], check=True, capture_output=True, text=True)
        
        print("   ✓ PyInstaller completed successfully")
        
        # Print any warnings
        if result.stderr:
            print("   ⚠️ Warnings:")
            for line in result.stderr.split('\n'):
                if line.strip() and 'WARNING' in line.upper():
                    print(f"     {line}")
        
    except subprocess.CalledProcessError as e:
        print(f"   ❌ PyInstaller failed with error code {e.returncode}")
        print("   Error output:")
        print(e.stderr)
        return False
    
    return True

def verify_build():
    """Verify that the build was successful."""
    print("🔍 Verifying build...")
    
    dist_dir = Path("dist")
    
    # Check for macOS app bundle
    app_bundle = dist_dir / "Sermon Slides Generator.app"
    if app_bundle.exists():
        print(f"   ✓ Created macOS app bundle: {app_bundle}")
        return True
    
    # Check for regular executable
    exe_file = dist_dir / "SermonSlidesGenerator"
    if exe_file.exists():
        print(f"   ✓ Created executable: {exe_file}")
        return True
    
    print("   ❌ No executable found in dist/")
    return False

def show_results():
    """Show build results and next steps."""
    print("\n🎉 Build completed!")
    
    dist_dir = Path("dist")
    
    if dist_dir.exists():
        print(f"\nBuild artifacts in: {dist_dir.absolute()}")
        
        # List contents
        for item in dist_dir.iterdir():
            if item.is_file():
                size_mb = item.stat().st_size / (1024 * 1024)
                print(f"   📄 {item.name} ({size_mb:.1f} MB)")
            elif item.is_dir():
                print(f"   📁 {item.name}/")
        
        print("\n📋 Next steps:")
        print("   1. Test the executable to ensure it works correctly")
        print("   2. Distribute the app bundle or executable as needed")
        
        # Platform-specific instructions
        if os.name == 'posix' and os.uname().sysname == 'Darwin':
            app_bundle = dist_dir / "Sermon Slides Generator.app"
            if app_bundle.exists():
                print(f"   3. On macOS, you can run: open '{app_bundle}'")
                print("   4. For distribution, you may need to code sign the app")
    
def main():
    """Main build process."""
    print("🚀 Building Sermon Slides Generator executable...\n")
    
    # Step 1: Clean previous builds
    clean_build()
    print()
    
    # Step 2: Build executable
    if not build_executable():
        print("❌ Build failed!")
        sys.exit(1)
    print()
    
    # Step 3: Verify build
    if not verify_build():
        print("❌ Build verification failed!")
        sys.exit(1)
    print()
    
    # Step 4: Show results
    show_results()

if __name__ == "__main__":
    main()