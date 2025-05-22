import sys
import pytest

def main():
    args = sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    sys.argv = [__file__] + args
    sys.exit(pytest.main())

if __name__ == "__main__":
    main()
