import os
import sys
import shutil
import subprocess

project_id = sys.argv[1]
defect_id = sys.argv[2]
java6_home = "/Library/Java/JavaVirtualMachines/1.6.0.jdk/Contents/Home"
java8_home = "/Library/Java/JavaVirtualMachines/jdk1.8.0_191.jdk/Contents/Home"

#os.system("export D4J_HOME=/Users/pranita/Downloads/Program_Repair/defects4j")
# os.environ['D4J_HOME'] = "/Users/pranita/Downloads/Program_Repair/defects4j"
# os.environ['GZOLTAR_JAR'] = "/Users/pranita/Downloads/Program_Repair/fault-localization-data/gzoltar/gzoltar.jar"
# os.environ['PATH'] += os.pathsep+"/Users/pranita/Downloads/Program_Repair/defects4j/framework/bin"
# os.environ['SLOC_HOME']="/usr/local/bin/sloccount"

#ignored - bash get_fixed_lines.sh Lang 37 .

if os.environ.get("D4J_HOME") is None or os.environ.get("GZOLTAR_JAR") is None or os.environ.get("SLOC_HOME"):
    sys.exit('Error! Please set D4J_HOME, GZOLTAR_JAR and SLOC_HOME')

if shutil.which("defects4j") is None:
    sys.exit("Please add defects4j to the PATH variable")

file_path = sys.argv[3]
if not os.path.exists(file_path):
    os.makedirs(file_path)

checkout_command = "defects4j checkout -p "+project_id+" -v "+defect_id+"b -w "+file_path+"/"+defect_id

#Checkout Project with Bug ID
print("Running " + checkout_command)

os.system(checkout_command)






#Project name
#bug ID
#workspace

