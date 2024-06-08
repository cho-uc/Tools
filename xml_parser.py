'''
Python script to parse XML file (reference vs input)

Store the values in a dictionary (containing tags and values).
Example:
    data/measurement_data                 [('name', 'measurement_data')]
	data/measurement_data/image_subg_nc   [('name', 'image_subg_nc'), ('length', '')]
	data/measurement_data/image_subg_nl   [('name', 'image_subg_nl'), ('length', '')]
Assumption:
    - the lowest level child is level-4
'''

import xml.etree.ElementTree as ET
import os, re, argparse
import subprocess
import math

def is_number(value):
  if value is None:
      return False
  try:
      float(value)
      return True
  except:
      return False

def parse_xml(filepath):
    tree = ET.parse(filepath)
    root = tree.getroot()

    xml_data = dict()
    subroot1 = list(root) # get children
    # print("Subroot1 has "+ str(len(subroot1)) + " children.")
    for idx1 in range(len(subroot1)):
        subroot2 = list(subroot1[idx1])  # get children
        # print("\tSubroot2: " + subroot1[idx1].attrib["name"] +" has: "+ str(len(subroot2)) + " children.")
        path1 = subroot1[idx1].attrib["name"]
        # print("\t\t" + str(subroot1[idx1].items()))
        xml_data[path1] = subroot1[idx1].items()     # store the values to a dict
        for idx2 in range(len(subroot2)): # go down 1 level
            subroot3 = list(subroot2[idx2])  # get children
            # print("\tSubroot3: " + subroot2[idx2].attrib["name"] +" has: "+ str(len(subroot3)) + " children.")
            path2 = path1 + "/" + subroot2[idx2].attrib["name"]
            # print("\t\t" + str(subroot2[idx2].items()))
            xml_data[path2] = subroot2[idx2].items()    # store the values to a dict
            for idx3 in range(len(subroot3)):  # go down 1 level
                subroot4 = list(subroot3[idx3])  # get children
                # print("\tSubroot4: " + subroot3[idx3].attrib["name"]+" has: "+str(len(subroot4)) + " children.")
                path3 = path2 + "/" + subroot3[idx3].attrib["name"]
                # print("\t\t" + str(subroot3[idx3].items()))
                xml_data[path3] = subroot3[idx3].items()    # store the values to a dict
                for idx4 in range(len(subroot4)):
                    # print("\t\t" + str(idx4) + " - " + str(subroot4[idx4].items()))
                    path4 = path3 + "/"+ subroot4[idx4].attrib["name"]
                    xml_data[path4] = subroot4[idx4].items()

    # Change values from tuples to list to be mutable
    normalize_data_type(xml_data)

    return xml_data

# Convert list of tuple (immutable) to be list of list (mutable)
def normalize_data_type(data):
    for key,value_list in data.items():
        size = len(value_list)     # store size to avoid dynamically changed size during iteration
        for idx in range (size):
            # pop values starting from first element
            new_list = list((value_list[0][0], value_list[0][1]))
            del value_list[0]
            value_list.append(new_list) 

    # Replace strings numeric with numeric values
    for key,value_list in data.items():
        obj_value = None
        obj_type = None
        for item in value_list:
            if (item[0] == 'value'):
                obj_value = item[1]
            if (item[0] == 'type'):
                obj_type = item[1]

        if (obj_type == 'float') or (obj_type == 'double'):
            for item in value_list:
                if (item[0] == 'value'):
                    if is_number(obj_value):
                        item[1] = float(obj_value)
                    else:
                        item[1] = 0 # special case when 'type' is float/double but 'value' is not number (example : TBC)

def compare_tags(file, xml_data_input, xml_data_ref):
    # Compare input data with reference (tags)
    logfile1 = open("missing-xml-tags.txt", "a")
    logfile1.write("Comparing input vs reference (tags)-----------------------------\n")
    logfile1.write("Input: " + file +"\n")
    logfile1.write("List of non matching ref vs input (missing tags in input) -------\n")
    non_matching_count1 = 0
    matching_count1 = 0
    for ref_key,ref_val in xml_data_ref.items():
        if ref_key not in xml_data_input.keys():
            logfile1.write("\t" + ref_key + ' doesn\'t exist in input file\n')
            non_matching_count1 += 1
        else:
            matching_count1 += 1
    logfile1.write("Total non matching tag ref vs input (missing tags in input): "+ str(non_matching_count1) + "\n")
    logfile1.write("Total matching ref tag vs input: "+ str(matching_count1) + "\n\n")
    logfile1.close()

    # Compare reference with input data (tag)
    logfile2 = open("extra-xml-tags.txt", "a")
    logfile2.write("Comparing reference vs input (tags)-----------------------------\n")
    logfile2.write("Input: " + file +"\n")
    logfile2.write("List of non matching input vs ref (extra tags in input) -------\n")
    non_matching_count2 = 0
    matching_count2 = 0
    for input_key,input_val in xml_data_input.items():
        if input_key not in xml_data_ref.keys():
            logfile2.write("\t" + input_key + ' doesn\'t exist in reference file\n')
            non_matching_count2 += 1
        else:
            matching_count2 += 1
    logfile2.write("Total non matching tags input vs ref (extra tags in input): "+ str(non_matching_count2) + "\n")
    logfile2.write("Total matching tags input vs ref: "+ str(matching_count2) + "\n\n")
    logfile2.close()

    # Make sure that all matching tags exist in both input and ref files
    assert(matching_count1 == matching_count2)

def compare_values(file, xml_data_input, xml_data_ref):
    logfile = open("value-comparison.txt", "a")
    logfile.write("Comparing input vs reference (values)-----------------------------\n")
    logfile.write("Input: " + file +"\n")
    val_matching_count = 0
    val_nonmatching_count = 0
    for ref_key,ref_val in xml_data_ref.items():
        if ref_key in xml_data_input.keys():
            # Aggregate all strings in the tuple list and sort
            tuple_input = []
            tuple_ref = []
            for item in xml_data_input.get(ref_key):
                tuple_input.append(str(item[0]))
                tuple_input.append(str(item[1]))
            for item in xml_data_ref.get(ref_key):
                tuple_ref.append(str(item[0]))
                tuple_ref.append(str(item[1]))
            tuple_input.sort()
            tuple_ref.sort()
            if (tuple_input == tuple_ref):
                val_matching_count += 1
            else:
                logfile.write("Value does not match for tag "+ ref_key + ": \n")
                logfile.write("\tInput: " + str(xml_data_input.get(ref_key)) + "\n")
                logfile.write("\tRef:" + str(xml_data_ref.get(ref_key)) + "\n")
                val_nonmatching_count +=1
    logfile.write("Total matched values: "+ str(val_matching_count) + "\n")
    logfile.write("Total non-matching values: "+ str(val_nonmatching_count) + "\n\n")
    logfile.close()

def is_float(value):
  if value is None:
      return False
  try:
      float(value)
      return True
  except:
      return False

# Differentiate between comparing values as string an as numbers
def compare_value(val1, val2):
    if (is_float(val1) and is_float(val2)):
        return math.isclose(float(val1), float(val2), rel_tol=1e-19)
    else:
        return val1 == val2


if __name__ == '__main__':

    # Perform XML analysis
    print("\nPerform XML analysis .........")
    xml_data_ref = parse_xml('reference.xml')
    xml_data_input_list =[]
    xml_data_input_size = []
    xml_data_input_name = []

    xml_input_dir = '/path/containing/xml/files'
    # r = root, d = directories, f = files
    for r, d, f in os.walk(xml_input_dir):
        for file in f:
            abs_path = os.path.join(r, file)
            print("\nParsing " + abs_path + ' ....')
            xml_data_input = parse_xml(abs_path)
            xml_data_input_list.append(xml_data_input) # store to a list
            xml_data_input_size.append(len(xml_data_input))
            xml_data_input_name.append(file)

            # print("Final dict: ------------------")  # print all dict values
            # for key,val in xml_data_ref.items():
            #     print("\t" + str(key) + " - " + str(val))

            # Compare input data with reference (tags)
            compare_tags(file, xml_data_input, xml_data_ref)

            # Compare input data with reference (values)
            compare_values(file, xml_data_input, xml_data_ref)
            
    print("\nTotal: "+ str(len(xml_data_input_list))+" files.\n")

    print("\nFinish analysis")


