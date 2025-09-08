from dataclasses import dataclass
from typing import Optional, List
import json
from enum import Enum

class BuildConfigEnum(Enum):
    Debug = 1
    Development = 2
    Test = 3
    Shipping = 4

class CookEnum(Enum):
    Full = 1
    Iterative = 2
    Incremental = 3
    Skip = 4

@dataclass
class Platform:
    platformName: str
    platform: str
    architecture: Optional[str] = None
    enabled: bool = False

@dataclass
class PlatformsConfig:
    platforms: List[Platform]

@dataclass
class AdditionalParams:
    platform: str
    params: str

@dataclass
class ProjectConfig:
    # Data from json
    uprojectFullPath: str
    engineDir: str
    buildArchiveDir: str
    waitTimeBeforeREtryingBuildSeconds: int = 5
    retryCount: int = 1
    multiProcessCookEnabled: bool = False
    cookProcessCount: int = 4
    buildCrashReporter: bool = False
    buildForDistribution: bool = False
    additionalParams: List[AdditionalParams] = None

    # Additional generated data
    uprojectName: Optional[str] = None
    logsDir: Optional[str] = None
    fullBuildsDir: Optional[str] = None

@dataclass 
class PackagedBuild:
    platformConfig: Platform
    buildConfig: BuildConfigEnum
    buildCook: CookEnum

@dataclass
class PackagedBuildsToMake:
    builds: List[PackagedBuild]
    killProcesses: Optional[bool] = False

def parse_platforms_config(json_file: dict) -> PlatformsConfig:
    with open(json_file, 'r') as file:
        data = json.load(file)

    platforms = [Platform(**item) for item in data.get("platforms", [])]
    return PlatformsConfig(platforms=platforms)

def parse_project_config(json_file: dict) -> ProjectConfig:
    with open(json_file, 'r') as file:
        data = json.load(file)
    
    additionalParams = [AdditionalParams(**item) for item in data.get("additionalParams", [])]
    return ProjectConfig(
        uprojectFullPath=data["uprojectFullPath"],
        engineDir=data["engineDir"],
        buildArchiveDir=data["buildArchiveDir"],
        waitTimeBeforeREtryingBuildSeconds=data.get("waitTimeBeforeREtryingBuildSeconds", 5),
        retryCount=data.get("retryCount", 1),
        multiProcessCookEnabled=data.get("multiProcessCookEnabled", False),
        cookProcessCount=data.get("cookProcessCount", 4),
        buildCrashReporter=data.get("buildCrashReporter", False),
        buildForDistribution=data.get("buildForDistribution", False),
        additionalParams=additionalParams
    )