import UEBuilder.build_data as build_data
import UEBuilder.ui as ui
from pathlib import Path
import os
import datetime
import subprocess
import time

class Builder():
    def __init__(self, platforms_config_json, project_config_json):
        super().__init__()

        self.platforms_config_json = platforms_config_json
        self.project_config_json = project_config_json

        self.platforms_config = build_data.parse_platforms_config(platforms_config_json)
        self.project_config = build_data.parse_project_config(project_config_json)

        uproject_path = Path(self.project_config.uprojectFullPath)
        self.project_config.uprojectName = uproject_path.stem

        self.project_config.logsDir =  f"{self.project_config.buildArchiveDir}\\Logs"
        if not os.path.isdir(self.project_config.logsDir):
            os.mkdir(self.project_config.logsDir)

        current_time = datetime.datetime.now()
        self.project_config.fullBuildsDir = f"{self.project_config.buildArchiveDir}\\{current_time.strftime('%Y-%m-%d__%H-%M-%S')}"

        self.RunUAT_path = f"{self.project_config.engineDir}\\Engine\\Build\\BatchFiles\\RunUAT.bat"

    def package_build(self):
        ui.print_project_config(self.project_config, False)

        builds_to_make = ui.packaged_build(self.platforms_config)
        if builds_to_make and builds_to_make.builds:
            os.mkdir(self.project_config.fullBuildsDir)
            for build in builds_to_make.builds:
                self.make_packaged_build(build, builds_to_make.killProcesses)

    def windows_binaries_build(self):
        ui.print_project_config(self.project_config, True)
        build_config = ui.binaries_build()
        if build_config:
            windows_platform = None
            for platform in self.platforms_config.platforms:
                if platform.platform.lower() == "win64":
                    windows_platform = platform

            if not windows_platform:
                ui.print_error(f"No windows config found in {self.platforms_config_json}")
                return

            binaries_build_config = build_data.PackagedBuild(
                platformConfig=windows_platform,
                buildConfig=build_config,
                buildCook=0
            )

            log_file_path = f"{self.project_config.logsDir}\\windows_binaries_only.log"
            with open(log_file_path, "w", encoding='utf-8') as log_file:
                ui.print_separator_line()
                self.build(binaries_build_config ,True ,log_file)
                log_file.close()

    def make_packaged_build(self, build_config: build_data.PackagedBuild, kill_processes: bool):
        log_file_path = f"{self.project_config.logsDir}\\{build_config.platformConfig.platform}.log"
        with open(log_file_path, "w", encoding='utf-8') as log_file:
            current_build_try = 0
            print(f"Making {build_config.platformConfig.platformName} build")
            while current_build_try <= self.project_config.retryCount:
                ui.print_short_separator_line()
                print(f"Build attempt {current_build_try}")

                result = self.build(build_config, False, log_file)
                if not result:
                    current_build_try += 1
                    self.on_build_failed(current_build_try, kill_processes)
                    continue

                if build_config.buildCook != build_data.CookEnum.Skip:
                    result = self.cook(build_config, log_file)
                    if not result:
                        current_build_try += 1
                        self.on_build_failed(current_build_try, kill_processes)
                        continue
                else:
                    ui.print_success(f"{build_config.platformConfig.platformName} skipping cooking")

                result = self.package(build_config, log_file)
                if not result:
                    current_build_try += 1
                    self.on_build_failed(current_build_try, kill_processes)
                    continue

                ui.print_success(f"{build_config.platformConfig.platformName} build succeeded!")
                break
            
            ui.print_separator_line()
            log_file.close()


    def build(self, build_config: build_data.PackagedBuild, binaries_build: bool, log_file):

        build_command = [
            self.RunUAT_path,
            'Turnkey',
            '-command=VerifySdk',
            f"-platform={build_config.platformConfig.platform}",
            '-UpdateIfNeeded',
            f"-project={self.project_config.uprojectFullPath}",
            'BuildCookRun',
            f"-platform={build_config.platformConfig.platform}",
            f"-project={self.project_config.uprojectFullPath}",
            f"-target={self.project_config.uprojectName}",
            f"-clientconfig={build_config.buildConfig.name}",
            '-build',
            '-nocook'
        ]
        if build_config.platformConfig.architecture:
            build_command.append(f"-clientarchitecture={build_config.platformConfig.architecture}")

        self.add_optional_params(build_command, build_config, binaries_build)
        
        print(f"Building {build_config.platformConfig.platformName} binaries...")

        start_time = datetime.datetime.now()
        result = self.run_command(build_command, log_file)
        end_time = datetime.datetime.now()
        time_taken = end_time - start_time
        if result:
            ui.print_success(f"{build_config.platformConfig.platformName} binaries build succeeded! Time taken: {time_taken}")
        else:
            ui.print_error(f"{build_config.platformConfig.platformName} binaries build failed! Time taken: {time_taken}")

        return result

    def cook(self, build_config: build_data.PackagedBuild, log_file):
        build_command = [
            self.RunUAT_path,
            'BuildCookRun',
            f"-project={self.project_config.uprojectFullPath}",
            f"-target={self.project_config.uprojectName}",
            f"-platform={build_config.platformConfig.platform}",
            f"-clientconfig={build_config.buildConfig.name}",
            '-cook',
            '-nop4',
            '-nocompile',
            '-skipstage',
            '-skippak',
            '-unattended'
        ]

        if build_config.buildCook == build_data.CookEnum.Iterative:
            build_command.append('-iterativecooking')
        if build_config.buildCook == build_data.CookEnum.Incremental:
            build_command.append('-cookincremental')

        if self.project_config.multiProcessCookEnabled:
            build_command.append(f"-AdditionalCookerOptions=\"-cookprocesscount={self.project_config.cookProcessCount}\"")

        self.add_optional_params(build_command, build_config, False)

        print(f"Cooking {build_config.platformConfig.platformName} {build_config.buildCook.name}...")

        start_time = datetime.datetime.now()
        result = self.run_command(build_command, log_file)
        end_time = datetime.datetime.now()
        time_taken = end_time - start_time
        if result:
            ui.print_success(f"{build_config.platformConfig.platformName} cook succeeded! Time taken: {time_taken}")
        else:
            ui.print_error(f"{build_config.platformConfig.platformName} cook failed! Time taken: {time_taken}")

        return result

    def package(self, build_config: build_data.PackagedBuild, log_file):
        build_command = [
            self.RunUAT_path,
            'BuildCookRun',
            f"-project={self.project_config.uprojectFullPath}",
            f"-target={self.project_config.uprojectName}",
            f"-platform={build_config.platformConfig.platform}",
            f"-clientconfig={build_config.buildConfig.name}",
            '-nop4',
            '-nocompile',
            '-skipcook',
            '-stage',
            '-pak',
            '-package',
            '-unattended',
            '-prereqs',
            '-iostore',
            '-compressed',
            '-archive',
            f"-archivedirectory={self.project_config.fullBuildsDir}"
        ]

        self.add_optional_params(build_command, build_config, False)

        print(f"Packaging {build_config.platformConfig.platformName}...")

        start_time = datetime.datetime.now()
        result = self.run_command(build_command, log_file)
        end_time = datetime.datetime.now()
        time_taken = end_time - start_time
        if result:
            ui.print_success(f"{build_config.platformConfig.platformName} package succeeded! Time taken: {time_taken}")
        else:
            ui.print_error(f"{build_config.platformConfig.platformName} package failed! Time taken: {time_taken}")

        return result

    def run_command(self, command: list, log_file):
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        for line in process.stdout:
            log_file.flush()
            log_file.write(line)

        process.wait()

        # If returncode is 0 then command finished executing successfully 
        return process.returncode == 0
    
    def add_optional_params(self, build_command: list, build_config: build_data.PackagedBuild, binaries_build: bool):
        if self.project_config.buildCrashReporter:
            build_command.append('-crashreporter')

        if self.project_config.buildForDistribution and not binaries_build:
            build_command.append('-distribution')

        for additional_params in self.project_config.additionalParams:
            if additional_params.platform == build_config.platformConfig.platform:
                build_command.append(additional_params.params)
                break

        return build_command
    
    def on_build_failed(self, current_try: int, kill_processes: bool):
        if current_try > self.project_config.retryCount: 
            return
        
        if kill_processes:
            subprocess.run('taskkill /F /IM MSBuild.exe')
            subprocess.run('taskkill /F /IM dotnet.exe')

        ui.print_short_separator_line()
        print(f"Waiting {self.project_config.waitTimeBeforeREtryingBuildSeconds} seconds before retrying")
        time.sleep(self.project_config.waitTimeBeforeREtryingBuildSeconds)