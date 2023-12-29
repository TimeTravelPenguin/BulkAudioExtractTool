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
