import unittest
from backup import Config
from unittest.mock import mock_open, patch


class TestConfig(unittest.TestCase):
    def test_mock(self):
        data = """test"""
        with patch("builtins.open", mock_open(read_data=data)):
            with open(".env") as f:
                d = "".join(f.readlines())
                self.assertEqual(d, data)

    def test_simple_config(self):
        data = """
        PROJECT_IDS="project1"
        EMAIL="test@gmail.com"
        PASSWORD="test"
        """
        with patch("builtins.open", mock_open(read_data=data)):
            config = Config()
            self.assertEqual(config.project_ids, {"project1"})
            self.assertEqual(config.email, "test@gmail.com")
            self.assertEqual(config.password, "test")

    def test_config_handles_white_spaces(self):
        data = """
         PROJECT_IDS = "project1"     
           EMAIL = "test@gmail.com"   
          PASSWORD =  "test"   
        """
        with patch("builtins.open", mock_open(read_data=data)):
            config = Config()
            self.assertEqual(config.project_ids, {"project1"})
            self.assertEqual(config.email, "test@gmail.com")
            self.assertEqual(config.password, "test")

    def test_config_handles_comments(self):
        data = """
        PROJECT_IDS="project1"#comment
        EMAIL="test@gmail.com"  # comment
        PASSWORD="test" # comment
        """
        with patch("builtins.open", mock_open(read_data=data)):
            config = Config()
            self.assertEqual(config.project_ids, {"project1"})
            self.assertEqual(config.email, "test@gmail.com")
            self.assertEqual(config.password, "test")

    def test_config_handles_white_spaces_and_comments(self):
        data = """
         PROJECT_IDS = "project1"#comment     
           EMAIL = "test@gmail.com"   #comment
          PASSWORD =  "test"   #comment
        """
        with patch("builtins.open", mock_open(read_data=data)):
            config = Config()
            self.assertEqual(config.project_ids, {"project1"})
            self.assertEqual(config.email, "test@gmail.com")
            self.assertEqual(config.password, "test")

    def test_config_handles_multiple_projects(self):
        data = """
        PROJECT_IDS="project1,project2"
        EMAIL="test@gmail.com"
        PASSWORD="test"
        """
        with patch("builtins.open", mock_open(read_data=data)):
            config = Config()
            self.assertEqual(config.project_ids, {"project1", "project2"})
            self.assertEqual(config.email, "test@gmail.com")
            self.assertEqual(config.password, "test")

    def test_config_ignore_invalid_keys(self):
        data = """
        PROJECT_IDS="project1"
        EMAIL="test@gmail.com"
        PASSWORD="test"
        INVALID="invalid"
        INVALID2=12345"testTest"12345
        """
        with patch("builtins.open", mock_open(read_data=data)):
            config = Config()
            self.assertEqual(config.project_ids, {"project1"})
            self.assertEqual(config.email, "test@gmail.com")
            self.assertEqual(config.password, "test")

    def test_config_handles_all_valid_characters(self):
        data = """
        PROJECT_IDS="az0123456789"
        EMAIL="tEsT@gmail.com"
        PASSWORD="azAZ0123456789@#$%^&+=* "
        """
        with patch("builtins.open", mock_open(read_data=data)):
            config = Config()
            self.assertEqual(config.project_ids, {"az0123456789"})
            self.assertEqual(config.email, "tEsT@gmail.com")
            self.assertEqual(config.password, "azAZ0123456789@#$%^&+=* ")

    def test_config_fails_if_email_invalid(self):
        data = """
        PROJECT_IDS="test"
        PASSWORD="test"
        EMAIL=
        EMAIL=""
        EMAIL="???@gmail.com"
        EMAIL=" @gmail.com"
        """
        with patch("builtins.open", mock_open(read_data=data)):
            self.assertRaises(AssertionError, Config)

    def test_config_fails_if_password_invalid(self):
        data = """
        PROJECT_IDS="test"
        EMAIL="test"
        PASSWORD=""
        PASSWORD=
        PASSWORD="???"
        """
        with patch("builtins.open", mock_open(read_data=data)):
            self.assertRaises(AssertionError, Config)


if __name__ == "__main__":
    unittest.main()
