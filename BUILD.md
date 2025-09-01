# Building Sermon Slides Generator Executable

This document describes how to build a standalone executable from the Sermon Slides Generator GUI.

## Prerequisites

- Python 3.13+ installed
- All project dependencies installed (`uv sync`)

## Quick Build

To build the executable, simply run:

```bash
python build.py
```

This will:
1. Clean any previous build artifacts
2. Run PyInstaller with the custom spec file
3. Create both a standalone executable and macOS app bundle
4. Verify the build was successful

## Build Output

The build process creates two executables in the `dist/` directory:

### macOS App Bundle
- **File**: `dist/Sermon Slides Generator.app`
- **Usage**: Double-click to launch or run `open "dist/Sermon Slides Generator.app"`
- **Size**: ~19MB
- **Features**: Native macOS app with proper bundle structure

### Standalone Executable
- **File**: `dist/SermonSlidesGenerator`
- **Usage**: Run directly from terminal: `./dist/SermonSlidesGenerator`
- **Size**: ~18MB
- **Features**: Single executable file, no installation required

## Manual Build

If you prefer to run PyInstaller directly:

```bash
pyinstaller sermon_slides.spec --clean --noconfirm
```

## Customization

### Spec File (`sermon_slides.spec`)
The PyInstaller configuration includes:
- HTML template bundling
- Font file inclusion
- Excluded unnecessary dependencies for smaller size
- macOS app bundle configuration
- Hidden imports for PyWebView

### Build Script (`build.py`)
The build script provides:
- Automatic cleanup of previous builds
- Progress reporting
- Build verification
- Error handling
- Cross-platform support

## Distribution

### macOS
- **App Bundle**: `Sermon Slides Generator.app` - Ready for distribution
- **Code Signing**: For wider distribution, code sign the app:
  ```bash
  codesign --deep --force --verify --verbose --sign "Developer ID Application: Your Name" "dist/Sermon Slides Generator.app"
  ```

### Other Platforms
- The standalone executable can be distributed as-is
- Consider creating an installer for easier deployment

## Troubleshooting

### Common Issues
1. **Missing font files**: Ensure `JosefinSans-Medium.ttf` exists in the project root
2. **HTML template not found**: Verify `templates/index.html` exists
3. **Import errors**: Check the `hiddenimports` list in the spec file

### Build Warnings
- Minor warnings about optional modules are normal
- Check `build/sermon_slides/warn-sermon_slides.txt` for details

## File Sizes
- **App Bundle**: ~19MB (includes all dependencies and frameworks)
- **Executable**: ~18MB (standalone single file)
- **Compressed**: ~6-8MB when zipped for distribution

## Dependencies Included
The executable includes all necessary dependencies:
- PyWebView and web rendering engine
- Python standard library
- PIL/Pillow for image processing
- BeautifulSoup for HTML parsing
- Requests for HTTP requests
- All fonts and templates