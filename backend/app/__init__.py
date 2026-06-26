# is an empty file whose sole job is to mark its folder as an importable Python package. 
# There's one in app/, config/, db/, api/, and api/routes/. Without them, Python doesn't recognize the 
# folders as packages and imports like from app.db... fail with No module named 'app'. They stay empty — 
# their existence is the entire point.