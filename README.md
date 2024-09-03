# gtech_assignment
GTech Assignment

### 1. Download Govtech-Assignment.7z
Unzip 7z File in preferred location

### 2. Install prevailing version of MariaDB
Create Database
- CREATE DATABASE govtech_assignment

### 3. Run Scripts in SQL Folder in sequence

### 4. Run Application Codes (Ensure Python is installed)
- Govtech-Assignment\Scripts\activate
- python Govtech-Assignment\app.py

### 5. Load SwaggerUI
- https://editor.swagger.io/
- Import 'GTech-Assignment-SwaggerUI.yaml' file
- Test & Verify Endpoints


## __Appendix__

If starting from scratch, please begin with steps below before proceeding with above
### 1. Create Folder for Project

### 2. Create Project Virtual Environment
- python -m venv Govtech-Assignment
- Govtech-Assignment\Scripts\activate

### 3. Install MariaDB connector & CORs dependency
- pip install mariadb
- pip install -U flask-cors
