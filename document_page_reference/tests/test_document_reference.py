# Copyright 2019 Creu Blanca
# Copyright 2025 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from markupsafe import Markup

from odoo.exceptions import ValidationError
from odoo.tests import tagged

from odoo.addons.base.tests.common import BaseCommon


@tagged("post_install", "-at_install")
class TestDocumentReference(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.page_obj = cls.env["document.page"]
        cls.history_obj = cls.env["document.page.history"]
        cls.page1 = cls.page_obj.create(
            {"name": "Test Page 1", "content": Markup("{{r2}}"), "reference": "R1"}
        )
        cls.page2 = cls.page_obj.create(
            {"name": "Test Page 1", "content": Markup("{{r1}}"), "reference": "r2"}
        )

    def test_constraints_duplicate_reference(self):
        """Should raise if reference is not unique (same as another)."""
        with self.assertRaises(ValidationError):
            self.page2.write({"reference": self.page1.reference})

    def test_constraints_invalid_reference(self):
        """Should raise if reference does not match the required pattern."""
        with self.assertRaises(ValidationError):
            self.page2.write({"reference": self.page2.reference + "-02"})

    def test_no_contrains(self):
        self.page1.write({"reference": False})
        self.assertFalse(self.page1.reference)
        self.page2.write({"reference": False})
        self.assertFalse(self.page2.reference)

    def test_check_raw(self):
        self.assertEqual(self.page2.display_name, self.page1.get_raw_content())

    def test_auto_reference(self):
        """Test if reference is proposed when saving a page without one."""
        self.assertEqual(self.page1.reference, "R1")
        new_page = self.page_obj.create(
            {"name": "Test Page with no reference", "content": "some content"}
        )
        self.assertEqual(new_page.reference, "test_page_with_no_reference")
        with self.assertRaises(ValidationError):
            new_page_duplicated_name = self.page_obj.create(
                {
                    "name": "test page with no reference",
                    "content": "<p>this should have an empty reference "
                    "because reference must be unique</p>",
                }
            )
            self.assertFalse(new_page_duplicated_name.reference)

    def test_get_formview_action(self):
        res = self.page1.get_formview_action()
        self.assertEqual(res.get("type"), "ir.actions.act_window")
        self.assertEqual(res.get("res_model"), "document.page")
        self.assertEqual(res.get("res_id"), self.page1.id)
        self.assertEqual(res.get("target"), "current")
        # Check views contains a form view (view_id may vary if overridden)
        views = res.get("views", [])
        self.assertEqual(len(views), 1, "Expected exactly one view")
        self.assertEqual(views[0][1], "form", "Expected a form view")

    def test_compute_content_parsed(self):
        self.page1.content = Markup("<p></p>")
        self.assertEqual(self.page1.content_parsed, Markup("<p></p>"))

    def test_dollar_brace_reference_resolved(self):
        """${ref} syntax should be resolved to links, same as {{ref}}."""
        page = self.page_obj.create(
            {
                "name": "Dollar Ref Page",
                "content": Markup("<p>See ${r2} for details.</p>"),
                "reference": "dollar_test",
            }
        )
        parsed = page.content_parsed
        self.assertIn("<a ", parsed, "Dollar-brace reference not resolved to link")
        self.assertNotIn("${r2}", parsed, "Raw ${r2} token still present in output")

    def test_dollar_brace_unresolved_reference(self):
        """${unknown_ref} should still produce a link (with the code as text)."""
        page = self.page_obj.create(
            {
                "name": "Unresolved Dollar Ref",
                "content": Markup("<p>See ${nonexistent} here.</p>"),
                "reference": "unresolved_test",
            }
        )
        parsed = page.content_parsed
        self.assertIn("<a ", parsed, "Unresolved dollar-brace ref not converted")
        self.assertNotIn(
            "${nonexistent}", parsed, "Raw ${nonexistent} token still present"
        )

    def test_mixed_syntaxes(self):
        """Both {{ref}} and ${ref} in the same content should be resolved."""
        page = self.page_obj.create(
            {
                "name": "Mixed Syntax Page",
                "content": Markup("<p>Link1: {{r2}} and Link2: ${r2}</p>"),
                "reference": "mixed_test",
            }
        )
        parsed = page.content_parsed
        # Both references should be resolved — expect 2 <a> tags
        self.assertEqual(
            parsed.count("<a "), 2, "Expected 2 links but got: %s" % parsed
        )
