### Overview
<p>I wrangled data from the Mission District of San Francisco.  I made a custom extract on Mapzen at https://mapzen.com/data/metro-extracts/your-extracts/dfe5d8113149 and downloaded the "OSM XML" file.  The borders for my selected region are not exact so there is some data from neighboring districts as well.  The goal of this project was to iteratively parse, audit and clean the data, read the cleaned data into csv files, and then import those csv files into a SQL database.  The resultant database was queried to gain insight into the OpenStreetMap data.</p>  

<p>The OSM file was made up of "node" and "way" tags that contained nested tags.  Below is a small section of the raw OSM data from a sample file I created.</p>

``` Python
<node changeset="37490520" id="61674029" lat="37.7721197" lon="-122.4370577" timestamp="2016-02-27T22:21:55Z" uid="371121" user="AndrewSnow" version="9">
	<tag k="name" v="The Page" />
	<tag k="amenity" v="pub" />
	<tag k="addr:city" v="San Francisco" />
	<tag k="wheelchair" v="yes" />
	<tag k="addr:street" v="Divisadero Street" />
	<tag k="addr:housenumber" v="298" />
</node>
```

### Problems Encountered
<p>After examining the csv files written from data.py I noticed the following problems:</p>
<li>Overabbreviated street names ("Mision st.")</li>
<li>Inconsistent Postal Codes</li>
<li>Special Characters in Street Names</li>

### Writing the csv Files
<p>I used the data.py script I completed in an Udacity quiz to read the xml tags and organize them by 'nodes' and 'ways.'  The original osm file was written into 5 csv files:</p>  

<p>The attributes of the 'node' tags were written to a file called nodes.csv.  These attributes were the id, lat and lon coordinates, timestamp, user id and changeset for a particular node.</p>

<p>The attributes of the tags nested within a node were written to a file called nodes_tags.csv.  These attributes were the id, key, value, and type for that particular node.  Some of these keys were: "name", "amenity", "addr:street" and the corresponding values were: "The Page", "pub", "Divisadero Street."</p>

<p>The attributes of the 'way' tags were placed in a file called ways.csv and held the same categories as the nodes.csv file.</p>

<p>The 'way' tags contained two sub tags 'nd' and 'tag.'  The attributes in the 'nd' tags were written to a file called ways_nodes.csv and contained the tag's id, the id of the node it corresponds to, and the position of the tag.  The attributes in the 'tag' tags were written to a file called ways_tags.csv and contained the id, key, value, and type for that tag.</p>
