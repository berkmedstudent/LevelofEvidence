#!/bin/bash

# Clean up previous builds
rm -rf build dist

# Build the application using PyInstaller
pyinstaller evidence_grading.spec

# Create a temporary directory for DMG creation
mkdir -p dmg_temp

# Copy the application to the temporary directory
cp -r "dist/Evidence Grading Tool" dmg_temp/

# Create a symbolic link to the Applications folder
ln -s /Applications dmg_temp/Applications

# Create the DMG file
hdiutil create -volname "Evidence Grading Tool" -srcfolder dmg_temp -ov -format UDZO "Evidence Grading Tool.dmg"

# Clean up
rm -rf dmg_temp

echo "DMG file created successfully: Evidence Grading Tool.dmg" 