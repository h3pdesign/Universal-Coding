# From inside your project folder:
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt py2app

# Optional: Clean old builds
rm -rf build dist

# Build app
python setup.py py2app

# Debug launch
./dist/HP\ Calendar\ Agent.app/Contents/MacOS/HP\ Calendar\ Agent