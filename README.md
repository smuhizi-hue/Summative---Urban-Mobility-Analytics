NYC Urban Mobility Explorer

Project Overview

NYC urban Moblity EXplorer is a completed web application designed to analyze New York City yellow taxi trips from January 2019. The dashboard presents key mobility statistics through interactive charts, maps, filters, and trip tables.

Technologies Used

- Frontend: HTML, CSS, JavaScipt, Charts.js, Leaflet
- Backend: Python and Flask
- Database: MYSQL

Requirements
- Python 3
- MYSQL Server
- Node.js (optional, only for checking Javascript syntax)
- Internet connection for Chart.js and Leaflet CDN libraries

1. Set up the project
open a terminal in the project root:
cd Summative---Urban-Mobility-Analytics
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
On Windows Powershell, activate the environment with:
.venv\Scripts\Activate.ps1
Ensure MYSQL is running and the project database is configured with the correct credentials in backend/config.py.

2. Launch the application
-Start the backend
From the project root, run:

python backend/app.py

-Start the frontend
Open a second terminal in the project root and run:

    python3 -m http.server 5500
Worksheet https://docs.google.com/spreadsheets/d/1lYUoX1MxxuThjcXsZbpu_VWGurPzR74pRQHddQSTaVk/edit?usp=sharing
 groupmeeting https://drive.google.com/file/d/1Aaf0rRbw99r4TJ4gE63ygRqghspRJ9nz/view?usp=drivesdk

Database design diagram https://drive.google.com/file/d/1zIuUMrSekpdFZHwRvIcaA9FjsxMptOQX/view?usp=sharing
