DESCRIPTION
MetObjects-GalleryNumKnown.csv: Dataset of Met artworks with known gallery numbers. Only includes columns used in our code, and cleaned using OpenRefine
Algorithm2.py: Code for building and executing recommendation algorithms with web scraping. Also includes some data cleaning steps
Visualization.html: Code for building visualization
artworksGalNumKnown.json: JSON file built when running Algorithm2.py code. Includes list of top 20 recommendations for each item in the dataset with similarity scores
no_image_available.png: Placeholder image if missing image URL in Met website

Algorithm2.py builds artworksGalNumKnown.json based on the data within MetObjects-GalleryNumKnown.csv. Visualization.html then takes the data within artworksGalNumKnown.json to build the visualization, inputting the no_image_available.png as a default when no image is provided. Together, these create a museum recommendation network for users to use within the Met, allowing them to go from one artwork they have identified to finding other connected artworks. 

INSTALLATION
Requirements:
A web browser (desktop recommended)
Steps:
	Option 1 (recommended): 
Copy and paste this link into your web browser: https://cse6242-team115.github.io/CSE6242-Team-115-Project/Visualization.html

	Option 2:
Python 3.x required
Download and extract the provided zip project file: https://drive.google.com/file/d/1gyN0u-UP_BFVDBsGTRe2urIzn8jI4eV4/view
(Optional and not recommended — only if generating the JSON file yourself)
Run Algorithm2.py in Python to recreate artworksGalNumKnown.json
We have included artworksGalNumKnown.json upon setup as running the Algorithm2.py file to build the JSON file takes multiple hours to run
Set up a local HTTP server in the file folder to run the visualizations
Open Terminal/Windows Powershell
Navigate to folder in directory
Type/paste in “python -m http.server 8000”
Type/paste “http://localhost:8000/Visualization.html” into your web browser


HOW TO USE VISUALIZATION

Enter an artwork title or Object ID into the upper left input box
Example inputs:
“Bridge over a Pond of Water Lilies” or “29.100.113”
“Goddess of Upper Egypt” or “22.9.4”
“Ceramic Horn” or “89.4.1115”
“Viking Sword” or “55.46.1”
The exact title of the artwork or object id should be used for best performance
Use this link to find other specific artwork titles/Object IDs: https://www.metmuseum.org/art/collection/search
You can also search generic keywords/inputs
In cases where multiple object titles match/contain a given query, the first occurrence is returned
If searching for a specific piece, Object ID is recommended

Explore the Top 20 recommended artworks shown as nodes and in a table
Hover mouse over images in the nodes to see an enlarged preview
Select a node/row to see its information in the table header
Click the title hyperlink in the table header to open its Met Collection page in a new tab
Double-click a node/row to regenerate a new visualization with the top 20 recommendations for that object



DEMO VIDEO 
Following is a demo video on how to use the web application:
https://youtu.be/-citETzeU6Q
