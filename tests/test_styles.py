import unittest
import styles

class TestStyles(unittest.TestCase):
    def test_pill_template(self):
        qss = styles.get_capsule_style(shape_template="pill")
        self.assertIn("border-radius: 9999px;", qss)
        self.assertIn("CentralCapsule", qss)

    def test_badge_template(self):
        qss = styles.get_capsule_style(shape_template="badge")
        self.assertIn("border-radius:", qss)
        self.assertNotIn("9999px", qss)

    def test_rounded_template(self):
        qss = styles.get_capsule_style(shape_template="rounded")
        self.assertIn("border-radius:", qss)
        self.assertNotIn("9999px", qss)

    def test_text_only_template(self):
        qss = styles.get_capsule_style(shape_template="text_only")
        self.assertIn("border: none;", qss)
        self.assertIn("background-color: transparent;", qss)
        self.assertIn("border-radius: 0px;", qss)

    def test_zero_opacity_produces_transparent_background_and_no_border(self):
        qss = styles.get_capsule_style(opacity=0.0)
        self.assertIn("border: none;", qss)
        self.assertIn("background-color: transparent;", qss)

    def test_taskbar_pill_style(self):
        qss = styles.get_taskbar_style(shape_template="pill")
        self.assertIn("border-radius: 9999px;", qss)
        self.assertIn("CentralTaskbar", qss)

    def test_taskbar_text_only(self):
        qss = styles.get_taskbar_style(shape_template="text_only")
        self.assertIn("border: none;", qss)
        self.assertIn("background-color: transparent;", qss)

if __name__ == "__main__":
    unittest.main()
