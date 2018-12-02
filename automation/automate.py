import os
import sys
import shutil
import subprocess
import collections

project_id = sys.argv[1]
defect_id = sys.argv[2]
cwd=os.path.dirname(os.path.abspath(__file__))
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

d4j_dir=os.environ.get("D4J_HOME")

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
print("Running " + compile_command)
os.system(compile_command)
print("Running " + package_command)
os.system(package_command)

target_dir = os.path.join(defect_dir,"target")

os.chdir(target_dir)
junit_get_command = "wget https://github.com/downloads/junit-team/junit/junit-4.10.jar"
print("Running " + junit_get_command)
os.system(junit_get_command)

# os.environ[JAVA_HOME]=java8_home

junit_path = os.path.join(target_dir,"junit-4.10.jar")
class_path=[".",target_dir,os.path.join(target_dir,"test-classes"),os.path.join(target_dir,"commons-lang-3.0-SNAPSHOT.jar"),junit_path]


os.chdir(os.path.join(cwd,"src"))
compile_invoke_command = "javac -cp "+ ":".join(class_path) + " InvokeTests.java"
print("Running " + compile_invoke_command)
os.system(compile_invoke_command)


relevant_tests_list=None
relevant_test_file=os.path.join(d4j_dir,"framework","projects",project_id,"relevant_tests",defect_id)
with open(relevant_test_file) as f:
    relevant_tests_list=f.read().splitlines()

test_class_method_map = collections.OrderedDict()

for testclass in relevant_tests_list:
    list_test_command="java -cp "+ ":".join(class_path) + " InvokeTests "+defect_dir + " getTestCases " + testclass
    print("Running " + list_test_command)
    tests_list = subprocess.run(list_test_command,stdout=subprocess.PIPE,shell=True)
    tests_list = tests_list.stdout.decode("utf-8")
    tests_list = tests_list.splitlines()
    test_class_method_map[testclass] = tests_list
    

os.environ[JAVA_HOME]=java8_home
os.chdir(cwd)
if not os.path.exists("./javaslicer"):
    os.system("git clone https://github.com/hammacher/javaslicer")
    os.chdir("./javaslicer")
    os.system("bash assemble.sh")
    
tracer_dir = os.path.join(cwd,"javaslicer","assembly")

#os.system("cp "+os.path.join(cwd,"javaslicer","assembly","*.jar")+" "+target_dir    )

os.chdir(os.path.join(cwd,"src"))
os.makedirs(os.path.join(target_dir,"traces"))
count=0
for testclass in test_class_method_map:
    for testname in test_class_method_map[testclass]:
        tracer_command="java -cp "+ ":".join(class_path) + " -javaagent:"+ \
        os.path.join(tracer_dir,"tracer.jar")+"=tracefile:"+ \
        os.path.join(target_dir,"traces","trace."+testclass+"#"+testname)+ \
        " InvokeTests "+defect_dir+" runTestCase " + testclass + " " + testname
        print("Running "+tracer_command)
        os.system(tracer_command)
        
        traceReader_command="java -jar "+os.path.join(tracer_dir,"traceReader.jar")+" "+ \
        os.path.join(target_dir,"traces","trace."+testclass+"#"+testname) + " > " \
        + os.path.join(target_dir,"traces","trace."+testclass+"#"+testname+".output")
        print("Running "+traceReader_command)
        os.system(traceReader_command)

        count+=1
        if count==1:
            break
    break

gzoltars_dir=os.path.join(root_directory,"gzoltars",project_id,defect_id)

relevant_class=""

with open(os.path.join(gzoltars_dir,"spectra")) as f:
    relevant_class=f.read().splitlines()[0].split("#")[0]

grep_relevant_command="grep -rl "+relevant_class+" "+os.path.join(target_dir,"traces")
print("Running "+grep_relevant_command)
grep_tests_list = subprocess.run(grep_relevant_command,stdout=subprocess.PIPE,shell=True)
grep_tests_list = grep_tests_list.stdout.decode("utf-8")
grep_tests_list = grep_tests_list.splitlines()

print(grep_tests_list)
for i in range(len(grep_tests_list)):
    grep_tests_list[i] = os.path.basename(grep_tests_list[i])[6:]
    grep_tests_list[i] = grep_tests_list[i].split("#")
    grep_tests_list[i][1]=grep_tests_list[i][1][:-7]

print("Count of grep result: "+str(len(grep_tests_list)))

with open(os.path.join(cwd,"test_count.txt"),"w") as f:
    f.write("Count of grep result: "+str(len(grep_tests_list)))

os.chdir(os.path.join(cwd,"src"))
for test in grep_tests_list:
    testclass=test[0]
    testname=test[1]
    assert_list_command="java -cp "+ ":".join(class_path) +  \
    " InvokeTests "+defect_dir+" getAssertLines " + testclass + " " + testname
    print("Running "+assert_list_command)
    assert_list = subprocess.run(assert_list_command,stdout=subprocess.PIPE,shell=True)
    assert_list = assert_list.stdout.decode("utf-8")
    assert_list = assert_list.splitlines()
    slicing_criteria=[]
    for line in assert_list:
        slicing_criteria+=[testclass+"."+testname+":"+line+":*"]
    slice_command="java -Xmx2g -jar "+os.path.join(tracer_dir,"slicer.jar")+" -p "+ \
        os.path.join(target_dir,"traces","trace."+testclass+"#"+testname) +  \
        " " + ",".join(slicing_criteria) + \
        " > " + os.path.join(target_dir,"traces","trace."+testclass+"#"+testname+".slice")
    print("Running "+slice_command)
    os.system(slice_command)
    coverage_line_grep_command= "grep \"" + relevant_class  + "\\.\" " + os.path.join(target_dir,"traces","trace."+testclass+"#"+testname+".slice")