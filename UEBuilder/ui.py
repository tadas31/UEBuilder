import UEBuilder.build_data as build_data
import UEBuilder.input_validator as input_validator
from colorama import Fore, Style, init

def print_project_config(project_config: build_data.ProjectConfig, binaries_build: bool):
    print_separator_line()
    print(f"Building project: {project_config.uprojectFullPath}")
    print(f"Using engine:     {project_config.engineDir}")
    print(f"Log files dir:    {project_config.logsDir}")

    if binaries_build == False:
        print(f"Builds dir:       {project_config.fullBuildsDir}")

    print_separator_line()

def print_separator_line():
    print('----------------------------------------------------------------------')

def print_short_separator_line():
    print('---------------------------------')

def print_error(error: str):
    print(Fore.RED + error + Style.RESET_ALL)

def print_success(message: str):
    print(Fore.GREEN + message + Style.RESET_ALL)

def binaries_build():
    print('Making binaries only build')
    print_separator_line()
    print('Select build config:')
    print(
        '[1] - Debug\n'
        '[2] - Development\n'
        '[3] - Test\n'
        '[4] - Shipping'
    )
    build_config = input('')
    if input_validator.is_selected_option_valid(build_config, input_validator.CONFIG_VALID_VALUES):
        return build_data.BuildConfigEnum(int(build_config))
    else:
        return None

def packaged_build(platforms_config: build_data.PlatformsConfig):
    print('Making packaged builds')
    print_separator_line()
    builds_to_make = build_data.PackagedBuildsToMake([])
    for platform in platforms_config.platforms:
        if platform.enabled == False:
            continue

        print(f"Build for {platform.platformName} [y/n]")
        build_for_platform = input('')
        if input_validator.did_user_select_yes(build_for_platform):
            print(
                '[1] - Debug\n'
                '[2] - Development\n'
                '[3] - Test\n'
                '[4] - Shipping'
            )
            build_config = input('')
            if not input_validator.is_selected_option_valid(build_config, input_validator.CONFIG_VALID_VALUES):
                return None
            
            print(
                '[1] - Full cook\n'
                '[2] - Iterative - cook modified files only\n'
                '[3] - Incremental - cook modified files and dependencies -> recommended (added as of UE5.6)\n'
                '[4] - Skip cook'
            )
            build_cook = input('')
            if not input_validator.is_selected_option_valid(build_cook, input_validator.COOK_VALID_VALUES):
                return None
            
            package_build_data = build_data.PackagedBuild(
                platformConfig=platform,
                buildConfig=build_data.BuildConfigEnum(int(build_config)),
                buildCook=build_data.CookEnum(int(build_cook))
            )
            builds_to_make.builds.append(package_build_data)
            print_separator_line()
        else:
            print_separator_line()
    
    kill_processes = input('Kill .NET and MSBuild tasks if build fails before retrying? [y/n]\n')
    builds_to_make.killProcesses = input_validator.did_user_select_yes(kill_processes)
    print_separator_line()
    return builds_to_make