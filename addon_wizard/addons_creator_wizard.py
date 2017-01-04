import xml.etree.cElementTree as ET
from xml.dom import minidom

#function to put the XML file in proper format
def prettify(elem):

    rough_string = ET.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")

if __name__ == "__main__":

    root = ET.Element("oor:component-data")
    root.set("xmlns:oor","http://openoffice.org/2001/registry")
    root.set("xmlns:xs","http://www.w3.org/2001/XMLSchema")
    root.set("oor:name","Addons")
    root.set("oor:package","org.openoffice.Office")


    node = ET.SubElement(root, "node")
    node.set("oor:name","AddonUI")

    """ Taking inputs according to the user's preferences"""
    while True:

        print ("Enter\n1.To create OfficeMenuBar\n2.To create AddOn Menu\n .....")

        ch = input()

        if ch == "1":

            #OfficeMenuBar creator

            node1 = ET.SubElement(node, "node")
            node1.set("oor:name","org.openoffice.example.addon")
            node1.set("oor:op","replace")

            print ("Enter name of the OfficeMenuBar and Op")

            name = input()
            op = input()

            menu = ET.SubElement(node1, "node")
            menu.set("oor:name",name)
            menu.set("oor:op",op)

        break

    ET.SubElement(node, "node", name="test").text = "Just Testing"

    ans =  prettify(root)

    print (ans)
