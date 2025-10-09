from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from lcc.detection.java import MavenDetector


POM_XML = """
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
  <modelVersion>4.0.0</modelVersion>
  <groupId>com.example</groupId>
  <artifactId>demo</artifactId>
  <version>1.0.0</version>
  <dependencies>
    <dependency>
      <groupId>org.springframework</groupId>
      <artifactId>spring-core</artifactId>
      <version>5.3.0</version>
    </dependency>
  </dependencies>
  <dependencyManagement>
    <dependencies>
      <dependency>
        <groupId>org.junit.jupiter</groupId>
        <artifactId>junit-jupiter</artifactId>
        <version>5.10.0</version>
      </dependency>
    </dependencies>
  </dependencyManagement>
</project>
"""


class MavenDetectorTests(unittest.TestCase):
    def test_parses_dependencies(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            (root / "pom.xml").write_text(POM_XML, encoding="utf-8")
            detector = MavenDetector()

            components = detector.discover(root)
            names = {component.name for component in components}

            self.assertIn("com.example:demo", names)
            self.assertIn("org.springframework:spring-core", names)
            self.assertIn("org.junit.jupiter:junit-jupiter", names)


if __name__ == "__main__":
    unittest.main()
