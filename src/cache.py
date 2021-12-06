import subprocess
import os


def get_ccn_difference_value(sha):
    # Parse the branch name
    # import pdb
    # pdb.set_trace()
    k =subprocess.check_output("git branch".split()).decode("utf-8").split("\n")

    branch_name = ""
    for l in k:
        if "*" in l:
            branch_name = l

    branch_name = branch_name.split("*")[1].strip()

    # Checkout the branch
    os.system("git checkout "+sha)

    # Rollback to the given commit
    # subprocess.check_output("git reset --hard {}".format(sha).split())
    
    # Run lizard and extract ccn
    op = subprocess.check_output("lizard ./".split())
    op = op.strip().decode('utf-8')


    temp = op.splitlines()[-1:]
    temp = temp[0].split(" ")
    final_list = []
    for i in range(len(temp)):
        if temp[i]:
            final_list.append(temp[i])
    final_ccn_1 = final_list[2]

    # Rollback to previous sha from head and run lizard to extract ccn
    subprocess.check_output("git checkout HEAD~2".split())
    op_1 = subprocess.check_output("lizard ./".split())
    op_1 = op_1.strip().decode('utf-8')
    #print(op_1)
    temp_1 = op_1.splitlines()[-1:]
    temp_1 = temp_1[0].split(" ")
    final_list = []
    for i in range(len(temp_1)):
        if temp[i]:
            final_list.append(temp_1[i])
    final_ccn_2 = final_list[2]


    _ = subprocess.check_output("git checkout {}".format(branch_name).split())

    return float(final_ccn_1) - float(final_ccn_2)
