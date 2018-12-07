import os
import sys
import shutil
import subprocess
import collections
import multiprocessing
import json
from subprocess import Popen
from itertools import islice
import resource
import copy
import math

project_id = sys.argv[1]
defect_id = sys.argv[2]
cwd=os.path.dirname(os.path.abspath(__file__))
java6_home = "/Library/Java/JavaVirtualMachines/1.6.0.jdk/Contents/Home"
java8_home = "/Library/Java/JavaVirtualMachines/jdk1.8.0_191.jdk/Contents/Home"
JAVA_HOME="JAVA_HOME"
# tacoco_dir = "/Users/pranita/Downloads/Program_Repair/test-tacoco/tacoco"

# os.system("export D4J_HOME=/Users/pranita/Downloads/Program_Repair/defects4j")
# os.environ['D4J_HOME'] = "/Users/pranita/Downloads/Program_Repair/defects4j"
# os.environ['GZOLTAR_JAR'] = "/Users/pranita/Downloads/Program_Repair/fault-localization-data/gzoltar/gzoltar.jar"
# os.environ['PATH'] += os.pathsep+"/Users/pranita/Downloads/Program_Repair/defects4j/framework/bin"
# os.environ['SLOC_HOME']="/usr/local/bin/sloccount"


# Downgrade maven version
# os.system("brew install maven@3.2")
# os.system("brew unlink maven")
# os.system("brew link --force --overwrite maven@3.2")

#ignored - bash get_fixed_lines.sh Lang 37 .

#if os.environ.get("D4J_HOME") is None or os.environ.get("GZOLTAR_JAR") is None or os.environ.get("SLOC_HOME"):
#    sys.exit('Error! Please set D4J_HOME, GZOLTAR_JAR and SLOC_HOME')

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

defect_dir = os.path.join(project_dir,defect_id)
target_dir = os.path.join(defect_dir,"target")

if not os.path.exists(os.path.join(project_dir,defect_id)):
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

    compile_command="mvn compile"

    package_command="mvn -Dmaven.test.failure.ignore=true install"

    os.environ[JAVA_HOME]=java6_home
    os.chdir(defect_dir)
    print("Running " + compile_command)
    os.system(compile_command)
    print("Running " + package_command)
    os.system(package_command)

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

    

os.environ[JAVA_HOME]=java8_home
os.chdir(cwd)
if not os.path.exists("./javaslicer"):
    os.system("git clone https://github.com/hammacher/javaslicer")
    os.chdir("./javaslicer")
    os.system("bash assemble.sh")
    
tracer_dir = os.path.join(cwd,"javaslicer","assembly")

os.chdir(cwd)
if not os.path.exists("./tacoco"):
    os.system("git clone https://github.com/inf295uci-2015/primitive-hamcrest.git")
    os.chdir("primitive-hamcrest")
    os.system("mvn test")
    os.system("mvn install")
    os.chdir(cwd    )
    os.system("git clone https://github.com/jithinjohn7/tacoco.git")
    os.chdir("./tacoco")
    os.system("mvn compile")

tacoco_dir=os.path.join(cwd,"tacoco")

# os.system("cp "+os.path.join(cwd,"javaslicer","assembly","*.jar")+" "+target_dir    )


grep_tests_list=[]
kill_count=0

gzoltars_dir=os.path.join(root_directory,"gzoltars",project_id,defect_id)

relevant_class=""

with open(os.path.join(gzoltars_dir,"spectra")) as f:
    relevant_class=f.read().splitlines()[0].split("#")[0]

print(relevant_class)


os.chdir(tacoco_dir)
# tacoco_command_1="mvn -q exec:java -Plauncher -Dtacoco.sut="+defect_dir + " -Danalyzer.opts=configs/tacoco-analyzer.config"
# print("Running command "+ tacoco_command_1)
# os.system(tacoco_command_1)


#Read cov-matrix.json and find out activating tests

cov_matrix_fileName = defect_id + "-cov-matrix.json"
cov_matrix_filePath = os.path.join(tacoco_dir,"tacoco_output",cov_matrix_fileName)

tacoco_result_dir=os.path.join(root_directory,"tacocos")

tacoco_command = "bash " + os.path.join(cwd,"tacoco","scripts","run-tacoco")+" " + defect_dir + " " + tacoco_dir


if not os.path.exists(os.path.join(tacoco_result_dir,project_id)):
    os.makedirs(os.path.join(tacoco_result_dir,project_id))

# If tacoco result exist then don't run again
if not os.path.exists(os.path.join(tacoco_result_dir,project_id,cov_matrix_fileName)):
    print("Running command "+ tacoco_command)
    os.system(tacoco_command)
    os.rename(cov_matrix_filePath,os.path.join(tacoco_result_dir,project_id,cov_matrix_fileName))

cov_matrix_filePath=os.path.join(tacoco_result_dir,project_id,cov_matrix_fileName)


# Using Slice File


#print(column_numbers)

cov_matrix = []
start,end = 0,0
activating_tests = []
masterTestsList = []

def extractClassAndTestName(s):
    testName,testClass = s.split('(')
    testClass = testClass.split(')')
    testFailure=False
    if testClass[-1] == "_F":
        testFailure=True
    testClass=testClass[0]
    return [testClass,testName,testFailure]

def extractTestInfoAndIndexes(element):
    masterIndex = activating_tests.index(element)
    ClassName = extractClassAndTestName(element)
    return ClassName + [masterIndex]


with open(cov_matrix_filePath,'r') as f:
    datastore = json.load(f)
    masterTestsList = datastore['testsIndex']
    masterTestsList = list(map(str,masterTestsList))
    relevant = relevant_class.split('.')
    javaFilePath = '/'.join(relevant) + '.java'
    activating_tests_sequence = 0 
    for i in range(len(datastore['sources'])):
        if str(datastore['sources'][i]['source']['fullName']) == javaFilePath:
            activating_tests_sequence = i
            cov_matrix = datastore['sources'][i]['testStmtMatrix']
            start = datastore['sources'][i]['source']['firstLine']
            
            print(i)
            print("^^^^^^^^^^^^^^^^^^^^^^^^^^^^")
            end = datastore['sources'][i]['source']['lastLine']
    
            break

    activating_tests_indexes = datastore['sources'][activating_tests_sequence]['activatingTests']
    activating_tests = list(map(masterTestsList.__getitem__,activating_tests_indexes))



def extractTest(s):
    testName,testClass = s.split('(')
    testClass = testClass.split(')')[0]
    return [testClass,testName]

activating_tests = list(map(extractTestInfoAndIndexes,activating_tests))


#print(len(activating_tests))
print(activating_tests)

os.chdir(os.path.join(cwd,"src"))
if not os.path.exists(os.path.join(root_directory,"traces",project_id,defect_id)):
    os.makedirs(os.path.join(root_directory,"traces",project_id,defect_id))
traces_dir = os.path.join(root_directory,"traces",project_id,defect_id)
count=0


tracer_commands=[]
for test in activating_tests:
    testclass=test[0]
    testname=test[1]
    if os.path.exists(os.path.join(traces_dir,"trace."+testclass+"#"+testname)):
        # print("Skipping! Tracer output already exists for "+testclass+"#"+testname)
        continue
    tracer_command="java -cp "+ ":".join(class_path) + " -javaagent:"+ \
    os.path.join(tracer_dir,"tracer.jar")+"=tracefile:"+ \
    os.path.join(traces_dir,"trace."+testclass+"#"+testname)+ \
    " InvokeTests "+defect_dir+" runTestCase " + testclass + " " + testname
    tracer_commands.append(tracer_command)
    print("Preparing command "+tracer_command)
    
max_workers = 4  # no more than 2 concurrent processes
processes = (Popen(cmd, shell=True) for cmd in tracer_commands)
running_processes = list(islice(processes, max_workers))  # start new processes
while running_processes:
    for i, process in enumerate(running_processes):
        if process.poll() is not None:  # the process has finished
            running_processes[i] = next(processes, None)  # start new process
            if running_processes[i] is None: # no new processes
                del running_processes[i]
                break
    

slicer_commands=[]
os.chdir(os.path.join(cwd,"src"))
# print("GREP LIST")
# print(grep_tests_list)
for test in activating_tests:
    testclass=test[0]
    testname=test[1]
    if os.path.exists(os.path.join(traces_dir,"trace."+testclass+"#"+testname+".slice")):
        # print("Skipping! Slicer output already exists for "+testclass+"#"+testname)
        continue
    assert_list_command="java -cp "+ ":".join(class_path) +  \
    " InvokeTests "+defect_dir+" getAssertLines " + testclass + " " + testname
    # print("Running "+assert_list_command)
    assert_list = subprocess.run(assert_list_command,stdout=subprocess.PIPE,shell=True)
    assert_list = assert_list.stdout.decode("utf-8")
    assert_list = assert_list.splitlines()
    slicing_criteria=[]
    for line in assert_list:
        slicing_criteria+=[testclass+"."+testname+":"+line+":*"]
    slice_command="java -Xmx2g -jar "+os.path.join(tracer_dir,"slicer.jar")+" -p "+ \
        os.path.join(traces_dir,"trace."+testclass+"#"+testname) +  \
        " " + ",".join(slicing_criteria) + \
        " > " + os.path.join(traces_dir,"trace."+testclass+"#"+testname+".slice")
    print("Preparing "+slice_command)
    slicer_commands.append(slice_command)
    # os.system(slice_command)
    # coverage_line_grep_command= "grep \"" + relevant_class  + "\\.\" " + os.path.join(traces_dir,"trace."+testclass+"#"+testname+".slice")

max_workers = 4  # no more than 2 concurrent processes
processes = (Popen(cmd, shell=True) for cmd in slicer_commands)
running_processes = list(islice(processes, max_workers))  # start new processes
while running_processes:
    for i, process in enumerate(running_processes):
        if process.poll() is not None:  # the process has finished
            running_processes[i] = next(processes, None)  # start new process
            print(running_processes[i])
            if running_processes[i] is None: # no new processes
                del running_processes[i]
                break


summary_file = open(os.path.join(tacoco_result_dir,project_id,defect_id+"-slicing.summary"),"w")

print(len(cov_matrix),len(cov_matrix[0]))
suspic_dict={}
totalPassed=0
totalFailed=0

with open(os.path.join(tacoco_result_dir,project_id,defect_id+"-old-cov-matrix.json"),"w") as out:
    json.dump(cov_matrix,out)

old_cov_matrix=copy.deepcopy(cov_matrix)

for test in activating_tests:
    testclass=test[0]
    testname=test[1]
    testFailure=test[2]
    row_number = test[3]
    if testFailure is False:
        totalPassed+=1
    else:
        totalFailed+=1
    slice_file = os.path.join(traces_dir,"trace."+testclass+"#"+testname+".slice")
    column_numbers = []
    with open(slice_file,'r') as f:
        text = f.read()
        lines = text.splitlines()
        for line in lines:
            if line[:36] == relevant_class+".":
                test,number = line.split(':')
                number = number.split(' ')[0]
                column_numbers.append(number)
    column_numbers = list(map(int,column_numbers))

    column_numbers = list(set(column_numbers))
    # print(column_numbers)
    new_count = len(column_numbers)
    old_count = cov_matrix[row_number].count(True)
    summary_file.write(testclass+"#"+testname+" Diff: "+ str(old_count-new_count)  +" Old Count: "+str(old_count)+" New Count: "+str(new_count)+"\n")
    if len(column_numbers) > 0:
        cov_matrix[row_number][:] = [False]*len(cov_matrix[row_number])
    for col in column_numbers:
        try:
            adj_col = col - start
            cov_matrix[row_number][adj_col] = True
            
            # return_msg = "changed " + str(row_number) + " " + str(col)
            # print(row_number,col)
            # print(return_msg)
        except:
            print("ERROR: rwo: " + str(row_number)+" col: " + str(col))

    for col in range(len(cov_matrix[row_number])):

        adj_col = col + start

        if cov_matrix[row_number][col] is True:
            if adj_col not in suspic_dict:
                suspic_dict[adj_col]={"failed":0.0,"passed":0.0,"oldfailed":0.0,"oldpassed":0.0}
            if testFailure is True:
                suspic_dict[adj_col]["failed"]+=1
            else:
                suspic_dict[adj_col]["passed"]+=1

        if old_cov_matrix[row_number][col] is True:
            if adj_col not in suspic_dict:
                suspic_dict[adj_col]={"failed":0.0,"passed":0.0,"oldfailed":0.0,"oldpassed":0.0}
            if testFailure is True:
                suspic_dict[adj_col]["oldfailed"]+=1
            else:
                suspic_dict[adj_col]["oldpassed"]+=1
    




# print(cov_matrix)
with open(os.path.join(tacoco_result_dir,project_id,defect_id+"-updated-cov-matrix.json"),"w") as out:
    json.dump(cov_matrix,out)

summary_file.close()

f = sorted(suspic_dict)
print("Total Failed: "+str(totalFailed))
print("Total Passed: "+str(totalPassed))

tarantula_score_file = open(os.path.join(tacoco_result_dir,project_id,defect_id+"-"+relevant_class+"-tarantula.score"),"w")
for key in f:
    try:
        suspic_dict[key]["score"]=(suspic_dict[key]["failed"]/totalFailed)/((suspic_dict[key]["passed"]/totalPassed)+(suspic_dict[key]["failed"]/totalFailed))
    except ZeroDivisionError:
        # print("ERROR: passed: "+ str(suspic_dict[key]["passed"])+" failed: "+str(suspic_dict[key]["failed"]))
        suspic_dict[key]["score"]=0.0

    suspic_dict[key]["oldscore"]=(suspic_dict[key]["oldfailed"]/totalFailed)/((suspic_dict[key]["oldpassed"]/totalPassed)+(suspic_dict[key]["oldfailed"]/totalFailed))
    tarantula_score_file.write(relevant_class+"#"+str(key)+","+str(suspic_dict[key]["score"])+","+str(suspic_dict[key]["oldscore"])+"\n")
tarantula_score_file.close()

ochiai_score_file = open(os.path.join(tacoco_result_dir,project_id,defect_id+"-"+relevant_class+"-ochiai.score"),"w")
for key in f:
    try:
        suspic_dict[key]["score"]=(suspic_dict[key]["failed"])/math.sqrt(totalFailed*(suspic_dict[key]["failed"]+suspic_dict[key]["passed"]))
    except ZeroDivisionError:
        # print("ERROR: passed: "+ str(suspic_dict[key]["passed"])+" failed: "+str(suspic_dict[key]["failed"]))
        suspic_dict[key]["score"]=0.0

    suspic_dict[key]["oldscore"]=(suspic_dict[key]["oldfailed"])/math.sqrt(totalFailed*(suspic_dict[key]["oldfailed"]+suspic_dict[key]["oldpassed"]))
    ochiai_score_file.write(relevant_class+"#"+str(key)+","+str(suspic_dict[key]["score"])+","+str(suspic_dict[key]["oldscore"])+"\n")
ochiai_score_file.close()


sbi_score_file = open(os.path.join(tacoco_result_dir,project_id,defect_id+"-"+relevant_class+"-sbi.score"),"w")
for key in f:
    try:
        suspic_dict[key]["score"]=(suspic_dict[key]["failed"])/totalFailed
    except ZeroDivisionError:
        # print("ERROR: passed: "+ str(suspic_dict[key]["passed"])+" failed: "+str(suspic_dict[key]["failed"]))
        suspic_dict[key]["score"]=0.0

    suspic_dict[key]["oldscore"]=(suspic_dict[key]["oldfailed"])/totalFailed
    sbi_score_file.write(relevant_class+"#"+str(key)+","+str(suspic_dict[key]["score"])+","+str(suspic_dict[key]["oldscore"])+"\n")
sbi_score_file.close()


jaccard_score_file = open(os.path.join(tacoco_result_dir,project_id,defect_id+"-"+relevant_class+"-jaccard.score"),"w")
for key in f:
    try:
        suspic_dict[key]["score"]=(suspic_dict[key]["failed"])/(totalFailed+suspic_dict[key]["passed"])
    except ZeroDivisionError:
        # print("ERROR: passed: "+ str(suspic_dict[key]["passed"])+" failed: "+str(suspic_dict[key]["failed"]))
        suspic_dict[key]["score"]=0.0

    suspic_dict[key]["oldscore"]=(suspic_dict[key]["oldfailed"])/(totalFailed+suspic_dict[key]["oldpassed"])
    jaccard_score_file.write(relevant_class+"#"+str(key)+","+str(suspic_dict[key]["score"])+","+str(suspic_dict[key]["oldscore"])+"\n")
jaccard_score_file.close()


ochiai2_score_file = open(os.path.join(tacoco_result_dir,project_id,defect_id+"-"+relevant_class+"-ochiai2.score"),"w")
for key in f:
    try:
        suspic_dict[key]["score"]=(suspic_dict[key]["failed"] * (totalPassed-suspic_dict[key]["passed"]))/math.sqrt(((totalFailed-suspic_dict[key]["failed"])+totalPassed-suspic_dict[key]["passed"])*(suspic_dict[key]["failed"]+suspic_dict[key]["passed"]) * (totalFailed) * totalPassed)
    except ZeroDivisionError:
        # print("ERROR: passed: "+ str(suspic_dict[key]["passed"])+" failed: "+str(suspic_dict[key]["failed"]))
        suspic_dict[key]["score"]=0.0

    suspic_dict[key]["oldscore"]=(suspic_dict[key]["oldfailed"] * (totalPassed-suspic_dict[key]["oldpassed"]))/math.sqrt(((totalFailed-suspic_dict[key]["oldfailed"])+totalPassed-suspic_dict[key]["oldpassed"])*(suspic_dict[key]["oldfailed"]+suspic_dict[key]["oldpassed"]) * (totalFailed) * totalPassed)
    ochiai2_score_file.write(relevant_class+"#"+str(key)+","+str(suspic_dict[key]["score"])+","+str(suspic_dict[key]["oldscore"])+"\n")
ochiai2_score_file.close()


kulczynski2_score_file = open(os.path.join(tacoco_result_dir,project_id,defect_id+"-"+relevant_class+"-kulczynski2.score"),"w")
for key in f:
    try:
        suspic_dict[key]["score"]=0.5 * ((suspic_dict[key]["failed"] / totalFailed) + (suspic_dict[key]["failed"]/ (suspic_dict[key]["failed"]+suspic_dict[key]["passed"])))
    except ZeroDivisionError:
        # print("ERROR: passed: "+ str(suspic_dict[key]["passed"])+" failed: "+str(suspic_dict[key]["failed"]))
        suspic_dict[key]["score"]=0.0

    suspic_dict[key]["oldscore"]=0.5 * ((suspic_dict[key]["oldfailed"] / totalFailed) + (suspic_dict[key]["oldfailed"]/ (suspic_dict[key]["oldfailed"]+suspic_dict[key]["oldpassed"])))
    kulczynski2_score_file.write(relevant_class+"#"+str(key)+","+str(suspic_dict[key]["score"])+","+str(suspic_dict[key]["oldscore"])+"\n")
kulczynski2_score_file.close()