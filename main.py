import argparse
from UEBuilder.builder import Builder

if __name__ == "__main__":

    # Parse passed in args
    parser = argparse.ArgumentParser(prog='UEBuilder')
    parser.add_argument('-platc', '--platformsConfig', required=True, help='Path to platforms config json file - required')
    parser.add_argument('-projc', '--projectConfig', required=True, help='Path to project config json file - required')
    parser.add_argument('-wb', '--windowsBinaries', action='store_true', help='Should only windows binaries be built')
    args = parser.parse_args()
    
    # Make build
    builder = Builder(args.platformsConfig, args.projectConfig)
    if args.windowsBinaries:
        builder.windows_binaries_build()
    else:
        builder.package_build()