import re
from re import Pattern

from pydantic import BaseModel, ConfigDict, DirectoryPath, Field, field_validator
from typing_extensions import Annotated

file_type_pattern = re.compile(r"^\.?(\w+)$")


class AppVersion:
    def __init__(
        self,
        major,
        minor=None,
        patch=None,
        prerelease=None,
        build=None,
    ) -> None:
        self.major = major
        self.minor = minor or "0"
        self.patch = patch or "0"
        self.prerelease = prerelease
        self.build = build

    def __repr__(self) -> str:
        prerelease = f"-{self.prerelease}" if self.prerelease else ""
        build = f"+{self.build}" if self.build else ""
        return f"{self.major}.{self.minor}.{self.patch}{prerelease}{build}"


class InputFilters(BaseModel):
    include: Pattern | None = Field(...)
    exclude: Pattern | None = Field(...)

    @field_validator("include", mode="before")
    @classmethod
    def validate_include_nonempty(cls, v: str):
        if not v or not str.strip(v):
            return ".*"
        return v

    @field_validator("exclude", mode="before")
    @classmethod
    def validate_exclude_nonempty(cls, v: str):
        if not v or not str.strip(v):
            return None
        return v

    @field_validator("include", "exclude", mode="before")
    @classmethod
    def compile_to_pattern(cls, v: str):
        if not v:
            return None
        if isinstance(v, str):
            return re.compile(v)
        else:
            return v


class OutputConfigurationOptions(BaseModel):
    output_streams_separately: bool = Field(...)
    overwrite_existing: bool = Field(...)
    no_output_subdirs: bool = Field(...)
    acodec: str = Field(...)
    fallback_sample_rate: Annotated[int, Field(gt=0)] = Field(...)
    file_type: str = Field(...)

    @field_validator("file_type", mode="before")
    @classmethod
    def validate_file_type(cls, v: str):
        matched = file_type_pattern.match(v)
        if matched:
            return matched.group(1)
        raise ValueError(f"Invalid file type: {v}")


class DebugOptions(BaseModel):
    logging: bool = Field(...)
    dry_run: bool = Field(...)
    trim: Annotated[int, Field(gt=0)] | None = Field(...)
    print_args: bool = Field(...)
    show_ffmpeg_cmd: bool = Field(...)


class AppArgs(BaseModel):
    """Application commandline arguments.

    Raises:
        ValueError: The provided path is not a directory.

    Returns:
        DirectoryPath: Validated directory path.
    """

    model_config = ConfigDict(frozen=True, from_attributes=True)

    input_dir: DirectoryPath = Field(...)
    output_dir: DirectoryPath = Field(...)
    input_filters: InputFilters = Field(...)
    output_configuration: OutputConfigurationOptions = Field(...)
    debug_options: DebugOptions = Field(...)