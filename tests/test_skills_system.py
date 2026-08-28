import unittest
from app.skills.registry import SkillRegistry

class TestSkillsSystem(unittest.TestCase):
    def setUp(self):
        self.registry = SkillRegistry()

    def test_skills_count(self):
        self.assertGreaterEqual(len(self.registry.SKILLS_METADATA), 28)

    def test_dynamic_keyword_matching(self):
        # React prompt
        react_matches = self.registry.match_relevant_skills("How to optimize React useState hooks and avoid re-renders?")
        self.assertTrue(any(s["id"] == "react" for s in react_matches))

        # Python FastAPI prompt
        py_matches = self.registry.match_relevant_skills("Create an async Python FastAPI backend endpoint with Pydantic")
        self.assertTrue(any(s["id"] == "python" or s["id"] == "backend" for s in py_matches))

        # Security prompt
        sec_matches = self.registry.match_relevant_skills("Ensure JWT authentication security and prevent injection")
        self.assertTrue(any(s["id"] == "security" for s in sec_matches))

    def test_load_skill_content(self):
        content = self.registry.load_skill_content("software-engineering")
        self.assertIsNotNone(content)
        self.assertIn("Purpose", content)
        self.assertIn("Workflow", content)
        self.assertIn("Verification Checklist", content)

if __name__ == "__main__":
    unittest.main()
