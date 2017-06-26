# This script parses and cleans the xml data and then writes the cleaned data to csv files.
# The csv files were imported to a sql database.

from collections import defaultdict
import csv
import codecs
import pprint
import re
import xml.etree.cElementTree as ET

import cerberus
import schema


OSM_PATH = "mission_district.osm"

NODES_PATH = "nodes.csv"
NODE_TAGS_PATH = "nodes_tags.csv"
WAYS_PATH = "ways.csv"
WAY_NODES_PATH = "ways_nodes.csv"
WAY_TAGS_PATH = "ways_tags.csv"

LOWER_COLON = re.compile(r'^([a-z]|_)+:([a-z]|_)+')
PROBLEMCHARS = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')
street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)

SCHEMA = schema.schema

# Make sure the fields order in the csvs matches the column order in the sql table schema
NODE_FIELDS = ['id', 'lat', 'lon', 'user', 'uid', 'version', 'changeset', 'timestamp']
NODE_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_FIELDS = ['id', 'user', 'uid', 'version', 'changeset', 'timestamp']
WAY_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_NODES_FIELDS = ['id', 'node_id', 'position']

# Expected and Mapping are used to audit and fix the street names in the osm file.
expected = ["Street", "Avenue", "Boulevard", "Drive", "Court", "Place", "Square", "Lane", "Road", 
            "Trail", "Parkway", "Commons"]

mapping = {"St" : "Street", "St." : "Street"}


def audit_street_type(street_types, street_name):
    m = street_type_re.search(street_name)
    if m:
        street_type = m.group()
        if street_type not in expected:
            street_types[street_type].add(street_name)


def is_street_name(elem):
    return (elem.attrib['k'] == "addr:street")


def audit(osmfile):
    street_types = defaultdict(set)
    for event, elem in ET.iterparse(osmfile, events=("start",)):

        if elem.tag == "node" or elem.tag == "way":
            for tag in elem.iter("tag"):
                if is_street_name(tag):
                    audit_street_type(street_types, tag.attrib['v'])
    #print street_types
    return street_types

def update_name(name, mapping):

    # YOUR CODE HERE
    m = street_type_re.search(name)
    if m:
        street_type = m.group()
        if street_type in mapping.keys():
            
            # Had to use re.sub to replace last word in street names
            name = re.sub(street_type, mapping[street_type], name)
    
    return name

def is_postcode(elem):
    return (elem.attrib['k'] == "addr:postcode")


def shape_element(element, node_attr_fields=NODE_FIELDS, way_attr_fields=WAY_FIELDS,
                  problem_chars=PROBLEMCHARS, default_tag_type='regular'):
    """Clean and shape node or way XML element to Python dict"""

    node_attribs = {}
    way_attribs = {}
    way_nodes = []
    tags = []  # Handle secondary tags the same way for both node and way elements
    
    # I found this symbol in my audit of street names
    symbol = '#'                        
    
    if element.tag == 'node':
        
        for attribute in element.attrib:
            
            if attribute in node_attr_fields:
                node_attribs[attribute] = element.attrib[attribute]
        
        for sub in element:
            
            if sub.tag == 'tag':
                
                node_tags = {}
                                
                ### CLEAN STREET NAMES
                                
                # These are the street names that I want to call update_name on
                if is_street_name(sub):
                    #print sub.attrib['v']
                                        
                    ### REMOVE SPECIAL CHARACTERS
                    # Loop through st_types dictionary
                    
                    # If the street name contains a '#' character, split the street name on white spaces
                    # Delete the last element of the list which contains the '#'
                    # Recombine the remaining words and call update_name() ib them
                    
                    # Else, just call update_name()
                    
                    for st_type, ways in st_types.iteritems():
                        for name in ways:
                            if name == sub.attrib['v']:                                    
                                
                                if symbol in sub.attrib['v']:
                                    words_in_name = sub.attrib['v'].split(" ")
                                    del words_in_name[-1]
                                    sub.attrib['v'] = words_in_name[0] + " " + words_in_name[1]
                                    sub.attrib['v'] = update_name(sub.attrib['v'], mapping)
                                    
                                else:
                                    sub.attrib['v'] = update_name(name, mapping)
                                
                ### CLEAN POSTCODES
                
                # Change postcodes with format CA:94112 to 94112
                elif is_postcode(sub):
                    if len(sub.attrib['v'].split(":")) == 2:
                        sub.attrib['v'] = sub.attrib['v'].split(":")[1]

                # Look for problem chars
                if re.search(problem_chars, sub.get("k")):
                    pass
                                
                # at id and value to node_tags dictionary
                node_tags['id'] = element.attrib['id']
                node_tags['value'] = sub.attrib['v']
                
                # Look for colons in keys
                if len(sub.attrib['k'].split(":")) == 1:
                    node_tags['key'] = sub.attrib['k']
                    node_tags['type'] = default_tag_type
                    
                elif len(sub.attrib['k'].split(":")) == 2:
                    node_tags['key'] = sub.attrib['k'].split(":")[1]
                    node_tags['type'] = sub.attrib['k'].split(":")[0]
                    
                elif len(sub.attrib['k'].split(":")) == 3:
                    node_tags['key'] = sub.attrib['k'].split(":")[1] + sub.attrib['k'].split(":")[2]
                    node_tags['type'] = sub.attrib['k'].split(":")[0]

                tags.append(node_tags)
                
                #print sub.attrib
        
        #print node_attribs
        return {'node': node_attribs, 'node_tags': tags}
        
    elif element.tag == 'way':
        
        position = 0
        
        for attribute in element.attrib:
            
            if attribute in way_attr_fields:
                way_attribs[attribute] = element.attrib[attribute]
                #print way_attribs[attribute]
                
        for sub in element:
            if sub.tag == 'tag':
                                
                ### CLEAN STREET NAMES
                                
                # These are the street names that I want to call update_name on
                if is_street_name(sub):
                    #print sub.attrib['v']
                                        
                    ### REMOVE SPECIAL CHARACTERS
                    # Loop through st_types dictionary
                    
                    # If the street name contains a '#' character, split the street name on white spaces
                    # Delete the last element of the list which contains the '#'
                    # Recombine the remaining words and call update_name() on them
                    
                    # Else, just call update_name()
                    
                    for st_type, ways in st_types.iteritems():
                        for name in ways:
                            if name == sub.attrib['v']:                                    
                                
                                if symbol in sub.attrib['v']:
                                    words_in_name = sub.attrib['v'].split(" ")
                                    del words_in_name[-1]
                                    sub.attrib['v'] = words_in_name[0] + " " + words_in_name[1]
                                    sub.attrib['v'] = update_name(sub.attrib['v'], mapping)
                                    
                                else:
                                    sub.attrib['v'] = update_name(name, mapping)
                                
                ### CLEAN POSTCODES
                
                # Change postcodes with format CA:94112 to 94112
                elif is_postcode(sub):
                    if len(sub.attrib['v'].split(":")) == 2:
                        sub.attrib['v'] = sub.attrib['v'].split(":")[1]
                
                way_tags = {}
                way_tags['id'] = element.attrib['id']
                way_tags['value'] = sub.attrib['v']
                
                if len(sub.attrib['k'].split(":")) == 1:
                    way_tags['key'] = sub.attrib['k']
                    way_tags['type'] = default_tag_type
                    
                elif len(sub.attrib['k'].split(":")) == 2:
                    way_tags['key'] = sub.attrib['k'].split(":")[1]
                    way_tags['type'] = sub.attrib['k'].split(":")[0]
                    
                elif len(sub.attrib['k'].split(":")) == 3:
                    way_tags['key'] = sub.attrib['k'].split(":")[1] + ':' + sub.attrib['k'].split(":")[2]
                    way_tags['type'] = sub.attrib['k'].split(":")[0]
                                    
                tags.append(way_tags)
                
            elif sub.tag == 'nd':
                
                way_node_tags = {}
                way_node_tags['id'] = element.attrib['id']
                way_node_tags['node_id'] = sub.attrib['ref']
                way_node_tags['position'] = position
                way_nodes.append(way_node_tags)
                
                position += 1

        #print tags        
        return {'way': way_attribs, 'way_nodes': way_nodes, 'way_tags': tags}


# ================================================== #
#               Helper Functions                     #
# ================================================== #
def get_element(osm_file, tags=('node', 'way', 'relation')):
    """Yield element if it is the right type of tag"""

    context = ET.iterparse(osm_file, events=('start', 'end'))
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            root.clear()


def validate_element(element, validator, schema=SCHEMA):
    """Raise ValidationError if element does not match schema"""
    if validator.validate(element, schema) is not True:
        field, errors = next(validator.errors.iteritems())
        message_string = "\nElement of type '{0}' has the following errors:\n{1}"
        error_string = pprint.pformat(errors)
        
        raise Exception(message_string.format(field, error_string))


class UnicodeDictWriter(csv.DictWriter, object):
    """Extend csv.DictWriter to handle Unicode input"""

    def writerow(self, row):
        super(UnicodeDictWriter, self).writerow({
            k: (v.encode('utf-8') if isinstance(v, unicode) else v) for k, v in row.iteritems()
        })

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)


# ================================================== #
#               Main Function                        #
# ================================================== #
def process_map(file_in, validate):
    """Iteratively process each XML element and write to csv(s)"""

    with codecs.open(NODES_PATH, 'w') as nodes_file, \
         codecs.open(NODE_TAGS_PATH, 'w') as nodes_tags_file, \
         codecs.open(WAYS_PATH, 'w') as ways_file, \
         codecs.open(WAY_NODES_PATH, 'w') as way_nodes_file, \
         codecs.open(WAY_TAGS_PATH, 'w') as way_tags_file:

        nodes_writer = UnicodeDictWriter(nodes_file, NODE_FIELDS)
        node_tags_writer = UnicodeDictWriter(nodes_tags_file, NODE_TAGS_FIELDS)
        ways_writer = UnicodeDictWriter(ways_file, WAY_FIELDS)
        way_nodes_writer = UnicodeDictWriter(way_nodes_file, WAY_NODES_FIELDS)
        way_tags_writer = UnicodeDictWriter(way_tags_file, WAY_TAGS_FIELDS)

        nodes_writer.writeheader()
        node_tags_writer.writeheader()
        ways_writer.writeheader()
        way_nodes_writer.writeheader()
        way_tags_writer.writeheader()

        validator = cerberus.Validator()
                        
        for element in get_element(file_in, tags=('node', 'way')):
            el = shape_element(element)
            if el:                
                if validate is True:
                    validate_element(el, validator)

                if element.tag == 'node':
                    nodes_writer.writerow(el['node'])
                    node_tags_writer.writerows(el['node_tags'])
                elif element.tag == 'way':
                    ways_writer.writerow(el['way'])
                    way_nodes_writer.writerows(el['way_nodes'])
                    way_tags_writer.writerows(el['way_tags'])
        
if __name__ == '__main__':
    # Note: Validation is ~ 10X slower. For the project consider using a small
    # sample of the map when validating.
    
    ### This is the audit of street types ###
    st_types = audit(OSM_PATH)
    #print st_types
    
    process_map(OSM_PATH, validate=False)
