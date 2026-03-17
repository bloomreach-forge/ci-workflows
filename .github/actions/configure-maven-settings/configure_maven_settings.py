#!/usr/bin/env python3
"""Write ~/.m2/settings.xml with Bloomreach Maven credentials.

Reads credentials from BR_MAVEN_USERNAME and BR_MAVEN_PASSWORD env vars.
Optionally overrides the output path via MAVEN_SETTINGS_PATH.
"""
import html
import os
from pathlib import Path

_SETTINGS_TEMPLATE = """\
<settings xmlns="http://maven.apache.org/SETTINGS/1.0.0"
          xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
          xsi:schemaLocation="http://maven.apache.org/SETTINGS/1.0.0 https://maven.apache.org/xsd/settings-1.0.0.xsd">
  <servers>
    <server><id>bloomreach-maven2</id><username>{u}</username><password>{p}</password></server>
    <server><id>bloomreach-maven2-forge</id><username>{u}</username><password>{p}</password></server>
    <server><id>bloomreach-maven2-enterprise</id><username>{u}</username><password>{p}</password></server>
  </servers>
  <profiles>
    <profile>
      <id>bloomreach-repos</id>
      <activation><activeByDefault>true</activeByDefault></activation>
      <repositories>
        <repository>
          <id>bloomreach-maven2</id>
          <name>Bloomreach Maven 2 Repository</name>
          <url>https://maven.bloomreach.com/repository/maven2/</url>
        </repository>
        <repository>
          <id>bloomreach-maven2-forge</id>
          <name>Bloomreach Maven 2 Forge Repository</name>
          <url>https://maven.bloomreach.com/repository/maven2-forge/</url>
        </repository>
        <repository>
          <id>bloomreach-maven2-enterprise</id>
          <name>Bloomreach Maven 2 Enterprise Repository</name>
          <url>https://maven.bloomreach.com/repository/maven2-enterprise/</url>
        </repository>
      </repositories>
    </profile>
  </profiles>
</settings>
"""


def main() -> None:
    username = os.environ["BR_MAVEN_USERNAME"]
    password = os.environ["BR_MAVEN_PASSWORD"]
    output = Path(
        os.environ.get("MAVEN_SETTINGS_PATH", "~/.m2/settings.xml")
    ).expanduser()

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        _SETTINGS_TEMPLATE.format(u=html.escape(username), p=html.escape(password))
    )
    print(f"Maven settings written to {output}")


if __name__ == "__main__":
    main()
