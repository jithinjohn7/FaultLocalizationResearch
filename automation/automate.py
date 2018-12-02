import os
import sys
import shutil
import subprocess

project_id = sys.argv[1]
defect_id = sys.argv[2]
java6_home = "/Library/Java/JavaVirtualMachines/1.6.0.jdk/Contents/Home"
java8_home = "/Library/Java/JavaVirtualMachines/jdk1.8.0_191.jdk/Contents/Home"
JAVA_HOME="JAVA_HOME"

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

root_directory = sys.argv[3]
if not os.path.exists(root_directory):
    os.makedirs(root_directory)
project_dir = os.path.join(root_directory,project_id)
if not os.path.exists(project_dir):
    os.makedirs(project_dir)

info_command = "defects4j info -p "+project_id

result = subprocess.run(info_command,stdout=subprocess.PIPE,shell=True)
info_output = result.stdout.decode("utf-8")
info_output = info_output.splitlines()

count_line = info_output[14]
count_line = count_line.split(":")

bug_count = int(count_line[1])

if int(defect_id) > bug_count:
    sys.exit("Please provide valid bug id")

checkout_command = "defects4j checkout -p "+project_id+" -v "+defect_id+"b -w "+project_dir+"/"+defect_id

#Checkout Project with Bug ID
print("Running " + checkout_command)
os.system(checkout_command)

gzoltar_path = os.environ["GZOLTAR_JAR"]
gzoltar_path = gzoltar_path.split('/')[:-1]
gzoltar_path += ["run_gzoltar.sh"]
gzoltar_path = '/'.join(gzoltar_path)

run_gzoltar_command = "bash " + gzoltar_path + " " + project_id + " " + defect_id + " " +  root_directory+ " developer"

print("Running " + run_gzoltar_command)
os.system(run_gzoltar_command)

defect_dir = os.path.join(project_dir,defect_id)

compile_command="mvn compile"

package_command="mvn -Dmaven.test.failure.ignore=true install"

os.environ[JAVA_HOME]=java6_home
os.chdir(defect_dir)
os.system(compile_command)
os.system(package_command)


# os.chdir(os.path.join(defect_dir,"target"))

junit_get_command = "wget https://github.com/downloads/junit-team/junit/junit-4.10.jar"

# os.system(junit_get_command)

#Project name
#bug ID
#workspace

