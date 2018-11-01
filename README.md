# FaultLocalizationResearch



For Mac

Step 1: Set up Defects4J
    
    Refer https://github.com/rjust/defects4j
    Clone the repository
    Follow documentation steps
      Error:Can't Locate DBI.pm 
      Resolution: perl -MCPAN -e 'install DBI'
                    Install Postgres if required.
        
Step 2: Clone the repo https://bitbucket.org/rjust/fault-localization-data/overview

Step 3: Download and install JDK 1.6 and JDK 1.8.

Step 4: Set evnironment variables
    
    The path of defects4j installed in step 1
      export D4J_HOME=/Users/{username}/Downloads/defects4j
    
    The path to this root directory of the cloned repo fault-localization-data and append 'gzoltar/gzoltar.jar'
      export GZOLTAR_JAR=/Users/{username}/Downloads/fault-localization-data/gzoltar/gzoltar.jar 
    
    Set JAVA_HOME to point to JDK1.6 Home if you have a different Java default version
      export JAVA_HOME=/Library/Java/JavaVirtualMachines/1.6.0.jdk/Contents/Home
      
    Add to PATH variable
      export PATH=$PATH:$D4J_HOME/framework/bin


Step 6:
    Replace the run_gzoltar.sh provided in this repository in fault-localization-data/gzoltar/gzoltar

Step 5: Test if set up works
    
    Test defects4j
    
        defects4j info -p Lang
        
    Test Gzoltar 
    
        `bash run_gzoltar.sh Lang 37 . developer`

