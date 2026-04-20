import pytest
from rsmetacheck.scripts.pitfalls.p010 import (
    extract_license_from_file,
    check_copyright_only_license,
    detect_copyright_only_license
)


class TestExtractLicenseFromFile:
    """Test suite for extract_license_from_file function"""

    @pytest.mark.parametrize("somef_data,expected", [
        # No license key
        ({}, None),

        # license not a list
        ({"license": "MIT"}, None),

        # Empty license list
        ({"license": []}, None),

        # Valid LICENSE file
        (
                {
                    "license": [{
                        "source": "LICENSE",
                        "result": {"value": "MIT License\n\nCopyright (c) 2023 John Doe"}
                    }]
                },
                {"source": "LICENSE", "content": "MIT License\n\nCopyright (c) 2023 John Doe"}
        ),

        # LICENSE.md file
        (
                {
                    "license": [{
                        "source": "LICENSE.md",
                        "result": {"value": "# MIT License"}
                    }]
                },
                {"source": "LICENSE.md", "content": "# MIT License"}
        ),

        # LICENSE.txt file
        (
                {
                    "license": [{
                        "source": "repository/LICENSE.txt",
                        "result": {"value": "License text"}
                    }]
                },
                {"source": "repository/LICENSE.txt", "content": "License text"}
        ),

        # Case insensitive matching
        (
                {
                    "license": [{
                        "source": "license",
                        "result": {"value": "License content"}
                    }]
                },
                {"source": "license", "content": "License content"}
        ),

        # Multiple entries, first non-LICENSE
        (
                {
                    "license": [
                        {
                            "source": "README.md",
                            "result": {"value": "Some text"}
                        },
                        {
                            "source": "LICENSE",
                            "result": {"value": "License text"}
                        }
                    ]
                },
                {"source": "LICENSE", "content": "License text"}
        ),

        # Missing result key
        (
                {
                    "license": [{
                        "source": "LICENSE"
                    }]
                },
                None
        ),

        # Missing value in result
        (
                {
                    "license": [{
                        "source": "LICENSE",
                        "result": {}
                    }]
                },
                None
        ),

        # Non-LICENSE source
        (
                {
                    "license": [{
                        "source": "codemeta.json",
                        "result": {"value": "MIT"}
                    }]
                },
                None
        ),
    ])
    def test_extract_license_scenarios(self, somef_data, expected):
        """Test various license extraction scenarios"""
        result = extract_license_from_file(somef_data)
        assert result == expected


class TestCheckCopyrightOnlyLicense:
    """Test suite for check_copyright_only_license function"""

    @pytest.mark.parametrize("content,expected", [
        # Copyright-only patterns
        (
                "YEAR: 2017\nCOPYRIGHT HOLDER: Adam H. Sparks",
                True
        ),

        (
                "Year: 2020\nCopyright Holder: John Doe\nAuthor: Jane Smith",
                True
        ),

        (
                "Copyright © 2023 Example Corp",
                True
        ),

        (
                "Copyright (C) 2023 Example",
                True
        ),

        (
                "(c) 2023 Author Name",
                True
        ),

        # Full licenses (should return False)
        (
                """MIT License
    
                Copyright (c) 2023 John Doe
    
                Permission is hereby granted, free of charge, to any person obtaining a copy
                of this software and associated documentation files...""",
                False
        ),

        (
                """Copyright 2023 Author
    
                Licensed under the Apache License, Version 2.0""",
                False
        ),

        (
                """Copyright 2023
    
                Redistribution and use in source and binary forms, with or without
                modification, are permitted...""",
                False
        ),

        # Edge cases
        ("", False),
        (None, False),
        ("   ", False),

        # Short content with copyright info
        (
                "Copyright 2023\nAll rights reserved",
                True
        ),

        # Content with license terms
        (
                """YEAR: 2023
                COPYRIGHT HOLDER: Test
    
                Permission is hereby granted, free of charge...""",
                False
        ),

        # Only copyright line
        ("Copyright © 2023 Name", True),

        # Multiple copyright lines but no license
        (
                """Copyright 2020 Author1
                Copyright 2021 Author2
                Copyright 2022 Author3""",
                True
        ),

        # Content with "without restriction" (license term)
        (
                """Copyright 2023 Author
    
                You may use this without restriction""",
                False
        ),

        # Content with "warranty" (license term)
        (
                """Copyright 2023
    
                This software is provided without warranty""",
                False
        ),
    ])
    def test_check_copyright_only_scenarios(self, content, expected):
        """Test various copyright-only detection scenarios"""
        result = check_copyright_only_license(content)
        assert result == expected, f"Failed for content: {content[:50]}..."

    def test_year_pattern_variations(self):
        """Test various year pattern formats"""
        year_patterns = [
            "YEAR: 2023",
            "Year: 2023",
            "year:2023",
            "YEAR : 2023",
            "year  :  2023",
        ]

        for pattern in year_patterns:
            content = f"{pattern}\nCOPYRIGHT HOLDER: Test"
            result = check_copyright_only_license(content)
            assert result is True, f"Failed for pattern: {pattern}"

    def test_copyright_holder_variations(self):
        """Test various copyright holder formats"""
        holder_patterns = [
            "COPYRIGHT HOLDER: Name",
            "Copyright Holder: Name",
            "copyright holder: Name",
            "COPYRIGHT HOLDER:Name",
            "copyright  holder  :  Name",
        ]

        for pattern in holder_patterns:
            content = f"YEAR: 2023\n{pattern}"
            result = check_copyright_only_license(content)
            assert result is True, f"Failed for pattern: {pattern}"

    def test_mit_license_not_copyright_only(self):
        """Test that full MIT license is not detected as copyright-only"""
        mit_license = """MIT License

Copyright (c) 2023 John Doe

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT."""

        result = check_copyright_only_license(mit_license)
        assert result is False

    def test_apache_license_not_copyright_only(self):
        """Test that Apache license is not detected as copyright-only"""
        apache_license = """Copyright 2023 Author Name

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied."""

        result = check_copyright_only_license(apache_license)
        assert result is False

    def test_line_count_threshold(self):
        """Test that short files with copyright are detected"""
        # 5 lines or less with copyright info
        short_copyright = """Copyright 2023
Author Name
All Rights Reserved"""

        result = check_copyright_only_license(short_copyright)
        assert result is True

        # More than 5 lines with copyright should check for license terms
        longer_content = """Copyright 2023
Author Name
Line 3
Line 4
Line 5
Line 6
Line 7"""

        result = check_copyright_only_license(longer_content)
        # Should be True because it has copyright but no license terms
        assert result is True


class TestDetectCopyrightOnlyLicense:
    """Test suite for detect_copyright_only_license function"""

    @pytest.mark.parametrize(
        "somef_data,file_name,expected_has_pitfall,expected_is_copyright_only", [
            # No license data
            (
                    {},
                    "test_repo.json",
                    False,
                    False
            ),

            # Copyright-only license
            (
                    {
                        "license": [{
                            "source": "LICENSE",
                            "result": {"value": "YEAR: 2017\nCOPYRIGHT HOLDER: Adam H. Sparks"}
                        }]
                    },
                    "test_repo.json",
                    True,
                    True
            ),

            # Full MIT license
            (
                    {
                        "license": [{
                            "source": "LICENSE",
                            "result": {
                                "value": """MIT License

Copyright (c) 2023 John Doe

Permission is hereby granted, free of charge..."""
                            }
                        }]
                    },
                    "test_repo.json",
                    False,
                    False
            ),

            # Non-LICENSE source (should not extract)
            (
                    {
                        "license": [{
                            "source": "README.md",
                            "result": {"value": "YEAR: 2017\nCOPYRIGHT HOLDER: Test"}
                        }]
                    },
                    "test_repo.json",
                    False,
                    False
            ),

            # LICENSE.md with copyright only
            (
                    {
                        "license": [{
                            "source": "LICENSE.md",
                            "result": {"value": "Copyright © 2023 Author"}
                        }]
                    },
                    "test_repo.json",
                    True,
                    True
            ),

            # Multiple entries with LICENSE
            (
                    {
                        "license": [
                            {
                                "source": "codemeta.json",
                                "result": {"value": "MIT"}
                            },
                            {
                                "source": "LICENSE",
                                "result": {"value": "YEAR: 2020\nCOPYRIGHT HOLDER: Test"}
                            }
                        ]
                    },
                    "test_repo.json",
                    True,
                    True
            ),
        ])
    def test_detect_copyright_only_scenarios(self, somef_data, file_name,
                                             expected_has_pitfall,
                                             expected_is_copyright_only):
        """Test various copyright-only license detection scenarios"""
        result = detect_copyright_only_license(somef_data, file_name)

        assert result["has_pitfall"] == expected_has_pitfall
        assert result["file_name"] == file_name
        assert result["is_copyright_only"] == expected_is_copyright_only

    def test_result_structure(self):
        """Test that result always has the expected structure"""
        somef_data = {}
        result = detect_copyright_only_license(somef_data, "test.json")

        assert "has_pitfall" in result
        assert "file_name" in result
        assert "license_source" in result
        assert "is_copyright_only" in result

    def test_various_license_file_names(self):
        """Test detection with various LICENSE file name formats"""
        test_files = [
            "LICENSE",
            "LICENSE.md",
            "LICENSE.txt",
            "license",
            "License",
            "repository/LICENSE",
        ]

        copyright_content = "YEAR: 2023\nCOPYRIGHT HOLDER: Test Author"

        for file_name in test_files:
            somef_data = {
                "license": [{
                    "source": file_name,
                    "result": {"value": copyright_content}
                }]
            }

            result = detect_copyright_only_license(somef_data, "test.json")
            assert result["has_pitfall"] is True, f"Failed for file: {file_name}"
            assert result["license_source"] == file_name

    def test_full_license_examples(self):
        """Test that various full licenses are not detected as copyright-only"""
        licenses = {
            "MIT": """MIT License
Copyright (c) 2023 Author
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction...""",

            "Apache": """Copyright 2023 Author
Licensed under the Apache License, Version 2.0
http://www.apache.org/licenses/LICENSE-2.0""",

            "BSD": """Copyright 2023 Author
Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met...""",

            "GPL": """Copyright 2023 Author
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License...""",
        }

        for license_name, license_text in licenses.items():
            somef_data = {
                "license": [{
                    "source": "LICENSE",
                    "result": {"value": license_text}
                }]
            }

            result = detect_copyright_only_license(somef_data, "test.json")
            assert result["has_pitfall"] is False, f"False positive for {license_name}"

    def test_empty_license_content(self):
        """Test handling of empty license content"""
        somef_data = {
            "license": [{
                "source": "LICENSE",
                "result": {"value": ""}
            }]
        }

        result = detect_copyright_only_license(somef_data, "test.json")
        assert result["has_pitfall"] is False

    def test_license_source_populated(self):
        """Test that license_source is populated even when no pitfall"""
        somef_data = {
            "license": [{
                "source": "LICENSE",
                "result": {"value": "MIT License\nPermission is hereby granted..."}
            }]
        }

        result = detect_copyright_only_license(somef_data, "test.json")
        assert result["license_source"] == "LICENSE"
        assert result["has_pitfall"] is False