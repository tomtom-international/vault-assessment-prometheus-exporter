import sys
import argparse
from packaging.version import parse

parser = argparse.ArgumentParser(description="Checks version bump")
parser.add_argument("--current-branch", required=True, type=str, help="Current branch version")
parser.add_argument("--target-branch", type=str, required=True, help="Target branch version")
args = parser.parse_args()

if parse(args.current_branch) > parse(args.target_branch):
    print("SUCCESS: Current branch has higher version")
    sys.exit(0)
print("FAILURE: Current branch has same or lower version.")
sys.exit(1)
